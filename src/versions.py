"""Cargo-compatible version ranges used by the sparse-index reader."""

import re
from dataclasses import dataclass
from functools import total_ordering

PATTERN = re.compile(
    r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)"
    r"(?:-([0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?"
)


@total_ordering
@dataclass(frozen=True)
class Version:
    """A semantic version, excluding build metadata from comparison."""

    core: tuple[int, int, int]
    prerelease: tuple[str, ...] = ()

    def __lt__(self, other):
        if self.core != other.core:
            return self.core < other.core
        left = tuple((0, int(x)) if x.isdigit() else (1, x)
                     for x in self.prerelease)
        right = tuple((0, int(x)) if x.isdigit() else (1, x)
                      for x in other.prerelease)
        return (not self.prerelease, left) < (not other.prerelease, right)


def version(text):
    """Parse a complete major.minor.patch version."""
    match = PATTERN.fullmatch(text)
    if match is None:
        raise ValueError(f"Invalid semantic version: {text}")
    core = tuple(int(x) for x in match.groups()[:3])
    prerelease = tuple(match.group(4).split(".")) if match.group(4) else ()
    return Version(core, prerelease)


def components(text):
    """Expand partial versions and return their number of fixed components."""
    before, separator, after = text.partition("-")
    fields = before.split(".")
    fixed = []
    for field in fields:
        if field in {"*", "x", "X"}:
            break
        if not field.isdigit():
            raise ValueError(f"Invalid version requirement: {text}")
        fixed.append(int(field))
    if len(fields) > 3 or not fixed:
        raise ValueError(f"Invalid version requirement: {text}")
    core = tuple((fixed + [0, 0, 0])[:3])
    result = Version(core, tuple(after.split(".")) if separator else ())
    return result, len(fixed)


def comparator(candidate, expression):
    """Evaluate one comparator, caret, tilde or wildcard requirement."""
    match = re.fullmatch(r"([~^]|>=|<=|>|<|=)?\s*(.+)", expression.strip())
    if match is None:
        raise ValueError(f"Invalid version requirement: {expression}")
    operator, text = match.groups()
    if text in {"*", "x", "X"}:
        return not candidate.prerelease
    lower, count = components(text.split("+", 1)[0])
    if operator in {">", ">=", "<", "<="}:
        if count < 3 and operator in {">", "<="}:
            upper = next_boundary(lower, count - 1)
            return candidate >= upper if operator == ">" else candidate < upper
        return {
            ">": candidate > lower, ">=": candidate >= lower,
            "<": candidate < lower, "<=": candidate <= lower,
        }[operator]
    if operator == "=":
        return (candidate == lower if count == 3
                else candidate.core[:count] == lower.core[:count])
    if "*" in text or re.search(r"(^|\.)[xX]($|\.)", text):
        return candidate.core[:count] == lower.core[:count]
    pivot = min(count - 1, 1) if operator == "~" else next(
        (i for i, value in enumerate(lower.core[:count]) if value), count - 1
    )
    return lower <= candidate < next_boundary(lower, pivot)


def next_boundary(value, pivot):
    """Advance a range boundary and reset less significant components."""
    fields = list(value.core)
    fields[pivot] += 1
    fields[pivot + 1:] = [0] * (2 - pivot)
    return Version(tuple(fields))


def satisfies(text, requirement):
    """Match a version, applying Cargo's prerelease opt-in rule."""
    candidate = version(text)
    expressions = requirement.split(",")
    if candidate.prerelease:
        explicit = [
            re.sub(r"^[~^<>=\s]+", "", item.strip())
            for item in expressions if "-" in item
        ]
        if not any(components(item)[0].core == candidate.core
                   for item in explicit):
            return False
    return all(comparator(candidate, item) for item in expressions)
