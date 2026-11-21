"""Read Cargo sparse-index metadata directly using urllib."""

import json
import time
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from versions import satisfies, version

USER_AGENT = "Conf2-CargoGraph-Variant13/1.0 (educational dependency analysis)"
MAX_DOWNLOAD_ATTEMPTS = 3
RETRYABLE_HTTP_CODES = {429, 500, 502, 503, 504}
REVERSE_PAGE_SIZE = 100


def validate_record(record):
    """Check required sparse-index fields before following metadata."""
    if not isinstance(record, dict) or not isinstance(record.get("vers"), str):
        raise ValueError("Registry record must contain a version string")
    version(record["vers"])
    dependencies = record.get("deps")
    if not isinstance(dependencies, list):
        raise ValueError("Registry record must contain a dependency list")
    for dependency in dependencies:
        if (not isinstance(dependency, dict)
                or not isinstance(dependency.get("name"), str)
                or not isinstance(dependency.get("req"), str)):
            raise ValueError("Invalid dependency record")


@dataclass(frozen=True, order=True)
class Package:
    """A package identity including its resolved version."""

    name: str
    release: str

    def __str__(self):
        """Return the package identity used by graph labels."""
        return f"{self.name}@{self.release}"


def download(url):
    """Download UTF-8 data with a timeout and bounded transient retries."""
    last_attempt = MAX_DOWNLOAD_ATTEMPTS - 1
    for attempt in range(MAX_DOWNLOAD_ATTEMPTS):
        try:
            request = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(request, timeout=30) as response:
                return response.read().decode("utf-8")
        except HTTPError as error:
            if (error.code not in RETRYABLE_HTTP_CODES
                    or attempt == last_attempt):
                raise ValueError(f"HTTP {error.code}: {url}") from error
            time.sleep(0.5 * (attempt + 1))
        except (URLError, TimeoutError, UnicodeError) as error:
            raise ValueError(f"Cannot read {url}: {error}") from error


def index_path(name):
    """Return the sparse-index path specified by the Cargo registry format."""
    name = name.lower()
    short_prefixes = {1: "1", 2: "2", 3: f"3/{name[:1]}"}
    prefix = short_prefixes.get(len(name), f"{name[:2]}/{name[2:4]}")
    return f"{prefix}/{name}"


class Registry:
    """Resolve non-optional normal dependencies from sparse-index records."""

    def __init__(self, url, fetch=download):
        """Configure the HTTP source and an initially empty record cache."""
        self.url = url.rstrip("/")
        self.fetch = fetch
        self.cache = {}

    def records(self, name):
        """Fetch all published versions once per crate."""
        if name not in self.cache:
            text = self.fetch(f"{self.url}/{index_path(name)}")
            try:
                records = [json.loads(line) for line in text.splitlines()
                           if line.strip()]
                if not records:
                    raise ValueError("Empty sparse-index response")
                for record in records:
                    validate_record(record)
                self.cache[name] = records
            except (json.JSONDecodeError, TypeError) as error:
                raise ValueError(
                    f"Invalid registry record for {name}"
                ) from error
        return self.cache[name]

    def resolve(self, name, requirement="*"):
        """Select the highest non-yanked version satisfying a requirement."""
        candidates = [
            record for record in self.records(name)
            if not record.get("yanked", False)
            and satisfies(record["vers"], requirement)
        ]
        if not candidates:
            raise ValueError(f"No version of {name} matches {requirement}")
        selected = max(candidates, key=lambda r: version(r["vers"]))
        return Package(name, selected["vers"])

    def root(self, reference):
        """Resolve a configured root name or an exact name@version."""
        name, separator, release = reference.partition("@")
        return self.resolve(name, "=" + release if separator else "*")

    def dependencies(self, package):
        """Return required normal edges, including all target platforms."""
        record = next(r for r in self.records(package.name)
                      if r["vers"] == package.release)
        dependencies = []
        for item in record["deps"]:
            if item.get("optional") or item.get("kind") not in {None, "normal"}:
                continue
            if item.get("registry"):
                raise ValueError(
                    "Dependencies in another registry are unsupported"
                )
            name = item.get("package") or item["name"]
            dependencies.append(self.resolve(name, item["req"]))
        return sorted(set(dependencies))

    def dependents(self, package):
        """Read paginated reverse edges from a crates.io-compatible API."""
        config = json.loads(self.fetch(f"{self.url}/config.json"))
        api = config.get("api")
        if not api:
            raise ValueError("Registry has no reverse-dependency API")
        results = set()
        page = 1
        while True:
            url = (f"{api}/api/v1/crates/{package.name}/reverse_dependencies"
                   f"?page={page}&per_page={REVERSE_PAGE_SIZE}")
            data = json.loads(self.fetch(url))
            items = data["dependencies"]
            versions = {item["id"]: item for item in data["versions"]}
            for item in items:
                if (item.get("optional")
                        or item.get("kind") not in {None, "normal"}
                        or not satisfies(package.release, item["req"])):
                    continue
                dependent = versions[item["version_id"]]
                results.add(Package(dependent["crate"], dependent["num"]))
            if page * REVERSE_PAGE_SIZE >= data["meta"]["total"]:
                break
            page += 1
        return sorted(results)
