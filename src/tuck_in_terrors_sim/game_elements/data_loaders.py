# src/tuck_in_terrors_sim/game_elements/data_loaders.py
# Functions to load and parse cards.json, objectives.json
import json
from typing import Dict, List

from .card import Card 
from .objective import ObjectiveCard

class GameData:
    def __init__(self,
                 cards: Dict[str, Card],
                 objectives: Dict[str, ObjectiveCard]):
        self.cards = cards
        self.objectives = objectives

    def get_card_by_id(self, card_id: str) -> Card | None:
        return self.cards.get(card_id)

    def get_objective_by_id(self, objective_id: str) -> ObjectiveCard | None:
        return self.objectives.get(objective_id)


def load_card_definitions(filepath: str) -> Dict[str, Card]:
    cards: Dict[str, Card] = {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f) 

        if not isinstance(data, list):
            raise ValueError("Card data JSON should be a list of card objects.")

        for card_data in data:
            if not isinstance(card_data, dict):
                print(f"Warning: Skipping non-dictionary item in card data: {card_data}")
                continue
            
            card_id = card_data.get("card_id")
            if not card_id:
                print(f"Warning: Card data missing 'card_id'. Skipping item: {card_data.get('name', 'Unknown card')}")
                continue

            try:
                card_obj = Card.from_dict(card_data)
                cards[card_obj.card_id] = card_obj
            except Exception as e:
                print(f"Warning: Error parsing card data for '{card_id or card_data.get('name', 'Unknown card')}': {e}. Skipping.")

    except FileNotFoundError:
        print(f"Error: Card data file not found at {filepath}")
        raise
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in card data file {filepath}: {e}")
        raise
    
    print(f"Successfully loaded {len(cards)} card definitions from {filepath}")
    return cards


def load_objective_definitions(filepath: str) -> Dict[str, ObjectiveCard]:
    objectives: Dict[str, ObjectiveCard] = {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f) 

        if not isinstance(data, list):
            raise ValueError("Objective data JSON should be a list of objective objects.")

        for objective_data in data:
            if not isinstance(objective_data, dict):
                print(f"Warning: Skipping non-dictionary item in objective data: {objective_data}")
                continue

            objective_id = objective_data.get("objective_id")
            if not objective_id:
                print(f"Warning: Objective data missing 'objective_id'. Skipping item: {objective_data.get('title', 'Unknown objective')}")
                continue
            
            try:
                objective_obj = ObjectiveCard.from_dict(objective_data)
                objectives[objective_obj.objective_id] = objective_obj
            except Exception as e:
                print(f"Warning: Error parsing objective data for '{objective_id or objective_data.get('title', 'Unknown objective')}': {e}. Skipping.")

    except FileNotFoundError:
        print(f"Error: Objective data file not found at {filepath}")
        raise
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in objective data file {filepath}: {e}")
        raise
        
    print(f"Successfully loaded {len(objectives)} objective definitions from {filepath}")
    return objectives

def load_all_game_data(cards_filepath: str, objectives_filepath: str) -> GameData:
    print("Loading all game data...")
    card_defs = load_card_definitions(cards_filepath)
    objective_defs = load_objective_definitions(objectives_filepath)
    print("All game data loaded.")
    return GameData(cards=card_defs, objectives=objective_defs)

if __name__ == '__main__':
    print("Testing data loaders...")
    try:
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, "..", "..", "..")) 
        cards_path = os.path.join(project_root, "data", "cards.json")
        objectives_path = os.path.join(project_root, "data", "objectives.json")

        game_data_container = load_all_game_data(cards_path, objectives_path)

        print(f"\n--- Loaded Cards ({len(game_data_container.cards)}) ---")
        for card_id, card_obj in game_data_container.cards.items():
            print(f"  {card_obj}")

        print(f"\n--- Loaded Objectives ({len(game_data_container.objectives)}) ---")
        for objective_id, objective_obj in game_data_container.objectives.items():
            print(f"  {objective_obj}")

    except Exception as e:
        print(f"An error occurred during data loader testing: {e}")