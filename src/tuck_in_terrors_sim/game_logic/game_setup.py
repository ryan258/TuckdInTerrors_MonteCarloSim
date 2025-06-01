# src/tuck_in_terrors_sim/game_logic/game_setup.py
# Logic for initializing GameState based on a chosen Objective

import random
from typing import List, Dict, Tuple, Optional

from ..game_elements.enums import Zone, CardType, TurnPhase
from ..game_elements.card import Card
from ..game_elements.objective import ObjectiveCard
from .game_state import GameState, CardInPlay

INITIAL_HAND_SIZE = 5

def _build_deck(all_card_definitions: Dict[str, Card], current_objective: ObjectiveCard) -> List[Card]:
    deck: List[Card] = []
    banned_card_ids_list = []
    if current_objective.card_rotation: # Check if card_rotation is not None
        banned_card_ids_list = current_objective.card_rotation.get("banned_card_ids", [])
    
    banned_card_ids = set(banned_card_ids_list)

    for card_id, card_def in all_card_definitions.items():
        if card_id not in banned_card_ids:
            for _ in range(card_def.quantity_in_deck):
                deck.append(card_def)
    random.shuffle(deck)
    return deck

def _place_card_in_play_from_deck(game_state: GameState, temp_deck: List[Card], card_id: str) -> Optional[CardInPlay]:
    """Helper to find, remove a card from deck, and place it in play."""
    for i, card_in_deck in enumerate(temp_deck):
        if card_in_deck.card_id == card_id:
            card_to_place = temp_deck.pop(i)
            instance = CardInPlay(card_to_place)
            game_state.cards_in_play[instance.instance_id] = instance
            game_state.add_log_entry(f"Card '{card_to_place.name}' (ID: {card_id}) placed into play from deck (Objective Setup).")
            return instance
    game_state.add_log_entry(f"Card ID '{card_id}' for starting in play not found in deck.", level="WARNING")
    return None

def _add_card_to_hand_from_deck(game_state: GameState, temp_deck: List[Card], card_id: str) -> bool:
    """Helper to find, remove a card from deck, and add it to hand."""
    for i, card_in_deck in enumerate(temp_deck):
        if card_in_deck.card_id == card_id:
            card_to_hand = temp_deck.pop(i)
            game_state.hand.append(card_to_hand)
            game_state.add_log_entry(f"Card '{card_to_hand.name}' (ID: {card_id}) added to hand from deck (Objective Setup).")
            return True
    game_state.add_log_entry(f"Card ID '{card_id}' for starting hand not found in deck.", level="WARNING")
    return False

def _determine_and_place_first_memory(game_state: GameState, temp_deck: List[Card]) -> None:
    objective = game_state.current_objective
    fm_setup_logic = objective.first_memory_setup
    if not fm_setup_logic: 
        game_state.add_log_entry("No First Memory setup defined.", level="DEBUG")
        return

    chosen_fm_card: Optional[Card] = None
    
    if fm_setup_logic.component_type == "CHOOSE_TOY_FROM_HAND_PLACE_IN_PLAY":
        fm_card_id_to_find = fm_setup_logic.params.get("designated_first_memory_id")
        if not fm_card_id_to_find:
            game_state.add_log_entry("FM setup CHOOSE_TOY_FROM_HAND_PLACE_IN_PLAY requires 'designated_first_memory_id' in params for simulation.", level="ERROR")
            return

        for i, card in enumerate(temp_deck):
            if card.card_id == fm_card_id_to_find:
                if card.card_type == CardType.TOY:
                    chosen_fm_card = temp_deck.pop(i)
                    break
                else:
                    game_state.add_log_entry(f"Designated FM '{fm_card_id_to_find}' is not a TOY.", level="ERROR")
                    return
        
        if chosen_fm_card:
            instance = CardInPlay(chosen_fm_card)
            game_state.cards_in_play[instance.instance_id] = instance
            game_state.first_memory_card_definition = chosen_fm_card
            game_state.first_memory_instance_id = instance.instance_id
            game_state.first_memory_current_zone = Zone.IN_PLAY
        else:
            game_state.add_log_entry(f"Designated First Memory ID '{fm_card_id_to_find}' not found in deck.", level="ERROR")

    elif fm_setup_logic.component_type == "CHOOSE_TOY_FROM_TOP_X_DECK_TO_HAND":
        count = fm_setup_logic.params.get("card_count_to_look_at", 3)
        
        # Attempt to find a Toy in the top X cards
        found_in_top_x = False
        for i in range(min(count, len(temp_deck))):
            if temp_deck[i].card_type == CardType.TOY:
                chosen_fm_card = temp_deck.pop(i) # Remove from original position
                found_in_top_x = True
                break
        
        if not chosen_fm_card: # If no Toy in top X, search whole deck as per rule interpretation
            game_state.add_log_entry(f"No Toys in top {count}. Searching full deck for first Toy for FM.", level="INFO")
            for i, card_in_deck in enumerate(temp_deck):
                if card_in_deck.card_type == CardType.TOY:
                    chosen_fm_card = temp_deck.pop(i)
                    break
        
        if chosen_fm_card:
            game_state.hand.append(chosen_fm_card)
            game_state.first_memory_card_definition = chosen_fm_card
            game_state.first_memory_current_zone = Zone.HAND
        else:
            game_state.add_log_entry(f"No Toys found in the entire deck for First Memory selection.", level="WARNING")
    else:
        game_state.add_log_entry(f"Unknown First Memory setup type: {fm_setup_logic.component_type}", level="WARNING")

    if game_state.first_memory_card_definition:
        game_state.add_log_entry(f"First Memory is set to: {game_state.first_memory_card_definition.name}")


