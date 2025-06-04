# tests/ai/test_action_generator.py
# Unit tests for action_generator.py

import pytest
from typing import List, Dict, Any, Optional

# Game elements
from tuck_in_terrors_sim.game_elements.card import Card, Toy, Spell, Ritual, Effect, EffectAction, CardInstance
from tuck_in_terrors_sim.game_elements.objective import ObjectiveCard
from tuck_in_terrors_sim.game_elements.enums import CardType, EffectTriggerType, Zone, EffectActionType
from tuck_in_terrors_sim.game_logic.game_state import GameState, PlayerState
from tuck_in_terrors_sim.models.game_action_model import GameAction # GameAction from new location
from tuck_in_terrors_sim.ai.action_generator import ActionGenerator 
from tuck_in_terrors_sim.game_logic.game_setup import DEFAULT_PLAYER_ID 

@pytest.fixture
def empty_objective() -> ObjectiveCard:
    return ObjectiveCard(objective_id="OBJ_EMPTY_TEST", title="Empty Test Obj", difficulty="Test", nightfall_turn=10)

@pytest.fixture
def basic_card_definitions_for_action_gen() -> Dict[str, Card]: # Renamed to avoid clash if other test files import this
    dummy_action = EffectAction(action_type=EffectActionType.DRAW_CARDS, params={"count": 0})
    return {
        "T001_COST1": Toy(card_id="T001_COST1", name="Toy Cost 1", type=CardType.TOY, cost_mana=1),
        "T002_COST3": Toy(card_id="T002_COST3", name="Toy Cost 3", type=CardType.TOY, cost_mana=3),
        "S001_COST2": Spell(card_id="S001_COST2", name="Spell Cost 2", type=CardType.SPELL, cost_mana=2),
        "T003_ACTIVATABLE": Toy(
            card_id="T003_ACTIVATABLE", name="Activatable Toy", type=CardType.TOY, cost_mana=0,
            effects=[
                Effect(effect_id="E1_activate", trigger=EffectTriggerType.ACTIVATED_ABILITY, actions=[dummy_action], description="Test Ability 1"),
                Effect(effect_id="E2_tap", trigger=EffectTriggerType.TAP_ABILITY, actions=[dummy_action], description="Test Tap Ability")
            ]
        ),
        "T004_ONCE_PER_TURN": Toy(
            card_id="T004_ONCE_PER_TURN", name="OncePerTurn Toy", type=CardType.TOY, cost_mana=0,
            effects=[
                Effect(effect_id="E3_opt", trigger=EffectTriggerType.ACTIVATED_ABILITY, actions=[dummy_action], description="OPT Ability")
            ]
        )
    }

@pytest.fixture
def initial_game_state_for_action_gen(empty_objective: ObjectiveCard, basic_card_definitions_for_action_gen: Dict[str, Card]) -> GameState:
    gs = GameState(loaded_objective=empty_objective, all_card_definitions=basic_card_definitions_for_action_gen)
    player = PlayerState(player_id=DEFAULT_PLAYER_ID, initial_deck=[]) 
    gs.player_states[DEFAULT_PLAYER_ID] = player
    gs.active_player_id = DEFAULT_PLAYER_ID
    gs.current_turn = 1
    return gs

@pytest.fixture
def action_generator_instance() -> ActionGenerator: # Renamed to avoid clash
    return ActionGenerator()

def find_action(actions: List[GameAction], action_type_str: str, params_subset: Optional[Dict[str, Any]] = None) -> Optional[GameAction]:
    for action in actions:
        if action.type == action_type_str:
            if params_subset:
                match = True
                for key, value in params_subset.items():
                    if action.params.get(key) != value:
                        match = False
                        break
                if match:
                    return action
            else:
                return action
    return None

