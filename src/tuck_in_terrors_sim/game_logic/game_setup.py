# src/tuck_in_terrors_sim/game_logic/game_setup.py
# Logic for initializing GameState based on a chosen Objective

import random
from typing import List, Dict, Tuple, Optional

from ..game_elements.enums import Zone, CardType, TurnPhase
from ..game_elements.card import Card, CardInstance
from ..game_elements.objective import ObjectiveCard
from .game_state import GameState, PlayerState

INITIAL_HAND_SIZE = 5
DEFAULT_PLAYER_ID = 0

def _build_deck_definitions(all_card_definitions: Dict[str, Card], current_objective: ObjectiveCard) -> List[Card]:
    """Builds a list of Card definitions for the deck, considering objective bans."""
    deck_defs: List[Card] = []
    banned_card_ids_list = []
    if current_objective.card_rotation and isinstance(current_objective.card_rotation, dict):
        banned_card_ids_list = current_objective.card_rotation.get("banned", [])
    
    banned_card_ids_set = set(banned_card_ids_list)

    for card_id, card_def in all_card_definitions.items():
        if card_id not in banned_card_ids_set:
            deck_defs.append(card_def)

    if not deck_defs and all_card_definitions:
        print(f"Warning: Deck definition list is empty after filtering for objective '{current_objective.title}'.")
    elif not deck_defs and not all_card_definitions:
        raise ValueError("Cannot build deck: all_card_definitions is empty.")

    random.shuffle(deck_defs)
    return deck_defs

def _place_card_in_play_from_definitions(
    game_state: GameState,
    available_card_definitions: List[Card],
    card_id_to_place: str,
    player_id: int
) -> Optional[CardInstance]:
    """Finds a card definition, creates an instance, places it in play, and removes def from list."""
    found_card_def = None
    for i, card_def in enumerate(available_card_definitions):
        if card_def.card_id == card_id_to_place:
            found_card_def = available_card_definitions.pop(i)
            break
    
    if found_card_def:
        instance = CardInstance(definition=found_card_def, owner_id=player_id, current_zone=Zone.IN_PLAY)
        instance.turn_entered_play = game_state.current_turn
        
        game_state.cards_in_play[instance.instance_id] = instance
        player_state = game_state.get_player_state(player_id)
        if player_state:
            player_state.zones[Zone.IN_PLAY].append(instance)
        
        game_state.add_log_entry(f"Card '{found_card_def.name}' ({instance.instance_id}) placed into play for P{player_id} (Setup).")
        return instance
    
    game_state.add_log_entry(f"Card def ID '{card_id_to_place}' for starting in play not found in available definitions.", level="WARNING")
    return None

def _add_card_def_to_hand_setup_list(
    game_state: GameState,
    available_card_definitions: List[Card],
    card_id_to_add: str,
    target_hand_definitions_list: List[Card]
) -> bool:
    """Finds a card definition, removes it from available_card_definitions, and adds it to target_hand_definitions_list."""
    for i, card_def in enumerate(available_card_definitions):
        if card_def.card_id == card_id_to_add:
            card_to_hand_def = available_card_definitions.pop(i)
            target_hand_definitions_list.append(card_to_hand_def)
            game_state.add_log_entry(f"Card def '{card_to_hand_def.name}' designated for starting hand (Setup).")
            return True
            
    game_state.add_log_entry(f"Card def ID '{card_id_to_add}' for starting hand not found in available definitions.", level="WARNING")
    return False

