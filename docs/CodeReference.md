# LoneWolfSheet Code Reference

## Overview

This project is a Python CLI application for managing a Lone Wolf character sheet, saving it as JSON, and running a simple interactive play session with combat support.

The code is currently organized into these main areas:

- `main_programs/main.py`: program entry point
- `modules/DomainModels.py`: core game data models
- `modules/JsonRepository.py`: JSON load/save layer
- `modules/Cli.py`: command-line interface
- `modules/PlaySession.py`: interactive game session and combat flow
- `modules/RuleBooks1to5.py`: combat results table loader and resolver
- `modules/Validation.py`: placeholder for future validation logic

## Entry Point

### `main_programs/main.py`

python -m main_programs.main show sample_data\firstgame.json     --- shows the contents of the specified play file
python -m main_programs.main play sample_data\firstgame.json     --- plays a game using the specified play file

#### `main() -> int`

Purpose:
Creates the CLI application and runs it with command-line arguments.

Inputs:
- No direct parameters
- Uses `sys.argv[1:]` as the argument list

Outputs:
- Returns an integer process exit code
- `0` for success
- `2` for handled CLI/repository/value errors

Behavior:
- Instantiates `JsonRepository`
- Instantiates `CliApp`
- Delegates execution to `CliApp.Run(...)`

## Domain Models

### `modules/DomainModels.py`

This module contains the core in-memory data structures used by the rest of the application.

### Class: `Endurance`

Purpose:
Represents current and maximum Endurance Points.

Fields:
- `Current: int`
- `Max: int`

#### `Heal(Amount: int) -> None`

Purpose:
Increases current endurance without exceeding `Max`.

Inputs:
- `Amount`: amount to heal

Outputs:
- No return value

Behavior:
- Ignores values `<= 0`
- Caps result at `Max`

#### `TakeDamage(Amount: int) -> None`

Purpose:
Reduces current endurance without going below `0`.

Inputs:
- `Amount`: amount of damage

Outputs:
- No return value

Behavior:
- Ignores values `<= 0`
- Floors result at `0`

#### `ToDict() -> dict[str, int]`

Purpose:
Converts the object into a JSON-serializable dictionary.

Outputs:
- `{"Current": int, "Max": int}`

#### `FromDict(Data: dict[str, Any]) -> Endurance`

Purpose:
Builds an `Endurance` instance from dictionary data.

Inputs:
- `Data`: dictionary containing `Current` and `Max`

Outputs:
- A new `Endurance` object

### Class: `Inventory`

Purpose:
Stores character equipment and carried items.

Fields:
- `Weapons: list[str]`
- `BackpackItems: list[str]`
- `SpecialItems: list[str]`

Rules:
- Weapons are unique
- Special items are unique
- Backpack items may repeat

#### `AddWeapon(Name: str) -> bool`

Inputs:
- `Name`: weapon name

Outputs:
- `True` if added
- `False` if blank or already present

#### `RemoveWeapon(Name: str) -> bool`

Inputs:
- `Name`: weapon name

Outputs:
- `True` if removed
- `False` if not found

#### `AddBackpackItem(Name: str) -> bool`

Inputs:
- `Name`: backpack item name

Outputs:
- `True` if added
- `False` if blank

#### `RemoveBackpackItem(Name: str) -> bool`

Inputs:
- `Name`: backpack item name

Outputs:
- `True` if removed
- `False` if not found

#### `AddSpecialItem(Name: str) -> bool`

Inputs:
- `Name`: special item name

Outputs:
- `True` if added
- `False` if blank or already present

#### `RemoveSpecialItem(Name: str) -> bool`

Inputs:
- `Name`: special item name

Outputs:
- `True` if removed
- `False` if not found

#### `ToDict() -> dict[str, list[str]]`

Outputs:
- Dictionary with `Weapons`, `BackpackItems`, and `SpecialItems`

#### `FromDict(Data: dict[str, Any]) -> Inventory`

Inputs:
- `Data`: inventory dictionary

Outputs:
- A new `Inventory` object

### Class: `CharacterSheet`

Purpose:
Represents the full playable character state.

Fields:
- `Name: str`
- `CombatSkill: int`
- `Endurance: Endurance`
- `KaiRank: str = "Initiate"`
- `KaiDisciplines: list[str]`
- `GoldCrowns: int = 0`
- `CurrentBook: int = 1`
- `Inventory: Inventory`

#### `Heal(Amount: int) -> None`

Purpose:
Delegates healing to the `Endurance` object.

Inputs:
- `Amount`: healing amount

