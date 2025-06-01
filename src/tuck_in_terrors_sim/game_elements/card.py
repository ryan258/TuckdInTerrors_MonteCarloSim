# src/tuck_in_terrors_sim/game_elements/card.py
# Version 4: Addressing direct instantiation TypeError in subclasses

from typing import List, Dict, Any, Optional
from .enums import CardType, CardSubType # Make sure enums.py is in the same directory

class EffectLogic:
    """
    Represents the programmable logic of a card effect.
    This structure will be stored in JSON and parsed.
    """
    def __init__(self,
                 trigger: str, 
                 conditions: Optional[List[Dict[str, Any]]] = None,
                 actions: List[Dict[str, Any]] = None, 
                 activation_costs: Optional[List[Dict[str, Any]]] = None,
                 description: Optional[str] = None,
                 is_echo_effect: bool = False,
                 is_once_per_turn: bool = False,
                 is_once_per_game: bool = False
                 ):
        self.trigger = trigger
        self.conditions = conditions if conditions is not None else []
        self.actions = actions if actions is not None else []
        self.activation_costs = activation_costs if activation_costs is not None else []
        self.description = description
        self.is_echo_effect = is_echo_effect
        self.is_once_per_turn = is_once_per_turn
        self.is_once_per_game = is_once_per_game

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trigger": self.trigger,
            "conditions": self.conditions,
            "actions": self.actions,
            "activation_costs": self.activation_costs,
            "description": self.description,
            "is_echo_effect": self.is_echo_effect,
            "is_once_per_turn": self.is_once_per_turn,
            "is_once_per_game": self.is_once_per_game
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EffectLogic':
        return cls(
            trigger=data.get("trigger", ""),
            conditions=data.get("conditions"),
            actions=data.get("actions"),
            activation_costs=data.get("activation_costs"),
            description=data.get("description"),
            is_echo_effect=data.get("is_echo_effect", False),
            is_once_per_turn=data.get("is_once_per_turn", False),
            is_once_per_game=data.get("is_once_per_game", False)
        )

class Card:
    def __init__(self,
                 card_id: str,
                 name: str,
                 card_type: CardType, 
                 cost: int,
                 text_flavor: Optional[str] = "",
                 text_rules: Optional[str] = "",
                 sub_types: Optional[List[CardSubType]] = None,
                 effect_logic_list: Optional[List[EffectLogic]] = None,
                 quantity_in_deck: int = 1,
                 power: Optional[int] = None,
                 rarity: Optional[str] = None
                 ):
        self.card_id = card_id
        self.name = name
        self.card_type = card_type 
        self.cost = cost 
        self.text_flavor = text_flavor
        self.text_rules = text_rules 
        self.sub_types = sub_types if sub_types is not None else []
        self.effect_logic_list = effect_logic_list if effect_logic_list is not None else []
        self.quantity_in_deck = quantity_in_deck
        self.power = power
        self.rarity = rarity

    def __repr__(self):
        card_type_name = self.card_type.name if hasattr(self, 'card_type') and self.card_type else "UnknownType"
        name_val = self.name if hasattr(self, 'name') else "Unnamed"
        id_val = self.card_id if hasattr(self, 'card_id') else "NoID"
        cost_val = self.cost if hasattr(self, 'cost') else "NoCost"
        return f"{card_type_name}: {name_val} (ID: {id_val}, Cost: {cost_val})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "card_id": self.card_id,
            "name": self.name,
            "card_type": self.card_type.name,
            "cost": self.cost,
            "text_flavor": self.text_flavor,
            "text_rules": self.text_rules,
            "sub_types": [st.name for st in self.sub_types],
            "effect_logic_list": [el.to_dict() for el in self.effect_logic_list],
            "quantity_in_deck": self.quantity_in_deck,
            "power": self.power,
            "rarity": self.rarity
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Card':
        card_type_str = data.get("card_type", "").upper()
        try:
            card_type_enum = CardType[card_type_str]
        except KeyError:
            print(f"Warning: Unknown CardType string '{card_type_str}' for card '{data.get('name')}'.")
            raise ValueError(f"Unknown CardType: {card_type_str}")

        sub_types_enums = []
        if data.get("sub_types"):
            for st_str in data["sub_types"]:
                try:
                    sub_types_enums.append(CardSubType[st_str.upper()])
                except KeyError:
                    print(f"Warning: Unknown CardSubType string '{st_str}' for card '{data.get('name')}'. Skipping.")

        effect_logic_objects = []
        if data.get("effect_logic_list"):
            for el_data in data["effect_logic_list"]:
                effect_logic_objects.append(EffectLogic.from_dict(el_data))
        
        constructor_args = {
            "card_id": data.get("card_id", ""),
            "name": data.get("name", ""),
            "card_type": card_type_enum, 
            "cost": data.get("cost", 0),
            "text_flavor": data.get("text_flavor", ""),
            "text_rules": data.get("text_rules", ""),
            "sub_types": sub_types_enums,
            "effect_logic_list": effect_logic_objects,
            "quantity_in_deck": data.get("quantity_in_deck", 1),
            "power": data.get("power"),
            "rarity": data.get("rarity")
        }

        if card_type_enum == CardType.TOY:
            return Toy(**constructor_args)
        elif card_type_enum == CardType.RITUAL:
            return Ritual(**constructor_args)
        elif card_type_enum == CardType.SPELL:
            return Spell(**constructor_args)
        else:
            # This case should ideally not be reached if card_type_enum is validated
            print(f"Error: Unhandled card type enum '{card_type_enum}' in Card.from_dict.")
            raise ValueError(f"Unhandled CardType enum: {card_type_enum}")


class Toy(Card):
    def __init__(self, card_id: str, name: str, cost: int, **kwargs):
        # Ensure card_type is correctly passed for direct instantiation and from_dict calls
        resolved_kwargs = kwargs.copy() # Avoid modifying the original kwargs dict directly if passed around
        resolved_kwargs['card_type'] = CardType.TOY
        super().__init__(card_id=card_id, name=name, cost=cost, **resolved_kwargs)

class Ritual(Card):
    def __init__(self, card_id: str, name: str, cost: int, **kwargs):
        resolved_kwargs = kwargs.copy()
        resolved_kwargs['card_type'] = CardType.RITUAL
        super().__init__(card_id=card_id, name=name, cost=cost, **resolved_kwargs)

class Spell(Card):
    def __init__(self, card_id: str, name: str, cost: int, **kwargs):
        resolved_kwargs = kwargs.copy()
        resolved_kwargs['card_type'] = CardType.SPELL
        super().__init__(card_id=card_id, name=name, cost=cost, **resolved_kwargs)