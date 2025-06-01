# tests/game_logic/test_game_setup.py
# Unit tests for game_setup.py

import pytest
from typing import Dict

from tuck_in_terrors_sim.game_elements.card import Card
from tuck_in_terrors_sim.game_elements.objective import ObjectiveCard
from tuck_in_terrors_sim.game_elements.enums import Zone, CardType
from tuck_in_terrors_sim.game_logic.game_setup import initialize_new_game, INITIAL_HAND_SIZE
from tuck_in_terrors_sim.game_logic.game_state import GameState 

# Fixtures are defined in tests/conftest.py

class TestGameSetup:

    def test_initialize_new_game_first_night(self, 
                                             objective_def_first_night: ObjectiveCard, 
                                             all_card_definitions: Dict[str, Card]):
        """ Tests game setup for 'The First Night' objective. """
        if not objective_def_first_night.first_memory_setup.params.get("designated_first_memory_id"):
            pytest.skip("Skipping: OBJ01_THE_FIRST_NIGHT in objectives.json is missing 'designated_first_memory_id'.")
            return

        gs = initialize_new_game(current_objective=objective_def_first_night, 
                                 all_card_definitions=all_card_definitions)

        assert isinstance(gs, GameState)
        assert gs.current_objective == objective_def_first_night
        assert gs.current_turn == 1
        assert not gs.game_over
        assert gs.win_status is None
        assert gs.mana_pool == 1 

        fm_card_def = gs.first_memory_card_definition
        assert fm_card_def is not None, "First Memory card definition should be set for OBJ01."
        assert fm_card_def.card_id == "TCTOY001" # Toy Cow
        assert gs.first_memory_current_zone == Zone.IN_PLAY
        assert gs.first_memory_instance_id is not None
        assert gs.first_memory_instance_id in gs.cards_in_play
        assert gs.cards_in_play[gs.first_memory_instance_id].card_definition.card_id == "TCTOY001"

        assert len(gs.hand) == INITIAL_HAND_SIZE
        
        toy_cow_in_hand_count = sum(1 for card in gs.hand if card.card_id == "TCTOY001")
        assert toy_cow_in_hand_count == 1, "One Toy Cow (TCTOY001) should be in the starting hand for OBJ01."

        total_cards_in_full_deck = sum(
            c.quantity_in_deck for i, c in all_card_definitions.items() 
            if i not in (objective_def_first_night.card_rotation.get("banned_card_ids", []))
        )
        expected_deck_size = total_cards_in_full_deck - 1 - INITIAL_HAND_SIZE # 1 FM in play, 5 in hand
        assert len(gs.deck) == expected_deck_size
        
        assert any("Initializing new game for objective: The First Night" in entry for entry in gs.game_log)
        assert any("First Memory is set to: Toy Cow With Bell That Never Rings" in entry for entry in gs.game_log)

    def test_initialize_new_game_whisper_wake(self, 
                                              objective_def_whisper_wake: ObjectiveCard, 
                                              all_card_definitions: Dict[str, Card]):
        """Tests game setup for 'The Whisper Before Wake' objective."""
        ghost_doll_id_in_objective_setup = objective_def_whisper_wake.setup_instructions.params.get("start_cards_in_play", [None])[0]
        if ghost_doll_id_in_objective_setup != "TCTOY002" or "TCTOY002" not in all_card_definitions:
             pytest.skip(f"Skipping: Check OBJ02 setup in objectives.json to ensure 'start_cards_in_play' correctly references 'TCTOY002' (Ghost Doll) and TCTOY002 exists in cards.json.")
             return

        gs = initialize_new_game(current_objective=objective_def_whisper_wake, 
                                 all_card_definitions=all_card_definitions)

        assert isinstance(gs, GameState)
        assert gs.current_objective == objective_def_whisper_wake
        assert gs.current_turn == 1
        assert gs.mana_pool == 0 

        fm_card_def = gs.first_memory_card_definition
        assert fm_card_def is not None, "FM should be chosen for Whisper Wake."
        assert fm_card_def.card_type == CardType.TOY

        ghost_doll_card_id = "TCTOY002" # ID for Ghost Doll
        ghost_doll_starts_in_play = ghost_doll_id_in_objective_setup == ghost_doll_card_id

        # Assertions for First Memory location based on whether it IS the Ghost Doll
        if fm_card_def.card_id == ghost_doll_card_id and ghost_doll_starts_in_play:
            # If FM is Ghost Doll (TCTOY002), and OBJ02 starts TCTOY002 in play,
            # then FM should end up IN_PLAY and NOT in hand.
            assert fm_card_def not in gs.hand, "If FM (Ghost Doll) starts in play (OBJ02), it shouldn't also be in hand."
            assert gs.first_memory_current_zone == Zone.IN_PLAY, "If FM is Ghost Doll (OBJ02), it should end in play."
            assert gs.first_memory_instance_id is not None
            assert gs.first_memory_instance_id in gs.cards_in_play
        else:
            # If FM is some OTHER Toy, it should be in hand as per "CHOOSE_TOY_FROM_TOP_X_DECK_TO_HAND"
            assert fm_card_def in gs.hand, "If FM is not Ghost Doll (OBJ02), it should be in hand."
            assert gs.first_memory_current_zone == Zone.HAND
            assert gs.first_memory_instance_id is None # Not in play yet

        # Check if Ghost Doll is in play (it should be, as per objective setup)
        ghost_doll_actually_in_play = any(
            cip.card_definition.card_id == ghost_doll_card_id
            for cip in gs.cards_in_play.values()
        )
        assert ghost_doll_actually_in_play, f"{ghost_doll_card_id} (Ghost Doll) should be in play as per OBJ02 setup."
        
        assert len(gs.hand) == INITIAL_HAND_SIZE

        total_cards_in_all_zones = len(gs.deck) + len(gs.hand) + len(gs.discard_pile) + \
                                   len(gs.exile_zone) + len(gs.cards_in_play)
        
        expected_total_cards_in_game = sum(
            c.quantity_in_deck for i, c in all_card_definitions.items() 
            if i not in (objective_def_whisper_wake.card_rotation.get("banned_card_ids", []))
        )
        assert total_cards_in_all_zones == expected_total_cards_in_game
        
        assert any("Initializing new game for objective: The Whisper Before Wake" in entry for entry in gs.game_log)