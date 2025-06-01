# tests/game_logic/test_action_resolver.py
# Unit tests for action_resolver.py

import pytest
from unittest.mock import MagicMock, patch

from tuck_in_terrors_sim.game_logic.game_state import GameState, CardInPlay
from tuck_in_terrors_sim.game_logic.action_resolver import ActionResolver
from tuck_in_terrors_sim.game_logic.effect_engine import EffectEngine
from tuck_in_terrors_sim.game_elements.card import Card, Toy, Spell, Ritual, EffectLogic
from tuck_in_terrors_sim.game_elements.enums import CardType, Zone, EffectTriggerType
from tuck_in_terrors_sim.game_elements.objective import ObjectiveCard 

# Fixture 'initialized_game_environment' is defined in tests/conftest.py
# It provides: game_state, turn_manager, effect_engine, nightmare_module, win_loss_checker
# We need a slightly different fixture setup for ActionResolver, or to extract parts.

@pytest.fixture
def mock_effect_engine() -> MagicMock:
    """Mocks the EffectEngine."""
    return MagicMock(spec=EffectEngine)

@pytest.fixture
def game_state_for_actions(game_data) -> GameState:
    """Provides a basic GameState, initialized for an objective."""
    objective = game_data.get_objective_by_id("OBJ01_THE_FIRST_NIGHT")
    if not objective:
        pytest.fail("Objective OBJ01_THE_FIRST_NIGHT not found for test setup.")
    
    gs = GameState(loaded_objective=objective, all_card_definitions=game_data.cards)
    gs.current_turn = 1
    gs.mana_pool = 10 
    
    # Ensure card IDs used for deck population exist in game_data.cards
    deck_card_ids = ["TCTOY001", "TCSPL001", "TCRIT001"]
    gs.deck = [game_data.cards[cid] for cid in deck_card_ids if cid in game_data.cards]
    
    if not gs.deck: 
        print("Warning: Test setup for game_state_for_actions resulted in an empty deck. Check card IDs.")

    if len(gs.deck) >= 2:
        gs.hand.append(gs.deck.pop(0))
        gs.hand.append(gs.deck.pop(0))
    elif gs.deck: 
        gs.hand.append(gs.deck.pop(0))
    
    return gs

@pytest.fixture
def action_resolver(game_state_for_actions: GameState, mock_effect_engine: MagicMock) -> ActionResolver:
    """Provides an ActionResolver instance with a mocked EffectEngine."""
    return ActionResolver(game_state_for_actions, mock_effect_engine)

