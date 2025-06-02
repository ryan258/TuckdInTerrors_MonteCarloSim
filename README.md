# Tuck'd-In Terrors Monte Carlo Simulator

A Python-based Monte Carlo simulator for the solo card game "Tuck'd-In Terrors." This project aims to provide a tool for game balancing, strategy exploration, and understanding game mechanics through automated play.

## Project Status

The project has made significant progress:

- **Phase 1 (Core Game Logic & Basic Simulation): Completed.** Foundational data models and basic game structures are in place.
- **Phase 2 (Expanding Effect Engine & Card Interactions): Completed.** The EffectEngine has been enhanced with more complex effects, conditions, and triggers.
- **Phase 3 (Advanced Game Mechanics & Objective Implementation): Completed.** Key mechanics like Haunt, Echo, and full support for "The First Night" objective (including its Nightmare Creep) are implemented.
- **Phase 4 (Player Choice, AI Enhancement & Multi-Objective Foundation): In Progress.** A robust system for handling player choices within effects is substantially implemented and tested (e.g., `CHOOSE_YES_NO`, `DISCARD_CARD_OR_SACRIFICE_SPIRIT`, `CHOOSE_CARD_FROM_HAND`). The AI (`RandomAI`) has been updated to interact with these choices.

The simulator is now capable of resolving complex card interactions and player decisions driven by the AI.

## Features

- **Game Element Modeling**: Python classes for Cards (Toys, Rituals, Spells), Objectives, and game Enums.
- **Data Loading**: Parses game data from JSON files (`data/cards.json`, `data/objectives.json`).
- **Core Game Engine**:
  - `GameState`: Tracks the dynamic state of a game.
  - `GameSetup`: Initializes a game based on a chosen Objective.
  - `TurnManager`: Manages game turns and phases (Begin, Main, End).
  - `ActionResolver`: Handles player/AI actions like playing cards and activating abilities.
  - `EffectEngine`: Resolves card and game effects, including:
    - Conditional logic (IF_X_THEN_Y based on game state, counters, etc.).
    - A variety of action types (drawing, creating resources, placing counters, sacrificing, milling, exiling, moving cards between zones).
    - Player choice resolution (`PLAYER_CHOICE` action type with various `PlayerChoiceType` handlers like `CHOOSE_YES_NO`, `DISCARD_CARD_OR_SACRIFICE_SPIRIT`).
  - `NightmareCreepModule`: Applies objective-specific Nightmare Creep effects, often integrated with `PLAYER_CHOICE`.
  - `WinLossChecker`: Determines if win or loss conditions have been met for implemented objectives.
  - First Memory and other keyword mechanics (Haunt, Echo).
- **AI Player**:
  - `AIPlayerBase` for defining AI interfaces.
  - `RandomAI` capable of making game actions and responding to implemented player choices.
- **Unit Testing**: Comprehensive `pytest` suite covering data models, core game logic, effect resolution, and player choice scenarios.

## Setup

1.  **Clone the repository** (if you haven't already).
2.  **Ensure Python 3.9+ and `uv` are installed.**
    - You can install `uv` via pip: `pip install uv`
3.  **Navigate to the project root directory** (`TuckdInTerrors_MonteCarloSim/`).
4.  **Create and activate the virtual environment using `uv`:**
    ```bash
    uv venv
    ```
    Activate the environment:
    - On Windows (PowerShell): `.\.venv\Scripts\Activate.ps1`
    - On Linux/macOS (bash/zsh): `source .venv/bin/activate`
5.  **Install dependencies (including development dependencies like pytest):**
    ```bash
    uv pip install .[dev]
    ```

## Running Tests

With the virtual environment activated and development dependencies installed, run tests from the project root directory:

```bash
pytest
```

You should see all tests passing, indicating a healthy and functional codebase.

## Populating Game Data

The simulator loads game data from:

- `data/cards.json`: Contains definitions for all game cards.
- `data/objectives.json`: Contains definitions for all game objectives.

Ensure these files are populated according to the defined Python class structures.

## Running Simulations (Future - via `main.py`)

The `main.py` script will be the entry point for running simulations. Full command-line operation is part of future development (Phase 5).

A conceptual command might look like:

```bash
python main.py --objective OBJ01_THE_FIRST_NIGHT --simulations 1000 --ai random_ai
```

## Project Structure Overview

- `data/`: Contains JSON files for game cards and objectives.
- `results/`: (Will be used for) Output directory for simulation logs and analysis reports.
- `src/tuck_in_terrors_sim/`: Main Python package for the simulation engine.
  - `game_elements/`: Data models for cards, objectives, enums, and data loaders.
  - `game_logic/`: Core game engine (state, setup, turn flow, actions, effects, etc.).
  - `ai/`: AI player logic.
  - `simulation/`: Simulation orchestration and data analysis (to be developed).
  - `ui/`: (Future) Console output or simple reporting.
  - `utils/`: Common utility functions.
- `tests/`: Unit and integration tests.
- `main.py`: Main script to run simulations (to be fully implemented).
- `pyproject.toml`: Project metadata and dependencies.
- `ROADMAP.md`: Detailed development roadmap.
- `README.md`: This file.

## Next Steps (Roadmap)

The project is currently focused on **Phase 4: Player Choice, AI Enhancement & Multi-Objective Foundation**. Key upcoming tasks include:

- Implementing more `PlayerChoiceType` options (e.g., `CHOOSE_TARGET_FOR_EFFECT`, `ORDER_CARDS`).
- Implementing more cards from `cards.json` that utilize these advanced player choices.
- Further refining AI capabilities for these choices.

Refer to `ROADMAP.md` for detailed tasks within each phase.
