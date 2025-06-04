# tests/game_elements/test_data_loaders.py
import pytest
import json
import os
from typing import List, Dict, Any

from tuck_in_terrors_sim.game_elements.data_loaders import (
    load_cards, 
    load_objectives, 
    load_all_game_data,
    GameData,
    DEFAULT_CARDS_FILE, # For direct path manipulation if needed, though less ideal
    DEFAULT_OBJECTIVES_FILE
)
from tuck_in_terrors_sim.game_elements.card import Card, Toy, Spell, Effect, EffectAction
from tuck_in_terrors_sim.game_elements.objective import ObjectiveCard, ObjectiveLogicComponent
from tuck_in_terrors_sim.game_elements.enums import CardType, EffectTriggerType, EffectActionType


# --- Mock JSON Content ---
VALID_CARDS_JSON_CONTENT = """
[
    {
        "card_id": "T001",
        "name": "Test Toy Alpha",
        "card_type": "TOY",
        "cost": 1,
        "text": "A basic toy.",
        "effects": [
            {
                "effect_id": "T001_E1",
                "trigger": "ON_PLAY",
                "actions": [{"action_type": "DRAW_CARDS", "params": {"count": 1}}]
            }
        ]
    },
    {
        "card_id": "S001",
        "name": "Test Spell Beta",
        "card_type": "SPELL",
        "cost": 2,
        "text": "A basic spell.",
        "effects": [
            {
                "effect_id": "S001_E1",
                "trigger": "ON_PLAY",
                "actions": [{"action_type": "ADD_MANA", "params": {"amount": 1}}]
            }
        ]
    }
]
"""

VALID_OBJECTIVES_JSON_CONTENT = """
[
    {
        "objective_id": "OBJ01_TEST",
        "title": "Test Objective Alpha",
        "difficulty": "Easy",
        "description": "Complete this test.",
        "nightfall_turn": 10,
        "nightmare_creep_effects": [
            {
                "component_type": "STANDARD_NC", 
                "params": {
                    "effective_on_turn": 3,
                    "effect_to_apply": {
                         "actions": [{"action_type": "MILL_DECK", "params": {"count": 1}}]
                    }
                }
            }
        ]
    }
]
"""

INVALID_JSON_CONTENT = """{"name": "Test", "type": "TOY", cost: 1}""" # Missing comma, unquoted key

CARDS_MISSING_NAME_JSON_CONTENT = """[{"type": "TOY", "cost": 1}]"""
CARDS_MISSING_TYPE_JSON_CONTENT = """[{"name": "Nameless Wonder", "cost": 1}]"""


class TestDataLoaders:

    def test_load_cards_success(self, tmp_path):
        p = tmp_path / "cards_test.json"
        p.write_text(VALID_CARDS_JSON_CONTENT)
        cards = load_cards(str(p)) # Use renamed function
        assert len(cards) == 2
        assert cards[0].name == "Test Toy Alpha"
        assert cards[0].type == CardType.TOY
        assert cards[0].cost_mana == 1
        assert len(cards[0].effects) == 1
        assert cards[0].effects[0].trigger == EffectTriggerType.ON_PLAY
        assert cards[1].name == "Test Spell Beta"

    def test_load_cards_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_cards("non_existent_cards.json") # Use renamed function

    def test_load_cards_invalid_json(self, tmp_path):
        p = tmp_path / "invalid_cards.json"
        p.write_text(INVALID_JSON_CONTENT)
        with pytest.raises(ValueError, match="Error decoding JSON"): # Updated to check specific error type if possible
            load_cards(str(p)) # Use renamed function

    def test_load_cards_data_not_list(self, tmp_path):
        p = tmp_path / "not_list_cards.json"
        p.write_text("""{"card_id": "C001"}""") 
        with pytest.raises(ValueError, match="Card data in .* is not a list."): # Updated match
            load_cards(str(p)) # Use renamed function

    def test_load_cards_missing_name(self, tmp_path):
        p = tmp_path / "cards_missing_name.json"
        p.write_text(CARDS_MISSING_NAME_JSON_CONTENT)
        with pytest.raises(ValueError, match="Card data must have a 'name'."):
            load_cards(str(p)) # Use renamed function
            
    def test_load_cards_missing_type(self, tmp_path):
        p = tmp_path / "cards_missing_type.json"
        p.write_text(CARDS_MISSING_TYPE_JSON_CONTENT)
        # The error message comes from logic: if not card_type_json_val: raise ValueError(...)
        with pytest.raises(ValueError, match="must have a 'card_type' field in JSON"):
            load_cards(str(p)) # Use renamed function

    def test_load_objectives_success(self, tmp_path):
        p = tmp_path / "objectives_test.json"
        p.write_text(VALID_OBJECTIVES_JSON_CONTENT)
        objectives = load_objectives(str(p)) # Use renamed function
        assert len(objectives) == 1
        assert objectives[0].title == "Test Objective Alpha"
        assert objectives[0].difficulty == "Easy"
        assert len(objectives[0].nightmare_creep_effect) == 1
        assert objectives[0].nightmare_creep_effect[0].component_type == "STANDARD_NC"

    def test_load_objectives_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_objectives("non_existent_objectives.json") # Use renamed function

    def test_load_objectives_invalid_json(self, tmp_path):
        p = tmp_path / "invalid_objectives.json"
        p.write_text(INVALID_JSON_CONTENT) # Re-use invalid JSON
        with pytest.raises(ValueError, match="Error decoding JSON"): # Updated to check specific error type
            load_objectives(str(p)) # Use renamed function

    def test_load_all_game_data_success(self, tmp_path):
        cards_file = tmp_path / "all_cards.json"
        cards_file.write_text(VALID_CARDS_JSON_CONTENT)
        objectives_file = tmp_path / "all_objectives.json"
        objectives_file.write_text(VALID_OBJECTIVES_JSON_CONTENT)

        game_data = load_all_game_data(str(cards_file), str(objectives_file))
        assert isinstance(game_data, GameData)
        assert len(game_data.cards) == 2
        assert len(game_data.objectives) == 1
        assert game_data.get_card_by_id("T001").name == "Test Toy Alpha" # type: ignore
        assert game_data.get_objective_by_id("OBJ01_TEST").title == "Test Objective Alpha" # type: ignore