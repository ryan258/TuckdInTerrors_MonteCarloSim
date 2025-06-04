# tests/game_elements/test_card.py
# Unit tests for card.py (Card, Effect, EffectAction, Cost, Toy, Spell, Ritual classes)

import pytest
from typing import List, Dict, Any, Optional, Set # Added Set

from tuck_in_terrors_sim.game_elements.card import (
    Card, Toy, Ritual, Spell, Effect, EffectAction, Cost, CardInstance
)
# Ensure all used enums and DEFAULT_PLAYER_ID are imported
from tuck_in_terrors_sim.game_elements.enums import (
    CardType, CardSubType, EffectTriggerType, EffectActionType, 
    EffectActivationCostType, ResourceType, Zone, PlayerChoiceType, EffectConditionType
)
# Assuming DEFAULT_PLAYER_ID is a common constant, if it's defined in game_setup, import from there
# For test isolation, we can define it here or import if it's truly central.
# Let's assume it might come from game_setup for now, or define a local one for tests.
try:
    from tuck_in_terrors_sim.game_logic.game_setup import DEFAULT_PLAYER_ID
except ImportError:
    DEFAULT_PLAYER_ID = 0 # Local fallback for testing if not in game_setup

# --- Test Data for Effects and Costs ---
@pytest.fixture
def minimal_effect_action() -> EffectAction:
    # Using a confirmed valid EffectActionType
    return EffectAction(action_type=EffectActionType.DRAW_CARDS, params={"count": 1})

@pytest.fixture
def complex_effect_action(minimal_effect_action: EffectAction) -> EffectAction:
    return EffectAction(
        action_type=EffectActionType.PLAYER_CHOICE,
        params={
            "choice_type": PlayerChoiceType.CHOOSE_YES_NO, 
            "on_yes_actions": [ 
                EffectAction(action_type=EffectActionType.ADD_MANA, params={"amount": 1})
            ],
            "on_no_actions": []
        }
    )

@pytest.fixture
def minimal_cost() -> Cost:
    return Cost(cost_details={EffectActivationCostType.PAY_MANA: 1})

@pytest.fixture
def complex_cost() -> Cost:
    return Cost(cost_details={
        EffectActivationCostType.PAY_MANA: 2,
        EffectActivationCostType.TAP_THIS_CARD: True
    })

# --- Test Classes ---

class TestEffectAction:
    def test_creation_minimal(self):
        # Changed GAIN_SPIRIT to CREATE_SPIRIT_TOKENS, assuming that's a valid enum member
        action = EffectAction(action_type=EffectActionType.CREATE_SPIRIT_TOKENS, params={"amount": 1})
        assert action.action_type == EffectActionType.CREATE_SPIRIT_TOKENS
        assert action.params == {"amount": 1}

    def test_to_dict(self, minimal_effect_action: EffectAction):
        expected = {
            "action_type": "DRAW_CARDS",
            "params": {"count": 1},
            "description": ""
        }
        assert minimal_effect_action.to_dict() == expected

    def test_to_dict_with_enum_in_params(self):
        action = EffectAction(
            action_type=EffectActionType.PLACE_COUNTER_ON_CARD,
            params={"target_zone": Zone.IN_PLAY, "counter_type": "STUDY"} # Zone is now imported
        )
        expected_dict = {
            "action_type": "PLACE_COUNTER_ON_CARD",
            "params": {"target_zone": "IN_PLAY", "counter_type": "STUDY"}, 
            "description": ""
        }
        assert action.to_dict() == expected_dict


class TestCost:
    def test_creation(self, minimal_cost: Cost):
        assert minimal_cost.cost_details[EffectActivationCostType.PAY_MANA] == 1

    def test_to_dict(self, complex_cost: Cost):
        expected = {
            "PAY_MANA": 2,
            "TAP_THIS_CARD": True
        }
        assert complex_cost.to_dict() == expected

    def test_from_dict_valid(self):
        cost_data = {"PAY_MEMORY_TOKENS": 3, "SACRIFICE_FROM_PLAY": {"card_type": "TOY"}}
        cost = Cost.from_dict(cost_data)
        assert cost is not None
        assert cost.cost_details[EffectActivationCostType.PAY_MEMORY_TOKENS] == 3
        assert cost.cost_details[EffectActivationCostType.SACRIFICE_FROM_PLAY] == {"card_type": "TOY"}

    def test_from_dict_empty_and_none(self):
        assert Cost.from_dict(None) is None
        assert Cost.from_dict({}) is None 

