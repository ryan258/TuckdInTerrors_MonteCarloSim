# src/tuck_in_terrors_sim/ai/ai_profiles/scoring_ai.py
import random
from typing import TYPE_CHECKING, List, Dict, Any, Optional

from .random_ai import RandomAI
from ...game_elements.card import CardType, EffectActionType
from ...models.game_action_model import GameAction
from ...game_elements.enums import PlayerChoiceType

if TYPE_CHECKING:
    from ...game_logic.game_state import GameState


class ScoringAI(RandomAI):
    """
    An AI that scores possible actions based on how well they advance the
    current objective and chooses the best one.
    """

    def _get_action_score(self, action: 'GameAction', game_state: 'GameState') -> float:
        """Assigns a score to a single action based on the game state."""
        win_con = game_state.current_objective.primary_win_condition
        if not win_con:
            return 0

        # For "The First Night", score playing toys and creating spirits.
        if win_con.component_type == "PLAY_X_DIFFERENT_TOYS_AND_CREATE_Y_SPIRITS":
            score = 0
            # Base score for any non-pass action
            if action.type != "PASS_TURN":
                score += 1

            if action.type == "PLAY_CARD":
                card_id = action.params.get("card_id")
                card_instance = game_state.get_card_instance(card_id)
                if not card_instance:
                    return score

                # Heavily score playing a toy
                if card_instance.definition.type == CardType.TOY:
                    score += 10
                
                # Score cards that create spirits
                for effect in card_instance.definition.effects:
                    for effect_action in effect.actions:
                        if effect_action.action_type == EffectActionType.CREATE_SPIRIT_TOKENS:
                            score += 5 # Add points for spirit creation potential
                            break
            
            # You could add scoring for ACTIVATE_ABILITY here as well
            
            return score

        # Default score for unhandled objectives
        return 1 if action.type != "PASS_TURN" else 0

    def make_choice(self, game_state: 'GameState', choice_context: Dict[str, Any]) -> Any:
        """
        Overrides the default random choice to make smarter decisions,
        especially regarding the Nightmare Creep.
        """
        choice_type = choice_context.get("choice_type")

        # If faced with the Nightmare Creep choice, be smart about it.
        if choice_type == PlayerChoiceType.DISCARD_CARD_OR_SACRIFICE_SPIRIT:
            player_state = game_state.get_player_state(self.player_id)
            
            # If we have spirit tokens, ALWAYS use them instead of discarding a card.
            if player_state and player_state.spirit_tokens > 0:
                game_state.add_log_entry(f"AI P{self.player_id} (ScoringAI) chose to sacrifice a spirit to Nightmare Creep.", "AI_CHOICE")
                return "sacrifice" # Corresponds to the 'on_sacrifice_actions' in the effect

        # For all other choices, fall back to the default random behavior.
        return super().make_choice(game_state, choice_context)

    def decide_action(self, game_state: 'GameState', possible_actions: List['GameAction']) -> Optional['GameAction']:
        """Chooses the action with the highest score."""
        if not possible_actions:
            return None

        scored_actions = []
        for action in possible_actions:
            score = self._get_action_score(action, game_state)
            scored_actions.append((score, action))

        # Find the maximum score
        if not scored_actions:
            return super().decide_action(game_state, possible_actions)

        max_score = max(s[0] for s in scored_actions)
        
        # If the best actions are just "pass" or generic, don't bother logging greedily
        if max_score <= 1:
            return super().decide_action(game_state, possible_actions)

        # Get all actions that have the maximum score
        best_actions = [a for s, a in scored_actions if s == max_score]

        # Randomly choose from the best actions
        chosen_action = self.rng.choice(best_actions)
        game_state.add_log_entry(f"AI P{self.player_id} (ScoringAI) chose best action: {chosen_action.description} (Score: {max_score})", "AI_ACTION")
        return chosen_action