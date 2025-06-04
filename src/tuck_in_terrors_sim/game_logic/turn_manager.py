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
        
        # Update turns_in_play for cards controlled by active player (optional, rules dependent)
        # Reset effects_applied_this_turn for cards controlled by active player
        for card_instance in gs.cards_in_play.values():
            if card_instance.controller_id == active_player.player_id:
                if card_instance.turn_entered_play is not None: # Only if it has been in play
                    # This logic might be complex depending on how "turns in play" is defined
                    # For simplicity, we can assume it's just a counter for now or handled elsewhere
                    pass 
                card_instance.effects_active_this_turn.clear()


        active_player.has_played_free_toy_this_turn = False
        # gs.storm_count_this_turn = 0 # Storm count might be player specific or global
        gs.nightmare_creep_effect_applied_this_turn = False
        gs.nightmare_creep_skipped_this_turn = False


        # Mana gain - objectives can override first turn mana via game_setup
        # Standard gain: current_turn number (e.g. turn 1 = 1 mana, turn 2 = 2 mana etc.)
        # Let's assume mana is set to current_turn unless overridden
        mana_this_turn = gs.current_turn 
        is_first_turn_mana_override = False
        if gs.current_turn == 1 and gs.current_objective.setup_instructions:
            setup_params = gs.current_objective.setup_instructions.params
            if "first_turn_mana_override" in setup_params:
                # This mana should have been set during game_setup on PlayerState
                # This block is more of a check/log if mana was indeed overridden
                mana_this_turn = active_player.mana # Use pre-set mana
                is_first_turn_mana_override = True
                gs.add_log_entry(f"Mana for Turn 1 is {active_player.mana} (pre-set by objective).")
        
        if not is_first_turn_mana_override:
            active_player.mana = mana_this_turn # Set mana to current turn number
            gs.add_log_entry(f"Player {active_player.player_id} sets mana to {active_player.mana} for turn {gs.current_turn}.")


        # Draw card
        gs.add_log_entry(f"Player {active_player.player_id} attempts to draw {STANDARD_CARDS_TO_DRAW_PER_TURN} card(s).")
        drawn_cards = active_player.draw_cards(STANDARD_CARDS_TO_DRAW_PER_TURN, gs)
        
        # Handle "WHEN_CARD_DRAWN" triggers (simplified, a real event system would be better)
        # for drawn_card_inst in drawn_cards:
        #     if drawn_card_inst.definition.effects:
        #         for effect_obj in drawn_card_inst.definition.effects:
        #             if effect_obj.trigger == EffectTriggerType.WHEN_CARD_DRAWN: # This trigger type isn't on Effect itself
        #                 # This needs a global trigger check or specific card ability
        #                 pass
        # A general WHEN_CARD_DRAWN event for other cards to react to:
        # self.effect_engine.resolve_triggers_for_event(EffectTriggerType.WHEN_CARD_DRAWN, gs, active_player, {'drawn_cards': drawn_cards})


        # Nightmare Creep
        if self.nightmare_module.apply_nightmare_creep_for_current_turn():
            # This would trigger WHEN_NIGHTMARE_CREEP_APPLIES_TO_PLAYER
            # self.effect_engine.resolve_triggers_for_event(EffectTriggerType.WHEN_NIGHTMARE_CREEP_APPLIES_TO_PLAYER, gs, active_player)
            pass # Logging is inside apply_nightmare_creep_for_current_turn
        else:
            gs.add_log_entry("Nightmare Creep not active or skipped this turn.")

        # Begin player turn effects
        # self.effect_engine.resolve_triggers_for_event(EffectTriggerType.BEGIN_PLAYER_TURN, gs, active_player)


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