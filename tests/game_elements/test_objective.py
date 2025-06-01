# tests/game_elements/test_objective.py
# Unit tests for objective.py
import pytest
from tuck_in_terrors_sim.game_elements.objective import ObjectiveCard, ObjectiveLogicComponent

# Example Objective Data (similar to what would be in objectives.json)
FIRST_NIGHT_OBJECTIVE_DATA = {
    "objective_id": "OBJ01_THE_FIRST_NIGHT",
    "title": "The First Night",
    "difficulty": "Easy",
    "flavor_text": "The first whispers...",
    "primary_win_condition": {
      "component_type": "PLAY_X_DIFFERENT_TOYS_AND_CREATE_Y_SPIRITS",
      "params": {"toys_needed": 4, "spirits_needed": 4},
      "description": "Play 4 different Toys and create 4 Spirits."
    },
    "alternative_win_condition": {
      "component_type": "GENERATE_X_MANA_FROM_CARD_EFFECTS",
      "params": {"mana_needed": 5}
    },
    "first_memory_setup": {
      "component_type": "CHOOSE_TOY_FROM_HAND_PLACE_IN_PLAY",
      "params": {}
    },
    "nightmare_creep_effect": [
      {
        "component_type": "NIGHTMARE_CREEP_PHASED_EFFECT",
        "params": {"effective_on_turn": 5, "effect_to_apply": {"actions": [{"action_type": "PLAYER_CHOICE"}] } }
      }
    ],
    "setup_instructions": {
      "component_type": "CUSTOM_GAME_SETUP",
      "params": {"start_cards_in_hand": ["TCTOY001"], "first_turn_mana_override": 1}
    },
    "nightfall_turn": 4,
    "card_rotation": {"banned_card_ids": [], "featured_card_ids": ["TCTOY001"]},
    "special_rules_text": ["LIMIT/TWIST: None"]
}

class TestObjectiveLogicComponent:
    def test_creation_minimal(self):
        olc = ObjectiveLogicComponent(component_type="TEST_TYPE", params={"key": "value"})
        assert olc.component_type == "TEST_TYPE"
        assert olc.params["key"] == "value"
        assert olc.description is None

    def test_creation_full(self):
        olc = ObjectiveLogicComponent(
            component_type="ANOTHER_TYPE",
            params={"num": 10, "flag": True},
            description="A test component"
        )
        assert olc.component_type == "ANOTHER_TYPE"
        assert olc.params["num"] == 10
        assert olc.description == "A test component"

    def test_from_dict(self):
        data = {"component_type": "FROM_DICT_TYPE", "params": {"data": 123}, "description": "Desc"}
        olc = ObjectiveLogicComponent.from_dict(data)
        assert olc.component_type == "FROM_DICT_TYPE"
        assert olc.params["data"] == 123
        assert olc.description == "Desc"

    def test_to_dict(self):
        olc = ObjectiveLogicComponent(component_type="TO_DICT_TYPE", params={"p": "v"})
        data = olc.to_dict()
        assert data["component_type"] == "TO_DICT_TYPE"
        assert data["params"]["p"] == "v"

class TestObjectiveCard:
    def test_objective_creation_minimal(self):
        obj = ObjectiveCard(objective_id="OBJ_MIN", title="Minimal Obj", difficulty="Test", nightfall_turn=5)
        assert obj.objective_id == "OBJ_MIN"
        assert obj.title == "Minimal Obj"
        assert obj.nightfall_turn == 5
        assert obj.primary_win_condition is None # Make sure defaults are okay
        assert len(obj.nightmare_creep_effect) == 0

    def test_objective_from_dict(self):
        obj = ObjectiveCard.from_dict(FIRST_NIGHT_OBJECTIVE_DATA)
        assert obj.objective_id == "OBJ01_THE_FIRST_NIGHT"
        assert obj.title == "The First Night"
        assert obj.difficulty == "Easy"
        assert obj.nightfall_turn == 4
        
        assert isinstance(obj.primary_win_condition, ObjectiveLogicComponent)
        assert obj.primary_win_condition.component_type == "PLAY_X_DIFFERENT_TOYS_AND_CREATE_Y_SPIRITS"
        assert obj.primary_win_condition.params["toys_needed"] == 4
        
        assert isinstance(obj.alternative_win_condition, ObjectiveLogicComponent)
        assert obj.alternative_win_condition.component_type == "GENERATE_X_MANA_FROM_CARD_EFFECTS"

        assert isinstance(obj.first_memory_setup, ObjectiveLogicComponent)
        assert obj.first_memory_setup.component_type == "CHOOSE_TOY_FROM_HAND_PLACE_IN_PLAY"

        assert len(obj.nightmare_creep_effect) == 1
        assert isinstance(obj.nightmare_creep_effect[0], ObjectiveLogicComponent)
        assert obj.nightmare_creep_effect[0].component_type == "NIGHTMARE_CREEP_PHASED_EFFECT"

        assert isinstance(obj.setup_instructions, ObjectiveLogicComponent)
        assert obj.setup_instructions.params["first_turn_mana_override"] == 1
        
        assert obj.card_rotation["featured_card_ids"][0] == "TCTOY001"
        assert obj.special_rules_text[0] == "LIMIT/TWIST: None"

    def test_objective_to_dict_consistency(self):
        original_obj = ObjectiveCard.from_dict(FIRST_NIGHT_OBJECTIVE_DATA)
        obj_dict = original_obj.to_dict()
        recreated_obj = ObjectiveCard.from_dict(obj_dict)

        assert recreated_obj.objective_id == original_obj.objective_id
        assert recreated_obj.title == original_obj.title
        assert recreated_obj.nightfall_turn == original_obj.nightfall_turn
        assert (recreated_obj.primary_win_condition.component_type ==
                original_obj.primary_win_condition.component_type)