# src/tuck_in_terrors_sim/ai/ai_profiles/scoring_ai.py

from typing import TYPE_CHECKING, List, Dict, Any, Optional

from .random_ai import RandomAI
from ...game_elements.card import CardType
from ...game_elements.enums import EffectActionType, PlayerChoiceType

if TYPE_CHECKING:
    from ...game_logic.game_state import GameState
    from ...models.game_action_model import GameAction


class ScoringAI(RandomAI):
    """
    An AI that scores possible actions based on how well they advance the
    current objective and chooses the best one. It is also aware of key choices.
    """

    def _get_action_score(self, action: 'GameAction', game_state: 'GameState') -> float:
        """Assigns a score to a single action based on the game state's needs."""
        win_con = game_state.current_objective.primary_win_condition
        if not win_con or win_con.component_type != "PLAY_X_DIFFERENT_TOYS_AND_CREATE_Y_SPIRITS":
            return 1.0 if action.type != "PASS_TURN" else 0

        progress = game_state.objective_progress
        toys_played_count = len(progress.get("distinct_toys_played_ids", set()))
        spirits_created_count = progress.get("spirits_created_total_game", 0)

        toys_needed_to_win = win_con.params.get("toys_needed", 4)
        spirits_needed_to_win = win_con.params.get("spirits_needed", 4)

        score = 1.0

        if action.type == "PLAY_CARD":
            card_id = action.params.get("card_id")
            card_instance = game_state.get_card_instance(card_id)
            if not card_instance:
                return score

            if card_instance.definition.type == CardType.TOY:
                if toys_played_count < toys_needed_to_win:
                    score += 10

            creates_spirits = any(
                ea.action_type == EffectActionType.CREATE_SPIRIT_TOKENS
                for effect in card_instance.definition.effects
                for ea in effect.actions
            )
            if creates_spirits:
                if spirits_created_count < spirits_needed_to_win:
                    score += 10
        
        elif action.type == "ACTIVATE_ABILITY":
            score += 2

        return score

    def make_choice(self, game_state: 'GameState', choice_context: Dict[str, Any]) -> Any:
        """Overrides the default random choice to make smarter decisions."""
        choice_type = choice_context.get("choice_type")

        if choice_type == PlayerChoiceType.DISCARD_CARD_OR_SACRIFICE_SPIRIT:
            player_state = game_state.get_player_state(self.player_id)
            if player_state and player_state.spirit_tokens > 0:
                return "sacrifice"

        return super().make_choice(game_state, choice_context)

    def decide_action(self, game_state: 'GameState', possible_actions: List['GameAction']) -> Optional['GameAction']:
        """Chooses the action with the highest score."""
        if not possible_actions:
            return None

        scored_actions = [(self._get_action_score(action, game_state), action) for action in possible_actions]
        if not scored_actions:
            return super().decide_action(game_state, possible_actions)

        max_score = max(s[0] for s in scored_actions)
        if max_score <= 1:
            return super().decide_action(game_state, possible_actions)

        best_actions = [a for s, a in scored_actions if s == max_score]
        chosen_action = self.rng.choice(best_actions)
        return chosen_action