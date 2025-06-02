# tests/ai/test_action_generator.py
# Unit tests for action_generator.py

import pytest
from typing import List, Dict, Any

# Game elements
from tuck_in_terrors_sim.game_elements.card import Card, Toy, Spell, EffectLogic
from tuck_in_terrors_sim.game_elements.objective import ObjectiveCard
from tuck_in_terrors_sim.game_elements.enums import CardType, EffectTriggerType

# Game logic
from tuck_in_terrors_sim.game_logic.game_state import GameState, CardInPlay
from tuck_in_terrors_sim.ai.action_generator import ActionGenerator

# Mock data / fixtures
@pytest.fixture
def empty_objective() -> ObjectiveCard:
    return ObjectiveCard(objective_id="OBJ_EMPTY_TEST", title="Empty Test Obj", difficulty="Test", nightfall_turn=10)

@pytest.fixture
def basic_card_definitions() -> Dict[str, Card]:
    return {
        "T001_COST1": Toy(card_id="T001_COST1", name="Toy Cost 1", card_type=CardType.TOY, cost=1, quantity_in_deck=1),
        "T002_COST3": Toy(card_id="T002_COST3", name="Toy Cost 3", card_type=CardType.TOY, cost=3, quantity_in_deck=1),
        "S001_COST2": Spell(card_id="S001_COST2", name="Spell Cost 2", card_type=CardType.SPELL, cost=2, quantity_in_deck=1),
        "T003_ACTIVATABLE": Toy(
            card_id="T003_ACTIVATABLE", name="Activatable Toy", card_type=CardType.TOY, cost=0, quantity_in_deck=1,
            effect_logic_list=[
                EffectLogic(trigger=EffectTriggerType.ACTIVATED_ABILITY.name, actions=[], description="Test Ability 1"),
                EffectLogic(trigger=EffectTriggerType.TAP_ABILITY.name, actions=[], description="Test Tap Ability")
            ]
        ),
        "T004_ONCE_PER_TURN": Toy(
            card_id="T004_ONCE_PER_TURN", name="OncePerTurn Toy", card_type=CardType.TOY, cost=0, quantity_in_deck=1,
            effect_logic_list=[
                EffectLogic(trigger=EffectTriggerType.ACTIVATED_ABILITY.name, actions=[], description="OPT Ability", is_once_per_turn=True)
            ]
        )
    }

@pytest.fixture
def initial_game_state(empty_objective: ObjectiveCard, basic_card_definitions: Dict[str, Card]) -> GameState:
    gs = GameState(loaded_objective=empty_objective, all_card_definitions=basic_card_definitions)
    # gs.current_turn = 1 # GameSetup usually handles this, but for isolated tests, set as needed
    # gs.current_phase = TurnPhase.MAIN_PHASE # Assume it's main phase for action generation
    return gs

@pytest.fixture
def action_generator() -> ActionGenerator:
    return ActionGenerator()

# Helper to find specific actions in the list
def find_action(actions: List[Dict[str, Any]], action_type: str, params_subset: Dict[str, Any] = None) -> Dict[str, Any] | None:
    for action in actions:
        if action.get('type') == action_type:
            if params_subset:
                match = True
                for key, value in params_subset.items():
                    if action.get('params', {}).get(key) != value:
                        match = False
                        break
                if match:
                    return action
            else:
                return action
    return None

