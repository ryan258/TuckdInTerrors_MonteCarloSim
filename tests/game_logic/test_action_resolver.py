# tests/game_logic/test_action_resolver.py

import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, List, Optional, Any, Tuple # Added Dict here

# Game elements
from tuck_in_terrors_sim.game_elements.card import Card, Toy, Spell, Ritual, Effect, EffectAction, CardInstance
from tuck_in_terrors_sim.game_elements.objective import ObjectiveCard
from tuck_in_terrors_sim.game_elements.enums import CardType, EffectTriggerType, Zone, EffectActionType
# Game logic
from tuck_in_terrors_sim.game_logic.game_state import GameState, PlayerState
from tuck_in_terrors_sim.game_logic.effect_engine import EffectEngine
from tuck_in_terrors_sim.game_logic.action_resolver import ActionResolver # Import ActionResolver
from tuck_in_terrors_sim.game_logic.game_setup import DEFAULT_PLAYER_ID


@pytest.fixture
def mock_effect_engine() -> MagicMock:
    return MagicMock(spec=EffectEngine)

@pytest.fixture
def empty_objective_card() -> ObjectiveCard:
    return ObjectiveCard(objective_id="test_obj", title="Test Objective", difficulty="easy", nightfall_turn=10)

@pytest.fixture
def card_defs_for_resolver() -> Dict[str, Card]: # Type hint 'Dict' is now defined
    dummy_action = EffectAction(action_type=EffectActionType.DRAW_CARDS, params={"count": 1})
    return {
        "toy1": Toy(card_id="toy1", name="Test Toy", type=CardType.TOY, cost_mana=1, 
                    effects=[Effect(effect_id="toy1_onplay", trigger=EffectTriggerType.ON_PLAY, actions=[dummy_action])]),
        "spell1": Spell(card_id="spell1", name="Test Spell", type=CardType.SPELL, cost_mana=2,
                       effects=[Effect(effect_id="spell1_onplay", trigger=EffectTriggerType.ON_PLAY, actions=[dummy_action])]),
        "ritual1": Ritual(card_id="ritual1", name="Test Ritual", type=CardType.RITUAL, cost_mana=3,
                         effects=[Effect(effect_id="ritual1_onplay", trigger=EffectTriggerType.ON_PLAY, actions=[dummy_action])]),
        "activatable_toy": Toy(card_id="act_toy", name="Activatable Toy", type=CardType.TOY, cost_mana=1,
                               effects=[
                                   Effect(effect_id="act1", trigger=EffectTriggerType.ACTIVATED_ABILITY, actions=[dummy_action], description="Ability 1"),
                                   Effect(effect_id="tap_ab", trigger=EffectTriggerType.TAP_ABILITY, actions=[dummy_action], description="Tap Ability")
                               ])
    }

@pytest.fixture
def game_state_for_actions(empty_objective_card: ObjectiveCard, card_defs_for_resolver: Dict[str, Card]) -> GameState:
    gs = GameState(loaded_objective=empty_objective_card, all_card_definitions=card_defs_for_resolver)
    player = PlayerState(player_id=DEFAULT_PLAYER_ID, initial_deck=[]) 
    gs.player_states[DEFAULT_PLAYER_ID] = player
    gs.active_player_id = DEFAULT_PLAYER_ID
    gs.current_turn = 1
    # Initialize EffectEngine for GameState if it's expected by any internal GameState logic (not typical)
    # gs.effect_engine = mock_effect_engine() # If needed by GameState itself
    return gs

@pytest.fixture
def action_resolver(game_state_for_actions: GameState, mock_effect_engine: MagicMock) -> ActionResolver:
    # Pass the game_state_for_actions to the EffectEngine if it's stored as a reference
    # Assuming EffectEngine init might be: EffectEngine(game_state_ref=game_state_for_actions)
    # For this test, effect_engine is mocked, so its internal gs reference might not matter unless methods are called on it
    return ActionResolver(game_state_for_actions, mock_effect_engine)

