# src/tuck_in_terrors_sim/game_elements/card.py
from typing import List, Dict, Any, Optional, Set
from .enums import (
    CardType, CardSubType, EffectTriggerType, EffectActionType,
    EffectConditionType, Zone, ResourceType, EffectActivationCostType
)

class Cost:
    def __init__(self, cost_details: Dict[EffectActivationCostType, Any]):
        self.cost_details = cost_details
        # Example: {EffectActivationCostType.PAY_MANA: 2, EffectActivationCostType.TAP_THIS_CARD: True}

    def __repr__(self):
        costs_str = []
        for k, v in self.cost_details.items():
            costs_str.append(f"{k.name}: {v}")
        return f"Cost({', '.join(costs_str)})"

    def to_dict(self) -> Dict[str, Any]:
        # Convert enum keys to strings for JSON serialization
        return {k.name: v for k, v in self.cost_details.items()}

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Optional['Cost']:
        if data is None: # Allow empty cost
            return None
        
        parsed_details = {}
        for cost_type_str, value in data.items():
            try:
                cost_type_enum = EffectActivationCostType[cost_type_str.upper()]
                parsed_details[cost_type_enum] = value
            except KeyError:
                # This should ideally raise an error or be logged more formally
                print(f"Warning: Unknown cost type '{cost_type_str}' encountered in Cost.from_dict. Skipping.")
                continue # Skip unknown cost types
        
        if not parsed_details and data: # If data was provided but no valid costs parsed
             print(f"Warning: Cost data {data} provided but no valid cost types recognized. Interpreting as no cost.")
             return None
        elif not parsed_details: # No data, no costs
            return None
            
        return cls(parsed_details)


class EffectAction:
    def __init__(self,
                 action_type: EffectActionType,
                 params: Dict[str, Any],
                 description: Optional[str] = ""):
        self.action_type = action_type
        # Params can contain nested EffectAction objects for sub-actions (e.g., in PLAYER_CHOICE)
        # These nested actions are expected to be parsed into EffectAction instances by data_loaders
        self.params = params
        self.description = description

    def __repr__(self):
        return f"EffectAction(type={self.action_type.name}, params={self.params})"

    def to_dict(self) -> Dict[str, Any]:
        # Handle nested EffectAction objects in params for serialization
        serialized_params = {}
        for key, value in self.params.items():
            if isinstance(value, EffectAction):
                serialized_params[key] = value.to_dict()
            elif isinstance(value, list) and value and all(isinstance(item, EffectAction) for item in value):
                serialized_params[key] = [item.to_dict() for item in value]
            # Serialize enums in params to their names (strings)
            elif isinstance(value, (Zone, CardType, ResourceType, EffectActionType, EffectConditionType, EffectActivationCostType, CardSubType)): # Add PlayerChoiceType if used directly in params
                serialized_params[key] = value.name
            elif isinstance(value, dict): # Recursively serialize enums in nested dicts
                serialized_params[key] = self._serialize_dict_enums(value)
            elif isinstance(value, list): # Recursively serialize enums in nested lists
                 serialized_params[key] = self._serialize_list_enums(value)
            else:
                serialized_params[key] = value
        
        return {
            "action_type": self.action_type.name, # Store enum name
            "params": serialized_params,
            "description": self.description
        }

    def _serialize_dict_enums(self, d: Dict[str, Any]) -> Dict[str, Any]:
        """Helper to serialize enums within a dictionary."""
        new_dict = {}
        for k, v in d.items():
            if isinstance(v, (Zone, CardType, ResourceType, EffectActionType, EffectConditionType, EffectActivationCostType, CardSubType)):
                new_dict[k] = v.name
            elif isinstance(v, dict):
                new_dict[k] = self._serialize_dict_enums(v)
            elif isinstance(v, list):
                new_dict[k] = self._serialize_list_enums(v)
            else:
                new_dict[k] = v
        return new_dict

    def _serialize_list_enums(self, l: List[Any]) -> List[Any]:
        """Helper to serialize enums within a list."""
        new_list = []
        for item in l:
            if isinstance(item, (Zone, CardType, ResourceType, EffectActionType, EffectConditionType, EffectActivationCostType, CardSubType)):
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
                 condition: Optional[Dict[EffectConditionType, Any]] = None, # Parsed condition
                 cost: Optional[Cost] = None,
                 description: Optional[str] = "",
                 is_replacement_effect: bool = False,
                 temporary_effect_data: Optional[Dict[str, Any]] = None,
                 source_card_id: Optional[str] = None
                ):
        self.effect_id = effect_id
        self.trigger = trigger
        self.actions = actions # List of EffectAction objects
        self.condition = condition # e.g. {EffectConditionType.PLAYER_HAS_RESOURCE: {"resource_type": ResourceType.MANA, "amount": 1}}
        self.cost = cost # Cost object
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
            # Assuming condition is {EnumType: params_dict}
            condition_type_enum, params_dict = list(self.condition.items())[0]
            # Serialize enums within params_dict before storing
            serialized_params = {}
            for k, v in params_dict.items():
                if isinstance(v, (Zone, CardType, ResourceType, EffectActionType, EffectConditionType)):
                     serialized_params[k] = v.name
                else:
                    serialized_params[k] = v
            serialized_condition = {"condition_type": condition_type_enum.name, "params": serialized_params}

        return {
            "effect_id": self.effect_id,
            "trigger": self.trigger.name, # Store enum name
            "actions": [action.to_dict() for action in self.actions],
            "condition": serialized_condition,
            "cost": self.cost.to_dict() if self.cost else None,
            "description": self.description,
            "is_replacement_effect": self.is_replacement_effect,
            "temporary_effect_data": self.temporary_effect_data,
            "source_card_id": self.source_card_id
        }