def _determine_and_prepare_first_memory(
    game_state: GameState,
    deck_definitions_pool: List[Card], 
    hand_definitions_for_setup: List[Card],
    player_id: int
) -> None:
    objective = game_state.current_objective
    fm_setup_logic = objective.first_memory_setup
    player_s = game_state.get_player_state(player_id)

    if not fm_setup_logic or not player_s:
        game_state.add_log_entry("No First Memory setup or player state for FM.", level="DEBUG"); return

    chosen_fm_card_def: Optional[Card] = None
    fm_target_disposition: Optional[Zone] = None
    
    if fm_setup_logic.component_type == "CHOOSE_TOY_FROM_HAND_PLACE_IN_PLAY": # Implies from deck to play
        fm_id = fm_setup_logic.params.get("designated_first_memory_id")
        if not fm_id: game_state.add_log_entry("FM setup needs 'designated_first_memory_id'.", "ERROR"); return
        for i, c_def in enumerate(deck_definitions_pool):
            if c_def.card_id == fm_id:
                if c_def.type == CardType.TOY: chosen_fm_card_def = deck_definitions_pool.pop(i); fm_target_disposition = Zone.IN_PLAY; break
                else: game_state.add_log_entry(f"Designated FM '{fm_id}' not a TOY.", "ERROR"); return
        if not chosen_fm_card_def: game_state.add_log_entry(f"Designated FM ID '{fm_id}' not in deck defs.", "ERROR"); return
            
    elif fm_setup_logic.component_type == "CHOOSE_TOY_FROM_TOP_X_DECK_TO_HAND":
        count = fm_setup_logic.params.get("card_count_to_look_at", 3)
        found_toy_def: Optional[Card] = None
        
        temp_selection_pool = [] # Cards viewed but not chosen, to be returned to deck bottom
        
        # Look in top X
        for _ in range(min(count, len(deck_definitions_pool))): # Iterate 'count' times or until deck_definitions_pool is empty
            if not deck_definitions_pool: break # Stop if deck runs out
            card_from_top = deck_definitions_pool.pop(0) # Take from top
            if card_from_top.type == CardType.TOY and not found_toy_def:
                found_toy_def = card_from_top # Select first toy found
            else:
                temp_selection_pool.append(card_from_top) # Add to temp pool if not the chosen toy or not a toy
        
        # Add remaining viewed cards from temp_selection_pool back to deck (conceptually bottom)
        deck_definitions_pool.extend(temp_selection_pool) # Simplification: add to end, shuffle later if needed

        # If not in top X (or if specified by repeat_if_none_found, which isn't explicitly handled here but implied by full deck search)
        if not found_toy_def and fm_setup_logic.params.get("repeat_if_none_found", False): # Check repeat_if_none_found
            # Search rest of deck (excluding those already popped and in temp_selection_pool if logic was more complex)
            # Current simple approach: deck_definitions_pool now contains rest + non-chosen from top X
            for i, c_def in enumerate(deck_definitions_pool):
                if c_def.type == CardType.TOY:
                    found_toy_def = deck_definitions_pool.pop(i)
                    break
        
        if found_toy_def:
            chosen_fm_card_def = found_toy_def
            fm_target_disposition = Zone.HAND
        else:
            game_state.add_log_entry("No Toys in deck for FM selection after searching.", level="WARNING")
            return
    else:
        game_state.add_log_entry(f"Unknown FM setup type: {fm_setup_logic.component_type}", level="WARNING"); return

    if chosen_fm_card_def and fm_target_disposition:
        player_s.first_memory_card_id = chosen_fm_card_def.card_id

        if fm_target_disposition == Zone.IN_PLAY:
            fm_instance = CardInstance(definition=chosen_fm_card_def, owner_id=player_id, current_zone=Zone.IN_PLAY)
            fm_instance.custom_data["is_first_memory"] = True
            fm_instance.turn_entered_play = game_state.current_turn
            game_state.cards_in_play[fm_instance.instance_id] = fm_instance
            player_s.zones[Zone.IN_PLAY].append(fm_instance)
            game_state.first_memory_instance_id = fm_instance.instance_id
        elif fm_target_disposition == Zone.HAND:
            hand_definitions_for_setup.append(chosen_fm_card_def)
        
        game_state.add_log_entry(f"FM '{chosen_fm_card_def.name}' designated for {fm_target_disposition.name} (Setup). Player FM ID set: {player_s.first_memory_card_id}")

