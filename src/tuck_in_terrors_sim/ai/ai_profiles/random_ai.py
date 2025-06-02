# src/tuck_in_terrors_sim/ai/ai_profiles/random_ai.py
# Implements basic AI that makes random valid moves

import random
from typing import List, Any, Dict, TYPE_CHECKING

from tuck_in_terrors_sim.ai.ai_player_base import AIPlayerBase
from tuck_in_terrors_sim.game_elements.enums import PlayerChoiceType # For make_choice logic

if TYPE_CHECKING:
    from tuck_in_terrors_sim.game_logic.game_state import GameState
    # from tuck_in_terrors_sim.game_elements.card import Card # If options in make_choice are Card objects


class RandomAI(AIPlayerBase):
    """
    An AI player that makes random valid decisions.
    """

    def __init__(self, player_name: str = "RandomAI"):
        super().__init__(player_name)

    def choose_action(self, game_state: 'GameState', valid_actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Randomly selects an action from the list of valid actions.
        It will try to avoid choosing 'PASS_TURN' if other actions are available.
        """
        if not valid_actions:
            # This case should ideally not be reached if ActionGenerator always provides PASS_TURN
            game_state.add_log_entry(f"AI ({self.player_name}): No valid actions provided to choose_action. This is unexpected.", level="WARNING")
            return {'type': 'PASS_TURN', 'params': {}} # Fallback

        # Separate PASS_TURN from other actions
        non_pass_actions = [action for action in valid_actions if action.get('type') != 'PASS_TURN']
        pass_action = next((action for action in valid_actions if action.get('type') == 'PASS_TURN'), None)

        if non_pass_actions:
            # Prefer to make a non-pass action if available
            chosen_action = random.choice(non_pass_actions)
            game_state.add_log_entry(f"AI ({self.player_name}): Randomly chose action: {chosen_action.get('description', chosen_action.get('type'))}", level="DEBUG")
            return chosen_action
        elif pass_action:
            # If only PASS_TURN is available (or was the only one left by chance, though unlikely with above logic)
            game_state.add_log_entry(f"AI ({self.player_name}): Only PASS_TURN action available or chosen.", level="DEBUG")
            return pass_action
        else:
            # Should not happen if ActionGenerator works correctly
            game_state.add_log_entry(f"AI ({self.player_name}): No actions (not even PASS_TURN) found in valid_actions. Critical error.", level="ERROR")
            # Return a synthetic pass action to prevent crashes, but this indicates a deeper issue.
            return {'type': 'PASS_TURN', 'params': {}}


    def make_choice(self, game_state: 'GameState', choice_context: Dict[str, Any]) -> Any:
        """
        Makes a random choice based on the provided context.
        """
        choice_id = choice_context.get('choice_id', 'UnknownChoice')
        choice_type_str = choice_context.get('choice_type')
        options = choice_context.get('options')
        prompt = choice_context.get('prompt_text', 'Make a choice.')

        game_state.add_log_entry(f"AI ({self.player_name}): Making choice for '{prompt}' (ID: {choice_id}, Type: {choice_type_str})", level="DEBUG")

        # Attempt to convert choice_type_str to PlayerChoiceType enum member for comparison
        try:
            choice_type_enum = PlayerChoiceType[choice_type_str] if choice_type_str else None
        except KeyError:
            game_state.add_log_entry(f"AI ({self.player_name}): Unknown choice_type string '{choice_type_str}'. Cannot make specific random choice.", level="WARNING")
            choice_type_enum = None

        decision = None

        if choice_type_enum == PlayerChoiceType.CHOOSE_YES_NO:
            decision = random.choice([True, False])
            game_state.add_log_entry(f"AI ({self.player_name}): Randomly chose Yes/No: {decision}", level="DEBUG")
            return decision
        
        elif choice_type_enum == PlayerChoiceType.DISCARD_CARD_OR_SACRIFICE_SPIRIT:
            # Example: For Nightmare Creep choice.
            # 'options' might be something like ["DISCARD", "SACRIFICE_SPIRIT"]
            # or the EffectEngine might just expect one of these strings as a return.
            # Let's assume for now options is a list of string identifiers for the choices.
            if isinstance(options, list) and options:
                decision = random.choice(options)
                game_state.add_log_entry(f"AI ({self.player_name}): Randomly chose from {options}: {decision}", level="DEBUG")
                return decision
            else: # Fallback if options not provided as expected
                decision = random.choice(["DISCARD", "SACRIFICE_SPIRIT"]) # Defaulting to a hardcoded random choice
                game_state.add_log_entry(f"AI ({self.player_name}): Options for {choice_type_str} not clear, defaulting random choice: {decision}", level="WARNING")

        # Generic handling for choices where 'options' is a list
        elif isinstance(options, list) and options:
            decision = random.choice(options)
            # For logging, if options are objects, we might want a more descriptive name
            log_decision = decision
            if hasattr(decision, 'name'): # e.g. if it's a Card object
                log_decision = getattr(decision, 'name')
            elif isinstance(decision, dict) and 'description' in decision:
                log_decision = decision['description']

            game_state.add_log_entry(f"AI ({self.player_name}): Randomly chose '{log_decision}' from list of options.", level="DEBUG")
            return decision

        # Add more specific random choice logic for other PlayerChoiceType members as needed.
        # For example, CHOOSE_NUMBER_FROM_RANGE would need 'min' and 'max' in choice_context.
        # CHOOSE_CARD_FROM_HAND would have 'options' as a list of Card objects.

        if decision is None:
            game_state.add_log_entry(f"AI ({self.player_name}): Could not make a random choice for '{prompt}'. Options format or choice type might be unhandled by RandomAI. Returning None.", level="WARNING")
        
        return decision


if __name__ == '__main__':
    print("RandomAI module: Implements an AI that makes random valid moves.")
    # To test this, you would integrate it into a game simulation loop.
    # Example of how it might be used (conceptual):
    #
    # from tuck_in_terrors_sim.game_logic.game_state import GameState # Mock or real
    # from tuck_in_terrors_sim.game_elements.enums import PlayerChoiceType
    #
    # ai_player = RandomAI()
    # mock_game_state = GameState(None, {}) # Highly simplified
    #
    # # Test choose_action
    # sample_actions = [
    #     {'type': 'PLAY_CARD', 'params': {'card_id': 'C001'}, 'description': 'Play Card 1'},
    #     {'type': 'ACTIVATE_ABILITY', 'params': {'ability_id': 'A001'}, 'description': 'Activate Ability 1'},
    #     {'type': 'PASS_TURN', 'params': {}, 'description': 'Pass'}
    # ]
    # chosen = ai_player.choose_action(mock_game_state, sample_actions)
    # print(f"RandomAI chose action: {chosen}")
    #
    # # Test make_choice (Yes/No)
    # yes_no_context = {
    #     'choice_id': 'test_yes_no',
    #     'choice_type': PlayerChoiceType.CHOOSE_YES_NO.name, # Assuming PlayerChoiceType is imported
    #     'prompt_text': 'Do the thing?',
    #     'options': [True, False] # Or could be inferred by choice_type
    # }
    # choice = ai_player.make_choice(mock_game_state, yes_no_context)
    # print(f"RandomAI made Yes/No choice: {choice}")
    #
    # # Test make_choice (List of options)
    # list_context = {
    #     'choice_id': 'test_list_choice',
    #     'choice_type': 'SOME_LIST_CHOICE', # A hypothetical choice type
    #     'prompt_text': 'Choose an item:',
    #     'options': ["OptionA", "OptionB", "OptionC"]
    # }
    # choice = ai_player.make_choice(mock_game_state, list_context)
    # print(f"RandomAI made list choice: {choice}")