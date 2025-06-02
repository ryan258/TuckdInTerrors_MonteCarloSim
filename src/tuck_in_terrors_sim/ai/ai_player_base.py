# src/tuck_in_terrors_sim/ai/ai_player_base.py
# Abstract base class for different AI strategies

from abc import ABC, abstractmethod
from typing import List, Any, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from tuck_in_terrors_sim.game_logic.game_state import GameState
    from tuck_in_terrors_sim.game_logic.action_resolver import ActionResolver
    from tuck_in_terrors_sim.ai.action_generator import ActionGenerator
    # We might define a more specific type for 'valid_actions' (e.g., a TypedDict or a custom Action class)
    # and for 'choice_context' and the return type of 'make_choice'.


class AIPlayerBase(ABC):
    """
    Abstract base class for all AI player implementations.
    Defines the interface that the game simulation will use to get decisions from an AI.
    """

    def __init__(self, player_name: str = "AI Player"):
        self.player_name = player_name
        # AI might need access to an ActionResolver to understand action outcomes,
        # or the ActionGenerator might provide sufficient pre-vetted actions.
        # For now, it's not directly passed here but in take_turn_actions.

    @abstractmethod
    def choose_action(self, game_state: 'GameState', valid_actions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Called by the AI's take_turn_actions method to select an action.

        Args:
            game_state: The current state of the game.
            valid_actions: A list of valid actions the AI can currently take.
                           Each action is expected to be a dictionary with at least a 'type' key
                           (e.g., 'PLAY_CARD', 'ACTIVATE_ABILITY', 'PASS_TURN')
                           and a 'params' key holding necessary details.

        Returns:
            The chosen action dictionary from the valid_actions list, or an action dictionary
            representing a 'PASS_TURN' action if no other action is chosen.
            Should return None if no actions are possible (though ActionGenerator should always provide PASS).
        """
        pass

    @abstractmethod
    def make_choice(self, game_state: 'GameState', choice_context: Dict[str, Any]) -> Any:
        """
        Called by the EffectEngine or other game logic modules when the AI needs to
        make a decision for a PLAYER_CHOICE effect or other game prompts.

        Args:
            game_state: The current state of the game.
            choice_context: A dictionary describing the choice to be made.
                              This will typically include:
                              - 'choice_id': A unique identifier for the type of choice.
                              - 'choice_type': An enum member from PlayerChoiceType (as string).
                              - 'prompt_text': A human-readable description of the choice.
                              - 'options': A list or dict of available options.
                              - Potentially other parameters specific to the choice type.
                              (e.g. for CHOOSE_CARD_FROM_HAND, options would be a list of Card objects)

        Returns:
            The AI's decision, formatted appropriately for the specific choice_type.
            For example, for a YES_NO choice, it might return True or False.
            For choosing a card, it might return the Card object or its ID.
        """
        pass

    def take_turn_actions(self, game_state: 'GameState', action_resolver: 'ActionResolver', action_generator: 'ActionGenerator') -> None:
        """
        Orchestrates the AI's turn by repeatedly getting valid actions and choosing one
        until no more actions are desired or possible.

        The TurnManager will call this method during the AI's main phase.

        Args:
            game_state: The current GameState.
            action_resolver: An instance of ActionResolver to execute chosen actions.
            action_generator: An instance of ActionGenerator to get valid actions.
        """
        game_state.add_log_entry(f"AI ({self.player_name}): Starting main phase actions.")
        # Max actions per turn is a safeguard against potential infinite loops with simple AIs or bugs.
        # A more sophisticated AI might have its own criteria for ending its turn.
        max_actions_per_turn = 20 # TODO: Make this configurable or part of game rules/objective?
        actions_taken_this_turn = 0

        while actions_taken_this_turn < max_actions_per_turn:
            if game_state.game_over:
                game_state.add_log_entry(f"AI ({self.player_name}): Game ended mid-turn. Halting actions.")
                break

            valid_actions = action_generator.get_valid_actions(game_state)

            if not valid_actions: # Should ideally always at least include a PASS_TURN action
                game_state.add_log_entry(f"AI ({self.player_name}): No valid actions returned by ActionGenerator. Passing turn.", level="WARNING")
                break

            chosen_action_data = self.choose_action(game_state, valid_actions)

            if chosen_action_data is None or chosen_action_data.get('type') == 'PASS_TURN':
                game_state.add_log_entry(f"AI ({self.player_name}): Chose to PASS_TURN or no action selected.")
                break # AI decides to end its main phase

            # Attempt to resolve the chosen action
            action_type = chosen_action_data.get('type')
            action_params = chosen_action_data.get('params', {})
            action_resolved_successfully = False

            game_state.add_log_entry(f"AI ({self.player_name}): Chose action -> Type: {action_type}, Params: {action_params}")

            if action_type == 'PLAY_CARD':
                card_def = action_params.get('card_definition')
                is_free = action_params.get('is_free_toy_play', False)
                targets = action_params.get('targets') # Optional
                if card_def:
                    action_resolved_successfully = action_resolver.play_card_from_hand(
                        card_to_play=card_def,
                        is_free_toy_play=is_free,
                        targets=targets
                    )
            elif action_type == 'ACTIVATE_ABILITY':
                instance_id = action_params.get('card_instance_id')
                effect_idx = action_params.get('effect_logic_index')
                targets = action_params.get('targets') # Optional
                if instance_id is not None and effect_idx is not None:
                    action_resolved_successfully = action_resolver.activate_ability(
                        card_in_play_instance_id=instance_id,
                        effect_logic_index=effect_idx,
                        targets=targets
                    )
            else:
                game_state.add_log_entry(f"AI ({self.player_name}): Unknown action type '{action_type}' chosen. Cannot resolve.", level="ERROR")
                break # Unknown action type, critical issue

            if not action_resolved_successfully:
                game_state.add_log_entry(f"AI ({self.player_name}): Chosen action {action_type} with params {action_params} FAILED to resolve. AI might be stuck or action was invalid.", level="WARNING")
                # Depending on AI sophistication, it might try another action or just end its turn.
                # For a basic AI, breaking here prevents potential loops if it keeps choosing the same failing action.
                break
            else:
                game_state.add_log_entry(f"AI ({self.player_name}): Action {action_type} resolved successfully.")


            actions_taken_this_turn += 1
            # Optional: Add a check for game_over again here if actions can end the game immediately

        if actions_taken_this_turn >= max_actions_per_turn:
            game_state.add_log_entry(f"AI ({self.player_name}): Reached max actions per turn ({max_actions_per_turn}). Ending turn.", level="WARNING")

        game_state.add_log_entry(f"AI ({self.player_name}): Concluding main phase actions.")

if __name__ == '__main__':
    print("AIPlayerBase module: Defines the abstract base class for AI players.")
    # This class is not meant to be run directly but inherited by concrete AI implementations.
    # Example (requires GameState, PlayerChoiceType from enums, etc. to be importable for full test):
    #
    # from tuck_in_terrors_sim.game_elements.enums import PlayerChoiceType # Assuming this path
    #
    # class RandomAI(AIPlayerBase):
    #     def choose_action(self, game_state: 'GameState', valid_actions: List[Dict[str, Any]]) -> Dict[str, Any]:
    #         import random
    #         if not valid_actions:
    #             return {'type': 'PASS_TURN', 'params': {}}
    #         return random.choice(valid_actions)
    #
    #     def make_choice(self, game_state: 'GameState', choice_context: Dict[str, Any]) -> Any:
    #         import random
    #         options = choice_context.get('options')
    #         choice_type_str = choice_context.get('choice_type')
    #
    #         # Example handling for a YES_NO choice
    #         # Ensure PlayerChoiceType.CHOOSE_YES_NO.name is correctly compared
    #         if choice_type_str == PlayerChoiceType.CHOOSE_YES_NO.name: # Accessing enum by name assuming it's loaded
    #             return random.choice([True, False])
    #
    #         # Example handling for choosing from a list of options
    #         if isinstance(options, list) and options:
    #             return random.choice(options)
    #
    #         # Fallback for unhandled or simple choices
    #         game_state.add_log_entry(f"AI ({self.player_name}): RandomAI making default/random choice for: {choice_context.get('prompt_text')}", level="DEBUG")
    #         if isinstance(options, list) and options: # Double check options
    #            return random.choice(options)
    #         elif options: # if options is not a list but is truthy (e.g. a dict of options) - this needs specific handling
                # For now, returning None if options format is not a simple list
    #             return None
    #         return None # Default if no specific logic matches or options are not clear