Outputs:
- No return value

#### `TakeDamage(Amount: int) -> None`

Purpose:
Delegates damage to the `Endurance` object.

Inputs:
- `Amount`: damage amount

Outputs:
- No return value

#### `AddGold(Amount: int) -> None`

Purpose:
Increases gold count.

Inputs:
- `Amount`: gold to add

Outputs:
- No return value

Behavior:
- Ignores values `<= 0`

#### `SpendGold(Amount: int) -> bool`

Purpose:
Attempts to spend gold.

Inputs:
- `Amount`: gold to spend

Outputs:
- `True` if the amount was spent
- `False` if insufficient funds

Behavior:
- Returns `True` for values `<= 0`

#### `AddDiscipline(DisciplineName: str) -> None`

Purpose:
Adds a Kai discipline if it is non-blank and not already present.

Inputs:
- `DisciplineName`: discipline name

Outputs:
- No return value

#### `RemoveDiscipline(DisciplineName: str) -> None`

Purpose:
Removes a Kai discipline if present.

Inputs:
- `DisciplineName`: discipline name

Outputs:
- No return value

#### `ToDict() -> dict[str, Any]`

Purpose:
Serializes the character sheet to the current JSON schema.

Outputs:
- Dictionary containing:
  - `SchemaVersion`
  - `Game`
  - `Character`
  - `Inventory`

#### `FromDict(Data: dict[str, Any]) -> CharacterSheet`

Purpose:
Deserializes a character sheet from schema-shaped JSON data.

Inputs:
- `Data`: loaded JSON object

Outputs:
- A new `CharacterSheet`

## JSON Repository

### `modules/JsonRepository.py`

This module handles persistence of `CharacterSheet` objects.

### Exception Classes

#### `JsonRepositoryError`

Base exception for repository-related errors.

#### `JsonSchemaVersionError`

Raised when a JSON file uses an unsupported schema version.

#### `JsonLoadError`

Raised when loading fails due to file access, invalid JSON, or mismatched structure.

#### `JsonSaveError`

Raised when saving fails due to serialization or file-system errors.

### Class: `JsonRepository`

Purpose:
Loads and saves `CharacterSheet` objects as JSON files.

Fields:
- `SupportedSchemaVersions: tuple[int, ...] = (1,)`

#### `LoadCharacter(FilePath: str | Path) -> CharacterSheet`

Inputs:
- `FilePath`: path to the JSON file

Outputs:
- A `CharacterSheet` object

Raises:
- `JsonLoadError`
- `JsonSchemaVersionError`

Behavior:
- Reads the file
- Parses JSON
- Verifies top-level object type
- Verifies `SchemaVersion`
- Converts data via `CharacterSheet.FromDict(...)`

#### `SaveCharacter(Sheet: CharacterSheet, FilePath: str | Path) -> None`

Inputs:
- `Sheet`: character sheet to save
- `FilePath`: target file path

Outputs:
- No return value

Raises:
- `JsonSaveError`
- `JsonSchemaVersionError`

Behavior:
- Converts the sheet to schema-shaped data
- Verifies schema version
- Serializes JSON with indentation
- Creates parent directories if needed
- Writes the file using UTF-8

## CLI Layer

### `modules/Cli.py`

This module contains the top-level command-line interface.

### Class: `CliApp`

Purpose:
Parses CLI arguments and routes them to the correct handler.

Fields:
- `Repo: JsonRepository`

#### `Run(Argv: Sequence[str]) -> int`

Purpose:
Main CLI dispatcher.

Inputs:
- `Argv`: command-line tokens excluding the executable name

Outputs:
- Integer exit code

Commands supported:
- `create <path>`
- `show <path>`
- `heal <path> <amount>`
- `damage <path> <amount>`
- `play <path>`

Behavior:
- Builds the parser
- Parses command arguments
- Calls a handler based on `Args.Command`
- Converts repository and value errors into exit code `2`

Note:
- The code references `Sequence[str]` but does not currently import `Sequence`

#### `_BuildParser() -> argparse.ArgumentParser`

Purpose:
Creates the top-level CLI parser and subcommands.

Outputs:
- Configured `ArgumentParser`

#### `_HandleCreate(FilePath: Path) -> int`

Purpose:
Creates a default character and saves it to disk.

Inputs:
- `FilePath`: output path for the new save

Outputs:
- `0` on success

Side effects:
- Writes a new JSON save file
- Prints confirmation

#### `_HandleShow(FilePath: Path) -> int`

Purpose:
Loads and displays a character summary.

