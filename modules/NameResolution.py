"""Name matching shared by catalogs and saved inventory names."""

from dataclasses import dataclass
from typing import Iterable, Literal


@dataclass(frozen=True)
class NameResolutionResult:
    Status: Literal["found", "not_found", "ambiguous"]
    Name: str | None = None
    Candidates: tuple[str, ...] = ()


def BuildNameIndex(Names: Iterable[str]) -> dict[str, str]:
    """Index canonical catalog names, rejecting normalized collisions."""
    Index: dict[str, str] = {}
    for Name in Names:
        Key = Name.strip().casefold()
        if not Key or Key in Index:
            raise ValueError(f"Blank or duplicate name: {Name!r}")
        Index[Key] = Name
    return Index


def ResolveName(Query: str, Names: Iterable[str]) -> NameResolutionResult:
    """Match exact names, then prefixes, then substrings; preserve original spelling.

    Repeated identical names count once. Differently spelled names with the same
    normalized form remain ambiguous, allowing callers to select the saved spelling.
    """
    Key = Query.strip().casefold()
    if not Key:
        return NameResolutionResult(Status="not_found")
    Entries = [(Name.strip().casefold(), Name) for Name in dict.fromkeys(Names)]
    Matches = [Name for Normalized, Name in Entries if Normalized == Key]
    if not Matches:
        Matches = [Name for Normalized, Name in Entries if Normalized.startswith(Key)]
    if not Matches:
        Matches = [Name for Normalized, Name in Entries if Key in Normalized]
    if len(Matches) == 1:
        return NameResolutionResult(Status="found", Name=Matches[0])
    if Matches:
        return NameResolutionResult(
            Status="ambiguous", Candidates=tuple(sorted(Matches, key=lambda Name: (Name.casefold(), Name)))
        )
    return NameResolutionResult(Status="not_found")
