# src/tuck_in_terrors_sim/game_logic/turn_manager.py
# Manages turn phases (begin, main, end) and turn progression

import random
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING: 
    from .game_state import GameState, PlayerState # Added PlayerState
    from ..ai.ai_player_base import AIPlayerBase
    from .effect_engine import EffectEngine
    from .nightmare_creep import NightmareCreepModule
    from .win_loss_checker import WinLossChecker
    from .action_resolver import ActionResolver 
    from ..ai.action_generator import ActionGenerator 

from ..game_elements.enums import TurnPhase, EffectTriggerType, Zone # Added Zone
from ..game_elements.card import CardInstance # Added CardInstance for type hinting
# Import necessary classes for instantiation
from .action_resolver import ActionResolver # Ensure this is imported for use
from ..ai.action_generator import ActionGenerator # Ensure this is imported for use


# Constants
STANDARD_MANA_GAIN_PER_TURN_BASE = 1 # Default mana gain if not turn 0 and not overridden
STANDARD_CARDS_TO_DRAW_PER_TURN = 1
STANDARD_MAX_HAND_SIZE = 7

class TurnManager:
    def __init__(self,
                 game_state: 'GameState',
                 action_resolver: 'ActionResolver', # Added action_resolver
                 effect_engine: 'EffectEngine',
                 nightmare_module: 'NightmareCreepModule',
                 win_loss_checker: 'WinLossChecker'
                 ):
        self.game_state = game_state
        self.action_resolver = action_resolver # Store action_resolver
        self.effect_engine = effect_engine
        self.nightmare_module = nightmare_module
        self.win_loss_checker = win_loss_checker
        # ActionGenerator can still be instantiated on demand in _main_phase if it's stateless
        self.action_generator = ActionGenerator()

    def _begin_turn_phase(self):
        gs = self.game_state
        active_player = gs.get_active_player_state()
        if not active_player:
            gs.add_log_entry("Begin Turn: No active player!", level="ERROR"); return

        gs.current_phase = TurnPhase.BEGIN_TURN
        gs.add_log_entry(f"Turn {gs.current_turn} - Begin Phase (Player {active_player.player_id}).")

        # Untap cards
        for card_instance in list(gs.cards_in_play.values()): # Iterate copy
            if card_instance.controller_id == active_player.player_id and card_instance.is_tapped:
                card_instance.untap()
                gs.add_log_entry(f"Untapped '{card_instance.definition.name}' ({card_instance.instance_id}).")
        
        # Clear once-per-turn effect usage trackers for cards controlled by the player
        for card_instance in gs.cards_in_play.values():
            if card_instance.controller_id == active_player.player_id:
                # Ensure the attribute exists, similar to action_generator.py
                if hasattr(card_instance, 'effects_active_this_turn'): # Ensure correct attribute name
                    card_instance.effects_active_this_turn.clear()
                else: # Defensive initialization if somehow missing
                    card_instance.effects_active_this_turn = set()


        active_player.has_played_free_toy_this_turn = False
        gs.storm_count_this_turn = 0
        gs.nightmare_creep_effect_applied_this_turn = False
        gs.nightmare_creep_skipped_this_turn = False

        # Reset per-turn objective progress trackers
        gs.objective_progress["max_toy_loops_this_turn"] = 0
        gs.objective_progress["toy_loop_counts"] = {}
        gs.objective_progress["different_spells_cast_this_turn"] = set()

        # Mana Gain Logic
        mana_this_turn = gs.current_turn + STANDARD_MANA_GAIN_PER_TURN_BASE
        is_first_turn_mana_override = False
        if gs.current_turn == 1 and gs.current_objective.setup_instructions:
            setup_params = gs.current_objective.setup_instructions.params
            if "first_turn_mana_override" in setup_params:
                # This part was identified as a bit complex but functionally okay
                # due to game_setup.py pre-setting mana for turn 1 override.
                # The effective mana for turn 1 will be what game_setup set it to.
                # For other turns, or if no override, the standard gain applies.
                if active_player.mana == setup_params["first_turn_mana_override"]: # Check if it was set by setup
                     mana_this_turn = active_player.mana # type: ignore
                     is_first_turn_mana_override = True
                     gs.add_log_entry(f"Mana for Turn 1 is {active_player.mana} (as per objective override).")
                else: # If not already set by setup, apply the override now (should not happen if setup is correct)
                    mana_this_turn = setup_params["first_turn_mana_override"]
                    active_player.mana = mana_this_turn
                    is_first_turn_mana_override = True
                    gs.add_log_entry(f"Mana for Turn 1 set to {active_player.mana} (objective override in TurnManager).")


        if not is_first_turn_mana_override:
            active_player.mana = mana_this_turn
            gs.add_log_entry(f"Player {active_player.player_id} sets mana to {active_player.mana} (Turn {gs.current_turn} + {STANDARD_MANA_GAIN_PER_TURN_BASE}).")
        elif gs.current_turn == 1 and active_player.mana != (gs.current_turn + STANDARD_MANA_GAIN_PER_TURN_BASE) and is_first_turn_mana_override:
             # This log entry might be redundant if mana is correctly set as per override
             gs.add_log_entry(f"Player {active_player.player_id} mana is {active_player.mana} for Turn 1 (objective override). Standard gain would have been {gs.current_turn + STANDARD_MANA_GAIN_PER_TURN_BASE}.", level="DEBUG")


        # Draw card(s)
        gs.add_log_entry(f"Player {active_player.player_id} attempts to draw {STANDARD_CARDS_TO_DRAW_PER_TURN} card(s).")
        active_player.draw_cards(STANDARD_CARDS_TO_DRAW_PER_TURN, gs)
        if gs.game_over: return # Check if drawing from empty deck ended game (if that rule were active)

        # Apply Nightmare Creep
        if not gs.game_over:
            if self.nightmare_module.apply_nightmare_creep_for_current_turn():
                pass
            else:
                gs.add_log_entry("Nightmare Creep not active or skipped this turn.")
            if gs.game_over: return # NC might end the game

        # Resolve "at the beginning of turn" effects for cards in play (oldest first)
        if not gs.game_over:
            gs.add_log_entry("Resolving 'at beginning of turn' effects for cards in play.", "EFFECT_DEBUG")
            
            # Get cards controlled by the active player
            player_cards_in_play = [
                card_inst for card_inst in gs.cards_in_play.values()
                if card_inst.controller_id == active_player.player_id
            ]

            # Sort them: oldest first (by turn_entered_play, then by instance_id for tie-breaking)
            # CardInstance.instance_id includes a numeric suffix that increments, acting as a tie-breaker.
            def sort_key(card_instance: CardInstance): # type: ignore
                # Ensure turn_entered_play is not None; default to a high number if it is (should not happen for cards in play)
                turn_entered = card_instance.turn_entered_play if card_instance.turn_entered_play is not None else float('inf')
                return (turn_entered, card_instance.instance_id)

            player_cards_in_play.sort(key=sort_key)

            for card_instance in player_cards_in_play: # type: ignore
                if gs.game_over: break # Stop if an effect ends the game
                for effect_obj in card_instance.definition.effects: # type: ignore
                    if effect_obj.trigger == EffectTriggerType.AT_BEGINNING_OF_TURN:
                        gs.add_log_entry(f"Attempting AT_BEGINNING_OF_TURN effect for '{card_instance.definition.name}' ({card_instance.instance_id}).", "EFFECT_DEBUG") # type: ignore
                        self.effect_engine.resolve_effect(
                            effect=effect_obj,
                            game_state=gs,
                            player=active_player, # The player whose turn it is
                            source_card_instance=card_instance, # type: ignore
                            triggering_event_context={'event_type': EffectTriggerType.AT_BEGINNING_OF_TURN.name, 'turn': gs.current_turn}
                        )
                        if gs.game_over: break
                if gs.game_over: break
      
    def _main_phase(self): # AI player is now fetched from game_state
        gs = self.game_state
        active_player = gs.get_active_player_state()
        ai_agent = gs.get_active_player_agent()

        if not active_player or not ai_agent:
            gs.add_log_entry("Main Phase: No active player or AI agent.", level="ERROR"); return

        gs.current_phase = TurnPhase.MAIN_PHASE
        gs.add_log_entry(f"Main Phase - Player {active_player.player_id} (AI: {type(ai_agent).__name__}).")

        # AI makes decisions until it passes
        max_actions_per_turn = 20 # Safety break for loops
        actions_taken_this_phase = 0
        while actions_taken_this_phase < max_actions_per_turn:
            if gs.game_over: break

            possible_actions = self.action_generator.get_valid_actions(gs)
            if not possible_actions: # Should at least have PASS_TURN
                gs.add_log_entry("No possible actions available (not even PASS). Ending main phase.", level="WARNING")
                break

            chosen_game_action = ai_agent.decide_action(gs, possible_actions)

            if not chosen_game_action or chosen_game_action.type == "PASS_TURN":
                gs.add_log_entry(f"Player {active_player.player_id} chose to PASS turn or no action taken.")
                break 
            
            gs.add_log_entry(f"Player {active_player.player_id} attempts action: {chosen_game_action.type} - {chosen_game_action.description}", level="ACTION")
            
            # Resolve the chosen action using ActionResolver
            success = False
            if chosen_game_action.type == "PLAY_CARD":
                success = self.action_resolver.play_card(
                    card_instance_id_in_hand=chosen_game_action.params.get("card_id"),
                    is_free_toy_play=chosen_game_action.params.get("is_free_toy_play", False)
                    # targets param might be needed if ActionGenerator includes target pre-selection
                )
            elif chosen_game_action.type == "ACTIVATE_ABILITY":
                success = self.action_resolver.activate_ability(
                    card_instance_id=chosen_game_action.params.get("card_instance_id"),
                    effect_index=chosen_game_action.params.get("effect_index")
                    # targets param might be needed
                )
            
            if success:
                gs.add_log_entry(f"Action {chosen_game_action.type} resolved successfully.", "ACTION_SUCCESS")
            else:
                gs.add_log_entry(f"Action {chosen_game_action.type} FAILED to resolve.", "ACTION_FAIL")
                # If an action fails, AI might loop; consider breaking or different AI logic
                # For now, we continue to see if AI tries something else or passes.

            actions_taken_this_phase += 1
            if actions_taken_this_phase >= max_actions_per_turn:
                gs.add_log_entry("Reached max actions for main phase.", level="WARNING")
                break
        
        gs.add_log_entry(f"Main phase ended for Player {active_player.player_id}.")


    def _end_turn_phase(self):
        gs = self.game_state
        active_player = gs.get_active_player_state()
        if not active_player:
            gs.add_log_entry("End Turn: No active player!", level="ERROR"); return

        gs.current_phase = TurnPhase.END_TURN_PHASE
        gs.add_log_entry(f"End Phase - Player {active_player.player_id}.")

        # End player turn effects
        # self.effect_engine.resolve_triggers_for_event(EffectTriggerType.END_PLAYER_TURN, gs, active_player)

        # Lose unspent mana
        if active_player.mana > 0:
            gs.add_log_entry(f"Player {active_player.player_id} loses {active_player.mana} unspent mana.")
            active_player.mana = 0
        
        # Discard down to max hand size
        current_max_hand_size = STANDARD_MAX_HAND_SIZE # TODO: Allow objective to modify this
        
        if len(active_player.zones[Zone.HAND]) > current_max_hand_size:
            num_to_discard = len(active_player.zones[Zone.HAND]) - current_max_hand_size
            gs.add_log_entry(f"Hand size ({len(active_player.zones[Zone.HAND])}) exceeds max ({current_max_hand_size}). Player {active_player.player_id} must discard {num_to_discard}.")
            
            # TODO: Implement Player Choice for discard, or AI choice.
            # For now, simplistic random discard of CardInstance objects.
            for _ in range(num_to_discard):
                if not active_player.zones[Zone.HAND]: break
                
                # For AI to choose:
                # chosen_card_to_discard_id = ai_agent.choose_cards_to_discard(gs, 1)[0]
                # chosen_card_instance = gs.get_card_instance(chosen_card_to_discard_id)
                # if chosen_card_instance in active_player.zones[Zone.HAND]:
                #    gs.move_card_zone(chosen_card_instance, Zone.DISCARD, active_player.player_id)
                # else: # Fallback if AI choice fails or is not implemented
                
                # Fallback: random discard
                discard_idx = random.randrange(len(active_player.zones[Zone.HAND]))
                discarded_instance = active_player.zones[Zone.HAND].pop(discard_idx)
                gs.move_card_zone(discarded_instance, Zone.DISCARD, active_player.player_id) # This handles logging
                gs.add_log_entry(f"Player {active_player.player_id} discarded '{discarded_instance.definition.name}' due to hand size.")
                # Trigger ON_DISCARD_THIS_CARD for the discarded_instance.definition
                # for effect_obj in discarded_instance.definition.effects:
                #    if effect_obj.trigger == EffectTriggerType.ON_DISCARD_THIS_CARD:
                #        self.effect_engine.resolve_effect(effect_obj, gs, active_player, discarded_instance, 
                #                                          {'reason': 'HAND_SIZE', 'discarded_card_instance_id': discarded_instance.instance_id})


        # Check win/loss conditions
        if self.win_loss_checker.check_all_conditions(): # This updates gs.game_over
            gs.add_log_entry(f"Game end condition met. Status: {gs.win_status or 'Unknown'}", level="GAME_END")
        
        gs.add_log_entry(f"End of Turn {gs.current_turn} for Player {active_player.player_id}.")


    def execute_full_turn(self): # AI player is now fetched from game_state
        if self.game_state.game_over:
            self.game_state.add_log_entry("Attempted turn, but game already over.", level="WARNING")
            return

        self.game_state.current_turn += 1
        self.game_state.add_log_entry(f"--- Starting Turn {self.game_state.current_turn} ---", level="INFO_TURN_SEPARATOR")

        self._begin_turn_phase()
        if self.game_state.game_over: return

        self._main_phase() # Uses active_player from game_state
        if self.game_state.game_over: return
        
        self._end_turn_phase()
        
        if self.game_state.game_over and self.game_state.win_status:
             self.game_state.add_log_entry(f"Game concluded EOT {self.game_state.current_turn}. Final Status: {self.game_state.win_status}", level="GAME_END")
        elif not self.game_state.game_over:
             self.game_state.add_log_entry(f"Turn {self.game_state.current_turn} complete. Ready for next.")

if __name__ == '__main__':
    print("TurnManager module: Manages the phases and progression of a game turn.")