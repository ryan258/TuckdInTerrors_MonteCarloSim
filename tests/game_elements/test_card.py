# tests/game_elements/test_card.py
# Unit tests for card.py
import pytest
from tuck_in_terrors_sim.game_elements.card import Card, Toy, Ritual, Spell, EffectLogic
from tuck_in_terrors_sim.game_elements.enums import CardType, CardSubType, EffectTriggerType, EffectActionType, EffectConditionType

# Example Card Data (similar to what would be in cards.json)
TOY_COW_DATA = {
    "card_id": "TCTOY001",
    "name": "Toy Cow With Bell That Never Rings",
    "card_type": "TOY",
    "cost": 2,
    "text_flavor": "Her stitched eyes follow you...",
    "text_rules": "Haunt. When Toy Cow returns...",
    "sub_types": ["HAUNT", "BROWSE_SEARCH"],
    "effect_logic_list": [
        {
            "trigger": "ON_LEAVE_PLAY",
            "actions": [{"action_type": "CREATE_SPIRIT_TOKENS", "params": {"amount": 1}}],
            "description": "Haunt effect"
        },
        {
            "trigger": "ON_PLAY",
            "is_echo_effect": True,
            "actions": [{"action_type": "CREATE_SPIRIT_TOKENS", "params": {"amount": 1}}],
            "description": "Echo effect"
        }
    ],
    "quantity_in_deck": 2,
    "rarity": "Toy - Core Set"
}

SPELL_DATA_SIMPLE = {
    "card_id": "TCSPL002",
    "name": "Simple Spell",
    "card_type": "SPELL",
    "cost": 1,
    "effect_logic_list": [
        {
            "trigger": "ON_PLAY",
            "actions": [{"action_type": "DRAW_CARDS", "params": {"amount": 1}}]
        }
    ],
    "quantity_in_deck": 3
}

RITUAL_DATA_SIMPLE = {
    "card_id": "TCRIT002",
    "name": "Simple Ritual",
    "card_type": "RITUAL",
    "cost": 3,
    "effect_logic_list": [
        {
            "trigger": "BEGIN_PLAYER_TURN",
            "actions": [{"action_type": "ADD_MANA", "params": {"amount": 1}}]
        }
    ],
    "quantity_in_deck": 1
}


class TestEffectLogic:
    def test_effect_logic_creation_minimal(self):
        effect = EffectLogic(trigger="ON_PLAY", actions=[{"action_type": "DRAW_CARDS", "params": {"amount": 1}}])
        assert effect.trigger == "ON_PLAY"
        assert len(effect.actions) == 1
        assert effect.actions[0]["action_type"] == "DRAW_CARDS"
        assert not effect.conditions
        assert not effect.is_echo_effect
        assert not effect.is_once_per_game
        assert not effect.is_once_per_turn

    def test_effect_logic_creation_full(self):
        effect = EffectLogic(
            trigger="ON_LEAVE_PLAY",
            conditions=[{"condition_type": "IS_FIRST_MEMORY", "params": {}}],
            actions=[{"action_type": "CREATE_MEMORY_TOKENS", "params": {"amount": 1}}],
            description="Test Effect",
            is_echo_effect=True,
            is_once_per_turn=True,
            is_once_per_game=False
        )
        assert effect.trigger == "ON_LEAVE_PLAY"
        assert len(effect.conditions) == 1
        assert effect.conditions[0]["condition_type"] == "IS_FIRST_MEMORY"
        assert len(effect.actions) == 1
        assert effect.actions[0]["action_type"] == "CREATE_MEMORY_TOKENS"
        assert effect.description == "Test Effect"
        assert effect.is_echo_effect
        assert effect.is_once_per_turn
        assert not effect.is_once_per_game

    def test_effect_logic_from_dict(self):
        data = {
            "trigger": "ON_PLAY",
            "actions": [{"action_type": "DRAW_CARDS", "params": {"amount": 1}}],
            "is_echo_effect": True
        }
        effect = EffectLogic.from_dict(data)
        assert effect.trigger == "ON_PLAY"
        assert len(effect.actions) == 1
        assert effect.actions[0]["action_type"] == "DRAW_CARDS"
        assert effect.is_echo_effect

    def test_effect_logic_to_dict(self):
        effect = EffectLogic(trigger="ON_PLAY", actions=[{"action_type": "DRAW_CARDS", "params": {"amount": 1}}])
        data = effect.to_dict()
        assert data["trigger"] == "ON_PLAY"
        assert len(data["actions"]) == 1
        assert data["actions"][0]["action_type"] == "DRAW_CARDS"