def _apply_objective_specific_setup(
    game_state: GameState,
    deck_definitions_pool: List[Card],
    hand_definitions_for_setup: List[Card],
    player_id: int
) -> None:
    objective = game_state.current_objective
    player_s = game_state.get_player_state(player_id)
    if not objective.setup_instructions or not player_s: return

    setup_params = objective.setup_instructions.params
    component_type = objective.setup_instructions.component_type

    if component_type == "CUSTOM_GAME_SETUP":
        start_cards_hand_ids = setup_params.get("start_cards_in_hand", [])
        for card_id in start_cards_hand_ids:
            is_fm_and_in_hand_list = player_s.first_memory_card_id == card_id and \
                                   any(hd_def.card_id == card_id for hd_def in hand_definitions_for_setup)
            if is_fm_and_in_hand_list:
                game_state.add_log_entry(f"Card '{card_id}' (FM) already in hand_definitions_for_setup by FM logic, not adding again via start_cards_in_hand.")
                continue
            _add_card_def_to_hand_setup_list(game_state, deck_definitions_pool, card_id, hand_definitions_for_setup)

        start_cards_in_play_ids = setup_params.get("start_cards_in_play", [])
        for card_id in start_cards_in_play_ids:
            # Case 1: The card to start in play IS the chosen First Memory
            if player_s.first_memory_card_id == card_id:
                fm_card_definition = game_state.all_card_definitions.get(player_s.first_memory_card_id)
                
                if not fm_card_definition:
                    game_state.add_log_entry(f"CRITICAL: First Memory card definition ID '{player_s.first_memory_card_id}' not found in all_card_definitions. Cannot place '{card_id}' as FM.", level="ERROR")
                    continue

                # Remove its definition from hand_definitions_for_setup if it was put there by FM "to_hand" logic
                original_hand_defs_len = len(hand_definitions_for_setup)
                hand_definitions_for_setup[:] = [hd_def for hd_def in hand_definitions_for_setup if hd_def.card_id != player_s.first_memory_card_id]
                if len(hand_definitions_for_setup) < original_hand_defs_len:
                    game_state.add_log_entry(f"Removed FM def '{player_s.first_memory_card_id}' from hand_definitions_for_setup as it will start in play.")

                # Safeguard: Remove from deck_definitions_pool (should have been popped by FM selection if from deck)
                original_deck_pool_len = len(deck_definitions_pool)
                deck_definitions_pool[:] = [dd_def for dd_def in deck_definitions_pool if dd_def.card_id != player_s.first_memory_card_id]
                if len(deck_definitions_pool) < original_deck_pool_len:
                     game_state.add_log_entry(f"Removed FM def '{player_s.first_memory_card_id}' from deck_definitions_pool as it starts in play.")

                # Create instance, place in play, mark as FM, set GameState's FM instance ID
                instance = CardInstance(definition=fm_card_definition, owner_id=player_id, current_zone=Zone.IN_PLAY)
                instance.turn_entered_play = game_state.current_turn
                instance.custom_data["is_first_memory"] = True
                
                game_state.cards_in_play[instance.instance_id] = instance
                player_s.zones[Zone.IN_PLAY].append(instance)
                game_state.first_memory_instance_id = instance.instance_id # CRITICAL ASSIGNMENT
                
                game_state.add_log_entry(
                    f"First Memory '{instance.definition.name}' (ID: {instance.instance_id}) "
                    f"placed into IN_PLAY (as per start_cards_in_play), marked, and GameState.first_memory_instance_id set."
                )
            # Case 2: The card to start in play is NOT the First Memory
            # OR the First Memory was already placed by _determine_and_prepare_first_memory (e.g., "OBJ01_THE_FIRST_NIGHT")
            else:
                 # Check if this card is already the instanced FM (e.g. OBJ01 FM setup)
                fm_is_this_and_already_in_play = False
                if game_state.first_memory_instance_id:
                    fm_inst = game_state.get_card_instance(game_state.first_memory_instance_id)
                    if fm_inst and fm_inst.definition.card_id == card_id and fm_inst.current_zone == Zone.IN_PLAY:
                        fm_is_this_and_already_in_play = True
                
                if fm_is_this_and_already_in_play:
                    game_state.add_log_entry(f"Card '{card_id}' is already the instanced FM in play. Skipping redundant placement via start_cards_in_play.")
                    continue
                
                # If not the FM, or if it is the FM but already handled by direct FM placement,
                # just place it normally if it's not the active FM instance being tracked by game_state.first_memory_instance_id.
                # This avoids double-placing an FM that _determine_and_prepare_first_memory might have already put in play.
                _place_card_in_play_from_definitions(game_state, deck_definitions_pool, card_id, player_id)

        if "first_turn_mana_override" in setup_params:
            player_s.mana = setup_params["first_turn_mana_override"]
            game_state.add_log_entry(f"P{player_id}'s initial mana set to {player_s.mana} by objective.")
    else:
        game_state.add_log_entry(f"Unknown setup instruction type: {component_type}", level="WARNING")

