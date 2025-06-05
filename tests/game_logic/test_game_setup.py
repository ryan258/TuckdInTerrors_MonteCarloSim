# tests/game_logic/test_game_setup.py
import pytest
from typing import Dict, List

from tuck_in_terrors_sim.game_logic.game_setup import initialize_new_game, DEFAULT_PLAYER_ID, INITIAL_HAND_SIZE
from tuck_in_terrors_sim.game_logic.game_state import GameState, PlayerState
from tuck_in_terrors_sim.game_elements.card import Card, CardInstance, Toy
from tuck_in_terrors_sim.game_elements.objective import ObjectiveCard
from tuck_in_terrors_sim.game_elements.enums import Zone, CardType

# Fixtures objective_def_first_night, objective_def_whisper_wake, and 
# all_card_definitions_dict are expected to be in conftest.py

class TestGameSetup:

    def test_initialize_new_game_first_night(self,
                                             objective_def_first_night: ObjectiveCard,
                                             all_card_definitions_dict: Dict[str, Card]): # Use the Dict fixture
        """ Tests game setup for 'The First Night' objective. """
        
        gs = initialize_new_game(current_objective=objective_def_first_night,
                                 all_card_definitions=all_card_definitions_dict)

        assert isinstance(gs, GameState)
        assert gs.current_objective == objective_def_first_night
        assert gs.active_player_id == DEFAULT_PLAYER_ID
        player = gs.get_active_player_state()
        assert player is not None
        assert isinstance(player, PlayerState)

        # Check First Memory setup (OBJ01_THE_FIRST_NIGHT specifics)
        # It expects "designated_first_memory_id": "TCTOY001" (Toy Cow) to start in play.
        fm_card_id_from_objective = objective_def_first_night.first_memory_setup.params.get("designated_first_memory_id") # type: ignore
        assert fm_card_id_from_objective is not None, "Objective OBJ01 should designate a First Memory ID in setup params"
        
        fm_instance = gs.get_card_instance(gs.first_memory_instance_id) if gs.first_memory_instance_id else None
        
        assert fm_instance is not None, "First Memory instance should be created and set on GameState"
        assert fm_instance.definition.card_id == fm_card_id_from_objective, "GameState First Memory instance should match objective's designated ID" #type: ignore
        assert fm_instance.current_zone == Zone.IN_PLAY, "First Memory should start in play for OBJ01" #type: ignore
        assert fm_instance.custom_data.get("is_first_memory") is True, "FM instance should be marked" #type: ignore

        # Check for "Toy Cow With Bell That Never Rings" in hand (also TCTOY001, but this is extra copy)
        # Note: The logic in game_setup for OBJ01 might have a specific card_id for hand.
        # For "The First Night", setup says: "Start with Toy Cow With Bell That Never Rings in hand"
        # This is distinct from the FM. If FM is also Toy Cow, this test needs nuance.
        # Assuming Toy Cow ID is TCTOY001, and it's *also* the FM for this objective.
        # The game_setup logic tries to avoid adding duplicates if FM is already set for a zone.
        
        # Check hand size and deck size
        assert len(player.zones[Zone.HAND]) == INITIAL_HAND_SIZE
        # Exact deck size depends on total cards, FM selection, and objective setup cards.
        # For now, just check it's not empty if there were cards to begin with.
        if all_card_definitions_dict:
            assert len(player.zones[Zone.DECK]) < len(all_card_definitions_dict) 

        assert gs.current_turn == 1
        assert gs.game_over is False


    def test_initialize_new_game_whisper_wake(self,
                                              objective_def_whisper_wake: ObjectiveCard,
                                              all_card_definitions_dict: Dict[str, Card]): # Use the Dict fixture
        """Tests game setup for 'The Whisper Before Wake' objective."""
        
        # OBJ02_WHISPER_WAKE setup: "Start with Ghost Doll (TCTOY002) in play."
        # And FM is "Choose a Toy from top 3 of deck, add to hand."
        
        # Ensure TCTOY002 exists in definitions for this test to be valid
        if "TCTOY002" not in all_card_definitions_dict:
            pytest.fail("Test prerequisite: Card TCTOY002 (Ghost Doll) must be in all_card_definitions_dict for this test.")

        gs = initialize_new_game(current_objective=objective_def_whisper_wake,
                                 all_card_definitions=all_card_definitions_dict)

        assert isinstance(gs, GameState)
        player = gs.get_active_player_state()
        assert player is not None

        # Check for Ghost Doll (TCTOY002) in play
        ghost_doll_in_play = False
        for inst_id, card_inst in gs.cards_in_play.items():
            if card_inst.definition.card_id == "TCTOY002":
                ghost_doll_in_play = True
                break
        assert ghost_doll_in_play, "Ghost Doll (TCTOY002) should start in play for Whisper Wake objective."

        # Check First Memory setup (chosen from top 3 of deck to hand)
        assert player.first_memory_card_id is not None, "First Memory card ID should be set on PlayerState"
        fm_def_id = player.first_memory_card_id
        
        # Check First Memory properties and location
        assert gs.first_memory_instance_id is not None, \
            "GameState's first_memory_instance_id should be set if a First Memory was chosen."

        fm_instance = gs.get_card_instance(gs.first_memory_instance_id)
        assert fm_instance is not None, \
            "gs.first_memory_instance_id should point to a valid card instance."

        assert fm_instance.definition.card_id == fm_def_id, \
            (f"The GameState's First Memory instance (Definition ID: {fm_instance.definition.card_id}) "
             f"should match the PlayerState's First Memory card ID (Definition ID: {fm_def_id}).")
        assert fm_instance.definition.type == CardType.TOY, \
            "The First Memory must be a Toy."
        assert fm_instance.custom_data.get("is_first_memory") is True, \
            (f"The First Memory instance (Instance ID: {fm_instance.instance_id}) "
             f"should be marked with custom_data['is_first_memory']=True.")

        # For OBJ02_WHISPER_WAKE (Whisper Wake):
        # - TCTOY002 (Ghost Doll) is specified by the objective to "start_cards_in_play".
        # - The First Memory selection rule is "CHOOSE_TOY_FROM_TOP_X_DECK_TO_HAND".
        # Case 1: Ghost Doll (TCTOY002) was chosen as First Memory.
        #         It should end up IN_PLAY (due to "start_cards_in_play" taking precedence)
        #         and be the game_state.first_memory_instance_id. It should NOT also be in hand.
        # Case 2: A different Toy was chosen as First Memory.
        #         That different Toy should be IN_HAND and be game_state.first_memory_instance_id.
        #         TCTOY002 (Ghost Doll) will still be in play but NOT as the First Memory instance.

        if fm_def_id == "TCTOY002":  # If Ghost Doll was chosen as First Memory
            assert fm_instance.current_zone == Zone.IN_PLAY, \
                (f"If First Memory is TCTOY002 (Ghost Doll), it should be in play for Whisper Wake, "
                 f"not {fm_instance.current_zone}.")
            # Ensure it's not also in hand
            fm_also_in_hand = any(hand_card.definition.card_id == "TCTOY002" for hand_card in player.zones[Zone.HAND])
            assert not fm_also_in_hand, \
                "TCTOY002 (as First Memory in play) should not simultaneously be in the player's hand."
        else:  # If a Toy other than Ghost Doll was chosen as First Memory
            assert fm_instance.current_zone == Zone.HAND, \
                (f"If First Memory is {fm_def_id} (not TCTOY002), it should be in hand for Whisper Wake, "
                 f"not {fm_instance.current_zone}.")
            # Additionally, ensure TCTOY002 (Ghost Doll) is still in play but is NOT the First Memory instance
            ghost_doll_in_play_obj = None
            for card_in_play_area in gs.cards_in_play.values():
                if card_in_play_area.definition.card_id == "TCTOY002":
                    ghost_doll_in_play_obj = card_in_play_area
                    break
            assert ghost_doll_in_play_obj is not None, \
                "TCTOY002 (Ghost Doll) should still be in play as per objective setup, even if not the First Memory."
            assert ghost_doll_in_play_obj.instance_id != gs.first_memory_instance_id, \
                ("If the First Memory is not TCTOY002, then the TCTOY002 (Ghost Doll) instance in play "
                 "should not be the game_state.first_memory_instance_id.")
        
        # # Ensure FM is not also in play (unless it's also the Ghost Doll, which is unlikely by design)
        # if gs.first_memory_instance_id:
        #     fm_instance_in_play = gs.get_card_instance(gs.first_memory_instance_id)
        #     assert fm_instance_in_play is None or fm_instance_in_play.definition.card_id != fm_def_id or fm_instance_in_play.definition.card_id == "TCTOY002", \
        #         "First Memory (if chosen from deck to hand) should not also be a separate instance in play unless it's the Ghost Doll."

        assert len(player.zones[Zone.HAND]) == INITIAL_HAND_SIZE
        assert gs.current_turn == 1