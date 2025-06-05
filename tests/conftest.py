# tests/conftest.py
import pytest
import os
from typing import Dict, List, Tuple, Any

from tuck_in_terrors_sim.game_elements.data_loaders import GameData, load_all_game_data
from tuck_in_terrors_sim.game_elements.card import Card
from tuck_in_terrors_sim.game_elements.objective import ObjectiveCard
from tuck_in_terrors_sim.game_logic.game_state import GameState
from tuck_in_terrors_sim.game_logic.game_setup import initialize_new_game
from tuck_in_terrors_sim.game_logic.effect_engine import EffectEngine
from tuck_in_terrors_sim.game_logic.nightmare_creep import NightmareCreepModule
from tuck_in_terrors_sim.game_logic.win_loss_checker import WinLossChecker
from tuck_in_terrors_sim.game_logic.turn_manager import TurnManager
from tuck_in_terrors_sim.game_logic.action_resolver import ActionResolver

@pytest.fixture(scope="session")
def project_root_dir() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

@pytest.fixture(scope="session")
def game_data(project_root_dir: str) -> GameData:
    cards_filepath = os.path.join(project_root_dir, "data", "cards.json")
    objectives_filepath = os.path.join(project_root_dir, "data", "objectives.json")
    if not os.path.exists(cards_filepath):
        pytest.fail(f"Cards data file not found: {cards_filepath}", pytrace=False)
    if not os.path.exists(objectives_filepath):
        pytest.fail(f"Objectives data file not found: {objectives_filepath}", pytrace=False)
    return load_all_game_data(cards_filepath, objectives_filepath)

@pytest.fixture
def all_card_definitions_dict(game_data: GameData) -> Dict[str, Card]:
    return game_data.cards_by_id

@pytest.fixture
def all_card_definitions_list(game_data: GameData) -> List[Card]:
    return game_data.cards

@pytest.fixture
def objective_def_first_night(game_data: GameData) -> ObjectiveCard:
    obj = game_data.get_objective_by_id("OBJ01_THE_FIRST_NIGHT")
    if not obj:
        pytest.fail("Objective OBJ01_THE_FIRST_NIGHT not found.", pytrace=False)
    return obj

@pytest.fixture
def objective_def_whisper_wake(game_data: GameData) -> ObjectiveCard:
    obj = game_data.get_objective_by_id("OBJ02_WHISPER_WAKE")
    if not obj:
        pytest.fail("Objective OBJ02_WHISPER_WAKE not found.", pytrace=False)
    return obj

@pytest.fixture
def initialized_game_environment(
    game_data: GameData, 
    objective_def_first_night: ObjectiveCard
) -> Tuple[GameState, ActionResolver, EffectEngine, TurnManager, NightmareCreepModule, WinLossChecker]: # Now returns 6 items
    
    game_state = initialize_new_game(objective_def_first_night, game_data.cards_by_id)
    
    effect_engine = EffectEngine(game_state_ref=game_state)
    # MODIFIED: Instantiate WinLossChecker before ActionResolver
    win_loss_checker = WinLossChecker(game_state)
    # MODIFIED: Pass win_loss_checker to ActionResolver
    action_resolver = ActionResolver(game_state, effect_engine, win_loss_checker) 
    
    nightmare_module = NightmareCreepModule(game_state, effect_engine)
    
    # TurnManager now gets the ActionResolver that has the WinLossChecker
    turn_manager = TurnManager(
        game_state=game_state, 
        action_resolver=action_resolver, 
        effect_engine=effect_engine, 
        nightmare_module=nightmare_module, 
        win_loss_checker=win_loss_checker
    )
    
    return game_state, action_resolver, effect_engine, turn_manager, nightmare_module, win_loss_checker