Inputs:
- `FilePath`: path to existing save

Outputs:
- `0` on success

Side effects:
- Prints formatted character information

#### `_HandleHeal(FilePath: Path, Amount: int) -> int`

Purpose:
Loads a character, heals endurance, saves the result.

Inputs:
- `FilePath`: save path
- `Amount`: heal amount

Outputs:
- `0` on success

Side effects:
- Updates the save file
- Prints before/after endurance

#### `_HandleDamage(FilePath: Path, Amount: int) -> int`

Purpose:
Loads a character, applies damage, saves the result.

Inputs:
- `FilePath`: save path
- `Amount`: damage amount

Outputs:
- `0` on success

Side effects:
- Updates the save file
- Prints before/after endurance

#### `_FormatSummary(Sheet: CharacterSheet) -> str`

Purpose:
Formats a `CharacterSheet` into a human-readable summary.

Inputs:
- `Sheet`: character to display

Outputs:
- Multi-line string summary

#### `_HandlePlay(FilePath: Path) -> int`

Purpose:
Runs the interactive play loop.

Inputs:
- `FilePath`: path to save file

Outputs:
- `0` when the play session exits

Interactive commands:
- `help`
- `status`
- `save`
- `heal <n>`
- `damage <n>`
- `gold +<n>`
- `gold -<n>`
- `inv`
- `add-weapon <name>`
- `remove-weapon <name>`
- `add-backpack <name>`
- `remove-backpack <name>`
- `add-special <name>`
- `remove-special <name>`
- `fight <enemyCS> <enemyEP>`
- `roll`
- `round`
- `apply <yourDamage> <enemyDamage>`
- `quit`
- `exit`

Behavior:
- Creates or loads a `PlaySession`
- Reads user input in a loop
- Delegates state changes to the session and domain objects
- Saves after most state-changing actions

## Interactive Session

### `modules/PlaySession.py`

This module contains the state and behavior for the interactive `play` mode.

### Class: `FightState`

Purpose:
Stores the currently active enemy in combat.

Fields:
- `EnemyCombatSkill: int`
- `EnemyEndurance: Endurance`

### Class: `PlaySession`

Purpose:
Owns the active character, save path, combat table, and current fight state.

Fields:
- `Repo: JsonRepository`
- `SavePath: Path`
- `Sheet: CharacterSheet`
- `CtrTable: CombatResultsTable`
- `Fight: FightState | None`
- `Rng: random.Random`

#### `CreateOrLoad(Repo: JsonRepository, SavePath: Path) -> PlaySession`

Purpose:
Creates a new play session or loads an existing one.

Inputs:
- `Repo`: repository for save/load
- `SavePath`: target save file

Outputs:
- A `PlaySession`

Raises:
- `FileNotFoundError` if `configs/CombatResultsTable_local.json` is missing

Behavior:
- Loads the local combat table
- Loads an existing character if the save file exists
- Otherwise creates a default character and saves it

#### `Save() -> None`

Purpose:
Writes the current character state to disk.

Outputs:
- No return value

#### `RollRandomNumber() -> int`

Purpose:
Generates a Lone Wolf random number.

Outputs:
- Integer from `0` to `9`

#### `GetCombatRatio() -> int`

Purpose:
Computes the current combat ratio.

Outputs:
- `Sheet.CombatSkill - Fight.EnemyCombatSkill`

Raises:
- `ValueError` if there is no active fight

#### `StartFight(EnemyCombatSkill: int, EnemyEndurancePoints: int) -> str`

Purpose:
Creates a new active fight.

Inputs:
- `EnemyCombatSkill`: enemy combat skill
- `EnemyEndurancePoints`: enemy endurance

Outputs:
- Human-readable multi-line status text

Behavior:
- Creates `FightState`
- Calculates the combat ratio
- Does not automatically resolve a round

#### `ApplyFightRound(YourDamage: int, EnemyDamage: int) -> str`

Purpose:
Applies explicit round damage values to both sides.

Inputs:
- `YourDamage`: damage dealt to Lone Wolf
- `EnemyDamage`: damage dealt to the enemy

Outputs:
- Human-readable round result string

Behavior:
- Returns a message if there is no active fight
- Applies damage to both combatants
- Clears `Fight` if the enemy reaches `0`
- Saves the session after applying results

#### `ResolveAutomaticRound() -> str`

Purpose:
Resolves a round automatically using the combat table.

Inputs:
- No direct parameters

Outputs:
- Human-readable combat summary including:
  - current combat ratio
  - random number rolled
  - CRT result
  - post-round state changes

