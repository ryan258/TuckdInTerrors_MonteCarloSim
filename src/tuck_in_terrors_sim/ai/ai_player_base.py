# src/tuck_in_terrors_sim/ai/ai_player_base.py
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List, Dict, Any, Optional

if TYPE_CHECKING:
    from ..game_logic.game_state import GameState
    from ..models.game_action_model import GameAction
    from ..game_elements.card import CardInstance # For type hinting if needed

class AIPlayerBase(ABC):
    def __init__(self, player_id: int, game_config: Optional[Dict[str, Any]] = None):
        self.player_id = player_id
        self.game_config = game_config if game_config is not None else {}

    @property
    def player_name(self) -> str:
        return f"AI Player {self.player_id}"

    @abstractmethod
    def decide_action(self, game_state: 'GameState', possible_actions: List['GameAction']) -> Optional['GameAction']:
        """Decide the next game action to take from the provided list."""
        pass

    @abstractmethod
    def make_choice(self, game_state: 'GameState', choice_context: Dict[str, Any]) -> Any:
        """Make a decision when presented with a choice by the game engine."""
        pass
    
    @abstractmethod
    def choose_targets(self, game_state: 'GameState', action_params: Dict[str, Any], num_targets: int, target_filter: Dict[str, Any]) -> List[str]:
        """
        Choose target instance_ids for an action if required.
        action_params: The parameters of the action/effect requiring targeting.
        num_targets: How many targets to choose.
        target_filter: A dictionary describing valid targets.
        Returns a list of chosen target instance_ids.
        """
        pass
    
    @abstractmethod
    def choose_cards_to_discard(self, game_state: 'GameState', num_to_discard: int, reason: Optional[str] = None) -> List[str]:
        """Choose card instance_ids from hand to discard."""
        pass