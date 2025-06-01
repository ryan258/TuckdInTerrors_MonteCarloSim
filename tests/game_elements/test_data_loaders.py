# tests/game_elements/test_data_loaders.py
# Unit tests for data_loaders.py
import pytest
import json
import os
from tuck_in_terrors_sim.game_elements.data_loaders import load_card_definitions, load_objective_definitions, GameData, load_all_game_data
from tuck_in_terrors_sim.game_elements.card import Card, Toy, Spell, Ritual
from tuck_in_terrors_sim.game_elements.objective import ObjectiveCard

# Sample valid JSON data for cards (as a string to be written to a temp file)
VALID_CARDS_JSON_CONTENT = """
[
  {
    "card_id": "TCTOY001",
    "name": "Toy Cow",
    "card_type": "TOY",
    "cost": 2,
    "sub_types": ["HAUNT"],
    "effect_logic_list": [],
    "quantity_in_deck": 2
  },
  {
    "card_id": "TCSPL001",
    "name": "Quick Spell",
    "card_type": "SPELL",
    "cost": 1,
    "effect_logic_list": [{"trigger": "ON_PLAY", "actions": [{"action_type": "DRAW_CARDS", "params": {"amount": 1}}]}],
    "quantity_in_deck": 3
  }
]
"""

# Sample valid JSON data for objectives
VALID_OBJECTIVES_JSON_CONTENT = """
[
  {
    "objective_id": "OBJ01_TEST",
    "title": "Test Objective One",
    "difficulty": "Easy",
    "nightfall_turn": 5,
    "primary_win_condition": {
      "component_type": "TEST_WIN_CON",
      "params": {"value": 10}
    }
  }
]
"""

# Sample invalid JSON
INVALID_JSON_CONTENT = """{"name": "Test", "value": 123""" # Missing closing brace

# Sample card data missing required fields
CARDS_MISSING_ID_JSON_CONTENT = """
[
  {"name": "Nameless Card", "card_type": "TOY", "cost": 1}
]
"""

class TestDataLoaders:
    def test_load_card_definitions_success(self, tmp_path):
        # tmp_path is a pytest fixture providing a temporary directory path object
        d = tmp_path / "data"
        d.mkdir()
        p = d / "cards_test.json"
        p.write_text(VALID_CARDS_JSON_CONTENT)

        cards = load_card_definitions(str(p))
        assert len(cards) == 2
        assert "TCTOY001" in cards
        assert isinstance(cards["TCTOY001"], Toy)
        assert cards["TCTOY001"].name == "Toy Cow"
        assert cards["TCTOY001"].cost == 2
        assert "TCSPL001" in cards
        assert isinstance(cards["TCSPL001"], Spell)
        assert cards["TCSPL001"].quantity_in_deck == 3

    def test_load_card_definitions_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_card_definitions("non_existent_cards.json")

    def test_load_card_definitions_invalid_json(self, tmp_path):
        p = tmp_path / "invalid_cards.json"
        p.write_text(INVALID_JSON_CONTENT)
        with pytest.raises(json.JSONDecodeError):
            load_card_definitions(str(p))
            
    def test_load_card_definitions_data_not_list(self, tmp_path):
        p = tmp_path / "not_list_cards.json"
        p.write_text("""{"card_id": "C001"}""") # JSON object, not list
        with pytest.raises(ValueError, match="Card data JSON should be a list"):
            load_card_definitions(str(p))


    def test_load_card_definitions_missing_id(self, tmp_path, capsys):
        # capsys is a pytest fixture to capture stdout/stderr
        p = tmp_path / "cards_missing_id.json"
        p.write_text(CARDS_MISSING_ID_JSON_CONTENT)
        
        cards = load_card_definitions(str(p)) # Should print warning and skip
        assert len(cards) == 0
        captured = capsys.readouterr()
        assert "Warning: Card data missing 'card_id'" in captured.out


    def test_load_objective_definitions_success(self, tmp_path):
        d = tmp_path / "data"
        d.mkdir()
        p = d / "objectives_test.json"
        p.write_text(VALID_OBJECTIVES_JSON_CONTENT)

        objectives = load_objective_definitions(str(p))
        assert len(objectives) == 1
        assert "OBJ01_TEST" in objectives
        assert isinstance(objectives["OBJ01_TEST"], ObjectiveCard)
        assert objectives["OBJ01_TEST"].title == "Test Objective One"
        assert objectives["OBJ01_TEST"].nightfall_turn == 5
        assert objectives["OBJ01_TEST"].primary_win_condition.component_type == "TEST_WIN_CON"

    def test_load_objective_definitions_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_objective_definitions("non_existent_objectives.json")

    def test_load_objective_definitions_invalid_json(self, tmp_path):
        p = tmp_path / "invalid_objectives.json"
        p.write_text(INVALID_JSON_CONTENT)
        with pytest.raises(json.JSONDecodeError):
            load_objective_definitions(str(p))

    def test_load_all_game_data_success(self, tmp_path):
        data_dir = tmp_path / "game_data_for_all"
        data_dir.mkdir()
        cards_file = data_dir / "all_cards.json"
        cards_file.write_text(VALID_CARDS_JSON_CONTENT)
        objectives_file = data_dir / "all_objectives.json"
        objectives_file.write_text(VALID_OBJECTIVES_JSON_CONTENT)

        game_data = load_all_game_data(str(cards_file), str(objectives_file))
        assert isinstance(game_data, GameData)
        assert len(game_data.cards) == 2
        assert len(game_data.objectives) == 1
        assert game_data.get_card_by_id("TCTOY001") is not None
        assert game_data.get_objective_by_id("OBJ01_TEST") is not None