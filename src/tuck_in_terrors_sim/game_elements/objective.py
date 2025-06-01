# Defines Objective class, win conditions, setup logic
# src/tuck_in_terrors_sim/game_elements/objective.py
from typing import List, Dict, Any, Optional
# from .enums import ... # Import any enums needed for condition/action types if not already in effect_logic

# Assuming EffectLogic structure from card.py can be reused for some objective-specific effects
# or a similar structure is defined here for win conditions, nightmare creep, etc.

class ObjectiveLogicComponent:
    """ A generic component for storing structured logic for objectives,
        e.g., for win conditions, setup instructions, nightmare creep phases.
    """
    def __init__(self, component_type: str, params: Dict[str, Any], description: Optional[str] = None):
        self.component_type = component_type # e.g., "PLAY_X_TOYS", "REACH_NIGHTFALL_TURN"
        self.params = params
        self.description = description # Optional text description

    def to_dict(self) -> Dict[str, Any]:
        return {
            "component_type": self.component_type,
            "params": self.params,
            "description": self.description
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ObjectiveLogicComponent':
        return cls(
            component_type=data.get("component_type", ""),
            params=data.get("params", {}),
            description=data.get("description")
        )


class ObjectiveCard:
    def __init__(self,
                 objective_id: str,
                 title: str,
                 difficulty: str, # E.g., "Easy", "Moderate", "Hard"
                 flavor_text: Optional[str] = "",
                 primary_win_condition: ObjectiveLogicComponent = None,
                 alternative_win_condition: Optional[ObjectiveLogicComponent] = None,
                 first_memory_setup: ObjectiveLogicComponent = None, # How First Memory is chosen/placed
                 # List of effects that might apply due to First Memory specific to this objective
                 first_memory_ongoing_effects: Optional[List[Dict[str, Any]]] = None, # Simplified for now
                 nightmare_creep_effect: List[ObjectiveLogicComponent] = None, # List for escalating effects
                 setup_instructions: Optional[ObjectiveLogicComponent] = None, # Starting cards, mana etc.
                 nightfall_turn: int = 0,
                 card_rotation: Optional[Dict[str, List[str]]] = None, # E.g., {"banned": ["card_id1"], "featured": ["card_id2"]}
                 special_rules_text: Optional[List[str]] = None # Text description of special rules
                 ):
        self.objective_id = objective_id
        self.title = title
        self.difficulty = difficulty
        self.flavor_text = flavor_text
        self.primary_win_condition = primary_win_condition
        self.alternative_win_condition = alternative_win_condition
        self.first_memory_setup = first_memory_setup
        self.first_memory_ongoing_effects = first_memory_ongoing_effects if first_memory_ongoing_effects is not None else []
        self.nightmare_creep_effect = nightmare_creep_effect if nightmare_creep_effect is not None else [] # Represents phases/escalations
        self.setup_instructions = setup_instructions
        self.nightfall_turn = nightfall_turn
        self.card_rotation = card_rotation if card_rotation is not None else {"banned": [], "featured": []}
        self.special_rules_text = special_rules_text if special_rules_text is not None else []

    def __repr__(self):
        return f"Objective: {self.title} (ID: {self.objective_id}, Difficulty: {self.difficulty})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "objective_id": self.objective_id,
            "title": self.title,
            "difficulty": self.difficulty,
            "flavor_text": self.flavor_text,
            "primary_win_condition": self.primary_win_condition.to_dict() if self.primary_win_condition else None,
            "alternative_win_condition": self.alternative_win_condition.to_dict() if self.alternative_win_condition else None,
            "first_memory_setup": self.first_memory_setup.to_dict() if self.first_memory_setup else None,
            "first_memory_ongoing_effects": self.first_memory_ongoing_effects, # Keep as list of dicts for now
            "nightmare_creep_effect": [nce.to_dict() for nce in self.nightmare_creep_effect],
            "setup_instructions": self.setup_instructions.to_dict() if self.setup_instructions else None,
            "nightfall_turn": self.nightfall_turn,
            "card_rotation": self.card_rotation,
            "special_rules_text": self.special_rules_text
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ObjectiveCard':
        primary_wc_data = data.get("primary_win_condition")
        alt_wc_data = data.get("alternative_win_condition")
        fm_setup_data = data.get("first_memory_setup")
        setup_instr_data = data.get("setup_instructions")
        nc_effects_data = data.get("nightmare_creep_effect", [])

        return cls(
            objective_id=data.get("objective_id", ""),
            title=data.get("title", ""),
            difficulty=data.get("difficulty", ""),
            flavor_text=data.get("flavor_text", ""),
            primary_win_condition=ObjectiveLogicComponent.from_dict(primary_wc_data) if primary_wc_data else None,
            alternative_win_condition=ObjectiveLogicComponent.from_dict(alt_wc_data) if alt_wc_data else None,
            first_memory_setup=ObjectiveLogicComponent.from_dict(fm_setup_data) if fm_setup_data else None,
            first_memory_ongoing_effects=data.get("first_memory_ongoing_effects"),
            nightmare_creep_effect=[ObjectiveLogicComponent.from_dict(nce_data) for nce_data in nc_effects_data],
            setup_instructions=ObjectiveLogicComponent.from_dict(setup_instr_data) if setup_instr_data else None,
            nightfall_turn=data.get("nightfall_turn", 0),
            card_rotation=data.get("card_rotation"),
            special_rules_text=data.get("special_rules_text")
        )