class TestActionGenerator:

    def test_always_has_pass_action(self, action_generator_instance: ActionGenerator, initial_game_state_for_action_gen: GameState):
        actions = action_generator_instance.get_valid_actions(initial_game_state_for_action_gen)
        pass_action = find_action(actions, 'PASS_TURN')
        assert pass_action is not None
        assert "Pass turn" in pass_action.description

    def test_play_card_actions_sufficient_mana(self, action_generator_instance: ActionGenerator, initial_game_state_for_action_gen: GameState, basic_card_definitions_for_action_gen: Dict[str, Card]):
        gs = initial_game_state_for_action_gen
        player = gs.get_active_player_state()
        assert player is not None

        toy1_def = basic_card_definitions_for_action_gen["T001_COST1"]
        spell1_def = basic_card_definitions_for_action_gen["S001_COST2"]
        
        toy1_inst = CardInstance(definition=toy1_def, owner_id=player.player_id, current_zone=Zone.HAND)
        spell1_inst = CardInstance(definition=spell1_def, owner_id=player.player_id, current_zone=Zone.HAND)
        player.zones[Zone.HAND].extend([toy1_inst, spell1_inst])
        player.mana = 3

        actions = action_generator_instance.get_valid_actions(gs)
        
        play_toy1_action = find_action(actions, 'PLAY_CARD', {'card_id': toy1_inst.instance_id, 'is_free_toy_play': False})
        assert play_toy1_action is not None

        play_spell1_action = find_action(actions, 'PLAY_CARD', {'card_id': spell1_inst.instance_id, 'is_free_toy_play': False})
        assert play_spell1_action is not None

    def test_play_card_actions_insufficient_mana(self, action_generator_instance: ActionGenerator, initial_game_state_for_action_gen: GameState, basic_card_definitions_for_action_gen: Dict[str, Card]):
        gs = initial_game_state_for_action_gen
        player = gs.get_active_player_state()
        assert player is not None

        toy_cost3_def = basic_card_definitions_for_action_gen["T002_COST3"]
        toy_cost3_inst = CardInstance(definition=toy_cost3_def, owner_id=player.player_id, current_zone=Zone.HAND)
        player.zones[Zone.HAND].append(toy_cost3_inst)
        player.mana = 1 

        actions = action_generator_instance.get_valid_actions(gs)
        play_toy_cost3_action = find_action(actions, 'PLAY_CARD', {'card_id': toy_cost3_inst.instance_id, 'is_free_toy_play': False})
        assert play_toy_cost3_action is None

    def test_free_toy_play_action_available(self, action_generator_instance: ActionGenerator, initial_game_state_for_action_gen: GameState, basic_card_definitions_for_action_gen: Dict[str, Card]):
        gs = initial_game_state_for_action_gen
        player = gs.get_active_player_state()
        assert player is not None

        toy1_def = basic_card_definitions_for_action_gen["T001_COST1"]
        toy1_inst = CardInstance(definition=toy1_def, owner_id=player.player_id, current_zone=Zone.HAND)
        player.zones[Zone.HAND].append(toy1_inst)
        player.mana = 0 
        player.has_played_free_toy_this_turn = False

        actions = action_generator_instance.get_valid_actions(gs)

        free_play_toy1_action = find_action(actions, 'PLAY_CARD', {'card_id': toy1_inst.instance_id, 'is_free_toy_play': True})
        assert free_play_toy1_action is not None
        
        paid_play_toy1_action = find_action(actions, 'PLAY_CARD', {'card_id': toy1_inst.instance_id, 'is_free_toy_play': False})
        assert paid_play_toy1_action is None 

    def test_activate_ability_actions(self, action_generator_instance: ActionGenerator, initial_game_state_for_action_gen: GameState, basic_card_definitions_for_action_gen: Dict[str, Card]):
        gs = initial_game_state_for_action_gen
        player = gs.get_active_player_state()
        assert player is not None

        activatable_toy_def = basic_card_definitions_for_action_gen["T003_ACTIVATABLE"]
        activatable_toy_instance = CardInstance(definition=activatable_toy_def, owner_id=player.player_id, current_zone=Zone.IN_PLAY)
        gs.cards_in_play[activatable_toy_instance.instance_id] = activatable_toy_instance
        player.zones[Zone.IN_PLAY].append(activatable_toy_instance)

        actions = action_generator_instance.get_valid_actions(gs)

        activate_ab1_action = find_action(actions, 'ACTIVATE_ABILITY', {
            'card_instance_id': activatable_toy_instance.instance_id,
            'effect_index': 0 
        })
        assert activate_ab1_action is not None
        assert "Test Ability 1" in activate_ab1_action.description

        activate_tap_ab_action = find_action(actions, 'ACTIVATE_ABILITY', {
            'card_instance_id': activatable_toy_instance.instance_id,
            'effect_index': 1
        })
        assert activate_tap_ab_action is not None
        assert "Test Tap Ability" in activate_tap_ab_action.description

    def test_activate_tap_ability_unavailable_if_tapped(self, action_generator_instance: ActionGenerator, initial_game_state_for_action_gen: GameState, basic_card_definitions_for_action_gen: Dict[str, Card]):
        gs = initial_game_state_for_action_gen
        player = gs.get_active_player_state()
        assert player is not None

        activatable_toy_def = basic_card_definitions_for_action_gen["T003_ACTIVATABLE"]
        activatable_toy_instance = CardInstance(definition=activatable_toy_def, owner_id=player.player_id, current_zone=Zone.IN_PLAY)
        activatable_toy_instance.tap() 
        gs.cards_in_play[activatable_toy_instance.instance_id] = activatable_toy_instance
        player.zones[Zone.IN_PLAY].append(activatable_toy_instance)
        
        actions = action_generator_instance.get_valid_actions(gs)
        
        activate_tap_ab_action = find_action(actions, 'ACTIVATE_ABILITY', {
            'card_instance_id': activatable_toy_instance.instance_id,
            'effect_index': 1 
        })
        assert activate_tap_ab_action is None

    def test_activate_once_per_turn_ability(self, action_generator_instance: ActionGenerator, initial_game_state_for_action_gen: GameState, basic_card_definitions_for_action_gen: Dict[str, Card]):
        gs = initial_game_state_for_action_gen
        player = gs.get_active_player_state()
        assert player is not None

        opt_toy_def = basic_card_definitions_for_action_gen["T004_ONCE_PER_TURN"]
        opt_toy_instance = CardInstance(definition=opt_toy_def, owner_id=player.player_id, current_zone=Zone.IN_PLAY)
        gs.cards_in_play[opt_toy_instance.instance_id] = opt_toy_instance
        player.zones[Zone.IN_PLAY].append(opt_toy_instance)
        
        # Ensure the CardInstance has the effects_applied_this_turn set
        # This was missing in the CardInstance definition I provided earlier.
        # Assuming CardInstance now has: self.effects_applied_this_turn: Set[str] = set()
        if not hasattr(opt_toy_instance, 'effects_applied_this_turn'):
             opt_toy_instance.effects_applied_this_turn = set()


        actions = action_generator_instance.get_valid_actions(gs)
        activate_opt_action = find_action(actions, 'ACTIVATE_ABILITY', {
            'card_instance_id': opt_toy_instance.instance_id,
            'effect_index': 0
        })
        assert activate_opt_action is not None

        # Simulate using the ability by adding its effect_id to the instance's used set
        if opt_toy_instance.definition.effects:
             effect_id_to_mark = opt_toy_instance.definition.effects[0].effect_id
             opt_toy_instance.effects_applied_this_turn.add(effect_id_to_mark) # Corrected attribute name

        actions_after_use = action_generator_instance.get_valid_actions(gs)
        activate_opt_action_after_use = find_action(actions_after_use, 'ACTIVATE_ABILITY', {
            'card_instance_id': opt_toy_instance.instance_id,
            'effect_index': 0
        })
        assert activate_opt_action_after_use is None