# tests/game_logic/test_game_state.py
# Unit tests for game_state.py

import pytest
from typing import Dict

from tuck_in_terrors_sim.game_elements.card import Card, Toy
from tuck_in_terrors_sim.game_elements.objective import ObjectiveCard, ObjectiveLogicComponent
from tuck_in_terrors_sim.game_elements.enums import CardType, Zone, TurnPhase
from tuck_in_terrors_sim.game_logic.game_state import GameState
# If the test needs CardInstance, add:
# from tuck_in_terrors_sim.game_elements.card import CardInstance
# --- Test Fixtures / Mock Data ---

@pytest.fixture
def mock_card_definitions() -> Dict[str, Card]:
    """Provides a dictionary of mock Card definitions."""
    return {
        "TCTOY001": Toy(card_id="TCTOY001", name="Mock Toy Cow", cost=2, quantity_in_deck=2),
        "TCSPL001": Card(card_id="TCSPL001", name="Mock Spell", card_type=CardType.SPELL, cost=1, quantity_in_deck=3)
    }

@pytest.fixture
def mock_objective() -> ObjectiveCard:
    """Provides a mock ObjectiveCard."""
    return ObjectiveCard(
        objective_id="OBJ_TEST_GS",
        title="Test GameState Objective",
        difficulty="Test",
        nightfall_turn=5,
        primary_win_condition=ObjectiveLogicComponent(
            component_type="TEST_PRIMARY_WIN", 
            params={"value": 10}
        )
        # Add other necessary fields if GameState init directly accesses them deeply
    )

@pytest.fixture
def initial_game_state(mock_objective: ObjectiveCard, mock_card_definitions: Dict[str, Card]) -> GameState:
    """Provides a GameState instance initialized with mock data."""
    return GameState(loaded_objective=mock_objective, all_card_definitions=mock_card_definitions)

# --- Tests for CardInPlay ---

class TestCardInPlay:
    def test_card_in_play_creation(self, mock_card_definitions):
        base_toy = mock_card_definitions["TCTOY001"]
        cip = CardInPlay(base_card=base_toy)
        
        assert cip.card_definition == base_toy
        assert base_toy.card_id in cip.instance_id
        assert "play_" in cip.instance_id
        assert not cip.is_tapped
        assert cip.counters == {}
        assert cip.attachments == []
        assert cip.effects_active_this_turn == {}
        assert cip.turns_in_play == 0

    def test_tap_untap(self, mock_card_definitions):
        cip = CardInPlay(base_card=mock_card_definitions["TCTOY001"])
        assert not cip.is_tapped
        cip.tap()
        assert cip.is_tapped
        cip.untap()
        assert not cip.is_tapped

    def test_add_remove_counters(self, mock_card_definitions):
        cip = CardInPlay(base_card=mock_card_definitions["TCTOY001"])
        
        cip.add_counter("power", 2)
        assert cip.counters.get("power") == 2
        
        cip.add_counter("power", 1)
        assert cip.counters.get("power") == 3
        
        cip.remove_counter("power", 1)
        assert cip.counters.get("power") == 2
        
        cip.remove_counter("power", 5) # Remove more than present
        assert cip.counters.get("power") is None # Counter type should be removed if 0 or less
        
        cip.add_counter("damage", 1)
        assert cip.counters.get("damage") == 1
        cip.remove_counter("damage", 1)
        assert "damage" not in cip.counters


# --- Tests for GameState ---