class TestActionGenerator:

    def test_always_has_pass_action(self, action_generator: ActionGenerator, initial_game_state: GameState):
        actions = action_generator.get_valid_actions(initial_game_state)
        pass_action = find_action(actions, 'PASS_TURN')
        assert pass_action is not None
        assert pass_action['description'] == "Pass turn / End main phase actions."

    def test_play_card_actions_sufficient_mana(self, action_generator: ActionGenerator, initial_game_state: GameState, basic_card_definitions: Dict[str, Card]):
        gs = initial_game_state
        toy1 = basic_card_definitions["T001_COST1"]
        spell1 = basic_card_definitions["S001_COST2"]
        gs.hand = [toy1, spell1]
        gs.mana_pool = 3

        actions = action_generator.get_valid_actions(gs)

        play_toy1_action = find_action(actions, 'PLAY_CARD', {'card_definition': toy1, 'is_free_toy_play': False})
        assert play_toy1_action is not None
        assert play_toy1_action['params']['card_definition'].cost == 1

        play_spell1_action = find_action(actions, 'PLAY_CARD', {'card_definition': spell1, 'is_free_toy_play': False})
        assert play_spell1_action is not None
        assert play_spell1_action['params']['card_definition'].cost == 2

    def test_play_card_actions_insufficient_mana(self, action_generator: ActionGenerator, initial_game_state: GameState, basic_card_definitions: Dict[str, Card]):
        gs = initial_game_state
        toy_cost3 = basic_card_definitions["T002_COST3"]
        gs.hand = [toy_cost3]
        gs.mana_pool = 1 # Not enough for toy_cost3

        actions = action_generator.get_valid_actions(gs)
        play_toy_cost3_action = find_action(actions, 'PLAY_CARD', {'card_definition': toy_cost3, 'is_free_toy_play': False})
        assert play_toy_cost3_action is None # Should not be able to play

    def test_free_toy_play_action_available(self, action_generator: ActionGenerator, initial_game_state: GameState, basic_card_definitions: Dict[str, Card]):
        gs = initial_game_state
        toy1 = basic_card_definitions["T001_COST1"] # Cost 1 Toy
        gs.hand = [toy1]
        gs.mana_pool = 0 # Not enough for paid play
        gs.free_toy_played_this_turn = False

        actions = action_generator.get_valid_actions(gs)

        free_play_toy1_action = find_action(actions, 'PLAY_CARD', {'card_definition': toy1, 'is_free_toy_play': True})
        assert free_play_toy1_action is not None
        
        paid_play_toy1_action = find_action(actions, 'PLAY_CARD', {'card_definition': toy1, 'is_free_toy_play': False})
        assert paid_play_toy1_action is None # Cannot afford paid play

    def test_free_toy_play_action_unavailable_if_already_used(self, action_generator: ActionGenerator, initial_game_state: GameState, basic_card_definitions: Dict[str, Card]):
        gs = initial_game_state
        toy1 = basic_card_definitions["T001_COST1"]
        gs.hand = [toy1]
        gs.mana_pool = 5 # Can afford
        gs.free_toy_played_this_turn = True # Free toy slot used

        actions = action_generator.get_valid_actions(gs)

        free_play_toy1_action = find_action(actions, 'PLAY_CARD', {'card_definition': toy1, 'is_free_toy_play': True})
        assert free_play_toy1_action is None # Free slot used

        paid_play_toy1_action = find_action(actions, 'PLAY_CARD', {'card_definition': toy1, 'is_free_toy_play': False})
        assert paid_play_toy1_action is not None # Can still play normally

    def test_free_toy_play_action_not_for_spells(self, action_generator: ActionGenerator, initial_game_state: GameState, basic_card_definitions: Dict[str, Card]):
        gs = initial_game_state
        spell1 = basic_card_definitions["S001_COST2"]
        gs.hand = [spell1]
        gs.free_toy_played_this_turn = False

        actions = action_generator.get_valid_actions(gs)
        free_play_spell_action = find_action(actions, 'PLAY_CARD', {'card_definition': spell1, 'is_free_toy_play': True})
        assert free_play_spell_action is None

    def test_activate_ability_actions(self, action_generator: ActionGenerator, initial_game_state: GameState, basic_card_definitions: Dict[str, Card]):
        gs = initial_game_state
        activatable_toy_def = basic_card_definitions["T003_ACTIVATABLE"]
        activatable_toy_instance = CardInPlay(activatable_toy_def)
        gs.cards_in_play[activatable_toy_instance.instance_id] = activatable_toy_instance

        actions = action_generator.get_valid_actions(gs)

        # Check for first activatable ability (index 0)
        activate_ab1_action = find_action(actions, 'ACTIVATE_ABILITY', {
            'card_instance_id': activatable_toy_instance.instance_id,
            'effect_logic_index': 0
        })
        assert activate_ab1_action is not None
        assert "Test Ability 1" in activate_ab1_action['description']

        # Check for tap ability (index 1)
        activate_tap_ab_action = find_action(actions, 'ACTIVATE_ABILITY', {
            'card_instance_id': activatable_toy_instance.instance_id,
            'effect_logic_index': 1
        })
        assert activate_tap_ab_action is not None
        assert "Test Tap Ability" in activate_tap_ab_action['description']

    def test_activate_tap_ability_unavailable_if_tapped(self, action_generator: ActionGenerator, initial_game_state: GameState, basic_card_definitions: Dict[str, Card]):
        gs = initial_game_state
        activatable_toy_def = basic_card_definitions["T003_ACTIVATABLE"]
        activatable_toy_instance = CardInPlay(activatable_toy_def)
        activatable_toy_instance.tap() # Card is now tapped
        gs.cards_in_play[activatable_toy_instance.instance_id] = activatable_toy_instance

        actions = action_generator.get_valid_actions(gs)
        
        activate_tap_ab_action = find_action(actions, 'ACTIVATE_ABILITY', {
            'card_instance_id': activatable_toy_instance.instance_id,
            'effect_logic_index': 1 # Index of the TAP_ABILITY
        })
        assert activate_tap_ab_action is None # Should not be available

    def test_activate_once_per_turn_ability(self, action_generator: ActionGenerator, initial_game_state: GameState, basic_card_definitions: Dict[str, Card]):
        gs = initial_game_state
        opt_toy_def = basic_card_definitions["T004_ONCE_PER_TURN"]
        opt_toy_instance = CardInPlay(opt_toy_def)
        gs.cards_in_play[opt_toy_instance.instance_id] = opt_toy_instance

        # First time, ability should be available
        actions = action_generator.get_valid_actions(gs)
        activate_opt_action = find_action(actions, 'ACTIVATE_ABILITY', {
            'card_instance_id': opt_toy_instance.instance_id,
            'effect_logic_index': 0
        })
        assert activate_opt_action is not None

        # Mark as used this turn
        opt_toy_instance.effects_active_this_turn["effect_0"] = True
        actions_after_use = action_generator.get_valid_actions(gs)
        activate_opt_action_after_use = find_action(actions_after_use, 'ACTIVATE_ABILITY', {
            'card_instance_id': opt_toy_instance.instance_id,
            'effect_logic_index': 0
        })
        assert activate_opt_action_after_use is None # Should not be available

    # TODO: Add more tests:
    # - Abilities with costs (mana, sacrifice etc.) - once ActionGenerator checks these
    # - Actions requiring targets - once ActionGenerator identifies need for targets
    # - Scenarios with no cards in hand / no cards in play
    # - Interactions with game phase (though ActionGenerator is mostly for main phase actions)