class Card:
    """Represents the definition of a card."""
    def __init__(self,
                 card_id: str,
                 name: str,
                 type: CardType,
                 cost_mana: int,
                 text: Optional[str] = "",
                 flavor_text: Optional[str] = "",
                 subtypes: Optional[List[CardSubType]] = None,
                 effects: Optional[List[Effect]] = None,
                 power: Optional[int] = None, # For Toys that can be in play with power
                 is_first_memory_potential: bool = False,
                 art_elements: Optional[Dict[str, Any]] = None
                 ):
        self.card_id = card_id
        self.name = name
        self.type = type
        self.cost_mana = cost_mana
        self.text = text # Rules text
        self.flavor_text = flavor_text
        self.subtypes = subtypes if subtypes is not None else []
        self.effects = effects if effects is not None else [] # List of Effect objects
        self.power = power
        self.is_first_memory_potential = is_first_memory_potential
        self.art_elements = art_elements if art_elements is not None else {}

    def __repr__(self):
        return f"Card(id='{self.card_id}', name='{self.name}', type={self.type.name}, cost={self.cost_mana})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "card_id": self.card_id,
            "name": self.name,
            "type": self.type.name, # Store enum name
            "cost_mana": self.cost_mana,
            "text": self.text,
            "flavor_text": self.flavor_text,
            "subtypes": [st.name for st in self.subtypes], # Store enum names
            "effects": [eff.to_dict() for eff in self.effects],
            "power": self.power,
            "is_first_memory_potential": self.is_first_memory_potential,
            "art_elements": self.art_elements
        }


class CardInstance:
    """Represents an instance of a card in a game, with its own state."""
    _next_instance_id: int = 1

    def __init__(self,
                 definition: Card,
                 owner_id: int, # The player_id of the owner
                 current_zone: Zone = Zone.DECK # Initial zone
                ):
        self.instance_id: str = f"cardinst_{CardInstance._next_instance_id}"
        CardInstance._next_instance_id += 1
        
        self.definition: Card = definition # The Card definition object
        self.owner_id: int = owner_id
        self.controller_id: int = owner_id # Initially, owner is controller

        self.current_zone: Zone = current_zone
        self.previous_zone: Optional[Zone] = None

        # Common mutable states
        self.is_tapped: bool = False
        self.counters: Dict[str, int] = {} # e.g., {"damage": 1, "growth": 2}
        
        self.turn_entered_play: Optional[int] = None # Game turn number it entered play
        self.abilities_granted_this_turn: List[Any] = [] # Placeholder for temporary abilities
        self.effects_applied_this_turn: Set[str] = set() # IDs of effects already applied if once-per-turn for instance

        # Additional state for more complex interactions
        self.chosen_modes: Dict[str, Any] = {} # For modal cards, effect_id -> chosen_mode
        self.custom_data: Dict[str, Any] = {} # For any other dynamic data, e.g., "imprinted_card_id"

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
        if current_amount >= amount:
            self.counters[counter_type] = current_amount - amount
            if self.counters[counter_type] == 0:
                del self.counters[counter_type]
            return True
        return False
        
    def get_counter(self, counter_type: str) -> int:
        return self.counters.get(counter_type, 0)

    def change_zone(self, new_zone: Zone, game_turn: Optional[int] = None):
        self.previous_zone = self.current_zone
        self.current_zone = new_zone
        if new_zone == Zone.IN_PLAY and self.previous_zone != Zone.IN_PLAY:
            self.turn_entered_play = game_turn
            self.is_tapped = False # Generally untaps unless "enters tapped"
        elif new_zone != Zone.IN_PLAY:
            self.turn_entered_play = None # Reset when leaving play
            # Potentially reset other states like counters, depending on game rules for zone changes


# Card Subclasses (Toy, Ritual, Spell)
# These can be simple inheritances if the Card base class handles all common attributes.
# They primarily serve for type checking and potentially minor unique behaviors later.

class Toy(Card):
    def __init__(self, card_id: str, name: str, cost_mana: int, **kwargs):
        # Ensure 'type' is correctly passed for direct instantiation and from_dict calls
        resolved_kwargs = kwargs.copy()
        resolved_kwargs['type'] = CardType.TOY # Match Card base class attribute name
        super().__init__(card_id=card_id, name=name, cost_mana=cost_mana, **resolved_kwargs)

class Ritual(Card):
    def __init__(self, card_id: str, name: str, cost_mana: int, **kwargs):
        resolved_kwargs = kwargs.copy()
        resolved_kwargs['type'] = CardType.RITUAL
        super().__init__(card_id=card_id, name=name, cost_mana=cost_mana, **resolved_kwargs)

class Spell(Card):
    def __init__(self, card_id: str, name: str, cost_mana: int, **kwargs):
        resolved_kwargs = kwargs.copy()
        resolved_kwargs['type'] = CardType.SPELL
        super().__init__(card_id=card_id, name=name, cost_mana=cost_mana, **resolved_kwargs)