def initialize_new_game(current_objective: ObjectiveCard, all_card_definitions: Dict[str, Card]) -> GameState:
    game_state = GameState(loaded_objective=current_objective, all_card_definitions=all_card_definitions)
    game_state.current_turn = 0 
    game_state.add_log_entry(f"Init game for obj: {current_objective.title}")

    game_state.active_player_id = DEFAULT_PLAYER_ID
    player_s = PlayerState(player_id=DEFAULT_PLAYER_ID, initial_deck=[])
    game_state.player_states[DEFAULT_PLAYER_ID] = player_s
    
    deck_defs_pool: List[Card] = _build_deck_definitions(all_card_definitions, current_objective)
    game_state.add_log_entry(f"Built deck def list: {len(deck_defs_pool)} cards.")

    hand_defs_for_setup: List[Card] = []

    _determine_and_prepare_first_memory(game_state, deck_defs_pool, hand_defs_for_setup, DEFAULT_PLAYER_ID)
    _apply_objective_specific_setup(game_state, deck_defs_pool, hand_defs_for_setup, DEFAULT_PLAYER_ID)

    num_already_in_hand_list = len(hand_defs_for_setup)
    num_to_draw_additionally = max(0, INITIAL_HAND_SIZE - num_already_in_hand_list)
    
    drawn_card_defs: List[Card] = []
    if num_to_draw_additionally > 0:
        actual_drawn_count = min(num_to_draw_additionally, len(deck_defs_pool))
        drawn_card_defs = deck_defs_pool[:actual_drawn_count]
        deck_defs_pool = deck_defs_pool[actual_drawn_count:]
    
    final_hand_definitions = hand_defs_for_setup + drawn_card_defs

    active_player = game_state.get_active_player_state()
    if active_player:
        active_player.zones[Zone.DECK] = [CardInstance(definition=cd, owner_id=DEFAULT_PLAYER_ID, current_zone=Zone.DECK) for cd in deck_defs_pool]
        active_player.zones[Zone.HAND] = [CardInstance(definition=cd, owner_id=DEFAULT_PLAYER_ID, current_zone=Zone.HAND) for cd in final_hand_definitions]
        
        # Mark FM instance in hand if applicable and GameState.first_memory_instance_id hasn't been set by in-play FM logic
        if active_player.first_memory_card_id and not game_state.first_memory_instance_id:
            found_fm_in_hand = False
            for fm_hand_inst in active_player.zones[Zone.HAND]:
                if fm_hand_inst.definition.card_id == active_player.first_memory_card_id:
                    fm_hand_inst.custom_data["is_first_memory"] = True
                    game_state.first_memory_instance_id = fm_hand_inst.instance_id # Assign GameState's tracked FM instance
                    game_state.add_log_entry(f"First Memory '{fm_hand_inst.definition.name}' (ID: {fm_hand_inst.instance_id}) found in starting hand, marked, and GameState.first_memory_instance_id set.")
                    found_fm_in_hand = True
                    break 
            if not found_fm_in_hand:
                 game_state.add_log_entry(f"First Memory card ID '{active_player.first_memory_card_id}' was set, but no corresponding instance found in hand and not set from play.", level="WARNING")
        
        game_state.add_log_entry(f"P{DEFAULT_PLAYER_ID} init: Deck {len(active_player.zones[Zone.DECK])}, Hand {len(active_player.zones[Zone.HAND])}.")
    
    game_state.current_turn = 1
    game_state.current_phase = TurnPhase.BEGIN_TURN
    game_state.add_log_entry(f"Game setup complete. Turn {game_state.current_turn}.")
    return game_state

if __name__ == '__main__':
    print("This module (`game_setup.py`) is intended to be imported.")