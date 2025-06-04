# src/tuck_in_terrors_sim/game_elements/card.py
from typing import List, Dict, Any, Optional, Set, TYPE_CHECKING

# To handle List['CardInstance'] type hint if used for attachments
if TYPE_CHECKING:
    from .card import CardInstance # Forward reference

from .enums import (
    CardType, CardSubType, EffectTriggerType, EffectActionType,
    EffectConditionType, Zone, ResourceType, EffectActivationCostType, PlayerChoiceType
)

class Cost:
    def __init__(self, cost_details: Dict[EffectActivationCostType, Any]):
        self.cost_details = cost_details if cost_details is not None else {}

    def __repr__(self):
        costs_str = []
        for k, v in self.cost_details.items():
            costs_str.append(f"{k.name}: {v}")
        return f"Cost({', '.join(costs_str)})"

    def to_dict(self) -> Dict[str, Any]:
        return {k.name: v for k, v in self.cost_details.items()}

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional['Cost']:
        if data is None:
            return None
        
        parsed_details = {}
        
        # Handle {"cost_type": "TYPE", "params": value} structure
        cost_type_str_from_field = data.get("cost_type")
        if isinstance(cost_type_str_from_field, str):
            try:
                cost_type_enum = EffectActivationCostType[cost_type_str_from_field.upper()]
                # Store params directly or process them if needed. Assuming params is the value here.
                # For MANA, params might be {"amount": X}. For TAP_THIS_CARD, params might be empty or True.
                params = data.get("params", True) # Default to True if no params (like for TAP_THIS_CARD)
                parsed_details[cost_type_enum] = params
            except KeyError:
                # This is where the ValueError should be raised for test_parse_cost_various
                raise ValueError(f"Unknown EffectActivationCostType: {cost_type_str_from_field}")
        else:
            # Handle old format { "MANA": 2, "TAP_THIS_CARD": True }
            for cost_type_str_key, value in data.items():
                try:
                    cost_type_enum = EffectActivationCostType[cost_type_str_key.upper()]
                    parsed_details[cost_type_enum] = value
                except KeyError:
                    # This path is for keys that are not valid EffectActivationCostType names
                    # print(f"Warning: Unknown cost key '{cost_type_str_key}' encountered in Cost.from_dict. Skipping.")
                    pass # Continue, might be other valid keys

        if not parsed_details and data:
            # If data was provided but nothing was parsed (e.g., all keys were unknown in the old format
            # or "cost_type" was not a string or was an unknown enum value before raising error)
            # This warning might be redundant if ValueError is raised above.
            # For now, keep it, but ValueError should catch unknown "cost_type" string.
            # If "cost_type" field is missing, and all other keys are invalid, this warning is relevant.
            all_keys_are_cost_type_field = all(k in ["cost_type", "params"] for k in data.keys())
            if not (cost_type_str_from_field and all_keys_are_cost_type_field) : # Only warn if not the new structure that failed for other reasons
                 print(f"Warning: Cost data {data} provided but no valid cost types recognized. Interpreting as no cost.")
            return None # Or an empty Cost if that's preferred over None
        elif not parsed_details:
            return None
            
        return cls(cost_details=parsed_details)


