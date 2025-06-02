# src/tuck_in_terrors_sim/ai/action_generator.py
# Generates list of valid actions for AI in current GameState

from typing import List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from tuck_in_terrors_sim.game_logic.game_state import GameState
    from tuck_in_terrors_sim.game_elements.card import Card, EffectLogic
    from tuck_in_terrors_sim.game_elements.enums import CardType, EffectTriggerType
else: # Ensure EffectTriggerType and CardType are available at runtime if not just for type checking
    from tuck_in_terrors_sim.game_elements.enums import CardType, EffectTriggerType


class ActionGenerator:
    def __init__(self):
        # The ActionGenerator might not need to store state itself,
        # but it could be initialized with references to game data if needed for complex checks.
        pass

    def get_valid_actions(self, game_state: 'GameState') -> List[Dict[str, Any]]:
        """
        Analyzes the GameState and returns a list of all legal actions the AI can take.
        """
        valid_actions: List[Dict[str, Any]] = []

        # 1. Check for playing cards from hand
        for card_in_hand in game_state.hand:
            # Check standard play (paid)
            if game_state.mana_pool >= card_in_hand.cost:
                play_action = {
                    'type': 'PLAY_CARD',
                    'params': {
                        'card_definition': card_in_hand,
                        'is_free_toy_play': False,
                        'targets': None # Placeholder for targeting
                    },
                    'description': f"Play '{card_in_hand.name}' for {card_in_hand.cost} mana."
                }
                valid_actions.append(play_action)

            # Check free Toy play
            # CardType.TOY needs to be accessible here
            if card_in_hand.card_type == CardType.TOY and not game_state.free_toy_played_this_turn:
                # Offer free play if it's distinct (e.g. costs > 0, or to use the free slot for a 0-cost toy)
                # This avoids exact duplicate actions if a toy is 0-cost and can be played normally or freely.
                # A simple heuristic: if it costs > 0, free play is a distinct option.
                # If it costs 0, it's only a distinct option if we want to explicitly use the "free toy slot".
                # For now, let's offer it if it's a toy and slot is available, AI can choose.
                # A more refined ActionGenerator might only offer free play if it provides a mana advantage
                # or if normal play is not possible.
                
                # Check if this exact free play action would be functionally identical to an already added paid action (0-cost toy)
                # For simplicity, we'll add it if the "free toy slot" is available and it's a toy.
                # The AI can then decide if it wants to use the free slot for a 0-cost toy.
                free_play_action = {
                    'type': 'PLAY_CARD',
                    'params': {
                        'card_definition': card_in_hand,
                        'is_free_toy_play': True,
                        'targets': None # Placeholder
                    },
                    'description': f"Play '{card_in_hand.name}' as free Toy."
                }
                # Avoid adding the *exact same action object representation* if a 0-cost toy could be played normally.
                # However, "is_free_toy_play: True" makes it distinct.
                valid_actions.append(free_play_action)


        # 2. Check for activating abilities on cards in play
        for instance_id, card_instance in game_state.cards_in_play.items():
            for i, effect_logic in enumerate(card_instance.card_definition.effect_logic_list):
                is_activatable = False
                try:
                    # EffectTriggerType needs to be accessible here
                    trigger_type_enum = EffectTriggerType[effect_logic.trigger]
                    if trigger_type_enum == EffectTriggerType.ACTIVATED_ABILITY or \
                       trigger_type_enum == EffectTriggerType.TAP_ABILITY:
                        is_activatable = True
                except KeyError:
                    # Not a known trigger type, or not an activatable one
                    pass

                if is_activatable:
                    # Check if already used if once-per-turn
                    effect_signature = f"effect_{i}"
                    if effect_logic.is_once_per_turn and card_instance.effects_active_this_turn.get(effect_signature):
                        continue # Already used

                    # Check if tapped for TAP_ABILITY
                    if EffectTriggerType[effect_logic.trigger] == EffectTriggerType.TAP_ABILITY and card_instance.is_tapped:
                        continue # Already tapped

                    # TODO: Check activation costs (mana, sacrifice etc.) from effect_logic.activation_costs
                    # For now, assuming no additional costs beyond potential tap
                    can_pay_costs = True # Placeholder

                    if can_pay_costs:
                        # Corrected way to handle the description string
                        ability_desc_text = effect_logic.description if effect_logic.description else f"ability {i}"
                        
                        activate_action = {
                            'type': 'ACTIVATE_ABILITY',
                            'params': {
                                'card_instance_id': instance_id,
                                'effect_logic_index': i,
                                'targets': None # Placeholder
                            },
                            'description': f"Activate '{ability_desc_text}' on '{card_instance.card_definition.name}'."
                        }
                        valid_actions.append(activate_action)

        # 3. Always allow passing the turn (or ending main phase actions)
        pass_action = {
            'type': 'PASS_TURN',
            'params': {},
            'description': "Pass turn / End main phase actions."
        }
        valid_actions.append(pass_action)

        return valid_actions

if __name__ == '__main__':
    print("ActionGenerator module: Generates a list of valid actions for an AI player.")
    # To test this, you'd need a GameState instance populated with some data.
    # Example:
    # from tuck_in_terrors_sim.game_logic.game_state import GameState
    # from tuck_in_terrors_sim.game_elements.card import Card, Toy, EffectLogic # Added EffectLogic
    # from tuck_in_terrors_sim.game_elements.objective import ObjectiveCard
    # from tuck_in_terrors_sim.game_elements.enums import CardType, EffectTriggerType
    #
    # mock_objective = ObjectiveCard(objective_id="test_obj", title="Test", difficulty="Easy", nightfall_turn=5)
    # mock_cards_db = {"T001_COST1": Toy(card_id="T001_COST1", name="Test Toy", cost=1, card_type=CardType.TOY)}
    # gs = GameState(loaded_objective=mock_objective, all_card_definitions=mock_cards_db)
    # gs.hand.append(mock_cards_db["T001_COST1"])
    # gs.mana_pool = 1
    #
    # generator = ActionGenerator()
    # actions = generator.get_valid_actions(gs)
    # print("Valid Actions:")
    # for action in actions:
    #     print(action)