class TestEffect:
    def test_creation_minimal(self, minimal_effect_action: EffectAction):
        effect = Effect(effect_id="E001", trigger=EffectTriggerType.ON_PLAY, actions=[minimal_effect_action])
        assert effect.effect_id == "E001"
        assert effect.trigger == EffectTriggerType.ON_PLAY
        assert effect.actions == [minimal_effect_action]

    def test_creation_full(self, minimal_effect_action: EffectAction, complex_cost: Cost):
        # EffectConditionType and ResourceType are now imported
        condition = {EffectConditionType.PLAYER_HAS_RESOURCE: {"resource_type": ResourceType.SPIRIT, "amount": 1}}
        effect = Effect(
            effect_id="E002",
            trigger=EffectTriggerType.ON_LEAVE_PLAY,
            actions=[minimal_effect_action],
            condition=condition,
            cost=complex_cost,
            description="Test full effect",
            is_replacement_effect=True,
            source_card_id="C123"
        )
        assert effect.description == "Test full effect"
        assert effect.is_replacement_effect is True
        assert effect.source_card_id == "C123"
        assert effect.condition == condition # Verify condition is stored

    def test_to_dict(self, minimal_effect_action: EffectAction, minimal_cost: Cost):
        # EffectConditionType and ResourceType are now imported
        parsed_condition_for_effect = {EffectConditionType.DECK_SIZE_LE: {"count": 10}}
        effect = Effect(
            effect_id="E003",
            trigger=EffectTriggerType.BEGIN_PLAYER_TURN,
            actions=[minimal_effect_action],
            condition=parsed_condition_for_effect, # Use the one with Enum key
            cost=minimal_cost,
            source_card_id="CXYZ"
        )
        
        effect_dict = effect.to_dict()
        
        # Expected serialized condition
        expected_dict_condition = {
            "condition_type": EffectConditionType.DECK_SIZE_LE.name, # Enum name
            "params": {"count": 10} 
        }
        
        assert effect_dict["effect_id"] == "E003"
        assert effect_dict["trigger"] == "BEGIN_PLAYER_TURN" # Enum name
        assert len(effect_dict["actions"]) == 1
        assert effect_dict["actions"][0]["action_type"] == "DRAW_CARDS" # Enum name from EffectAction.to_dict()
        assert effect_dict["condition"] == expected_dict_condition
        assert effect_dict["cost"]["PAY_MANA"] == 1 # type: ignore # Enum name from Cost.to_dict()
        assert effect_dict["source_card_id"] == "CXYZ"

class TestCardClasses: # Renamed from TestCard for clarity
    @pytest.fixture
    def sample_effect(self, minimal_effect_action: EffectAction) -> Effect:
        return Effect(effect_id="SampleE1", trigger=EffectTriggerType.ON_PLAY, actions=[minimal_effect_action])

    def test_card_creation_minimal(self):
        # Corrected: uses 'type' and 'cost_mana'
        card = Card(card_id="C001", name="Minimal Card", type=CardType.SPELL, cost_mana=1)
        assert card.name == "Minimal Card"
        assert card.type == CardType.SPELL
        assert card.cost_mana == 1

    def test_toy_creation(self, sample_effect: Effect):
        # Corrected: uses 'cost_mana'. 'type' is set by Toy.__init__
        toy = Toy(card_id="T001", name="Brave Toy", cost_mana=2, 
                  effects=[sample_effect], subtypes=[CardSubType.HAUNT])
        assert toy.name == "Brave Toy"
        assert toy.type == CardType.TOY
        assert toy.cost_mana == 2
        assert toy.effects == [sample_effect]
        assert toy.subtypes == [CardSubType.HAUNT]

    def test_ritual_creation(self, sample_effect: Effect):
        # Corrected: uses 'cost_mana'. 'type' is set by Ritual.__init__
        ritual = Ritual(card_id="R001", name="Dark Ritual", cost_mana=3, effects=[sample_effect])
        assert ritual.name == "Dark Ritual"
        assert ritual.type == CardType.RITUAL
        assert ritual.cost_mana == 3

    def test_spell_creation(self):
        # Corrected: uses 'cost_mana'. 'type' is set by Spell.__init__
        spell = Spell(card_id="S001", name="Quick Spell", cost_mana=0)
        assert spell.name == "Quick Spell"
        assert spell.type == CardType.SPELL
        assert spell.cost_mana == 0
    
    def test_card_to_dict(self, sample_effect: Effect):
        card = Toy(
            card_id="T002", name="Complex Toy", type=CardType.TOY, cost_mana=3,
            text="Rules text.", flavor_text="Flavor.",
            subtypes=[CardSubType.LOOP, CardSubType.HAUNT], 
            effects=[sample_effect, sample_effect], 
            power=5,
            is_first_memory_potential=True, 
            art_elements={"artist": "Me"}
        )
        card_dict = card.to_dict()
        assert card_dict["card_id"] == "T002"
        assert card_dict["type"] == "TOY"
        assert card_dict["cost_mana"] == 3
        assert card_dict["subtypes"] == ["LOOP", "HAUNT"]
        assert len(card_dict["effects"]) == 2
        assert card_dict["effects"][0]["trigger"] == "ON_PLAY"

    # Note: Card.from_dict tests