class EffectAction:
    def __init__(self,
                 action_type: EffectActionType, # Changed from 'type'
                 params: Dict[str, Any],
                 description: Optional[str] = ""):
        self.action_type = action_type
        self.params = params
        self.description = description

    def __repr__(self):
        return f"EffectAction(action_type={self.action_type.name}, params={self.params})" # Changed 'type' to 'action_type'

    def to_dict(self) -> Dict[str, Any]:
        serialized_params = {}
        for key, value in self.params.items():
            if isinstance(value, EffectAction):
                serialized_params[key] = value.to_dict()
            elif isinstance(value, list) and value and all(isinstance(item, EffectAction) for item in value):
                serialized_params[key] = [item.to_dict() for item in value]
            elif isinstance(value, (Zone, CardType, ResourceType, EffectActionType, EffectConditionType, EffectActivationCostType, CardSubType, PlayerChoiceType)): # Added PlayerChoiceType
                serialized_params[key] = value.name
            elif isinstance(value, dict): 
                serialized_params[key] = self._serialize_dict_enums(value)
            elif isinstance(value, list): 
                serialized_params[key] = self._serialize_list_enums(value)
            else:
                serialized_params[key] = value
        
        return {
            "action_type": self.action_type.name,
            "params": serialized_params,
            "description": self.description
        }

    def _serialize_dict_enums(self, d: Dict[str, Any]) -> Dict[str, Any]:
        new_dict = {}
        for k, v in d.items():
            if isinstance(v, (Zone, CardType, ResourceType, EffectActionType, EffectConditionType, EffectActivationCostType, CardSubType, PlayerChoiceType)):
                new_dict[k] = v.name
            elif isinstance(v, dict):
                new_dict[k] = self._serialize_dict_enums(v)
            elif isinstance(v, list):
                new_dict[k] = self._serialize_list_enums(v)
            else:
                new_dict[k] = v
        return new_dict

    def _serialize_list_enums(self, l: List[Any]) -> List[Any]:
        new_list = []
        for item in l:
            if isinstance(item, (Zone, CardType, ResourceType, EffectActionType, EffectConditionType, EffectActivationCostType, CardSubType, PlayerChoiceType)):
                new_list.append(item.name)
            elif isinstance(item, dict):
                new_list.append(self._serialize_dict_enums(item))
            elif isinstance(item, list):
                new_list.append(self._serialize_list_enums(item))
            else:
                new_list.append(item)
        return new_list


class Effect:
    def __init__(self,
                 effect_id: str,
                 trigger: EffectTriggerType,
                 actions: List[EffectAction],
                 condition: Optional[Dict[EffectConditionType, Any]] = None, 
                 cost: Optional[Cost] = None,
                 description: Optional[str] = "",
                 is_replacement_effect: bool = False,
                 temporary_effect_data: Optional[Dict[str, Any]] = None,
                 source_card_id: Optional[str] = None
                ):
        self.effect_id = effect_id
        self.trigger = trigger
        self.actions = actions 
        self.condition = condition 
        self.cost = cost 
        self.description = description
        self.is_replacement_effect = is_replacement_effect
        self.temporary_effect_data = temporary_effect_data if temporary_effect_data is not None else {}
        self.source_card_id = source_card_id

    def __repr__(self):
        return (f"Effect(id='{self.effect_id}', trigger={self.trigger.name}, "
                f"actions_count={len(self.actions)}, condition_present={self.condition is not None}, "
                f"cost_present={self.cost is not None})")

    def to_dict(self) -> Dict[str, Any]:
        serialized_condition = None
        if self.condition:
            condition_type_enum, params_dict = list(self.condition.items())[0]
            serialized_params = {}
            for k, v in params_dict.items():
                if isinstance(v, (Zone, CardType, ResourceType, EffectActionType, EffectConditionType, PlayerChoiceType)): # Added PlayerChoiceType
                    serialized_params[k] = v.name
                else:
                    serialized_params[k] = v
            serialized_condition = {"condition_type": condition_type_enum.name, "params": serialized_params}

        return {
            "effect_id": self.effect_id,
            "trigger": self.trigger.name, 
            "actions": [action.to_dict() for action in self.actions],
            "condition": serialized_condition,
            "cost": self.cost.to_dict() if self.cost else None,
            "description": self.description,
            "is_replacement_effect": self.is_replacement_effect,
            "temporary_effect_data": self.temporary_effect_data,
            "source_card_id": self.source_card_id
        }


class Card:
    def __init__(self,
                 card_id: str,
                 name: str,
                 type: CardType, # Parameter name in constructor
                 cost_mana: int,
                 text: Optional[str] = "",
                 flavor_text: Optional[str] = "",
                 subtypes: Optional[List[CardSubType]] = None,
                 effects: Optional[List[Effect]] = None,
                 power: Optional[str] = None, # Changed to Optional[str] to match common "X/Y" format; parsing to int can be specific to Toy
                 is_first_memory_potential: bool = False,
                 art_elements: Optional[Dict[str, Any]] = None
                ):
        self.card_id = card_id
        self.name = name
        self.type = type # Attribute name matches parameter
        self.cost_mana = cost_mana
        self.text = text 
        self.flavor_text = flavor_text
        self.subtypes = subtypes if subtypes is not None else []
        self.effects = effects if effects is not None else [] 
        self.power = power 
        self.is_first_memory_potential = is_first_memory_potential
        self.art_elements = art_elements if art_elements is not None else {}

    def __repr__(self):
        return f"Card(id='{self.card_id}', name='{self.name}', type={self.type.name}, cost={self.cost_mana})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "card_id": self.card_id,
            "name": self.name,
            "type": self.type.name, 
            "cost_mana": self.cost_mana,
            "text": self.text,
            "flavor_text": self.flavor_text,
            "subtypes": [st.name for st in self.subtypes], 
            "effects": [eff.to_dict() for eff in self.effects],
            "power": self.power,
            "is_first_memory_potential": self.is_first_memory_potential,
            "art_elements": self.art_elements
        }


