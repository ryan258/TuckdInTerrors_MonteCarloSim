# src/tuck_in_terrors_sim/ai/ai_profiles/random_ai.py
# Implements basic AI that makes random valid moves

import random
from typing import List, Any, Dict, TYPE_CHECKING

from tuck_in_terrors_sim.ai.ai_player_base import AIPlayerBase
from tuck_in_terrors_sim.game_elements.enums import PlayerChoiceType 
from tuck_in_terrors_sim.game_elements.card import Card # Added import for type checking

if TYPE_CHECKING:
    from tuck_in_terrors_sim.game_logic.game_state import GameState
    # from tuck_in_terrors_sim.game_elements.card import Card # Already imported above


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
            game_state.add_log_entry(f"AI ({self.player_name}): No valid actions provided to choose_action. This is unexpected.", level="WARNING")
            return {'type': 'PASS_TURN', 'params': {}} 

        non_pass_actions = [action for action in valid_actions if action.get('type') != 'PASS_TURN']
        pass_action = next((action for action in valid_actions if action.get('type') == 'PASS_TURN'), None)

        if non_pass_actions:
            chosen_action = random.choice(non_pass_actions)
            game_state.add_log_entry(f"AI ({self.player_name}): Randomly chose action: {chosen_action.get('description', chosen_action.get('type'))}", level="DEBUG")
            return chosen_action
        elif pass_action:
            game_state.add_log_entry(f"AI ({self.player_name}): Only PASS_TURN action available or chosen.", level="DEBUG")
            return pass_action
        else:
            game_state.add_log_entry(f"AI ({self.player_name}): No actions (not even PASS_TURN) found in valid_actions. Critical error.", level="ERROR")
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
            # Options should be ["DISCARD", "SACRIFICE_SPIRIT"] or similar
            if isinstance(options, list) and options:
                decision = random.choice(options)
            else: 
                game_state.add_log_entry(f"AI ({self.player_name}): Options for {choice_type_str} not clear or missing, defaulting to random choice between DISCARD/SACRIFICE_SPIRIT.", level="WARNING")
                decision = random.choice(["DISCARD", "SACRIFICE_SPIRIT"]) 
            game_state.add_log_entry(f"AI ({self.player_name}): For {choice_type_str}, chose: {decision}", level="DEBUG")
            return decision

        elif choice_type_enum == PlayerChoiceType.CHOOSE_CARD_FROM_HAND:
            # 'options' should be a list of Card objects currently in hand, passed by EffectEngine
            if isinstance(options, list) and options: 
                # Ensure options are actually Card objects as expected by EffectEngine when processing discard
                valid_card_options = [opt for opt in options if isinstance(opt, Card)]
                if valid_card_options:
                    decision = random.choice(valid_card_options)
                    game_state.add_log_entry(f"AI ({self.player_name}): Randomly chose card from hand: '{decision.name if decision else 'None'}'", level="DEBUG")
                    return decision
                else:
                    game_state.add_log_entry(f"AI ({self.player_name}): No valid Card objects in options for CHOOSE_CARD_FROM_HAND. Options: {options}", level="WARNING")
                    return None # Cannot make a choice
            else: # Hand is empty or options malformed
                game_state.add_log_entry(f"AI ({self.player_name}): Cannot CHOOSE_CARD_FROM_HAND, hand is empty or options malformed. Options: {options}", level="INFO")
                return None
        
        # Generic handling for other choices where 'options' is a list
        elif isinstance(options, list) and options:
            decision = random.choice(options)
            log_decision = decision # Default log
            if hasattr(decision, 'name'): # e.g. if it's a Card object
                log_decision = getattr(decision, 'name')
            elif isinstance(decision, dict) and 'description' in decision: # e.g. if it's an action dict
                log_decision = decision['description']
            game_state.add_log_entry(f"AI ({self.player_name}): Randomly chose '{log_decision}' from generic list of options.", level="DEBUG")
            return decision
        
        if decision is None: # Fallback if no specific logic matched or options were unsuitable
            game_state.add_log_entry(f"AI ({self.player_name}): Could not make a random choice for '{prompt}' (Type: {choice_type_str}). Options format or choice type might be unhandled by RandomAI. Returning None.", level="WARNING")
        
        return decision