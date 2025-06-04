# src/tuck_in_terrors_sim/ai/ai_profiles/random_ai.py
import random
from typing import TYPE_CHECKING, List, Dict, Any, Optional

from ..ai_player_base import AIPlayerBase
from ...game_elements.card import CardInstance # For type hints
from ...game_logic.game_state import PlayerState # For type hints and accessing player state
from ...game_elements.enums import Zone, PlayerChoiceType # For make_choice logic
from ...models.game_action_model import GameAction 

if TYPE_CHECKING:
    from ...game_logic.game_state import GameState


class RandomAI(AIPlayerBase):
    def __init__(self, player_id: int, game_config: Optional[Dict[str, Any]] = None):
        super().__init__(player_id, game_config)
        self.rng = random.Random()

    def decide_action(self, game_state: 'GameState', possible_actions: List['GameAction']) -> Optional['GameAction']:
        if not possible_actions:
            game_state.add_log_entry(f"AI P{self.player_id} (RandomAI): No possible actions to decide from.", "AI_DEBUG")
            return None
        
        # Prefer non-pass actions if available
        non_pass_actions = [action for action in possible_actions if action.type != "PASS_TURN"]
        if non_pass_actions:
            chosen_action = self.rng.choice(non_pass_actions)
            game_state.add_log_entry(f"AI P{self.player_id} (RandomAI) decided action: {chosen_action.description}", "AI_ACTION")
            return chosen_action
        
        # If only PASS_TURN is available, choose it (or if list was empty, which is handled above)
        chosen_action = self.rng.choice(possible_actions) 
        game_state.add_log_entry(f"AI P{self.player_id} (RandomAI) decided action: {chosen_action.description}", "AI_ACTION")
        return chosen_action

    def make_choice(self, game_state: 'GameState', choice_context: Dict[str, Any]) -> Any:
        choice_type: Optional[PlayerChoiceType] = choice_context.get("choice_type")
        options: Optional[List[Any]] = choice_context.get("options")
        prompt = choice_context.get("prompt_text", f"AI P{self.player_id} making a choice")
        game_state.add_log_entry(f"AI P{self.player_id} (RandomAI) sees choice: {prompt} (Type: {choice_type}, Options: {options})", "AI_DEBUG")

        player_s = game_state.get_player_state(self.player_id) # Get player state for context

        if choice_type == PlayerChoiceType.CHOOSE_YES_NO:
            decision = self.rng.choice([True, False])
            game_state.add_log_entry(f"AI P{self.player_id} chose: {'YES' if decision else 'NO'} for '{prompt}'", "AI_CHOICE")
            return decision
        
        elif choice_type == PlayerChoiceType.DISCARD_CARD_OR_SACRIFICE_SPIRIT:
            can_discard = False
            if player_s and player_s.zones.get(Zone.HAND):
                can_discard = True
            
            can_sacrifice_spirit = False
            if player_s and player_s.spirit_tokens > 0:
                can_sacrifice_spirit = True

            available_choices = []
            if can_discard: available_choices.append("DISCARD")
            if can_sacrifice_spirit: available_choices.append("SACRIFICE_SPIRIT")

            if not available_choices: # Cannot do either
                game_state.add_log_entry(f"AI P{self.player_id}: Cannot satisfy DISCARD_CARD_OR_SACRIFICE_SPIRIT. Defaulting to 'fail sacrifice' (False).", "WARNING")
                return False # Corresponds to "no" / "sacrifice" path, engine handles inability

            chosen_ai_option = self.rng.choice(available_choices)
            game_state.add_log_entry(f"AI P{self.player_id} chose: {chosen_ai_option} for '{prompt}'", "AI_CHOICE")
            return chosen_ai_option == "DISCARD" # True if discard, False if sacrifice

        elif options and isinstance(options, list) and options:
            decision = self.rng.choice(options)
            game_state.add_log_entry(f"AI P{self.player_id} chose: {decision} from options for '{prompt}'", "AI_CHOICE")
            return decision
        else: 
            game_state.add_log_entry(f"AI P{self.player_id}: No options for {choice_type} or type unhandled. Defaulting to None for '{prompt}'.", "WARNING")
            return None # Default for unhandled or option-less choices

    def choose_targets(self, game_state: 'GameState', action_params: Dict[str, Any], num_targets: int, target_filter: Dict[str, Any]) -> List[str]:
        player_s = game_state.get_player_state(self.player_id)
        if not player_s: return []
        
        # Simplified: get all card instances in play controlled by the player
        # A real AI would use target_filter to narrow down valid targets
        potential_targets = [inst.instance_id for inst in game_state.cards_in_play.values() if inst.controller_id == self.player_id]
        
        if not potential_targets: return []
        
        actual_num_to_choose = min(num_targets, len(potential_targets))
        if actual_num_to_choose == 0 and num_targets > 0: return []
        
        chosen_targets = self.rng.sample(potential_targets, actual_num_to_choose)
        game_state.add_log_entry(f"AI P{self.player_id} chose targets: {chosen_targets}", "AI_DEBUG")
        return chosen_targets

    def choose_cards_to_discard(self, game_state: 'GameState', num_to_discard: int, reason: Optional[str] = None) -> List[str]:
        player_s = game_state.get_player_state(self.player_id)
        if not player_s: return []

        hand_instances = player_s.zones.get(Zone.HAND, [])
        if not hand_instances: return []
        
        hand_card_ids = [card.instance_id for card in hand_instances]
        
        actual_num_to_discard = min(num_to_discard, len(hand_card_ids))
        if actual_num_to_discard == 0: return []
        
        chosen_to_discard_ids = self.rng.sample(hand_card_ids, actual_num_to_discard)
        game_state.add_log_entry(f"AI P{self.player_id} chose to discard IDs: {chosen_to_discard_ids} (Reason: {reason or 'N/A'})", "AI_ACTION")
        return chosen_to_discard_ids