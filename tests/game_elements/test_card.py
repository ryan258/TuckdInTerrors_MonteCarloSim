# tests/game_elements/test_card.py
import pytest
from typing import Dict, List, Any, Optional

from tuck_in_terrors_sim.game_elements.card import (
    Card, Toy, Spell, Ritual, Effect, EffectAction, Cost, CardInstance
)
from tuck_in_terrors_sim.game_elements.enums import (
    CardType, CardSubType, EffectTriggerType, EffectActionType, Zone,
    EffectConditionType, ResourceType, EffectActivationCostType
)

# --- Test Fixtures / Mock Data ---

@pytest.fixture
def minimal_card_data() -> Dict[str, Any]:
    return {
        "card_id": "C001",
        "name": "Test Card",
        "type": CardType.TOY,
        "cost_mana": 1
    }

@pytest.fixture
def toy_card_data(minimal_card_data: Dict[str, Any]) -> Dict[str, Any]:
    data = minimal_card_data.copy()
    data.update({
        "name": "Test Toy Alpha", # Specific name for this fixture
        "type": CardType.TOY,
        "text": "A simple toy.",
        "flavor_text": "It's fun!",
        "subtypes": [CardSubType.TEDDY_BEAR],
        "power": "2/2" # Assuming power is parsed elsewhere or not directly used by base Card
    })
    return data

@pytest.fixture
def spell_card_data(minimal_card_data: Dict[str, Any]) -> Dict[str, Any]:
    data = minimal_card_data.copy()
    data.update({
        "card_id": "S001",
        "name": "Test Spell Beta", # Specific name
        "type": CardType.SPELL,
        "cost_mana": 2,
        "text": "Draw a card."
    })
    return data

@pytest.fixture
def ritual_card_data(minimal_card_data: Dict[str, Any]) -> Dict[str, Any]:
    data = minimal_card_data.copy()
    data.update({
        "card_id": "R001",
        "name": "Test Ritual Gamma", # Specific name
        "type": CardType.RITUAL,
        "cost_mana": 3,
        "text": "Do something ritualistic."
    })
    return data


@pytest.fixture
def minimal_effect_action() -> EffectAction:
    return EffectAction(action_type=EffectActionType.DRAW_CARDS, params={"count": 1})

@pytest.fixture
def complex_cost() -> Cost:
    # Cost.__init__ expects 'cost_details'
    return Cost(cost_details={EffectActivationCostType.PAY_MANA: 2, EffectActivationCostType.TAP_THIS_CARD: True})


# --- Tests for Cost ---
class TestCost:
    def test_creation(self):
        cost_dict_details = {EffectActivationCostType.PAY_MANA: 3, EffectActivationCostType.SACRIFICE_THIS_CARD: True}
        cost = Cost(cost_details=cost_dict_details)
        assert cost.cost_details[EffectActivationCostType.PAY_MANA] == 3
        assert cost.cost_details[EffectActivationCostType.SACRIFICE_THIS_CARD] is True

    def test_to_dict(self):
        cost_dict_details = {EffectActivationCostType.PAY_MANA: 1, EffectActivationCostType.TAP_THIS_CARD: True}
        cost = Cost(cost_details=cost_dict_details)
        expected_dict = {"PAY_MANA": 1, "TAP_THIS_CARD": True} 
        assert cost.to_dict() == expected_dict

    def test_from_dict_valid(self):
        data = {"MANA": 2, "TAP_THIS_CARD": True} # from_dict expects keys to be enum names
        cost = Cost.from_dict(data)
        assert cost is not None
        assert cost.cost_details.get(EffectActivationCostType.MANA) == 2
        assert cost.cost_details.get(EffectActivationCostType.TAP_THIS_CARD) is True

    def test_from_dict_empty_or_none(self):
        assert Cost.from_dict({}) is None 
        assert Cost.from_dict(None) is None

# --- Tests for EffectAction ---
class TestEffectAction:
    def test_creation(self):
        action = EffectAction(action_type=EffectActionType.ADD_MANA, params={"amount": 5}, description="Gain mana.")
        assert action.action_type == EffectActionType.ADD_MANA
        assert action.params["amount"] == 5
        assert action.description == "Gain mana."

    def test_to_dict_with_enum_in_params(self):
        action = EffectAction(
            action_type=EffectActionType.PLACE_COUNTER_ON_CARD, 
            params={"counter_type": "STUDY", "target_zone": Zone.IN_PLAY},
            description="Add study counter."
        )
        # Test serialization of enum in params
        action_dict = action.to_dict()
        assert action_dict["params"]["target_zone"] == "IN_PLAY"