class TestGameState:
    def test_game_state_initialization(self, initial_game_state: GameState, mock_objective: ObjectiveCard, mock_card_definitions: Dict[str, Card]):
        gs = initial_game_state
        
        assert gs.current_objective == mock_objective
        assert gs.all_card_definitions == mock_card_definitions
        
        assert gs.deck == [] # GameSetup will populate this
        assert gs.hand == []
        assert gs.discard_pile == []
        assert gs.exile_zone == []
        assert gs.cards_in_play == {}
        
        assert gs.mana_pool == 0
        assert gs.spirit_tokens == 0
        assert gs.memory_tokens == 0
        
        assert gs.first_memory_card_definition is None
        assert gs.first_memory_instance_id is None
        assert gs.first_memory_current_zone is None
        
        assert gs.current_turn == 0 # GameSetup will set to 1
        assert gs.current_phase is None # GameSetup or TurnManager will set
        
        assert not gs.nightmare_creep_effect_applied_this_turn
        
        # Check initial objective_progress structure based on GameState's initialize_objective_progress
        assert "toys_played_this_game_count" in gs.objective_progress
        assert "distinct_toys_played_ids" in gs.objective_progress
        assert "spirits_created_total_game" in gs.objective_progress
        assert "mana_from_card_effects_total_game" in gs.objective_progress
        if mock_objective.primary_win_condition and \
           mock_objective.primary_win_condition.component_type == "PLAY_X_DIFFERENT_TOYS_AND_CREATE_Y_SPIRITS":
            assert "primary_toys_needed" in gs.objective_progress # This part of init depends on objective type
            assert "primary_spirits_needed" in gs.objective_progress

        assert not gs.free_toy_played_this_turn
        assert not gs.flashback_used_this_game
        assert gs.storm_count_this_turn == 0
        
        assert not gs.game_over
        assert gs.win_status is None
        assert gs.game_log == []

    def test_add_log_entry(self, initial_game_state: GameState):
        gs = initial_game_state
        gs.current_turn = 1
        gs.current_phase = TurnPhase.MAIN_PHASE
        
        gs.add_log_entry("Test log message.")
        assert len(gs.game_log) == 1
        assert "T1 (MAIN_PHASE): Test log message." in gs.game_log[0]
        
        gs.add_log_entry("Another message.", level="ERROR")
        assert len(gs.game_log) == 2
        assert "[ERROR] T1 (MAIN_PHASE): Another message." in gs.game_log[1]

    def test_get_card_in_play_by_instance_id(self, initial_game_state: GameState, mock_card_definitions):
        gs = initial_game_state
        toy_def = mock_card_definitions["TCTOY001"]
        cip = CardInPlay(base_card=toy_def)
        
        assert gs.get_card_in_play_by_instance_id(cip.instance_id) is None # Not yet in play area
        
        gs.cards_in_play[cip.instance_id] = cip
        assert gs.get_card_in_play_by_instance_id(cip.instance_id) == cip
        assert gs.get_card_in_play_by_instance_id("non_existent_id") is None

    def test_move_card_object_between_zones(self, initial_game_state: GameState, mock_card_definitions):
        gs = initial_game_state
        card1 = mock_card_definitions["TCTOY001"] # This is a Card definition, not an instance
        card2 = mock_card_definitions["TCSPL001"]
        
        # Note: The GameState zones (deck, hand, discard, exile) store Card definitions, not CardInPlay instances.
        # CardInPlay is specifically for gs.cards_in_play.
        # The helper `move_card_object_between_zones` is for these list-based zones.

        gs.hand = [card1, card2]
        gs.discard_pile = []
        
        gs.move_card_object_between_zones(card1, gs.hand, gs.discard_pile)
        assert card1 not in gs.hand
        assert card1 in gs.discard_pile
        assert len(gs.hand) == 1
        assert len(gs.discard_pile) == 1
        
        # Test moving a card not in the source zone (should log error, not crash)
        non_existent_card_in_hand = Toy(card_id="TEMP001", name="Temp", cost=0) 
        initial_hand_len = len(gs.hand)
        initial_discard_len = len(gs.discard_pile)
        gs.move_card_object_between_zones(non_existent_card_in_hand, gs.hand, gs.discard_pile)
        assert len(gs.hand) == initial_hand_len # No change
        assert len(gs.discard_pile) == initial_discard_len
        assert f"Error: Card '{non_existent_card_in_hand.name}' not found" in gs.game_log[-1]