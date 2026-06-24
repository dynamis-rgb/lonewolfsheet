from dataclasses import dataclass
from pathlib import Path
import json

@dataclass(frozen=True)
class AppConfig:
    SaveDirectory: Path

def LoadAppConfig() -> AppConfig:
    ConfigPath = Path("configs") / "appsettings.json"
    DefaultSaveDirectory = Path("sample_data")

    if not ConfigPath.exists():
        return AppConfig(SaveDirectory=DefaultSaveDirectory)

    Data = json.loads(ConfigPath.read_text(encoding="utf-8"))
    RawSaveDirectory = str(Data.get("SaveDirectory", "")).strip()
    if not RawSaveDirectory:
        return AppConfig(SaveDirectory=DefaultSaveDirectory)

    return AppConfig(SaveDirectory=Path(RawSaveDirectory))
