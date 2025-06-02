# tests/ai/test_random_ai.py
# Unit tests for random_ai.py

import pytest
import random as py_random # To avoid conflict with a fixture named 'random' if any
from typing import List, Dict, Any
from unittest.mock import MagicMock

# AI Profile
from tuck_in_terrors_sim.ai.ai_profiles.random_ai import RandomAI

# Game Logic & Elements (minimal for mocking GameState if needed)
from tuck_in_terrors_sim.game_logic.game_state import GameState
from tuck_in_terrors_sim.game_elements.objective import ObjectiveCard
from tuck_in_terrors_sim.game_elements.enums import PlayerChoiceType

@pytest.fixture
def random_ai_player() -> RandomAI:
    return RandomAI(player_name="TestRandomAI")

@pytest.fixture
def mock_game_state() -> GameState:
    # Create a very basic GameState mock, or use a simplified real one if necessary
    # For these tests, RandomAI mostly interacts with structured choices and action lists,
    # so GameState might only be needed for logging or very specific choice contexts.
    objective = ObjectiveCard(objective_id="test_obj", title="Test", difficulty="Easy", nightfall_turn=5)
    gs = GameState(loaded_objective=objective, all_card_definitions={})
    gs.game_log = [] # Ensure clean log for each test
    return gs

class TestRandomAIChooseAction:

    def test_choose_action_selects_from_valid_actions(self, random_ai_player: RandomAI, mock_game_state: GameState):
        valid_actions = [
            {'type': 'PLAY_CARD', 'params': {'card_id': 'C001'}, 'description': 'Play C001'},
            {'type': 'ACTIVATE_ABILITY', 'params': {'ability_id': 'A001'}, 'description': 'Activate A001'},
            {'type': 'PASS_TURN', 'params': {}, 'description': 'Pass'}
        ]
        # Seed random for predictable choice if needed, or just check if it's one of them
        # py_random.seed(0) # Optional: for deterministic tests of random choice
        
        chosen_action = random_ai_player.choose_action(mock_game_state, valid_actions)
        
        assert chosen_action in valid_actions
        # Check if game state logged the choice (RandomAI's choose_action logs DEBUG)
        # This depends on the exact logging implemented in RandomAI
        # For now, just assert it's a valid action.

    def test_choose_action_prefers_non_pass_if_available(self, random_ai_player: RandomAI, mock_game_state: GameState):
        valid_actions = [
            {'type': 'PLAY_CARD', 'params': {'card_id': 'C001'}, 'description': 'Play C001'},
            {'type': 'PASS_TURN', 'params': {}, 'description': 'Pass'}
        ]
        # Run multiple times to increase chance of catching error if it only picks PASS
        non_pass_chosen_count = 0
        for _ in range(20): # Statistically, PASS should not be chosen if others are available
            chosen_action = random_ai_player.choose_action(mock_game_state, valid_actions)
            assert chosen_action in valid_actions
            if chosen_action['type'] != 'PASS_TURN':
                non_pass_chosen_count +=1
        
        assert non_pass_chosen_count > 0 # It should have picked PLAY_CARD at least once

    def test_choose_action_returns_pass_if_only_option(self, random_ai_player: RandomAI, mock_game_state: GameState):
        valid_actions = [
            {'type': 'PASS_TURN', 'params': {}, 'description': 'Pass'}
        ]
        chosen_action = random_ai_player.choose_action(mock_game_state, valid_actions)
        assert chosen_action is not None
        assert chosen_action['type'] == 'PASS_TURN'

    def test_choose_action_handles_empty_list_gracefully(self, random_ai_player: RandomAI, mock_game_state: GameState):
        # ActionGenerator should ideally always provide PASS_TURN, but test AI's robustness
        valid_actions: List[Dict[str, Any]] = []
        chosen_action = random_ai_player.choose_action(mock_game_state, valid_actions)
        assert chosen_action is not None
        assert chosen_action['type'] == 'PASS_TURN' # Fallback in RandomAI
        assert any("No valid actions provided" in log for log in mock_game_state.game_log if "WARNING" in log)


class TestRandomAIMakeChoice:

    def test_make_choice_yes_no(self, random_ai_player: RandomAI, mock_game_state: GameState):
        choice_context = {
            'choice_id': 'test_yes_no_1',
            'choice_type': PlayerChoiceType.CHOOSE_YES_NO.name,
            'prompt_text': 'Proceed with awesome action?',
            'options': [True, False] # Options might be implicit for YES_NO in some designs
        }
        decision = random_ai_player.make_choice(mock_game_state, choice_context)
        assert decision in [True, False]

    def test_make_choice_from_list_options(self, random_ai_player: RandomAI, mock_game_state: GameState):
        options_list = ["OptionA", "OptionB", "OptionC"]
        choice_context = {
            'choice_id': 'test_list_choice_1',
            'choice_type': 'SOME_CUSTOM_LIST_CHOICE', # A generic or custom type for list choices
            'prompt_text': 'Select one item:',
            'options': options_list
        }
        decision = random_ai_player.make_choice(mock_game_state, choice_context)
        assert decision in options_list
        
    def test_make_choice_discard_or_sacrifice_spirit(self, random_ai_player: RandomAI, mock_game_state: GameState):
        # Example for Nightmare Creep choice
        choice_context = {
            'choice_id': 'nc_choice_test',
            'choice_type': PlayerChoiceType.DISCARD_CARD_OR_SACRIFICE_SPIRIT.name,
            'prompt_text': 'Nightmare Creep: Discard or Sacrifice?',
            'options': ["DISCARD", "SACRIFICE_SPIRIT"] # Assuming options are string identifiers
        }
        decision = random_ai_player.make_choice(mock_game_state, choice_context)
        assert decision in ["DISCARD", "SACRIFICE_SPIRIT"]

    def test_make_choice_empty_options_list(self, random_ai_player: RandomAI, mock_game_state: GameState):
        choice_context = {
            'choice_id': 'test_empty_list',
            'choice_type': 'SOME_LIST_CHOICE',
            'prompt_text': 'Choose from nothing:',
            'options': []
        }
        decision = random_ai_player.make_choice(mock_game_state, choice_context)
        assert decision is None # RandomAI returns None if options list is empty
        assert any("Could not make a random choice" in log for log in mock_game_state.game_log if "WARNING" in log)

    def test_make_choice_unknown_choice_type_with_options(self, random_ai_player: RandomAI, mock_game_state: GameState):
        # If choice_type is unknown, it should still try to pick from 'options' if it's a list
        options_list = [{"id": 1, "data": "A"}, {"id": 2, "data": "B"}]
        choice_context = {
            'choice_id': 'test_unknown_type',
            'choice_type': 'TOTALLY_NEW_CHOICE_TYPE_UNKNOWN_TO_AI',
            'prompt_text': 'A new kind of choice:',
            'options': options_list
        }
        decision = random_ai_player.make_choice(mock_game_state, choice_context)
        assert decision in options_list
        assert any("Unknown choice_type string" in log for log in mock_game_state.game_log if "WARNING" in log)


    # TODO: Add tests for more specific PlayerChoiceType scenarios as their 'choice_context'
    #       and 'options' structures become more defined by the EffectEngine.
    #       Examples:
    #       - CHOOSE_CARD_FROM_HAND (options = list of Card objects)
    #       - CHOOSE_NUMBER_FROM_RANGE (options = {'min': X, 'max': Y})
    #       - CHOOSE_MODAL_EFFECT (options = list of effect descriptions/IDs)