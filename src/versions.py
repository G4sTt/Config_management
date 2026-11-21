"""Cargo-compatible version ranges used by the sparse-index reader."""

import re
from dataclasses import dataclass
from functools import total_ordering

CORE_COMPONENT_COUNT = 3
MINOR_INDEX = 1
WILDCARDS = {"*", "x", "X"}
ORDERED_OPERATORS = {">", ">=", "<", "<="}
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
        """Compare core fields and SemVer prerelease identifier order."""
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
    core = tuple(int(x) for x in match.groups()[:CORE_COMPONENT_COUNT])
    prerelease = tuple(match.group(4).split(".")) if match.group(4) else ()
    return Version(core, prerelease)


def components(text):
    """Expand partial versions and return their number of fixed components."""
    before, separator, after = text.partition("-")
    fields = before.split(".")
    fixed = []
    for field in fields:
        if field in WILDCARDS:
            break
        if not field.isdigit():
            raise ValueError(f"Invalid version requirement: {text}")
        fixed.append(int(field))
    if len(fields) > CORE_COMPONENT_COUNT or not fixed:
        raise ValueError(f"Invalid version requirement: {text}")
    core = tuple((fixed + [0, 0, 0])[:CORE_COMPONENT_COUNT])
    result = Version(core, tuple(after.split(".")) if separator else ())
    return result, len(fixed)


def ordered_comparison(candidate, lower, count, operator):
    """Evaluate relational operators, including partial version bounds."""
    if count < CORE_COMPONENT_COUNT and operator in {">", "<="}:
        upper = next_boundary(lower, count - 1)
        return candidate >= upper if operator == ">" else candidate < upper
    return {
        ">": candidate > lower, ">=": candidate >= lower,
        "<": candidate < lower, "<=": candidate <= lower,
    }[operator]


def compatible_comparison(candidate, lower, count, operator):
    """Evaluate caret or tilde compatibility using an exclusive upper bound."""
    if operator == "~":
        pivot = min(count - 1, MINOR_INDEX)
    else:
        pivot = next(
            (i for i, value in enumerate(lower.core[:count]) if value),
            count - 1,
        )
    return lower <= candidate < next_boundary(lower, pivot)


def comparator(candidate, expression):
    """Dispatch one comparator to its relational or compatibility rule."""
    match = re.fullmatch(r"([~^]|>=|<=|>|<|=)?\s*(.+)", expression.strip())
    if match is None:
        raise ValueError(f"Invalid version requirement: {expression}")
    operator, text = match.groups()
    if text in WILDCARDS:
        return not candidate.prerelease
    lower, count = components(text.split("+", 1)[0])
    if operator in ORDERED_OPERATORS:
        return ordered_comparison(candidate, lower, count, operator)
    if operator == "=" and count == CORE_COMPONENT_COUNT:
        return candidate == lower
    if (operator == "=" or "*" in text
            or re.search(r"(^|\.)[xX]($|\.)", text)):
        return candidate.core[:count] == lower.core[:count]
    return compatible_comparison(candidate, lower, count, operator)


def next_boundary(value, pivot):
    """Advance a range boundary and reset less significant components."""
    fields = list(value.core)
    fields[pivot] += 1
    fields[pivot + 1:] = [0] * (2 - pivot)
    return Version(tuple(fields))


def same_prerelease_core(expression, core):
    """Check whether a requirement explicitly opts into this prerelease core."""
    lower, _ = components(expression)
    return lower.core == core


def satisfies(text, requirement):
    """Match a version, applying Cargo's prerelease opt-in rule."""
    candidate = version(text)
    expressions = requirement.split(",")
    if candidate.prerelease:
        explicit = [
            re.sub(r"^[~^<>=\s]+", "", item.strip())
            for item in expressions if "-" in item
        ]
        if not any(same_prerelease_core(item, candidate.core)
                   for item in explicit):
            return False
    return all(comparator(candidate, item) for item in expressions)
