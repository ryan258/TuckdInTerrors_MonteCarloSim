# tests/game_logic/test_win_loss_checker.py
# Unit tests for win_loss_checker.py

import pytest
from typing import Tuple, Any, Dict

from tuck_in_terrors_sim.game_logic.game_state import GameState
from tuck_in_terrors_sim.game_logic.win_loss_checker import WinLossChecker
from tuck_in_terrors_sim.game_elements.objective import ObjectiveCard, ObjectiveLogicComponent
from tuck_in_terrors_sim.game_elements.data_loaders import GameData # For game_data fixture type hint

# Fixture 'initialized_game_environment' provides GameState, TurnManager, EffectEngine, 
# NightmareCreepModule, WinLossChecker using "OBJ01_THE_FIRST_NIGHT" by default.
# Fixture 'game_data' provides loaded cards and objectives.
# Both are defined in tests/conftest.py

class TestWinLossChecker:

    def test_nightfall_loss_condition(
        self, 
        initialized_game_environment: Tuple[GameState, Any, Any, Any, WinLossChecker]
    ):
        game_state, _, _, _, win_loss_checker = initialized_game_environment
        
        game_state.current_turn = game_state.current_objective.nightfall_turn + 1
        game_state.game_over = False # Ensure game isn't already over
        game_state.win_status = None

        assert win_loss_checker.check_all_conditions() is True
        assert game_state.game_over is True
        assert game_state.win_status == "LOSS_NIGHTFALL"
        assert any("Nightfall reached" in entry for entry in game_state.game_log)

    def test_game_already_over(
        self,
        initialized_game_environment: Tuple[GameState, Any, Any, Any, WinLossChecker]
    ):
        game_state, _, _, _, win_loss_checker = initialized_game_environment
        game_state.game_over = True
        game_state.win_status = "PREVIOUS_WIN" # Some prior win
        
        assert win_loss_checker.check_all_conditions() is True # Should return True as game is over
        assert game_state.win_status == "PREVIOUS_WIN" # Status should not change

    # --- Tests for "The First Night" (OBJ01_THE_FIRST_NIGHT) ---
    def test_first_night_primary_win_met(
        self,
        initialized_game_environment: Tuple[GameState, Any, Any, Any, WinLossChecker]
    ):
        game_state, _, _, _, win_loss_checker = initialized_game_environment
        # Ensure we are using the correct objective for this test
        assert game_state.current_objective.objective_id == "OBJ01_THE_FIRST_NIGHT"

        # Manually set progress to meet primary win condition
        # Primary: Play 4 different Toys and create 4 Spirits
        # component_type: "PLAY_X_DIFFERENT_TOYS_AND_CREATE_Y_SPIRITS", params: {"toys_needed": 4, "spirits_needed": 4}
        game_state.objective_progress["distinct_toys_played_ids"] = {"T1", "T2", "T3", "T4"}
        game_state.objective_progress["spirits_created_total_game"] = 4
        game_state.current_turn = 1 # Ensure not past nightfall

        assert win_loss_checker.check_all_conditions() is True
        assert game_state.game_over is True
        assert game_state.win_status == "PRIMARY_WIN"
        assert any("Objective Win Condition Met" in entry for entry in game_state.game_log)

    def test_first_night_alternative_win_met(
        self,
        initialized_game_environment: Tuple[GameState, Any, Any, Any, WinLossChecker]
    ):
        game_state, _, _, _, win_loss_checker = initialized_game_environment
        assert game_state.current_objective.objective_id == "OBJ01_THE_FIRST_NIGHT"

        # Manually set progress for alternative win condition
        # Alt: Generate 5 total mana using card effects
        # component_type: "GENERATE_X_MANA_FROM_CARD_EFFECTS", params: {"mana_needed": 5}
        game_state.objective_progress["mana_from_card_effects_total_game"] = 5
        game_state.current_turn = 1

        assert win_loss_checker.check_all_conditions() is True
        assert game_state.game_over is True
        assert game_state.win_status == "ALTERNATIVE_WIN"
        assert any("Objective Win Condition Met" in entry for entry in game_state.game_log)

    def test_first_night_no_win_no_loss(
        self,
        initialized_game_environment: Tuple[GameState, Any, Any, Any, WinLossChecker]
    ):
        game_state, _, _, _, win_loss_checker = initialized_game_environment
        assert game_state.current_objective.objective_id == "OBJ01_THE_FIRST_NIGHT"

        # Ensure progress is insufficient
        game_state.objective_progress["distinct_toys_played_ids"] = {"T1"}
        game_state.objective_progress["spirits_created_total_game"] = 1
        game_state.objective_progress["mana_from_card_effects_total_game"] = 1
        game_state.current_turn = 1 # Well before nightfall (OBJ01 nightfall is 4)

        assert win_loss_checker.check_all_conditions() is False
        assert game_state.game_over is False
        assert game_state.win_status is None

    # --- Tests for "The Whisper Before Wake" (OBJ02_WHISPER_WAKE) ---
    # We need a fixture or way to set the current objective for these tests
    @pytest.fixture
    def whisper_wake_game_env(self, game_data: GameData) -> Tuple[GameState, WinLossChecker]:
        """Sets up a GameState with OBJ02_WHISPER_WAKE for WinLossChecker tests."""
        from tuck_in_terrors_sim.game_logic.game_setup import initialize_new_game # Local import
        
        objective = game_data.get_objective_by_id("OBJ02_WHISPER_WAKE")
        if not objective:
            pytest.fail("Objective OBJ02_WHISPER_WAKE not found for test setup.")
        
        # Initialize GameState with minimal setup, WinLossChecker will use current_objective
        # Note: initialize_new_game will fully set up deck, hand etc.
        # For pure WinLossChecker tests, we might directly instantiate GameState
        # and set current_objective, then manually set objective_progress.
        # However, using initialize_new_game ensures GameState is valid.
        gs = initialize_new_game(objective, game_data.cards) # This will also log
        gs.game_log.clear() # Clear logs from initialize_new_game for focused test logs
        win_loss_checker = WinLossChecker(gs)
        return gs, win_loss_checker

    def test_whisper_wake_primary_win_met(self, whisper_wake_game_env: Tuple[GameState, WinLossChecker]):
        game_state, win_loss_checker = whisper_wake_game_env
        # Primary: Cast Fluffstorm of Forgotten Names with Storm 5+
        # component_type: "CAST_SPELL_WITH_STORM_COUNT", params: {"spell_name_or_id": "TCSPL_FLUFFSTORM_PLACEHOLDER", "min_storm_count": 5, ...}
        # The WinLossChecker expects a flag like: objective_progress["CAST_SPELL_EVENT_MET_TCSPL_FLUFFSTORM_PLACEHOLDER_STORM_5"] = True
        
        spell_id = game_state.current_objective.primary_win_condition.params.get("spell_card_id_or_name", "UNKNOWN_SPELL")
        min_storm = game_state.current_objective.primary_win_condition.params.get("min_storm_count", 100) # High default
        event_key = f"CAST_SPELL_EVENT_MET_{spell_id}_STORM_{min_storm}"
        game_state.objective_progress[event_key] = True
        game_state.current_turn = 1 # Ensure not past nightfall

        assert win_loss_checker.check_all_conditions() is True
        assert game_state.game_over is True
        assert game_state.win_status == "PRIMARY_WIN"

    def test_whisper_wake_alternative_win_met(self, whisper_wake_game_env: Tuple[GameState, WinLossChecker]):
        game_state, win_loss_checker = whisper_wake_game_env
        # Alt: Bring 10+ Spirits into existence
        # component_type: "CREATE_TOTAL_X_SPIRITS_GAME", params: {"spirits_needed": 10}
        game_state.objective_progress["spirits_created_total_game"] = 10
        game_state.current_turn = 1

        assert win_loss_checker.check_all_conditions() is True
        assert game_state.game_over is True
        assert game_state.win_status == "ALTERNATIVE_WIN"

    def test_win_condition_unknown_type(self, initialized_game_environment: Tuple[GameState, Any, Any, Any, WinLossChecker]):
        game_state, _, _, _, win_loss_checker = initialized_game_environment
        
        # Create a dummy win condition with an unknown type
        unknown_win_con = ObjectiveLogicComponent(component_type="TOTALLY_UNKNOWN_WIN_TYPE", params={})
        game_state.current_objective.primary_win_condition = unknown_win_con
        game_state.current_objective.alternative_win_condition = None # Simplify
        game_state.game_log.clear()

        assert win_loss_checker.check_all_conditions() is False # Should not win, should log warning
        assert game_state.game_over is False
        assert any("Win condition type 'TOTALLY_UNKNOWN_WIN_TYPE' not yet implemented" in entry for entry in game_state.game_log)