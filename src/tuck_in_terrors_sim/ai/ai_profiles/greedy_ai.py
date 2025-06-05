# src/tuck_in_terrors_sim/ai/ai_profiles/greedy_ai.py
import random
from typing import TYPE_CHECKING, List, Dict, Any, Optional

from .random_ai import RandomAI
from ...game_elements.card import CardType

if TYPE_CHECKING:
    from ...game_logic.game_state import GameState
    from ...models.game_action_model import GameAction


class GreedyAI(RandomAI):
    """
    A simple 'greedy' AI that prioritizes actions that directly contribute to the
    current objective's win condition. For other choices, it behaves randomly.
    """

    def decide_action(self, game_state: 'GameState', possible_actions: List['GameAction']) -> Optional['GameAction']:
        """
        Overrides the random choice to greedily select actions that help the objective.
        """
        if not possible_actions:
            return None

        # Check the primary win condition for the current objective
        win_con = game_state.current_objective.primary_win_condition
        
        # For "The First Night" (OBJ01), we want to play toys.
        if win_con and win_con.component_type == "PLAY_X_DIFFERENT_TOYS_AND_CREATE_Y_SPIRITS":
            
            # Find all actions that involve playing a toy.
            toy_playing_actions = []
            for action in possible_actions:
                if action.type == "PLAY_CARD":
                    card_id = action.params.get("card_id")
                    card_instance = game_state.get_card_instance(card_id)
                    if card_instance and card_instance.definition.type == CardType.TOY:
                        toy_playing_actions.append(action)

            # If there are toy-playing actions available, choose one of them randomly.
            if toy_playing_actions:
                chosen_action = self.rng.choice(toy_playing_actions)
                game_state.add_log_entry(f"AI P{self.player_id} (GreedyAI) chose priority action: {chosen_action.description}", "AI_ACTION")
                return chosen_action

        # If no priority actions are found, fall back to the RandomAI's behavior.
        return super().decide_action(game_state, possible_actions)