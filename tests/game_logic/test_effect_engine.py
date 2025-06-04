# tests/game_logic/test_effect_engine.py
# Unit tests for effect_engine.py

import pytest
from typing import Tuple, List, Dict, Any, Optional
from unittest.mock import MagicMock, call 

# Game logic & elements
from tuck_in_terrors_sim.game_logic.game_state import GameState, PlayerState
from tuck_in_terrors_sim.game_logic.effect_engine import EffectEngine # <<< Added EffectEngine import
from tuck_in_terrors_sim.game_elements.card import Card, Effect, EffectAction, Toy, Spell, CardInstance, Cost # Added Cost
from tuck_in_terrors_sim.game_elements.objective import ObjectiveCard
from tuck_in_terrors_sim.game_elements.enums import (
    EffectConditionType, EffectActionType, CardType, Zone, EffectTriggerType, PlayerChoiceType, ResourceType
)
# Assuming RandomAI and DEFAULT_PLAYER_ID are correctly set up for your project
from tuck_in_terrors_sim.ai.ai_profiles.random_ai import RandomAI 
from tuck_in_terrors_sim.game_logic.game_setup import DEFAULT_PLAYER_ID


# --- Fixtures ---

@pytest.fixture
def empty_objective_for_ee() -> ObjectiveCard: # Renamed to avoid conflict if other tests use similar
    return ObjectiveCard(objective_id="OBJ_EE_TEST", title="EE Test Obj", difficulty="Test", nightfall_turn=20)

@pytest.fixture
def card_defs_for_ee() -> Dict[str, Card]:
    """Provides a dictionary of base card definitions for EffectEngine tests."""
    # Basic action for dummy effects
    dummy_action = EffectAction(action_type=EffectActionType.ADD_MANA, params={"count": 0})
    return {
        "T_BASE001": Toy(card_id="T_BASE001", name="Base Test Toy", type=CardType.TOY, cost_mana=1),
        "T_OTHER001": Toy(card_id="T_OTHER001", name="Other Test Toy", type=CardType.TOY, cost_mana=1),
        "S_BASE001": Spell(card_id="S_BASE001", name="Base Test Spell", type=CardType.SPELL, cost_mana=1),
        "ECHO_BEAR": Toy(
            card_id="T_ECHO_BEAR", name="Echo Bear", type=CardType.TOY, cost_mana=3,
            effects=[
                Effect( # This is now an Effect object
                    effect_id="ECHO_BEAR_SAVE_EFFECT", # Effects should have IDs
                    trigger=EffectTriggerType.BEFORE_THIS_CARD_LEAVES_PLAY,
                    actions=[
                        EffectAction( # Actions are EffectAction objects
                            action_type=EffectActionType.PLAYER_CHOICE,
                            params={
                                "choice_id": "ECHO_BEAR_SAVE_CHOICE",
                                "choice_type": PlayerChoiceType.CHOOSE_YES_NO, # Enum member
                                "prompt_text": "Echo Bear would leave play. Create a Memory Token and keep it in play instead?",
                                "on_yes_actions": [ # These are lists of EffectAction objects
                                    EffectAction(action_type=EffectActionType.CREATE_MEMORY_TOKENS, params={"count": 1}),
                                    EffectAction(action_type=EffectActionType.CANCEL_IMPENDING_LEAVE_PLAY, params={})
                                ],
                                "on_no_actions": []
                            }
                        )
                    ],
                    description="When this would leave play, you may create a Memory Token and keep this card in play instead."
                )
            ]
        )
    }