class TestCard:
    def test_card_creation_minimal(self):
        card = Card(card_id="C001", name="Test Card", card_type=CardType.SPELL, cost=1)
        assert card.card_id == "C001"
        assert card.name == "Test Card"
        assert card.card_type == CardType.SPELL
        assert card.cost == 1
        assert card.quantity_in_deck == 1
        assert len(card.effect_logic_list) == 0

    def test_toy_creation(self):
        toy = Toy(card_id="T001", name="Test Toy", cost=2, quantity_in_deck=2)
        assert toy.card_id == "T001"
        assert toy.name == "Test Toy"
        assert toy.card_type == CardType.TOY
        assert toy.cost == 2
        assert toy.quantity_in_deck == 2

    def test_ritual_creation(self):
        ritual = Ritual(card_id="R001", name="Test Ritual", cost=3)
        assert ritual.card_type == CardType.RITUAL

    def test_spell_creation(self):
        spell = Spell(card_id="S001", name="Test Spell", cost=0)
        assert spell.card_type == CardType.SPELL

    def test_card_from_dict_toy(self):
        card = Card.from_dict(TOY_COW_DATA)
        assert isinstance(card, Toy)
        assert card.card_id == "TCTOY001"
        assert card.name == "Toy Cow With Bell That Never Rings"
        assert card.card_type == CardType.TOY
        assert card.cost == 2
        assert CardSubType.HAUNT in card.sub_types
        assert CardSubType.BROWSE_SEARCH in card.sub_types
        assert len(card.effect_logic_list) == 2
        assert isinstance(card.effect_logic_list[0], EffectLogic)
        assert card.effect_logic_list[0].trigger == EffectTriggerType.ON_LEAVE_PLAY.name # from_dict converts to string trigger from EffectLogic
        assert card.effect_logic_list[1].is_echo_effect == True
        assert card.quantity_in_deck == 2

    def test_card_from_dict_spell(self):
        card = Card.from_dict(SPELL_DATA_SIMPLE)
        assert isinstance(card, Spell)
        assert card.card_id == "TCSPL002"
        assert card.card_type == CardType.SPELL
        assert len(card.effect_logic_list) == 1

    def test_card_from_dict_ritual(self):
        card = Card.from_dict(RITUAL_DATA_SIMPLE)
        assert isinstance(card, Ritual)
        assert card.card_id == "TCRIT002"
        assert card.card_type == CardType.RITUAL
        assert len(card.effect_logic_list) == 1

    def test_card_to_dict_consistency(self):
        # Test if to_dict output can be used by from_dict to recreate a similar object
        # (Exact recreation depends on how enums are handled - names vs values)
        original_card = Card.from_dict(TOY_COW_DATA)
        card_dict = original_card.to_dict()
        recreated_card = Card.from_dict(card_dict)

        assert recreated_card.card_id == original_card.card_id
        assert recreated_card.name == original_card.name
        assert recreated_card.card_type == original_card.card_type
        assert recreated_card.cost == original_card.cost
        assert len(recreated_card.sub_types) == len(original_card.sub_types)
        # Deeper comparison of effect_logic_list might be needed for full round-trip fidelity
        assert len(recreated_card.effect_logic_list) == len(original_card.effect_logic_list)
        assert recreated_card.effect_logic_list[0].trigger == original_card.effect_logic_list[0].trigger

    def test_card_from_dict_unknown_subtype(self):
        data_with_unknown_subtype = {
            "card_id": "T002", "name": "Toy With Bad SubType", "card_type": "TOY", "cost": 1,
            "sub_types": ["HAUNT", "UNKNOWN_SUBTYPE"]
        }
        card = Card.from_dict(data_with_unknown_subtype)
        assert CardSubType.HAUNT in card.sub_types
        assert len(card.sub_types) == 1 # Unknown subtype should be skipped as per Card.from_dict logic