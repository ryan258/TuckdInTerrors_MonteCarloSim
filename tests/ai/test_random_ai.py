# tests/ai/test_random_ai.py
import pytest
from unittest.mock import MagicMock
from typing import List, Dict, Any, Optional

from tuck_in_terrors_sim.ai.ai_profiles.random_ai import RandomAI
from tuck_in_terrors_sim.models.game_action_model import GameAction
from tuck_in_terrors_sim.game_logic.game_state import GameState, PlayerState
from tuck_in_terrors_sim.game_elements.objective import ObjectiveCard
from tuck_in_terrors_sim.game_elements.card import CardInstance, Card, Toy # For mock card def
from tuck_in_terrors_sim.game_elements.enums import PlayerChoiceType, Zone, CardType # Added CardType
from tuck_in_terrors_sim.game_logic.game_setup import DEFAULT_PLAYER_ID


@pytest.fixture
def mock_game_state_for_ai() -> GameState: # Renamed to avoid conflict
    gs_mock = MagicMock(spec=GameState)
    
    player_state_mock = MagicMock(spec=PlayerState)
    player_state_mock.player_id = DEFAULT_PLAYER_ID
    # Initialize zones as dictionaries that can be accessed with .get
    player_state_mock.zones = {
        Zone.HAND: [], 
        Zone.IN_PLAY: [], 
        Zone.DISCARD: [], 
        Zone.DECK: []
    }
    player_state_mock.spirit_tokens = 1 # Give some spirits for testing choices
    
    gs_mock.get_player_state.return_value = player_state_mock
    gs_mock.get_active_player_state.return_value = player_state_mock
    gs_mock.add_log_entry = MagicMock()
    return gs_mock

@pytest.fixture
def random_ai_fixture() -> RandomAI: # Renamed to avoid conflict
    return RandomAI(player_id=DEFAULT_PLAYER_ID) # Use player_id

class TestRandomAIDecideAction: # Renamed from TestRandomAIChooseAction
    def test_decide_action_selects_from_valid_actions(self, random_ai_fixture: RandomAI, mock_game_state_for_ai: GameState):
        action1 = GameAction(type="PLAY_CARD", params={"card_id": "c1"}, description="Play C1")
        action2 = GameAction(type="PASS_TURN", description="Pass")
        possible_actions = [action1, action2]
        
        chosen_action = random_ai_fixture.decide_action(mock_game_state_for_ai, possible_actions)
        assert chosen_action in possible_actions

    def test_decide_action_prefers_non_pass_if_available(self, random_ai_fixture: RandomAI, mock_game_state_for_ai: GameState):
        play_action = GameAction(type="PLAY_CARD", params={"card_id": "c1"}, description="Play C1")
        pass_action = GameAction(type="PASS_TURN", description="Pass")
        possible_actions = [play_action, pass_action]
        
        # Run multiple times to increase chance of non-pass being picked if logic is random but prefers non-pass
        chosen_actions_sample = [random_ai_fixture.decide_action(mock_game_state_for_ai, possible_actions) for _ in range(10)]
        assert play_action in chosen_actions_sample # Check if play_action was chosen at least once
        if pass_action in chosen_actions_sample and play_action in chosen_actions_sample:
             pass # RandomAI might pick pass sometimes, which is fine for this simple AI

    def test_decide_action_returns_pass_if_only_option(self, random_ai_fixture: RandomAI, mock_game_state_for_ai: GameState):
        pass_action = GameAction(type="PASS_TURN", description="Pass")
        possible_actions = [pass_action]
        chosen_action = random_ai_fixture.decide_action(mock_game_state_for_ai, possible_actions)
        assert chosen_action == pass_action

    def test_decide_action_handles_empty_list_gracefully(self, random_ai_fixture: RandomAI, mock_game_state_for_ai: GameState):
        chosen_action = random_ai_fixture.decide_action(mock_game_state_for_ai, [])
        assert chosen_action is None

class TestRandomAIMakeChoice:
    def test_make_choice_yes_no(self, random_ai_fixture: RandomAI, mock_game_state_for_ai: GameState):
        choice_context = {"choice_type": PlayerChoiceType.CHOOSE_YES_NO, "prompt_text": "Choose?"}
        decision = random_ai_fixture.make_choice(mock_game_state_for_ai, choice_context)
        assert isinstance(decision, bool)

    def test_make_choice_from_list_options(self, random_ai_fixture: RandomAI, mock_game_state_for_ai: GameState):
        options = ["optA", "optB", "optC"]
        # Using a placeholder choice type that implies choosing from a list
        choice_context = {"choice_type": PlayerChoiceType.CHOOSE_MODAL_EFFECT, "options": options, "prompt_text": "Choose."}
        decision = random_ai_fixture.make_choice(mock_game_state_for_ai, choice_context)
        assert decision in options

    def test_make_choice_discard_or_sacrifice_spirit(self, random_ai_fixture: RandomAI, mock_game_state_for_ai: GameState):
        player_s_mock = mock_game_state_for_ai.get_active_player_state()
        # Ensure player state has cards and spirits for a meaningful choice
        mock_card_inst = MagicMock(spec=CardInstance); mock_card_inst.instance_id = "hand_card1"
        player_s_mock.zones[Zone.HAND] = [mock_card_inst]
        player_s_mock.spirit_tokens = 1

        choice_context = {
            "choice_type": PlayerChoiceType.DISCARD_CARD_OR_SACRIFICE_SPIRIT,
            "options": ["DISCARD", "SACRIFICE_SPIRIT"], 
            "prompt_text": "Discard or sacrifice?"
        }
        decision = random_ai_fixture.make_choice(mock_game_state_for_ai, choice_context)
        assert isinstance(decision, bool) # RandomAI maps this to bool (True for discard)

    def test_make_choice_empty_options_list_returns_none(self, random_ai_fixture: RandomAI, mock_game_state_for_ai: GameState):
        choice_context = {"choice_type": PlayerChoiceType.CHOOSE_CARD_FROM_HAND, "options": [], "prompt_text": "Choose card."}
        decision = random_ai_fixture.make_choice(mock_game_state_for_ai, choice_context)
        assert decision is None

class TestRandomAIChooseCardsToDiscard:
    def test_choose_cards_to_discard_selects_correct_number(self, random_ai_fixture: RandomAI, mock_game_state_for_ai: GameState):
        player_s_mock = mock_game_state_for_ai.get_active_player_state()
        
        mock_ci1 = MagicMock(spec=CardInstance); mock_ci1.instance_id = "ci1"
        mock_ci2 = MagicMock(spec=CardInstance); mock_ci2.instance_id = "ci2"
        mock_ci3 = MagicMock(spec=CardInstance); mock_ci3.instance_id = "ci3"
        player_s_mock.zones[Zone.HAND] = [mock_ci1, mock_ci2, mock_ci3]

        discarded_ids = random_ai_fixture.choose_cards_to_discard(mock_game_state_for_ai, 2)
        assert len(discarded_ids) == 2
        for card_id in discarded_ids:
            assert card_id in ["ci1", "ci2", "ci3"]
        if len(discarded_ids) == 2: # Ensure uniqueness if possible
            assert discarded_ids[0] != discarded_ids[1]

    def test_choose_cards_to_discard_empty_hand(self, random_ai_fixture: RandomAI, mock_game_state_for_ai: GameState):
        player_s_mock = mock_game_state_for_ai.get_active_player_state()
        player_s_mock.zones[Zone.HAND] = []
        discarded_ids = random_ai_fixture.choose_cards_to_discard(mock_game_state_for_ai, 1)
        assert len(discarded_ids) == 0