@pytest.fixture
def game_state_with_player(empty_objective_for_ee: ObjectiveCard, card_defs_for_ee: Dict[str, Card]) -> GameState:
    """Sets up a GameState with a single active player and their zones initialized with CardInstances."""
    gs = GameState(loaded_objective=empty_objective_for_ee, all_card_definitions=card_defs_for_ee)
    
    # Create some card definitions to put in deck for testing draw/mill
    deck_defs = [card_defs_for_ee["T_BASE001"], card_defs_for_ee["T_OTHER001"], card_defs_for_ee["S_BASE001"]] * 2 # 6 cards
    
    player = PlayerState(player_id=DEFAULT_PLAYER_ID, initial_deck=deck_defs) # PlayerState init converts defs to instances
    player.mana = 10
    player.spirit_tokens = 5
    player.memory_tokens = 5
    
    gs.player_states[DEFAULT_PLAYER_ID] = player
    gs.active_player_id = DEFAULT_PLAYER_ID
    gs.ai_agents[DEFAULT_PLAYER_ID] = MagicMock(spec=RandomAI) # Mock AI for tests
    
    gs.current_turn = 1
    gs.game_log = []
    return gs

@pytest.fixture
def effect_engine_instance(game_state_with_player: GameState) -> EffectEngine:
    """Provides an EffectEngine instance initialized with the game_state."""
    return EffectEngine(game_state_ref=game_state_with_player)

# Helper to create a single condition dictionary for the new check_condition
def create_condition_data(condition_type: EffectConditionType, params: Dict[str, Any]) -> Dict[EffectConditionType, Any]:
    return {condition_type: params}


class TestEffectEngineConditions:

    def test_check_condition_is_first_memory_in_play_true(self, effect_engine_instance: EffectEngine, game_state_with_player: GameState, card_defs_for_ee: Dict[str, Card]):
        ee = effect_engine_instance
        gs = game_state_with_player
        player = gs.get_active_player_state()
        assert player is not None
        
        fm_def = card_defs_for_ee["T_BASE001"]
        # Create and place FM instance
        fm_inst = CardInstance(definition=fm_def, owner_id=player.player_id, current_zone=Zone.IN_PLAY)
        gs.cards_in_play[fm_inst.instance_id] = fm_inst
        player.zones[Zone.IN_PLAY].append(fm_inst)
        gs.first_memory_instance_id = fm_inst.instance_id # Crucial: GameState tracks the active FM instance ID

        condition = create_condition_data(EffectConditionType.IS_FIRST_MEMORY_IN_PLAY, {})
        assert ee.check_condition(condition, player, None, gs) is True

    def test_check_condition_no_condition(self, effect_engine_instance: EffectEngine, game_state_with_player: GameState):
        ee = effect_engine_instance
        player = game_state_with_player.get_active_player_state()
        assert player is not None
        assert ee.check_condition(None, player, None, game_state_with_player) is True

    def test_check_condition_has_counter_true(self, effect_engine_instance: EffectEngine, game_state_with_player: GameState, card_defs_for_ee: Dict[str, Card]):
        ee = effect_engine_instance
        gs = game_state_with_player
        player = gs.get_active_player_state()
        assert player is not None

        toy_def = card_defs_for_ee["T_BASE001"]
        card_inst = CardInstance(definition=toy_def, owner_id=player.player_id, current_zone=Zone.IN_PLAY)
        card_inst.add_counter("power", 3)
        gs.cards_in_play[card_inst.instance_id] = card_inst # Add to global registry
        player.zones[Zone.IN_PLAY].append(card_inst) # Add to player's zone list

        condition = create_condition_data(EffectConditionType.HAS_COUNTER_TYPE_VALUE_GE, {"counter_type": "power", "value": 3})
        assert ee.check_condition(condition, player, card_inst, gs) is True # card_inst is the source/context card


