from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from modules.DomainModels import CharacterSheet


class JsonRepositoryError(Exception):
    pass


class JsonSchemaVersionError(JsonRepositoryError):
    pass


class JsonLoadError(JsonRepositoryError):
    pass


class JsonSaveError(JsonRepositoryError):
    pass


@dataclass(frozen=True)
class JsonRepository:
    SupportedSchemaVersions: tuple[int, ...] = (1,)

    def LoadCharacter(self, FilePath: str | Path) -> CharacterSheet:
        PathObj = Path(FilePath)

        try:
            RawText = PathObj.read_text(encoding="utf-8")
        except OSError as Ex:
            raise JsonLoadError(f"Failed to read file: {PathObj}") from Ex

        try:
            Data = json.loads(RawText)
        except json.JSONDecodeError as Ex:
            raise JsonLoadError(f"Invalid JSON in file: {PathObj}") from Ex

        if not isinstance(Data, dict):
            raise JsonLoadError("Top-level JSON must be an object/dict.")

        SchemaVersion = int(Data.get("SchemaVersion", 0))
        if SchemaVersion not in self.SupportedSchemaVersions:
            raise JsonSchemaVersionError(
                f"Unsupported SchemaVersion: {SchemaVersion}. Supported: {self.SupportedSchemaVersions}"
            )

        try:
            return CharacterSheet.FromDict(Data)
        except (KeyError, TypeError, ValueError) as Ex:
            raise JsonLoadError("JSON structure did not match expected schema.") from Ex

    def SaveCharacter(self, Sheet: CharacterSheet, FilePath: str | Path) -> None:
        PathObj = Path(FilePath)

        Data = Sheet.ToDict()
        SchemaVersion = int(Data.get("SchemaVersion", 0))
        if SchemaVersion not in self.SupportedSchemaVersions:
            raise JsonSchemaVersionError(
                f"Refusing to save unsupported SchemaVersion: {SchemaVersion}. Supported: {self.SupportedSchemaVersions}"
            )

        try:
            JsonText = json.dumps(Data, indent=2, ensure_ascii=False)
        except (TypeError, ValueError) as Ex:
            raise JsonSaveError("Failed to serialize character sheet to JSON.") from Ex

        try:
            PathObj.parent.mkdir(parents=True, exist_ok=True)
            PathObj.write_text(JsonText + "\n", encoding="utf-8")
        except OSError as Ex:
            raise JsonSaveError(f"Failed to write file: {PathObj}") from Ex