# --- Tests for Effect ---
class TestEffect:
    def test_creation_minimal(self, minimal_effect_action: EffectAction):
        effect = Effect(effect_id="E001", trigger=EffectTriggerType.ON_PLAY, actions=[minimal_effect_action])
        assert effect.effect_id == "E001"
        assert effect.trigger == EffectTriggerType.ON_PLAY
        assert len(effect.actions) == 1
        assert effect.actions[0].action_type == EffectActionType.DRAW_CARDS

    def test_creation_full(self, minimal_effect_action: EffectAction, complex_cost: Cost):
        condition = {EffectConditionType.PLAYER_HAS_RESOURCE: {"resource_type": ResourceType.SPIRIT_TOKENS, "amount": 1}}
        effect = Effect(
            effect_id="E002",
            trigger=EffectTriggerType.ACTIVATED_ABILITY,
            actions=[minimal_effect_action, minimal_effect_action],
            condition=condition,
            description="Complex effect",
            cost=complex_cost, 
            is_replacement_effect=True,
            source_card_id="C_TEST"
        )
        assert effect.description == "Complex effect"
        assert effect.cost == complex_cost 
        assert effect.is_replacement_effect is True
        assert effect.condition[EffectConditionType.PLAYER_HAS_RESOURCE]["resource_type"] == ResourceType.SPIRIT_TOKENS

    def test_to_dict(self, minimal_effect_action, complex_cost):
        condition = {EffectConditionType.PLAYER_HAS_RESOURCE: {"resource_type": ResourceType.MANA, "amount": 3}}
        effect = Effect(
            effect_id="E_DICT",
            trigger=EffectTriggerType.ACTIVATED_ABILITY,
            actions=[minimal_effect_action],
            condition=condition,
            cost=complex_cost, 
            description="Test to_dict",
            source_card_id="C_SRC"
        )
        effect_dict = effect.to_dict()
        assert effect_dict["effect_id"] == "E_DICT"
        assert effect_dict["cost"] is not None


# --- Tests for Card Classes (Card, Toy, Spell, Ritual) ---
class TestCardClasses:
    def test_card_creation_minimal(self, minimal_card_data: Dict[str, Any]):
        card = Card(**minimal_card_data)
        assert card.card_id == "C001"
        assert card.name == "Test Card"
        assert card.type == CardType.TOY
        assert card.cost_mana == 1
        assert card.text == "" 
        assert card.effects == [] 

    def test_toy_creation(self, toy_card_data: Dict[str, Any]):
        toy = Toy(**toy_card_data)
        assert isinstance(toy, Toy)
        assert toy.name == "Test Toy Alpha"
        assert toy.type == CardType.TOY
        assert CardSubType.TEDDY_BEAR in toy.subtypes

    def test_spell_creation(self, spell_card_data: Dict[str, Any]):
        spell = Spell(**spell_card_data)
        assert isinstance(spell, Spell)
        assert spell.name == "Test Spell Beta"
        assert spell.type == CardType.SPELL

    def test_ritual_creation(self, ritual_card_data: Dict[str, Any]):
        ritual = Ritual(**ritual_card_data)
        assert isinstance(ritual, Ritual)
        assert ritual.name == "Test Ritual Gamma"
        assert ritual.type == CardType.RITUAL

    def test_card_to_dict(self, toy_card_data: Dict[str, Any]):
        toy = Toy(**toy_card_data)
        mock_action = EffectAction(EffectActionType.DRAW_CARDS, {"count":1})
        mock_effect = Effect("E1", EffectTriggerType.ON_PLAY, [mock_action])
        toy.effects = [mock_effect]
        
        toy_dict = toy.to_dict() 
        assert toy_dict["name"] == toy.name
        assert toy_dict["type"] == toy.type.name 
        assert toy_dict["cost_mana"] == toy.cost_mana
        assert toy_dict["subtypes"] == [st.name for st in toy.subtypes]
        assert len(toy_dict["effects"]) == 1
        assert toy_dict["effects"][0]["effect_id"] == "E1"


# --- Tests for CardInstance ---
class TestCardInstance:
    def test_card_instance_creation(self, toy_card_data: Dict[str, Any]):
        base_toy = Toy(**toy_card_data) # Name is "Test Toy Alpha", card_id is "C001" from minimal_card_data via toy_card_data
        instance = CardInstance(definition=base_toy, owner_id=0, current_zone=Zone.HAND)
        
        assert instance.definition == base_toy
        # This will be fixed by changing CardInstance.__init__
        assert instance.instance_id.startswith(base_toy.card_id) 
        
        assert instance.owner_id == 0
        assert instance.current_zone == Zone.HAND
        assert not instance.is_tapped
        assert instance.counters == {}
        # This will be fixed by adding self.attachments = [] to CardInstance.__init__
        assert instance.attachments == [] 
        assert instance.effects_active_this_turn == set()
        assert instance.turns_in_play == 0
        assert instance.turn_entered_play is None
        assert instance.custom_data == {}

    def test_tap_untap(self, toy_card_data: Dict[str, Any]):
        instance = CardInstance(Toy(**toy_card_data), 0, Zone.IN_PLAY)
        assert not instance.is_tapped
        instance.tap()
        assert instance.is_tapped
        instance.untap()
        assert not instance.is_tapped

    def test_add_remove_counters(self, toy_card_data: Dict[str, Any]):
        instance = CardInstance(Toy(**toy_card_data), 0, Zone.IN_PLAY)
        instance.add_counter("test_counter", 2)
        assert instance.counters["test_counter"] == 2
        instance.add_counter("test_counter", 1)
        assert instance.counters["test_counter"] == 3
        instance.remove_counter("test_counter", 1)
        assert instance.counters["test_counter"] == 2
        instance.remove_counter("test_counter", 5) # Try to remove 5 when only 2 exist
        # This will be fixed by CardInstance.remove_counter logic
        assert "test_counter" not in instance.counters 

    def test_enters_play_timestamp(self, toy_card_data: Dict[str, Any]):
        instance = CardInstance(Toy(**toy_card_data), 0, Zone.DECK)
        assert instance.turn_entered_play is None
        # Changed to call change_zone
        instance.change_zone(Zone.IN_PLAY, game_turn=3)
        assert instance.turn_entered_play == 3
        # To test turns_in_play, a turn increment mechanism would be needed,
        # or a direct call to a hypothetical instance.increment_turns_in_play()
        # For now, this part of the test is simplified.