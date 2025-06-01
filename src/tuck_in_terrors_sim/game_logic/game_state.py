# src/tuck_in_terrors_sim/game_logic/game_state.py
# Defines GameState class for tracking all dynamic game info

from typing import List, Dict, Any, Optional
import uuid # For unique card instance IDs

# Assuming your enums and card/objective definitions are accessible
# For relative imports from sibling directories (game_elements)
from ..game_elements.enums import Zone, TurnPhase, CardType
from ..game_elements.card import Card, EffectLogic # Assuming EffectLogic might be tracked
from ..game_elements.objective import ObjectiveCard

class CardInPlay:
    """
    Represents a unique instance of a card in the play area,
    tracking its state (e.g., tapped, counters).
    """
    def __init__(self, base_card: Card):
        self.instance_id: str = f"play_{base_card.card_id}_{uuid.uuid4().hex[:8]}"
        self.card_definition: Card = base_card # Reference to the original card definition
        self.is_tapped: bool = False
        self.counters: Dict[str, int] = {} # e.g., {"power": 2, "damage": 1}
        self.attachments: List['CardInPlay'] = [] # For cards attached to this card
        self.effects_active_this_turn: Dict[str, bool] = {} # For tracking once-per-turn effects (key by effect_id or description)
        self.turns_in_play: int = 0 # Incremented at the start of player's turn if card is in play

    def __repr__(self):
        return f"CardInPlay(ID: {self.instance_id}, Name: {self.card_definition.name}, Tapped: {self.is_tapped})"

    def tap(self):
        self.is_tapped = True

    def untap(self):
        self.is_tapped = False

    def add_counter(self, counter_type: str, amount: int = 1):
        self.counters[counter_type] = self.counters.get(counter_type, 0) + amount

    def remove_counter(self, counter_type: str, amount: int = 1):
        current_amount = self.counters.get(counter_type, 0)
        self.counters[counter_type] = max(0, current_amount - amount)
        if self.counters[counter_type] == 0:
            del self.counters[counter_type] # Clean up if counter type is depleted


class GameState:
    """
    Holds all the dynamic information for a single game instance of Tuck'd-In Terrors.
    """
    def __init__(self, loaded_objective: ObjectiveCard, all_card_definitions: Dict[str, Card]):
        # Core Game Identifiers & Data
        self.current_objective: ObjectiveCard = loaded_objective
        self.all_card_definitions: Dict[str, Card] = all_card_definitions # For easy lookup

        # Player's Zones & Resources
        self.deck: List[Card] = []
        self.hand: List[Card] = []
        self.discard_pile: List[Card] = []
        self.exile_zone: List[Card] = []
        self.cards_in_play: Dict[str, CardInPlay] = {} # Key: instance_id of CardInPlay

        self.mana_pool: int = 0
        self.spirit_tokens: int = 0
        self.memory_tokens: int = 0

        # First Memory Tracking
        self.first_memory_card_definition: Optional[Card] = None
        self.first_memory_instance_id: Optional[str] = None    # Instance ID if/when in play
        self.first_memory_current_zone: Optional[Zone] = None
        # self.first_memory_evolved_abilities: List[EffectLogic] = [] # For later if implementing evolution

        # Turn & Phase Tracking
        self.current_turn: int = 0 # Will be set to 1 by game_setup
        self.current_phase: Optional[TurnPhase] = None

        # Nightmare Creep Tracking
        self.nightmare_creep_effect_applied_this_turn: bool = False

        # Objective Progress Tracking
        self.objective_progress: Dict[str, Any] = self.initialize_objective_progress()

        # Game Flags/State Variables
        self.free_toy_played_this_turn: bool = False
        self.flashback_used_this_game: bool = False
        self.storm_count_this_turn: int = 0

        self.game_over: bool = False
        self.win_status: Optional[str] = None # E.g., "PRIMARY_WIN", "ALTERNATIVE_WIN", "LOSS_NIGHTFALL"

        self.game_log: List[str] = []

    def initialize_objective_progress(self) -> Dict[str, Any]:
        """
        Initializes the objective_progress dictionary based on the current objective.
        This can be expanded to be more dynamic based on objective needs.
        """
        # Basic common trackers, can be expanded by game_setup based on objective types
        progress = {
            "toys_played_this_game_count": 0,
            "distinct_toys_played_ids": set(),
            "spirits_created_total_game": 0,
            "mana_from_card_effects_total_game": 0,
            # Add more specific trackers as needed by objectives here or in game_setup
        }
        # Example: if primary win condition is "PLAY_X_DIFFERENT_TOYS_AND_CREATE_Y_SPIRITS"
        if self.current_objective and self.current_objective.primary_win_condition:
            if self.current_objective.primary_win_condition.component_type == "PLAY_X_DIFFERENT_TOYS_AND_CREATE_Y_SPIRITS":
                progress["primary_toys_needed"] = self.current_objective.primary_win_condition.params.get("toys_needed", 0)
                progress["primary_spirits_needed"] = self.current_objective.primary_win_condition.params.get("spirits_needed", 0)
        # Add similar for alternative win con if needed for tracking
        return progress

    def add_log_entry(self, message: str, level: str = "INFO"):
        turn_info = f"T{self.current_turn}"
        phase_info = self.current_phase.name if self.current_phase else "PREGAME"
        self.game_log.append(f"[{level}] {turn_info} ({phase_info}): {message}")

    def get_card_in_play_by_instance_id(self, instance_id: str) -> Optional[CardInPlay]:
        return self.cards_in_play.get(instance_id)

    def move_card_object_between_zones(self, card_obj: Card, from_zone_list: List[Card], to_zone_list: List[Card]):
        """ Helper to move a known card object between two zone lists. """
        try:
            from_zone_list.remove(card_obj) # Relies on object identity or proper __eq__
            to_zone_list.append(card_obj)
            self.add_log_entry(f"Moved card '{card_obj.name}' from {from_zone_list_name(from_zone_list, self)} to {from_zone_list_name(to_zone_list, self)}.")
        except ValueError:
            self.add_log_entry(f"Error: Card '{card_obj.name}' not found in specified from_zone during move.", level="ERROR")

    def __repr__(self):
        return (f"<GameState: Turn {self.current_turn}, Phase: {self.current_phase.name if self.current_phase else 'None'}, "
                f"Mana: {self.mana_pool}, Spirits: {self.spirit_tokens}, Memory: {self.memory_tokens}, "
                f"Hand: {len(self.hand)}, Deck: {len(self.deck)}, InPlay: {len(self.cards_in_play)}, "
                f"Discard: {len(self.discard_pile)}, Objective: {self.current_objective.title if self.current_objective else 'None'}>")

# Helper to get zone name for logging, not part of the class
def from_zone_list_name(zone_list: List[Card], game_state: GameState) -> str:
    if zone_list is game_state.deck: return "Deck"
    if zone_list is game_state.hand: return "Hand"
    if zone_list is game_state.discard_pile: return "Discard"
    if zone_list is game_state.exile_zone: return "Exile"
    return "UnknownZone"