class CardInstance:
    _next_instance_id: int = 1

    def __init__(self,
                 definition: Card,
                 owner_id: int, 
                 current_zone: Zone = Zone.DECK 
                ):
        # Corrected instance_id generation
        self.instance_id: str = f"{definition.card_id}_inst_{CardInstance._next_instance_id}"
        CardInstance._next_instance_id += 1
        
        self.definition: Card = definition 
        self.owner_id: int = owner_id
        self.controller_id: int = owner_id 

        self.current_zone: Zone = current_zone
        self.previous_zone: Optional[Zone] = None

        self.is_tapped: bool = False
        self.counters: Dict[str, int] = {} 
        self.attachments: List[Any] = [] # Added attachments attribute, using List[Any] for now
        
        self.turn_entered_play: Optional[int] = None 
        self.turns_in_play: int = 0
        self.abilities_granted_this_turn: List[Any] = [] 
        self.effects_active_this_turn: Set[str] = set() # Changed from effects_applied_this_turn

        self.chosen_modes: Dict[str, Any] = {} 
        self.custom_data: Dict[str, Any] = {} 

    def __repr__(self):
        return (f"CardInstance(id='{self.instance_id}', name='{self.definition.name}', "
                f"zone={self.current_zone.name}, owner={self.owner_id}, tapped={self.is_tapped}, "
                f"counters={self.counters})")

    def tap(self) -> bool:
        if not self.is_tapped:
            self.is_tapped = True
            return True
        return False

    def untap(self) -> bool:
        if self.is_tapped:
            self.is_tapped = False
            return True
        return False

    def add_counter(self, counter_type: str, amount: int = 1):
        self.counters[counter_type] = self.counters.get(counter_type, 0) + amount

    def remove_counter(self, counter_type: str, amount: int = 1) -> bool:
        current_amount = self.counters.get(counter_type, 0)
        new_amount = max(0, current_amount - amount) # Ensure counter doesn't go below 0
        
        if new_amount == 0:
            if counter_type in self.counters:
                del self.counters[counter_type]
                return True # Counter was present and removed
            return False # Counter was not present or already 0
        else:
            if current_amount > 0 : # only update if there was a counter to begin with
                self.counters[counter_type] = new_amount
                return True
            return False # No counter to remove from
            
    def get_counter(self, counter_type: str) -> int:
        return self.counters.get(counter_type, 0)

    def change_zone(self, new_zone: Zone, game_turn: Optional[int] = None):
        self.previous_zone = self.current_zone
        self.current_zone = new_zone
        if new_zone == Zone.IN_PLAY and self.previous_zone != Zone.IN_PLAY:
            self.turn_entered_play = game_turn
            self.is_tapped = False 
        elif new_zone != Zone.IN_PLAY:
            self.turn_entered_play = None 


class Toy(Card):
    def __init__(self, card_id: str, name: str, cost_mana: int, **kwargs):
        # 'type' will be in kwargs from the data loader
        # We want to ensure the correct type for this class (Toy) is passed to Card base
        # and avoid passing 'type' twice.
        actual_kwargs = kwargs.copy()
        actual_kwargs.pop('type', None) # Remove 'type' from the dict to be expanded
        super().__init__(card_id=card_id, name=name, type=CardType.TOY, cost_mana=cost_mana, **actual_kwargs)
class Ritual(Card):
    def __init__(self, card_id: str, name: str, cost_mana: int, **kwargs):
        actual_kwargs = kwargs.copy()
        actual_kwargs.pop('type', None) 
        super().__init__(card_id=card_id, name=name, type=CardType.RITUAL, cost_mana=cost_mana, **actual_kwargs)

class Spell(Card):
    def __init__(self, card_id: str, name: str, cost_mana: int, **kwargs):
        actual_kwargs = kwargs.copy()
        actual_kwargs.pop('type', None)
        super().__init__(card_id=card_id, name=name, type=CardType.SPELL, cost_mana=cost_mana, **actual_kwargs)