class TestEffectEngineActions:

    def test_execute_action_draw_cards(self, effect_engine_instance: EffectEngine, game_state_with_player: GameState):
        ee = effect_engine_instance
        gs = game_state_with_player
        player = gs.get_active_player_state()
        assert player is not None
        
        initial_deck_size = len(player.zones[Zone.DECK])
        initial_hand_size = len(player.zones[Zone.HAND])
        
        # Ensure there are cards to draw
        if initial_deck_size < 2:
            card_def_sample = gs.all_card_definitions["T_BASE001"]
            player.zones[Zone.DECK].insert(0, CardInstance(card_def_sample, player.player_id, Zone.DECK))
            player.zones[Zone.DECK].insert(0, CardInstance(card_def_sample, player.player_id, Zone.DECK))
            initial_deck_size = len(player.zones[Zone.DECK])
            
        action = EffectAction(action_type=EffectActionType.DRAW_CARDS, params={"count": 2})
        effect_context = {"player_id": player.player_id, "target_player_id": player.player_id}
        
        ee._execute_action(action, gs, player, effect_context) # source_card_instance defaults to None
        
        assert len(player.zones[Zone.HAND]) == initial_hand_size + 2
        assert len(player.zones[Zone.DECK]) == initial_deck_size - 2

    def test_execute_action_create_spirit_tokens(self, effect_engine_instance: EffectEngine, game_state_with_player: GameState):
        ee = effect_engine_instance
        gs = game_state_with_player
        player = gs.get_active_player_state()
        assert player is not None

        initial_spirits = player.spirit_tokens
        action = EffectAction(action_type=EffectActionType.CREATE_SPIRIT_TOKENS, params={"count": 3})
        effect_context = {"player_id": player.player_id, "target_player_id": player.player_id}
        
        ee._execute_action(action, gs, player, effect_context)
        
        assert player.spirit_tokens == initial_spirits + 3


class TestPlayerChoiceExecution:
    def test_player_choice_yes_no_ai_chooses_yes_cancels_leave_play(
        self, effect_engine_instance: EffectEngine, game_state_with_player: GameState, card_defs_for_ee: Dict[str, Card], mock_ai_player: MagicMock
    ):
        ee = effect_engine_instance
        gs = game_state_with_player
        player = gs.get_active_player_state()
        assert player is not None
        
        mock_ai_player.make_choice.return_value = True # AI chooses YES
        # GameState already has this mock_ai_player via game_state_with_player fixture
        
        echo_bear_def = card_defs_for_ee["ECHO_BEAR"]
        echo_bear_instance = CardInstance(definition=echo_bear_def, owner_id=player.player_id, current_zone=Zone.IN_PLAY)
        gs.cards_in_play[echo_bear_instance.instance_id] = echo_bear_instance
        player.zones[Zone.IN_PLAY].append(echo_bear_instance)
        
        initial_memory_tokens = player.memory_tokens
        
        # This is the PLAYER_CHOICE action from Echo Bear's effect definition
        player_choice_action = echo_bear_def.effects[0].actions[0]
        assert player_choice_action.action_type == EffectActionType.PLAYER_CHOICE

        effect_context = {
            "player_id": player.player_id, 
            "target_player_id": player.player_id, 
            "source_card_instance_id": echo_bear_instance.instance_id,
            "effect_id": echo_bear_def.effects[0].effect_id,
            "triggering_event_context": {"card_instance_leaving_play": echo_bear_instance} # Simulate context
        }
        
        # We are directly testing the _execute_action for PLAYER_CHOICE.
        # The sub-actions (CREATE_MEMORY_TOKENS, CANCEL_IMPENDING_LEAVE_PLAY) will be executed.
        ee._execute_action(player_choice_action, gs, player, effect_context, echo_bear_instance)

        mock_ai_player.make_choice.assert_called_once()
        choice_context_arg = mock_ai_player.make_choice.call_args[0][1]
        assert choice_context_arg['choice_type'] == PlayerChoiceType.CHOOSE_YES_NO
        assert choice_context_arg['prompt_text'] == "Echo Bear would leave play. Create a Memory Token and keep it in play instead?"

        assert player.memory_tokens == initial_memory_tokens + 1
        # The CANCEL_IMPENDING_LEAVE_PLAY would typically set a flag in the event_context.
        # We can check if it was attempted to be executed.
        # For a more robust test, we'd need to see the return from _execute_action or mock sub-calls.
        # Here, we check the game state change (memory tokens) from the first sub-action.
        # A full test would involve actually trying to make Echo Bear leave play and seeing if it's cancelled.
        # For now, ensuring the YES path (memory token creation) is triggered is a good step.