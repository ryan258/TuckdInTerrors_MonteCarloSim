# src/tuck_in_terrors_sim/game_logic/turn_manager.py
# Manages turn phases (begin, main, end) and turn progression

import random # random is used for hand size discard, not directly for AI here
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING: # To avoid circular imports for type hinting
    from .game_state import GameState
    from ..ai.ai_player_base import AIPlayerBase
    from .effect_engine import EffectEngine
    from .nightmare_creep import NightmareCreepModule
    from .win_loss_checker import WinLossChecker
    from .action_resolver import ActionResolver # Added for type hint
    from ..ai.action_generator import ActionGenerator # Added for type hint

from ..game_elements.enums import TurnPhase, EffectTriggerType
# Import necessary classes for instantiation
from .action_resolver import ActionResolver
from ..ai.action_generator import ActionGenerator


# Constants
STANDARD_MANA_GAIN_PER_TURN_BASE = 1
STANDARD_CARDS_TO_DRAW_PER_TURN = 1
STANDARD_MAX_HAND_SIZE = 7

class TurnManager:
    def __init__(self,
                 game_state: 'GameState',
                 effect_engine: 'EffectEngine',
                 nightmare_module: 'NightmareCreepModule',
                 win_loss_checker: 'WinLossChecker'
                 # ActionResolver and ActionGenerator will be instantiated per turn or as needed,
                 # as they are primarily used within the AI's turn context.
                 # Alternatively, they could be passed in if they held significant state
                 # or were expensive to create, but for now, let's create them on demand.
                 ):
        self.game_state = game_state
        self.effect_engine = effect_engine
        self.nightmare_module = nightmare_module
        self.win_loss_checker = win_loss_checker
        # We will instantiate ActionResolver and ActionGenerator in _main_phase

    def _begin_turn_phase(self):
        gs = self.game_state
        gs.current_phase = TurnPhase.BEGIN_TURN
        gs.add_log_entry(f"Beginning Turn {gs.current_turn} - {gs.current_phase.name}.")

        # Untap cards, update turn counters, reset turn flags
        for card_in_play_instance_id in list(gs.cards_in_play.keys()): # Iterate over a copy of keys
            card_instance = gs.cards_in_play.get(card_in_play_instance_id)
            if card_instance:
                if card_instance.is_tapped:
                    card_instance.untap()
                    gs.add_log_entry(f"Untapped '{card_instance.card_definition.name}' (Instance: {card_instance.instance_id}).")
                card_instance.turns_in_play += 1
                card_instance.effects_active_this_turn.clear()
        gs.add_log_entry("All cards in play untapped and turn counters updated.")

        gs.free_toy_played_this_turn = False
        gs.storm_count_this_turn = 0
        gs.nightmare_creep_effect_applied_this_turn = False # Ensure this is reset
        gs.add_log_entry("Turn-specific flags reset.")

        # Mana gain
        # (Assuming objective-specific first turn mana is handled by game_setup setting initial mana_pool)
        if not (gs.current_objective.setup_instructions and \
           gs.current_objective.setup_instructions.component_type == "CUSTOM_GAME_SETUP" and \
           "first_turn_mana_override" in gs.current_objective.setup_instructions.params and \
           gs.current_turn == 1):
            mana_to_gain = gs.current_turn + STANDARD_MANA_GAIN_PER_TURN_BASE
            gs.mana_pool += mana_to_gain
            gs.add_log_entry(f"Gained {mana_to_gain} mana. Total mana: {gs.mana_pool}.")
        else:
            gs.add_log_entry(f"Mana for Turn 1 is {gs.mana_pool} (pre-set by objective).")


        # Draw cards
        cards_to_draw = STANDARD_CARDS_TO_DRAW_PER_TURN # Can be modified by effects later
        for i in range(cards_to_draw):
            if not gs.deck:
                gs.add_log_entry("Cannot draw card: Deck is empty.", level="WARNING")
                break
            drawn_card = gs.deck.pop(0)
            gs.hand.append(drawn_card)
            gs.add_log_entry(f"Drew card: {drawn_card.name}. Hand size: {len(gs.hand)}.")
            self.effect_engine.trigger_effects(
                trigger_type=EffectTriggerType.WHEN_CARD_DRAWN,
                event_context={'drawn_card_definition': drawn_card}
            )
        if not gs.deck and cards_to_draw > 0 and i < cards_to_draw -1:
             gs.add_log_entry("Deck became empty during draw phase.", level="WARNING")


        # Nightmare Creep
        gs.add_log_entry("Checking for Nightmare Creep activation...")
        # nightmare_creep_effect_applied_this_turn is set within apply_nightmare_creep_for_current_turn
        if self.nightmare_module.apply_nightmare_creep_for_current_turn():
            # Log entry for application is handled within the module
            gs.add_log_entry("Objective's Nightmare Creep processed. Triggering card reactions to NC event.")
            # This trigger is for cards reacting to the player being affected by NC
            self.effect_engine.trigger_effects(EffectTriggerType.WHEN_NIGHTMARE_CREEP_APPLIES_TO_PLAYER)
        else:
            gs.add_log_entry("Nightmare Creep not scheduled or applicable this turn.")

        # Begin player turn effects
        gs.add_log_entry("Resolving 'beginning of player turn' effects...")
        self.effect_engine.trigger_effects(EffectTriggerType.BEGIN_PLAYER_TURN)


    def _main_phase(self, ai_player: 'AIPlayerBase'):
        gs = self.game_state
        gs.current_phase = TurnPhase.MAIN_PHASE
        gs.add_log_entry(f"Beginning {gs.current_phase.name} for {ai_player.player_name if ai_player else 'N/A'}.")

        if ai_player:
            # Instantiate ActionResolver and ActionGenerator for this AI's turn
            action_resolver = ActionResolver(gs, self.effect_engine)
            action_generator = ActionGenerator() # ActionGenerator is stateless for now

            gs.add_log_entry(f"AI Player ({ai_player.player_name}) taking actions...")
            ai_player.take_turn_actions(gs, action_resolver, action_generator)
            gs.add_log_entry(f"AI Player ({ai_player.player_name}) finished actions for main phase.")
        else:
            gs.add_log_entry("No AI player provided for main phase. Main phase skipped.", level="WARNING")

        gs.add_log_entry(f"Main phase ended.")


    def _end_turn_phase(self):
        gs = self.game_state
        gs.current_phase = TurnPhase.END_TURN
        gs.add_log_entry(f"Beginning {gs.current_phase.name}.")

        gs.add_log_entry("Resolving 'end of player turn' effects...")
        self.effect_engine.trigger_effects(EffectTriggerType.END_PLAYER_TURN)

        # Lose unspent mana
        if gs.mana_pool > 0:
            gs.add_log_entry(f"Losing {gs.mana_pool} unspent mana.")
            gs.mana_pool = 0
        else:
            gs.add_log_entry("No unspent mana to lose.")

        # Discard down to max hand size
        # Max hand size can be modified by objective special rules
        current_max_hand_size = STANDARD_MAX_HAND_SIZE
        if gs.current_objective and gs.current_objective.special_rules_text:
            for rule_text in gs.current_objective.special_rules_text:
                rule_text_lower = rule_text.lower()
                if "hand size limit:" in rule_text_lower:
                    try:
                        # Example: "Hand size limit: 4 (...)"
                        limit_str = rule_text_lower.split("hand size limit:")[1].strip().split(" ")[0]
                        current_max_hand_size = int(limit_str)
                        gs.add_log_entry(f"Applying special rule: Max hand size is {current_max_hand_size}.")
                        break # Assuming only one such rule
                    except (ValueError, IndexError) as e:
                        gs.add_log_entry(f"Could not parse hand size limit from rule: '{rule_text}'. Error: {e}", level="WARNING")


        if len(gs.hand) > current_max_hand_size:
            num_to_discard = len(gs.hand) - current_max_hand_size
            gs.add_log_entry(f"Hand size ({len(gs.hand)}) exceeds max ({current_max_hand_size}). Player must discard {num_to_discard} card(s).")
            # For now, AI discards randomly. A real AI might make smarter choices.
            # Or, this could become a PLAYER_CHOICE if we want the AI to pick.
            # For simplicity in a random AI context, random discard is fine.
            for _ in range(num_to_discard):
                if not gs.hand: break # Should not happen if num_to_discard > 0
                # Simplistic: discard last card (could be random for a more robust random AI)
                # For a simulation, deterministic discard (e.g., last card) might be better than random.
                # Let's make it random from hand for a bit more realism for now.
                discarded_card = gs.hand.pop(random.randrange(len(gs.hand)))
                gs.discard_pile.append(discarded_card)
                gs.add_log_entry(f"Discarded '{discarded_card.name}' due to hand size limit.")
                self.effect_engine.trigger_effects(
                    EffectTriggerType.ON_DISCARD_THIS_CARD,
                    source_card_definition_for_trigger=discarded_card,
                    event_context={'discarded_card_definition': discarded_card, 'reason': 'HAND_SIZE'}
                )
            gs.add_log_entry(f"Hand size after discard: {len(gs.hand)}.")

        # Check win/loss conditions
        gs.add_log_entry("Checking win/loss conditions at end of turn...")
        if self.win_loss_checker.check_all_conditions(): # This updates gs.game_over and gs.win_status
            gs.add_log_entry(f"Game end condition met. Status: {gs.win_status}", level="GAME_END")
        
        gs.add_log_entry(f"End of Turn {gs.current_turn} phase complete.")


    def execute_full_turn(self, ai_player: 'AIPlayerBase'):
        if self.game_state.game_over:
            self.game_state.add_log_entry("Attempted to execute turn, but game is already over.", level="WARNING")
            return

        # Increment turn *before* begin_turn_phase so logs/rules for "Turn X" are correct
        self.game_state.current_turn += 1
        self.game_state.add_log_entry(f"--- Starting Turn {self.game_state.current_turn} ---", level="INFO_TURN_SEPARATOR")


        self._begin_turn_phase()
        if self.game_state.game_over:
            log_status = self.game_state.win_status or "Unknown reason"
            self.game_state.add_log_entry(f"Game ended during Begin Turn Phase of Turn {self.game_state.current_turn}. Status: {log_status}", level="GAME_END")
            return

        # Main Phase
        self._main_phase(ai_player)
        if self.game_state.game_over:
            log_status = self.game_state.win_status or "Unknown reason"
            self.game_state.add_log_entry(f"Game ended during Main Phase of Turn {self.game_state.current_turn}. Status: {log_status}", level="GAME_END")
            return
        
        # End Phase (Win/loss check is also here)
        self._end_turn_phase()
        # game_state.game_over might have been set in _end_turn_phase by win_loss_checker
        
        if self.game_state.game_over:
             if self.game_state.win_status: # win_status should be set if game_over is True from win_loss_checker
                 self.game_state.add_log_entry(f"Game concluded at end of Turn {self.game_state.current_turn}. Final Status: {self.game_state.win_status}", level="GAME_END")
             else: # Should ideally not happen if win_loss_checker is robust
                 self.game_state.add_log_entry(f"Game ended at end of Turn {self.game_state.current_turn}, but win_status is not set. Check logic.", level="ERROR")
        else:
            self.game_state.add_log_entry(f"Turn {self.game_state.current_turn} concluded. Ready for next turn.")


if __name__ == '__main__':
    print("TurnManager module: Manages the phases and progression of a game turn.")