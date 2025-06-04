# Tuck'd-In Terrors Monte Carlo Simulator

A Python-based Monte Carlo simulator for the solo card game "Tuck'd-In Terrors." This project aims to provide a tool for game balancing, strategy exploration, and understanding game mechanics through automated play.

## Project Status

The project has made significant progress and is currently in a stable state with all unit tests passing.

- **Phase 1 (Core Game Logic & Basic Simulation): Completed.** Foundational data models and basic game structures are in place.
- **Phase 2 (Expanding Effect Engine & Card Interactions): Completed.** The EffectEngine has been enhanced with more complex effects, conditions, and triggers.
- **Phase 3 (Advanced Game Mechanics & Objective Implementation): Completed.** Key mechanics like Haunt, Echo, and full support for "The First Night" objective (including its Nightmare Creep) are implemented.
- **Phase 4 (Player Choice, AI Enhancement & Multi-Objective Foundation): Completed.** A robust system for handling player choices within effects is substantially implemented and tested (e.g., `CHOOSE_YES_NO`, `DISCARD_CARD_OR_SACRIFICE_SPIRIT`, `CHOOSE_CARD_FROM_HAND`). The AI (`RandomAI`) has been updated to interact with these choices. All core game logic components have been tested and verified.

The simulator is now capable of resolving complex card interactions and player decisions driven by the AI, with all 93 unit tests passing.

## Features

- **Game Element Modeling**: Python classes for Cards (Toys, Rituals, Spells), Objectives, and game Enums.
- **Data Loading**: Parses game data from JSON files (`data/cards.json`, `data/objectives.json`).
- **Core Game Engine**:
  - `GameState`: Tracks the dynamic state of a game.
  - `GameSetup`: Initializes a game based on a chosen Objective.
  - `TurnManager`: Manages game turns and phases (Begin, Main, End).
  - `ActionResolver`: Handles player/AI actions like playing cards and activating abilities.
  - `EffectEngine`: Resolves card and game effects, including conditional logic, various action types, and player choice resolution.
  - `NightmareCreepModule`: Applies objective-specific Nightmare Creep effects.
  - `WinLossChecker`: Determines if win or loss conditions have been met.
  - First Memory and other keyword mechanics (Haunt, Echo).
- **AI Player**:
  - `AIPlayerBase` for defining AI interfaces.
  - `RandomAI` capable of making game actions and responding to implemented player choices.
  - `ActionGenerator`: Generates lists of valid actions for AI.
- **Unit Testing**: Comprehensive `pytest` suite covering data models, core game logic, effect resolution, and player choice scenarios. All 93 tests are currently passing.

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
    (Note: `pyproject.toml` specifies `pytest` and `pytest-cov` as dev dependencies.)

## Running Tests

With the virtual environment activated and development dependencies installed, run tests from the project root directory:

```bash
pytest
```