class TestActionResolver:

    def test_play_card_from_hand_not_in_hand(self, action_resolver: ActionResolver, game_state_for_actions: GameState):
        non_hand_card = Toy(card_id="NOTINHAND", name="NotInHand Toy", cost=1, card_type=CardType.TOY)
        assert not action_resolver.play_card_from_hand(non_hand_card)
        assert "not in hand" in game_state_for_actions.game_log[-1].lower()

    def test_play_card_from_hand_toy_free_success(self, action_resolver: ActionResolver, game_state_for_actions: GameState, mock_effect_engine: MagicMock):
        gs = game_state_for_actions
        toy_to_play = Toy(card_id="FREE_TOY", name="Free Play Toy", cost=3, card_type=CardType.TOY) 
        gs.hand.append(toy_to_play)
        initial_hand_size = len(gs.hand)

        assert not gs.free_toy_played_this_turn
        result = action_resolver.play_card_from_hand(toy_to_play, is_free_toy_play=True)
        assert result is True
        assert gs.free_toy_played_this_turn is True
        assert len(gs.hand) == initial_hand_size - 1
        assert toy_to_play not in gs.hand
        
        played_instance = None
        for cip in gs.cards_in_play.values():
            if cip.card_definition == toy_to_play:
                played_instance = cip
                break
        assert played_instance is not None
        
        mock_effect_engine.trigger_effects.assert_any_call(
            trigger_type=EffectTriggerType.ON_PLAY,
            source_card_instance_for_trigger=played_instance,
            event_context={'played_card_instance': played_instance, 'targets': None}
        )
        mock_effect_engine.trigger_effects.assert_any_call(
            trigger_type=EffectTriggerType.WHEN_OTHER_CARD_ENTERS_PLAY,
            event_context={'entered_card_instance': played_instance}
        )

    def test_play_card_from_hand_toy_free_fail_already_used(self, action_resolver: ActionResolver, game_state_for_actions: GameState):
        gs = game_state_for_actions
        toy_to_play = Toy(card_id="ANOTHER_TOY", name="Another Toy", cost=1, card_type=CardType.TOY)
        gs.hand.append(toy_to_play)
        gs.free_toy_played_this_turn = True 

        assert not action_resolver.play_card_from_hand(toy_to_play, is_free_toy_play=True)
        assert "free toy already played" in gs.game_log[-1].lower()

    def test_play_card_from_hand_toy_free_fail_not_a_toy(self, action_resolver: ActionResolver, game_state_for_actions: GameState):
        gs = game_state_for_actions
        spell_to_play = Spell(card_id="ASPELL", name="NotAToySpell", cost=1, card_type=CardType.SPELL)
        gs.hand.append(spell_to_play)
        
        assert not action_resolver.play_card_from_hand(spell_to_play, is_free_toy_play=True)
        assert "only toys allowed" in gs.game_log[-1].lower()

    def test_play_card_from_hand_paid_spell_success(self, action_resolver: ActionResolver, game_state_for_actions: GameState, mock_effect_engine: MagicMock):
        gs = game_state_for_actions
        spell_to_play = Spell(card_id="PAID_SPELL", name="Paid Spell", cost=3, quantity_in_deck=1, card_type=CardType.SPELL)
        gs.hand.append(spell_to_play)
        initial_hand_size = len(gs.hand)
        initial_mana = gs.mana_pool
        initial_discard_size = len(gs.discard_pile)
        initial_storm = gs.storm_count_this_turn

        result = action_resolver.play_card_from_hand(spell_to_play, is_free_toy_play=False)
        assert result is True
        assert gs.mana_pool == initial_mana - spell_to_play.cost
        assert len(gs.hand) == initial_hand_size - 1
        assert spell_to_play not in gs.hand
        assert spell_to_play in gs.discard_pile
        assert len(gs.discard_pile) == initial_discard_size + 1
        assert gs.storm_count_this_turn == initial_storm + 1
        
        mock_effect_engine.trigger_effects.assert_any_call(
            trigger_type=EffectTriggerType.ON_PLAY,
            source_card_definition_for_trigger=spell_to_play,
            event_context={'played_card_definition': spell_to_play, 'targets': None}
        )

    def test_play_card_from_hand_paid_fail_not_enough_mana(self, action_resolver: ActionResolver, game_state_for_actions: GameState):
        gs = game_state_for_actions
        expensive_card = Toy(card_id="EXPENSIVE", name="Expensive Toy", cost=gs.mana_pool + 5, card_type=CardType.TOY)
        gs.hand.append(expensive_card)
        initial_hand_size = len(gs.hand)
        initial_mana = gs.mana_pool

        assert not action_resolver.play_card_from_hand(expensive_card, is_free_toy_play=False)
        assert "not enough mana" in gs.game_log[-1].lower()
        assert gs.mana_pool == initial_mana 
        assert len(gs.hand) == initial_hand_size 


    def test_activate_ability_success_basic(self, action_resolver: ActionResolver, game_state_for_actions: GameState, mock_effect_engine: MagicMock):
        gs = game_state_for_actions
        activatable_effect = EffectLogic( # This is the object we need to check
            trigger=EffectTriggerType.ACTIVATED_ABILITY.name, 
            actions=[{"action_type": "CREATE_SPIRIT_TOKENS", "params": {"amount": 1}}],
            description="Create a spirit"
        )
        card_def_with_ability = Toy(card_id="ABILITY_TOY", name="Ability Toy", cost=1, effect_logic_list=[activatable_effect], card_type=CardType.TOY)
        card_instance = CardInPlay(card_def_with_ability)
        gs.cards_in_play[card_instance.instance_id] = card_instance

        result = action_resolver.activate_ability(card_instance.instance_id, 0)
        assert result is True
        mock_effect_engine.resolve_effect_logic.assert_called_once_with(
            activatable_effect, # Use the correct variable name here
            source_card_instance=card_instance, 
            targets=None
        )
        
    def test_activate_ability_fail_not_activatable(self, action_resolver: ActionResolver, game_state_for_actions: GameState):
        gs = game_state_for_actions
        passive_effect = EffectLogic(trigger=EffectTriggerType.ON_PLAY.name, actions=[])
        card_def_passive = Toy(card_id="PASSIVE_TOY", name="Passive Toy", cost=1, effect_logic_list=[passive_effect], card_type=CardType.TOY)
        card_instance = CardInPlay(card_def_passive)
        gs.cards_in_play[card_instance.instance_id] = card_instance

        assert not action_resolver.activate_ability(card_instance.instance_id, 0)
        assert "not an activatable type" in gs.game_log[-1].lower()

    def test_activate_ability_fail_once_per_turn(self, action_resolver: ActionResolver, game_state_for_actions: GameState, mock_effect_engine: MagicMock):
        gs = game_state_for_actions
        once_per_turn_effect = EffectLogic(
            trigger=EffectTriggerType.ACTIVATED_ABILITY.name,
            actions=[{"action_type": "ADD_MANA", "params": {"amount": 1}}],
            is_once_per_turn=True,
            description="Gain 1 mana (1/turn)"
        )
        card_def_opt = Toy(card_id="OPT_TOY", name="OncePerTurn Toy", cost=1, effect_logic_list=[once_per_turn_effect], card_type=CardType.TOY)
        card_instance = CardInPlay(card_def_opt)
        gs.cards_in_play[card_instance.instance_id] = card_instance

        assert action_resolver.activate_ability(card_instance.instance_id, 0) is True
        mock_effect_engine.resolve_effect_logic.assert_called_with(once_per_turn_effect, source_card_instance=card_instance, targets=None)
        assert card_instance.effects_active_this_turn.get("effect_0") is True
        
        assert action_resolver.activate_ability(card_instance.instance_id, 0) is False
        assert "already used this turn" in gs.game_log[-1].lower()
        mock_effect_engine.resolve_effect_logic.assert_called_once() 

    def test_activate_ability_tap_ability(self, action_resolver: ActionResolver, game_state_for_actions: GameState, mock_effect_engine: MagicMock):
        gs = game_state_for_actions
        tap_effect = EffectLogic(
            trigger=EffectTriggerType.TAP_ABILITY.name,
            actions=[{"action_type": "DRAW_CARDS", "params": {"amount": 1}}],
            description="Tap: Draw a card"
        )
        card_def_tap = Toy(card_id="TAP_TOY", name="Tap Toy", cost=1, effect_logic_list=[tap_effect], card_type=CardType.TOY)
        card_instance = CardInPlay(card_def_tap)
        gs.cards_in_play[card_instance.instance_id] = card_instance

        assert not card_instance.is_tapped
        assert action_resolver.activate_ability(card_instance.instance_id, 0) is True
        assert card_instance.is_tapped
        mock_effect_engine.resolve_effect_logic.assert_called_with(tap_effect, source_card_instance=card_instance, targets=None)

        assert action_resolver.activate_ability(card_instance.instance_id, 0) is False
        assert "already tapped" in gs.game_log[-1].lower()