Behavior:
- Returns a message if there is no active fight
- Rolls a number from `0` to `9`
- Resolves the CRT row using `CombatResultsTable`
- Applies the resulting damage values

#### `StatusText() -> str`

Purpose:
Formats the session state for display in the play loop.

Outputs:
- Multi-line string including:
  - character basics
  - disciplines
  - inventory
  - active fight details if present

## Combat Table

### `modules/RuleBooks1to5.py`

This module loads and evaluates the combat results table used by `PlaySession`.

### Class: `CombatOutcome`

Purpose:
Represents the resolved damage for one combat round.

Fields:
- `YouDamage: int`
- `EnemyDamage: int`

Meaning:
- `YouDamage` is damage applied to Lone Wolf
- `EnemyDamage` is damage applied to the enemy

### Class: `CombatResultsTable`

Purpose:
Stores CRT rows and resolves a combat ratio plus random number into a `CombatOutcome`.

Fields:
- `MinRatio: int`
- `MaxRatio: int`
- `Rows: dict[int, list[list[int]]]`

Expected JSON shape:
- `MinRatio` and `MaxRatio` define valid ratio bounds
- `Rows` maps each combat ratio to a list of 10 cells
- Each cell is a two-value list in the source JSON:
  - index `0`: enemy damage
  - index `1`: your damage

#### `__init__(MinRatio: int, MaxRatio: int, Rows: dict[int, list[list[int]]]) -> None`

Purpose:
Initializes the CRT object.

Inputs:
- `MinRatio`
- `MaxRatio`
- `Rows`

Outputs:
- No return value

#### `LoadFromJson(FilePath: Path) -> CombatResultsTable`

Purpose:
Loads a combat table from a JSON file.

Inputs:
- `FilePath`: path to CRT JSON

Outputs:
- A `CombatResultsTable`

Behavior:
- Reads the file
- Parses JSON
- Converts row keys from strings to integers

#### `ResolveRound(CombatRatio: int, RandomNumber: int) -> CombatOutcome`

Purpose:
Finds the correct combat result for a ratio and random number.

Inputs:
- `CombatRatio`: computed combat ratio
- `RandomNumber`: random number from `0` to `9`

Outputs:
- `CombatOutcome`

Raises:
- `ValueError` if:
  - random number is outside `0..9`
  - no row exists for the ratio
  - the row does not contain exactly 10 entries
  - the selected cell is not a two-item list

Behavior:
- Clamps `CombatRatio` into `[MinRatio, MaxRatio]`
- Uses the random number as the row index
- Converts the JSON cell into:
  - `EnemyDamage = Cell[0]`
  - `YouDamage = Cell[1]`

## Validation

### `modules/Validation.py`

Purpose:
Currently a placeholder for future rules-based validation.

Current state:
- No classes
- No functions
- Contains only a comment describing the intent to validate character sheets for books 1 to 5

## Package Init

### `modules/__init__.py`

Purpose:
Package marker for the `modules` package.

Current state:
- Empty

## Config Files

These are not Python modules, but they are important to runtime behavior.

### `configs/CombatResultsTable_local.json`

Purpose:
Current runtime combat table used by `PlaySession.CreateOrLoad(...)`.

### `configs/CombatResultsTable_template.json`

Purpose:
Template combat table file.

Current state:
- Rows have placeholder `[0, 0]` values
- Not suitable for real combat resolution until populated with full 10-cell rows

Distribution note:
- This template file is intended to be the version committed to GitHub instead of the populated local combat table, to avoid sharing copyrighted combat table data
- The combat table can be accessed from Project Aon at `https://www.projectaon.org/en/xhtml/lw/01fftd/crtable.htm`
- This project is not intended for broad distribution, except possibly as a small showcase of your learning journey

### `configs/CombatResultsTable.json`

Purpose:
Legacy or transitional combat table file.

Current state:
- Present in the repository
- Not used by the current `PlaySession` code path

### `configs/defaultRules.json`

Purpose:
Static configuration related to default Lone Wolf data and rule metadata.

Current state:
- Present but not actively used by the runtime logic shown above

## Tests

The `tests` folder currently covers several parts of the project:

- `test_DomainModels.py`: domain model behavior
- `test_Inventory.py`: inventory behavior
- `test_JsonRepository.py`: JSON persistence and schema checks
- `test_CombatTable.py`: combat table loading and CRT resolution
- `test_Cli.py`: CLI behavior

Current note:
- `test_Cli.py` previously had an indentation issue during collection; if that file is still failing, it should be fixed separately from the runtime modules