def _apply_objective_setup_instructions(game_state: GameState, temp_deck: List[Card]) -> None:
    objective = game_state.current_objective
    if not objective.setup_instructions: return

    setup_params = objective.setup_instructions.params
    component_type = objective.setup_instructions.component_type

    if component_type == "CUSTOM_GAME_SETUP":
        start_cards_in_hand_ids = setup_params.get("start_cards_in_hand", [])
        for card_id in start_cards_in_hand_ids:
            # If this card is already FM and in hand, don't add another copy unless explicitly from deck
            if game_state.first_memory_card_definition and \
               game_state.first_memory_card_definition.card_id == card_id and \
               game_state.first_memory_current_zone == Zone.HAND:
                game_state.add_log_entry(f"Card ID '{card_id}' is FM and already in hand. Setup for hand satisfied by FM.", level="DEBUG")
                continue 
            _add_card_to_hand_from_deck(game_state, temp_deck, card_id)

        start_cards_in_play_ids = setup_params.get("start_cards_in_play", [])
        for card_id in start_cards_in_play_ids:
            fm_moved_to_play = False
            # If FM is this card ID and currently in hand, move it to play
            if game_state.first_memory_card_definition and \
               game_state.first_memory_card_definition.card_id == card_id and \
               game_state.first_memory_current_zone == Zone.HAND:
                
                fm_card_to_move = game_state.first_memory_card_definition
                # Ensure it's actually in hand before trying to remove
                # This check might be redundant if fm_current_zone is reliable
                try:
                    game_state.hand.remove(fm_card_to_move) # Remove the FM object from hand
                    instance = CardInPlay(fm_card_to_move)
                    game_state.cards_in_play[instance.instance_id] = instance
                    game_state.first_memory_instance_id = instance.instance_id
                    game_state.first_memory_current_zone = Zone.IN_PLAY
                    game_state.add_log_entry(f"First Memory '{fm_card_to_move.name}' moved from hand to start in play as per objective setup.")
                    fm_moved_to_play = True
                except ValueError:
                    game_state.add_log_entry(f"Attempted to move FM '{fm_card_to_move.name}' from hand to play, but it wasn't in hand.", level="WARNING")

            if not fm_moved_to_play:
                # If not the FM that was just moved from hand, or if FM is different, place from deck
                # Also handles case where FM is this ID but already in play (placed by _determine_and_place_first_memory)
                if not (game_state.first_memory_card_definition and \
                        game_state.first_memory_card_definition.card_id == card_id and \
                        game_state.first_memory_current_zone == Zone.IN_PLAY):
                    _place_card_in_play_from_deck(game_state, temp_deck, card_id)
                else:
                    game_state.add_log_entry(f"Card ID '{card_id}' is FM and already in play. Setup for play satisfied by FM.", level="DEBUG")


        if "first_turn_mana_override" in setup_params:
            game_state.mana_pool = setup_params["first_turn_mana_override"]
            game_state.add_log_entry(f"Initial mana pool set to {game_state.mana_pool} by objective.")

        if "conditional_deck_search" in setup_params:
            game_state.add_log_entry(f"Objective setup includes conditional deck search: {setup_params['conditional_deck_search']}.", level="DEBUG")
    else:
        game_state.add_log_entry(f"Unknown setup instruction type: {component_type}", level="WARNING")

def initialize_new_game(current_objective: ObjectiveCard, all_card_definitions: Dict[str, Card]) -> GameState:
    game_state = GameState(loaded_objective=current_objective, all_card_definitions=all_card_definitions)
    game_state.add_log_entry(f"Initializing new game for objective: {current_objective.title}")

    temp_deck: List[Card] = _build_deck(all_card_definitions, current_objective)
    game_state.add_log_entry(f"Initial deck built with {len(temp_deck)} cards and shuffled.")

    _determine_and_place_first_memory(game_state, temp_deck)
    _apply_objective_setup_instructions(game_state, temp_deck)

    cards_to_draw_for_initial_hand = INITIAL_HAND_SIZE - len(game_state.hand)
    if cards_to_draw_for_initial_hand > 0:
        if len(temp_deck) >= cards_to_draw_for_initial_hand:
            drawn_cards = temp_deck[:cards_to_draw_for_initial_hand]
            game_state.hand.extend(drawn_cards)
            temp_deck = temp_deck[cards_to_draw_for_initial_hand:]
            for card_obj in drawn_cards:
                game_state.add_log_entry(f"Card '{card_obj.name}' drawn into starting hand.")
        elif len(temp_deck) > 0 :
            drawn_cards = list(temp_deck)
            game_state.hand.extend(drawn_cards)
            temp_deck.clear()
            for card_obj in drawn_cards:
                game_state.add_log_entry(f"Card '{card_obj.name}' drawn into starting hand (deck empty).")
            game_state.add_log_entry(f"Drawn all remaining {len(drawn_cards)} cards. Deck empty.", level="WARNING")
        else:
            game_state.add_log_entry(f"Cannot draw {cards_to_draw_for_initial_hand} cards for hand: Deck is already empty.", level="WARNING")

    game_state.add_log_entry(f"Final starting hand size: {len(game_state.hand)}")
    game_state.deck = temp_deck
    game_state.add_log_entry(f"Final game deck size: {len(game_state.deck)}")

    game_state.current_turn = 1
    game_state.current_phase = None 
    game_state.game_over = False
    game_state.win_status = None
    
    game_state.add_log_entry(f"Game setup complete. Ready for Turn {game_state.current_turn}.")
    return game_state

if __name__ == '__main__':
    print("This module (`game_setup.py`) is intended to be imported.")