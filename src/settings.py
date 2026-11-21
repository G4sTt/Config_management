"""Read and validate the five INI settings of variant 13."""

import configparser
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from versions import version

FIELDS = {"package", "repository", "test_mode", "ascii_tree", "max_depth"}
CRATE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*(?:@[0-9A-Za-z.+-]+)?")
MIN_DEPTH = 0


@dataclass(frozen=True)
class Settings:
    """Validated configuration, with local paths resolved against the INI."""

    package: str
    repository: str
    test_mode: bool
    ascii_tree: bool
    max_depth: int


def validate_local_repository(package, repository, directory):
    """Validate a test package name and resolve its repository file."""
    if re.fullmatch(r"[A-Z]+", package) is None:
        raise ValueError("Test package must use uppercase Latin letters")
    path = directory / repository
    if not repository or not path.is_file():
        raise ValueError("Test repository must be an existing JSON file")
    return str(path.resolve())


def validate_registry(package, repository):
    """Validate the Cargo reference and sparse-index URL."""
    if CRATE.fullmatch(package) is None:
        raise ValueError("Package must be a Cargo name or name@version")
    if "@" in package:
        version(package.split("@", 1)[1])
    url = urlsplit(repository)
    if (url.scheme not in {"https", "http"} or not url.netloc
            or url.query or url.fragment or url.username
            or any(character.isspace() for character in repository)):
        raise ValueError("Repository must be an HTTP(S) sparse-index URL")
    return repository


def validate(values, directory):
    """Validate the selected repository and construct the settings."""
    package = values["package"].strip()
    repository = values["repository"].strip()
    if values["test_mode"]:
        repository = validate_local_repository(package, repository, directory)
    else:
        repository = validate_registry(package, repository)
    if values["max_depth"] < MIN_DEPTH:
        raise ValueError("max_depth must be a nonnegative integer")
    return Settings(
        package, repository.rstrip("/"), values["test_mode"],
        values["ascii_tree"], values["max_depth"],
    )


def load_settings(path):
    """Load an INI file, rejecting absent, unknown and malformed settings."""
    parser = configparser.ConfigParser(interpolation=None)
    try:
        parser.read_string(path.read_text(encoding="utf-8-sig"))
        if parser.sections() != ["analysis"] or parser.defaults():
            raise ValueError("Expected only an [analysis] section")
        section = parser["analysis"]
        if set(section) != FIELDS:
            raise ValueError(
                "Expected keys: package, repository, test_mode, "
                "ascii_tree, max_depth"
            )
        values = dict(section)
        values["test_mode"] = section.getboolean("test_mode")
        values["ascii_tree"] = section.getboolean("ascii_tree")
        values["max_depth"] = section.getint("max_depth")
    except configparser.Error as error:
        raise ValueError(f"Invalid INI: {error}") from error
    return validate(values, path.resolve().parent)