class TestActionResolverPlayCard:
    def test_play_toy_from_hand_sufficient_mana(self, action_resolver: ActionResolver, game_state_for_actions: GameState, card_defs_for_resolver: Dict[str, Card], mock_effect_engine: MagicMock):
        gs = game_state_for_actions
        player = gs.get_active_player_state()
        assert player is not None
        
        toy_card_def = card_defs_for_resolver["toy1"]
        toy_instance = CardInstance(definition=toy_card_def, owner_id=player.player_id, current_zone=Zone.HAND)
        player.zones[Zone.HAND].append(toy_instance)
        player.mana = 5

        success = action_resolver.play_card(toy_instance.instance_id, is_free_toy_play=False)
        
        assert success is True
        assert toy_instance not in player.zones[Zone.HAND] # Should be moved by move_card_zone
        assert toy_instance.instance_id in gs.cards_in_play
        assert gs.cards_in_play[toy_instance.instance_id] == toy_instance
        assert toy_instance.current_zone == Zone.IN_PLAY
        assert player.mana == 4 
        # Check if the ON_PLAY effect of toy1 was resolved
        # This assumes toy1_def.effects[0] is the ON_PLAY effect
        mock_effect_engine.resolve_effect.assert_any_call(
            effect=toy_card_def.effects[0],
            game_state=gs,
            player=player,
            source_card_instance=toy_instance,
            triggering_event_context={'played_card_instance_id': toy_instance.instance_id, 'targets': None}
        )


    def test_play_spell_from_hand(self, action_resolver: ActionResolver, game_state_for_actions: GameState, card_defs_for_resolver: Dict[str, Card], mock_effect_engine: MagicMock):
        gs = game_state_for_actions
        player = gs.get_active_player_state()
        assert player is not None

        spell_card_def = card_defs_for_resolver["spell1"]
        spell_instance = CardInstance(definition=spell_card_def, owner_id=player.player_id, current_zone=Zone.HAND)
        player.zones[Zone.HAND].append(spell_instance)
        player.mana = 3

        success = action_resolver.play_card(spell_instance.instance_id)

        assert success is True
        assert spell_instance not in player.zones[Zone.HAND]
        assert spell_instance in player.zones[Zone.DISCARD] 
        assert spell_instance.current_zone == Zone.DISCARD
        assert player.mana == 1 
        mock_effect_engine.resolve_effect.assert_any_call(
            effect=spell_card_def.effects[0],
            game_state=gs,
            player=player,
            source_card_instance=spell_instance,
            triggering_event_context={'played_spell_instance_id': spell_instance.instance_id, 'targets': None}
        )

    def test_play_card_not_in_hand(self, action_resolver: ActionResolver, game_state_for_actions: GameState):
        gs = game_state_for_actions
        player = gs.get_active_player_state()
        assert player is not None
        player.mana = 5
        
        success = action_resolver.play_card("nonexistent_instance_id")
        assert success is False
        # Check log for specific message (optional, good for debugging)
        # assert "not in P0's hand" in gs.game_log[-1] 

    def test_play_card_insufficient_mana(self, action_resolver: ActionResolver, game_state_for_actions: GameState, card_defs_for_resolver: Dict[str, Card]):
        gs = game_state_for_actions
        player = gs.get_active_player_state()
        assert player is not None

        toy_card_def = card_defs_for_resolver["toy1"] 
        toy_instance = CardInstance(definition=toy_card_def, owner_id=player.player_id, current_zone=Zone.HAND)
        player.zones[Zone.HAND].append(toy_instance)
        player.mana = 0

        success = action_resolver.play_card(toy_instance.instance_id)
        assert success is False
        assert player.mana == 0
        assert toy_instance in player.zones[Zone.HAND] 

    def test_free_toy_play(self, action_resolver: ActionResolver, game_state_for_actions: GameState, card_defs_for_resolver: Dict[str, Card]):
        gs = game_state_for_actions
        player = gs.get_active_player_state()
        assert player is not None

        toy_card_def = card_defs_for_resolver["toy1"]
        toy_instance = CardInstance(definition=toy_card_def, owner_id=player.player_id, current_zone=Zone.HAND)
        player.zones[Zone.HAND].append(toy_instance)
        player.mana = 0
        player.has_played_free_toy_this_turn = False

        success = action_resolver.play_card(toy_instance.instance_id, is_free_toy_play=True)
        assert success is True
        assert player.has_played_free_toy_this_turn is True
        assert toy_instance.instance_id in gs.cards_in_play
        assert player.mana == 0 

    def test_activate_ability(self, action_resolver: ActionResolver, game_state_for_actions: GameState, card_defs_for_resolver: Dict[str, Card], mock_effect_engine: MagicMock):
        gs = game_state_for_actions
        player = gs.get_active_player_state()
        assert player is not None

        act_toy_def = card_defs_for_resolver["activatable_toy"]
        act_toy_inst = CardInstance(definition=act_toy_def, owner_id=player.player_id, current_zone=Zone.IN_PLAY)
        gs.cards_in_play[act_toy_inst.instance_id] = act_toy_inst
        player.zones[Zone.IN_PLAY].append(act_toy_inst)

        success = action_resolver.activate_ability(act_toy_inst.instance_id, effect_index=0)
        assert success is True
        mock_effect_engine.resolve_effect.assert_called_once_with(
            effect=act_toy_def.effects[0],
            game_state=gs,
            player=player,
            source_card_instance=act_toy_inst,
            triggering_event_context={'activated_ability_on_instance_id': act_toy_inst.instance_id, 'targets': None}
        )

    def test_activate_tap_ability_when_untapped(self, action_resolver: ActionResolver, game_state_for_actions: GameState, card_defs_for_resolver: Dict[str, Card], mock_effect_engine: MagicMock):
        gs = game_state_for_actions
        player = gs.get_active_player_state()
        assert player is not None

        act_toy_def = card_defs_for_resolver["activatable_toy"]
        act_toy_inst = CardInstance(definition=act_toy_def, owner_id=player.player_id, current_zone=Zone.IN_PLAY)
        gs.cards_in_play[act_toy_inst.instance_id] = act_toy_inst
        player.zones[Zone.IN_PLAY].append(act_toy_inst)
        act_toy_inst.is_tapped = False

        success = action_resolver.activate_ability(act_toy_inst.instance_id, effect_index=1) # Index 1 is TAP_ABILITY
        assert success is True
        assert act_toy_inst.is_tapped is True
        mock_effect_engine.resolve_effect.assert_called_once()

    def test_activate_tap_ability_when_already_tapped_fails(self, action_resolver: ActionResolver, game_state_for_actions: GameState, card_defs_for_resolver: Dict[str, Card]):
        gs = game_state_for_actions
        player = gs.get_active_player_state()
        assert player is not None

        act_toy_def = card_defs_for_resolver["activatable_toy"]
        act_toy_inst = CardInstance(definition=act_toy_def, owner_id=player.player_id, current_zone=Zone.IN_PLAY)
        act_toy_inst.is_tapped = True 
        gs.cards_in_play[act_toy_inst.instance_id] = act_toy_inst
        player.zones[Zone.IN_PLAY].append(act_toy_inst)
        
        success = action_resolver.activate_ability(act_toy_inst.instance_id, effect_index=1)
        assert success is False
        # Check log for specific message (optional, good for debugging)
        # assert "already tapped" in gs.game_log[-1]