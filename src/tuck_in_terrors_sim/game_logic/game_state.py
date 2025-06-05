# src/tuck_in_terrors_sim/game_logic/game_state.py
# Defines GameState class for tracking all dynamic game info

from typing import List, Dict, Any, Optional, Set # Added Set
import uuid # For unique card instance IDs, though CardInstance handles its own

# Assuming your enums and card/objective definitions are accessible
# For relative imports from sibling directories (game_elements)
from ..game_elements.enums import Zone, TurnPhase, CardType
# Updated import: Using Effect and CardInstance from the corrected card.py
from ..game_elements.card import Card, Effect, CardInstance
from ..game_elements.objective import ObjectiveCard
from ..ai.ai_player_base import AIPlayerBase

# The CardInPlay class previously defined here is now superseded by CardInstance from card.py

class PlayerState: # Assuming a single-player game, this can be integrated or kept separate
    """Holds state specific to the player."""
    def __init__(self, player_id: int, initial_deck: List[Card]):
        self.player_id = player_id
        self.deck: List[Card] = initial_deck # List of Card definitions
        self.hand: List[CardInstance] = [] # Typically CardInstance for cards in hand to track unique properties if any
        self.discard_pile: List[CardInstance] = []
        self.exile_zone: List[CardInstance] = []
        self.set_aside_zone: List[CardInstance] = [] # For cards temporarily out of main zones

        self.mana: int = 0
        self.spirit_tokens: int = 0
        self.memory_tokens: int = 0
        
        self.zones: Dict[Zone, List[CardInstance]] = {
            Zone.DECK: [], # Will store CardInstance objects; initial deck of Card defs needs conversion
            Zone.HAND: self.hand,
            Zone.DISCARD: self.discard_pile,
            Zone.EXILE: self.exile_zone,
            Zone.IN_PLAY: [], # This will be managed by GameState.cards_in_play for direct dict access
            Zone.SET_ASIDE: self.set_aside_zone,
            Zone.BEING_CAST: [] # Temporarily holds card being cast
        }
        # Note: GameState.cards_in_play will be the primary way to access cards in Zone.IN_PLAY

        self.has_played_free_toy_this_turn: bool = False
        self.first_memory_card_id: Optional[str] = None # card_id of the definition
        
        # Method to convert initial deck of Card definitions to CardInstance objects
        self._initialize_deck_with_instances(initial_deck)

    def _initialize_deck_with_instances(self, initial_deck_definitions: List[Card]):
        self.zones[Zone.DECK] = [CardInstance(definition=card_def, owner_id=self.player_id, current_zone=Zone.DECK) for card_def in initial_deck_definitions]


    def draw_cards(self, count: int, game_state: 'GameState'): # Added game_state for logging
        drawn_instances = []
        for _ in range(count):
            if self.zones[Zone.DECK]:
                card_instance = self.zones[Zone.DECK].pop(0) # Draw from top (index 0)
                card_instance.change_zone(Zone.HAND, game_state.current_turn)
                self.zones[Zone.HAND].append(card_instance)
                drawn_instances.append(card_instance)
                game_state.add_log_entry(f"Player {self.player_id} drew {card_instance.definition.name} ({card_instance.instance_id})")
            else:
                game_state.add_log_entry(f"Player {self.player_id} tried to draw, but deck is empty.", level="WARNING")
                # TODO: Implement loss condition for drawing from empty deck if applicable
                break
        return drawn_instances

    def mill_deck(self, count: int, game_state: 'GameState'): # Added game_state
        milled_cards_info = []
        for _ in range(count):
            if self.zones[Zone.DECK]:
                card_instance = self.zones[Zone.DECK].pop(0)
                card_instance.change_zone(Zone.DISCARD, game_state.current_turn)
                self.zones[Zone.DISCARD].append(card_instance)
                milled_cards_info.append(f"{card_instance.definition.name} ({card_instance.instance_id})")
            else:
                game_state.add_log_entry(f"Player {self.player_id} deck empty, cannot mill further.", level="INFO")
                break
        if milled_cards_info:
            game_state.add_log_entry(f"Player {self.player_id} milled: {', '.join(milled_cards_info)}.")


