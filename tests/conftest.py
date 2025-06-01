# tests/conftest.py
# Pytest fixtures can be defined here

import pytest
import os
from typing import Dict, Tuple

# Game Element Imports
from tuck_in_terrors_sim.game_elements.data_loaders import GameData, load_all_game_data
from tuck_in_terrors_sim.game_elements.card import Card
from tuck_in_terrors_sim.game_elements.objective import ObjectiveCard

# Game Logic Imports (for the new fixture)
from tuck_in_terrors_sim.game_logic.game_state import GameState
from tuck_in_terrors_sim.game_logic.game_setup import initialize_new_game
from tuck_in_terrors_sim.game_logic.effect_engine import EffectEngine
from tuck_in_terrors_sim.game_logic.nightmare_creep import NightmareCreepModule
from tuck_in_terrors_sim.game_logic.win_loss_checker import WinLossChecker
from tuck_in_terrors_sim.game_logic.turn_manager import TurnManager
# from tuck_in_terrors_sim.game_logic.action_resolver import ActionResolver # If needed for some advanced test setups
# from tuck_in_terrors_sim.ai.ai_player_base import AIPlayerBase # If AI interaction tested here

@pytest.fixture(scope="session")
def project_root_dir() -> str:
    """Returns the absolute path to the project root directory."""
    # Assumes conftest.py is in the 'tests' directory, one level down from project root
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

@pytest.fixture(scope="session")
def game_data(project_root_dir: str) -> GameData:
    """
    Loads all game data (cards and objectives) once per test session
    using the actual JSON files in the data/ directory.
    """
    cards_filepath = os.path.join(project_root_dir, "data", "cards.json")
    objectives_filepath = os.path.join(project_root_dir, "data", "objectives.json")
    
    if not os.path.exists(cards_filepath):
        pytest.fail(f"Cards data file not found at: {cards_filepath}. Ensure data/cards.json exists and is populated with example data.", pytrace=False)
    if not os.path.exists(objectives_filepath):
        pytest.fail(f"Objectives data file not found at: {objectives_filepath}. Ensure data/objectives.json exists and is populated with example data.", pytrace=False)
        
    return load_all_game_data(cards_filepath, objectives_filepath)

@pytest.fixture
def all_card_definitions(game_data: GameData) -> Dict[str, Card]:
    """Provides the dictionary of all loaded card definitions."""
    return game_data.cards

@pytest.fixture
def objective_def_first_night(game_data: GameData) -> ObjectiveCard:
    """Provides 'The First Night' objective definition."""
    obj = game_data.get_objective_by_id("OBJ01_THE_FIRST_NIGHT")
    if not obj:
        pytest.fail("Objective OBJ01_THE_FIRST_NIGHT not found in loaded game data. Check data/objectives.json.", pytrace=False)
    return obj

@pytest.fixture
def objective_def_whisper_wake(game_data: GameData) -> ObjectiveCard:
    """Provides 'The Whisper Before Wake' objective definition."""
    obj = game_data.get_objective_by_id("OBJ02_WHISPER_WAKE")
    if not obj:
        pytest.fail("Objective OBJ02_WHISPER_WAKE not found in loaded game data. Check data/objectives.json.", pytrace=False)
    return obj

# New fixture for testing game logic modules
@pytest.fixture
def initialized_game_environment(game_data: GameData) -> Tuple[GameState, TurnManager, EffectEngine, NightmareCreepModule, WinLossChecker]:
    """
    Provides a fully initialized GameState and instances of core logic modules
    for 'The First Night' objective (OBJ01_THE_FIRST_NIGHT).
    """
    objective = game_data.get_objective_by_id("OBJ01_THE_FIRST_NIGHT")
    if not objective:
        # This check is also in objective_def_first_night, but good to have here too for clarity
        pytest.fail("Objective OBJ01_THE_FIRST_NIGHT (used for default test setup) not found in game_data.objectives.", pytrace=False)

    # Initialize GameState using game_setup
    game_state = initialize_new_game(objective, game_data.cards)
    
    # Initialize core logic modules
    effect_engine = EffectEngine(game_state)
    # ActionResolver would be instantiated here if TurnManager needed it, or if tests directly use it.
    # action_resolver = ActionResolver(game_state, effect_engine) 
    nightmare_module = NightmareCreepModule(game_state, effect_engine)
    win_loss_checker = WinLossChecker(game_state)
    
    # Ensure TurnManager is instantiated with all required arguments
    turn_manager = TurnManager(game_state, effect_engine, nightmare_module, win_loss_checker)
    
    return game_state, turn_manager, effect_engine, nightmare_module, win_loss_checker