class GameState:
    """
    Holds all the dynamic information for a single game instance of Tuck'd-In Terrors.
    """
    def __init__(self, loaded_objective: ObjectiveCard, all_card_definitions: Dict[str, Card]):
        # Core Game Identifiers & Data
        self.current_objective: ObjectiveCard = loaded_objective
        self.all_card_definitions: Dict[str, Card] = all_card_definitions # For easy lookup

        # Player State (assuming single player for now)
        # This will be initialized by game_setup
        self.player_states: Dict[int, PlayerState] = {} # player_id -> PlayerState
        self.active_player_id: Optional[int] = None # Usually player 1 in a solo game

        # Cards in play are CardInstance objects, keyed by their instance_id
        # This provides quick lookup for cards on the battlefield.
        self.cards_in_play: Dict[str, CardInstance] = {}

        # First Memory Tracking (refers to CardInstance when in a zone)
        self.first_memory_instance_id: Optional[str] = None
        # self.first_memory_evolved_abilities: List[Effect] = [] # Use Effect if uncommented

        # Turn & Phase Tracking
        self.current_turn: int = 0 # Will be set to 1 by game_setup
        self.current_phase: Optional[TurnPhase] = None

        # Nightmare Creep Tracking
        self.nightmare_creep_effect_applied_this_turn: bool = False
        self.nightmare_creep_skipped_this_turn: bool = False # If an effect skips NC

        # Objective Progress Tracking
        self.objective_progress: Dict[str, Any] = self._initialize_objective_progress()

        # Game Flags/State Variables
        self.game_over: bool = False
        self.win_status: Optional[str] = None # E.g., "PRIMARY_WIN", "ALTERNATIVE_WIN", "LOSS_NIGHTFALL"
        self.reason_for_game_end: str = ""
        self.storm_count_this_turn: int = 0 # ADDED FOR STORM MECHANIC

        self.game_log: List[str] = []
        self.ai_agents: Dict[int, AIPlayerBase] = {} # player_id -> AIPlayerBase instance
        
        # Global effects or state modifiers
        self.replacement_effects: List[Dict[str, Any]] = [] # Store details of active replacement effects
        self.triggered_effects_queue: List[Dict[str, Any]] = [] # Effects waiting to go on stack

    def _initialize_objective_progress(self) -> Dict[str, Any]:
        progress = {
            "toys_played_this_game_count": 0,
            "distinct_toys_played_ids": set(),
            "spirits_created_total_game": 0,
            "mana_from_card_effects_total_game": 0,
        }
        if self.current_objective and self.current_objective.primary_win_condition:
            pwc_params = self.current_objective.primary_win_condition.params
            pwc_type = self.current_objective.primary_win_condition.component_type
            # Example, can be more dynamic based on component_type and params keys
            if "toys_needed" in pwc_params: progress["primary_toys_needed"] = pwc_params["toys_needed"]
            if "spirits_needed" in pwc_params: progress["primary_spirits_needed"] = pwc_params["spirits_needed"]
            # Add more specific trackers based on self.current_objective.primary_win_condition.component_type
        if self.current_objective and self.current_objective.alternative_win_condition:
            awc_params = self.current_objective.alternative_win_condition.params
            # Example for alternative win con tracking
            if "mana_needed_from_effects" in awc_params: progress["alt_mana_needed"] = awc_params["mana_needed_from_effects"]

        return progress

    def add_log_entry(self, message: str, level: str = "INFO"):
        turn_info = f"T{self.current_turn}"
        phase_info = self.current_phase.name if self.current_phase else "SETUP"
        self.game_log.append(f"[{level}][{turn_info}][{phase_info}] {message}")

    def get_card_instance(self, instance_id: Optional[str]) -> Optional[CardInstance]:
        if not instance_id:
            return None
        # Check cards in play first
        if instance_id in self.cards_in_play:
            return self.cards_in_play[instance_id]
        
        # Check other zones for all players (assuming player_states is populated)
        for player_id, player_state in self.player_states.items():
            for zone, card_list in player_state.zones.items():
                if zone == Zone.IN_PLAY: continue # Already checked via self.cards_in_play
                for card_instance in card_list:
                    if card_instance.instance_id == instance_id:
                        return card_instance
        self.add_log_entry(f"CardInstance with ID '{instance_id}' not found in any known zone.", "WARNING")
        return None

    def get_player_state(self, player_id: int) -> Optional[PlayerState]:
        return self.player_states.get(player_id)

    def get_active_player_state(self) -> Optional[PlayerState]:
        if self.active_player_id is None:
            return None
        return self.get_player_state(self.active_player_id)
        
    def get_player_agent(self, player_id: int) -> Optional[AIPlayerBase]:
        return self.ai_agents.get(player_id)

    def get_active_player_agent(self) -> Optional[AIPlayerBase]:
        if self.active_player_id is None:
            return None
        return self.get_player_agent(self.active_player_id)

    def get_first_memory_instance(self) -> Optional[CardInstance]:
        if self.first_memory_instance_id:
            return self.get_card_instance(self.first_memory_instance_id)
        # Fallback: if FM is not instanced yet (e.g. in deck/hand/discard as definition)
        # This part might need refinement based on how FM is tracked before becoming an instance.
        active_player = self.get_active_player_state()
        if active_player and active_player.first_memory_card_id:
            # Search non-play zones for an instance matching the FM definition ID
            for zone_type, card_list in active_player.zones.items():
                if zone_type != Zone.IN_PLAY: # IN_PLAY should use first_memory_instance_id
                    for card_inst in card_list:
                        if card_inst.definition.card_id == active_player.first_memory_card_id:
                            # This assumes FM in hand/deck/discard is already an instance.
                            # If these zones store Card definitions, this logic needs to change.
                            # For now, aligns with PlayerState.zones storing CardInstance.
                            return card_inst 
        return None


    def create_card_instance_from_definition(self, card_def: Card, owner_id: int, initial_zone: Zone = Zone.SET_ASIDE) -> CardInstance:
        instance = CardInstance(definition=card_def, owner_id=owner_id, current_zone=initial_zone)
        # Log creation or handle adding to a temporary "limbo" zone if not immediately placed
        self.add_log_entry(f"Created instance {instance.instance_id} for {card_def.name} for player {owner_id} in zone {initial_zone.name}")
        return instance

    def move_card_zone(self, card_instance: CardInstance, new_zone_type: Zone, target_player_id: Optional[int] = None):
        """Moves a CardInstance to a new zone."""
        if target_player_id is None:
            target_player_id = card_instance.controller_id # Default to current controller for new zone

        target_player_state = self.get_player_state(target_player_id)
        if not target_player_state:
            self.add_log_entry(f"Cannot move {card_instance.instance_id}: Target player {target_player_id} not found.", "ERROR")
            return

        current_owner_state = self.get_player_state(card_instance.owner_id) # Original owner for some zones like discard
        if not current_owner_state: # Should not happen if card has valid owner
             self.add_log_entry(f"Cannot move {card_instance.instance_id}: Original owner {card_instance.owner_id} not found.", "ERROR")
             return


        old_zone_type = card_instance.current_zone
        old_zone_player_id = card_instance.controller_id # Assume card was in controller's zone

        # Remove from old zone
        if old_zone_type == Zone.IN_PLAY:
            if card_instance.instance_id in self.cards_in_play:
                del self.cards_in_play[card_instance.instance_id]
            # Also remove from the player's specific IN_PLAY list if they have one (current PlayerState.zones[Zone.IN_PLAY] is a bit redundant)
            old_player_state_for_in_play = self.get_player_state(old_zone_player_id)
            if old_player_state_for_in_play and card_instance in old_player_state_for_in_play.zones[Zone.IN_PLAY]:
                 old_player_state_for_in_play.zones[Zone.IN_PLAY].remove(card_instance)

        else: # Other zones are in PlayerState.zones
            old_player_state = self.get_player_state(old_zone_player_id)
            if old_player_state and card_instance in old_player_state.zones[old_zone_type]:
                old_player_state.zones[old_zone_type].remove(card_instance)
            else:
                self.add_log_entry(f"Card {card_instance.instance_id} not found in player {old_zone_player_id}'s zone {old_zone_type.name} for removal.", "WARNING")
        
        # Update card's internal zone and controller if changing
        card_instance.change_zone(new_zone_type, self.current_turn)
        card_instance.controller_id = target_player_id # Controller might change with zone

        # Add to new zone
        if new_zone_type == Zone.IN_PLAY:
            self.cards_in_play[card_instance.instance_id] = card_instance
            # Also add to player's IN_PLAY list for consistency if PlayerState.zones[Zone.IN_PLAY] is used
            target_player_state.zones[Zone.IN_PLAY].append(card_instance)
        elif new_zone_type in [Zone.DISCARD, Zone.EXILE] and new_zone_type in current_owner_state.zones:
            # Discard and Exile typically go to owner's zone
            card_instance.controller_id = card_instance.owner_id # Controller becomes owner
            current_owner_state.zones[new_zone_type].append(card_instance)
        elif new_zone_type in target_player_state.zones:
            target_player_state.zones[new_zone_type].append(card_instance)
        else:
            self.add_log_entry(f"Target zone {new_zone_type.name} not recognized in PlayerState for player {target_player_id}.", "ERROR")
            return

        self.add_log_entry(f"Moved {card_instance.definition.name} ({card_instance.instance_id}) from P{old_zone_player_id}'s {old_zone_type.name} to P{target_player_id}'s {new_zone_type.name}.")
        
        # TODO: Trigger zone change events


    def __repr__(self):
        active_player_s = self.get_active_player_state()
        mana_info = active_player_s.mana if active_player_s else "N/A"
        spirit_info = active_player_s.spirit_tokens if active_player_s else "N/A"
        memory_info = active_player_s.memory_tokens if active_player_s else "N/A"
        hand_size = len(active_player_s.zones[Zone.HAND]) if active_player_s else "N/A"
        deck_size = len(active_player_s.zones[Zone.DECK]) if active_player_s else "N/A"
        
        return (f"<GameState: Turn {self.current_turn}, Phase: {self.current_phase.name if self.current_phase else 'None'}, "
                f"Player {self.active_player_id} - Mana: {mana_info}, Spirits: {spirit_info}, Memory: {memory_info}, "
                f"Hand: {hand_size}, Deck: {deck_size}, InPlay: {len(self.cards_in_play)}, "
                f"Objective: {self.current_objective.title if self.current_objective else 'None'}>")