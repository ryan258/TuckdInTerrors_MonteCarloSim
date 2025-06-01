# src/tuck_in_terrors_sim/game_logic/turn_manager.py
# Manages turn phases (begin, main, end) and turn progression

import random
from typing import TYPE_CHECKING, Optional # Ensure Optional is imported

if TYPE_CHECKING: # To avoid circular imports for type hinting
    from .game_state import GameState
    from ..ai.ai_player_base import AIPlayerBase 
    from .effect_engine import EffectEngine
    from .nightmare_creep import NightmareCreepModule
    from .win_loss_checker import WinLossChecker

from ..game_elements.enums import TurnPhase, EffectTriggerType


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
                 ): 
        self.game_state = game_state
        self.effect_engine = effect_engine
        self.nightmare_module = nightmare_module
        self.win_loss_checker = win_loss_checker # Store it

    def _begin_turn_phase(self):
        gs = self.game_state
        gs.current_phase = TurnPhase.BEGIN_TURN
        gs.add_log_entry(f"Beginning Turn {gs.current_turn} - {gs.current_phase.name}.")

        for card_in_play_instance_id in list(gs.cards_in_play.keys()):
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
        gs.nightmare_creep_effect_applied_this_turn = False
        gs.add_log_entry("Turn-specific flags reset.")

        if gs.current_objective.setup_instructions and \
           gs.current_objective.setup_instructions.component_type == "CUSTOM_GAME_SETUP" and \
           "first_turn_mana_override" in gs.current_objective.setup_instructions.params and \
           gs.current_turn == 1:
            gs.add_log_entry(f"Mana for Turn 1 was {gs.mana_pool} (pre-set by objective).")
        else:
            mana_to_gain = gs.current_turn + STANDARD_MANA_GAIN_PER_TURN_BASE
            gs.mana_pool += mana_to_gain
            gs.add_log_entry(f"Gained {mana_to_gain} mana. Total mana: {gs.mana_pool}.")

        if len(gs.deck) >= STANDARD_CARDS_TO_DRAW_PER_TURN:
            for i in range(STANDARD_CARDS_TO_DRAW_PER_TURN):
                drawn_card = gs.deck.pop(0) 
                gs.hand.append(drawn_card)
                gs.add_log_entry(f"Drew card: {drawn_card.name}. Hand size: {len(gs.hand)}.")
                self.effect_engine.trigger_effects(
                    trigger_type=EffectTriggerType.WHEN_CARD_DRAWN,
                    event_context={'drawn_card_definition': drawn_card}
                )
        elif len(gs.deck) > 0: 
             while gs.deck:
                drawn_card = gs.deck.pop(0)
                gs.hand.append(drawn_card)
                gs.add_log_entry(f"Drew last card: {drawn_card.name}. Hand size: {len(gs.hand)}.")
                self.effect_engine.trigger_effects(
                    trigger_type=EffectTriggerType.WHEN_CARD_DRAWN,
                    event_context={'drawn_card_definition': drawn_card}
                )
             gs.add_log_entry("Deck is now empty after drawing.", level="WARNING")
        else:
            gs.add_log_entry("Cannot draw card: Deck is empty.", level="WARNING")

        gs.add_log_entry("Checking for Nightmare Creep activation...")
        if self.nightmare_module.apply_nightmare_creep_for_current_turn():
            gs.add_log_entry("Objective's Nightmare Creep processed. Triggering card reactions to NC event.")
            self.effect_engine.trigger_effects(EffectTriggerType.WHEN_NIGHTMARE_CREEP_APPLIES_TO_PLAYER)
        else:
            gs.add_log_entry("Nightmare Creep not scheduled or applicable this turn.")

        gs.add_log_entry("Resolving 'beginning of player turn' effects...")
        self.effect_engine.trigger_effects(EffectTriggerType.BEGIN_PLAYER_TURN)


    def _main_phase(self, ai_player: 'AIPlayerBase'): 
        gs = self.game_state
        gs.current_phase = TurnPhase.MAIN_PHASE
        gs.add_log_entry(f"Beginning {gs.current_phase.name}.")

        if ai_player:
            gs.add_log_entry("AI Player taking actions...")
            # ai_player.take_turn_actions(gs) 
            gs.add_log_entry("Placeholder: AI actions (calling ActionResolver) would be performed here.")
        else:
            gs.add_log_entry("No AI player provided for main phase.", level="WARNING")

        gs.add_log_entry(f"Main phase ended.")


    def _end_turn_phase(self):
        gs = self.game_state
        gs.current_phase = TurnPhase.END_TURN
        gs.add_log_entry(f"Beginning {gs.current_phase.name}.")

        gs.add_log_entry("Resolving 'end of player turn' effects...")
        self.effect_engine.trigger_effects(EffectTriggerType.END_PLAYER_TURN)

        if gs.mana_pool > 0:
            gs.add_log_entry(f"Losing {gs.mana_pool} unspent mana.")
            gs.mana_pool = 0
        else:
            gs.add_log_entry("No unspent mana to lose.")

        max_hand_size = STANDARD_MAX_HAND_SIZE
        if gs.current_objective.special_rules_text: 
            for rule_text in gs.current_objective.special_rules_text:
                rule_text_lower = rule_text.lower()
                if "hand size limit:" in rule_text_lower:
                    try:
                        max_hand_size = int(rule_text_lower.split("hand size limit:")[1].strip().split(" ")[0])
                    except (ValueError, IndexError):
                        gs.add_log_entry(f"Could not parse hand size limit from rule: '{rule_text}'", level="WARNING")
                        
        if len(gs.hand) > max_hand_size:
            num_to_discard = len(gs.hand) - max_hand_size
            gs.add_log_entry(f"Hand size ({len(gs.hand)}) exceeds max ({max_hand_size}). Player must discard {num_to_discard} cards.")
            for i in range(num_to_discard):
                if gs.hand:
                    discarded_card = gs.hand.pop() 
                    gs.discard_pile.append(discarded_card)
                    gs.add_log_entry(f"AI discarded '{discarded_card.name}' to meet hand size.")
                    self.effect_engine.trigger_effects(
                        EffectTriggerType.ON_DISCARD_THIS_CARD, 
                        source_card_definition_for_trigger=discarded_card,
                        event_context={'discarded_card_definition': discarded_card, 'reason': 'HAND_SIZE'}
                    )
                else: break 
            gs.add_log_entry(f"Hand size after discard: {len(gs.hand)}.")

        gs.add_log_entry("Checking win/loss conditions...")
        self.win_loss_checker.check_all_conditions() # Call WinLossChecker
        
        gs.add_log_entry(f"End of Turn {gs.current_turn} phase complete.")


    def execute_full_turn(self, ai_player: 'AIPlayerBase'):
        if self.game_state.game_over:
            self.game_state.add_log_entry("Attempted to execute turn, but game is already over.", level="WARNING")
            return

        self._begin_turn_phase()
        if self.game_state.game_over: 
            log_status = self.game_state.win_status or "Unknown reason"
            self.game_state.add_log_entry(f"Game ended during Begin Turn Phase of Turn {self.game_state.current_turn}. Status: {log_status}")
            return

        if not self.game_state.game_over:
            self._main_phase(ai_player)
            if self.game_state.game_over:
                log_status = self.game_state.win_status or "Unknown reason"
                self.game_state.add_log_entry(f"Game ended during Main Phase of Turn {self.game_state.current_turn}. Status: {log_status}")
                return
        
        if not self.game_state.game_over:
            self._end_turn_phase() 
        
        if self.game_state.game_over and self.game_state.win_status:
             self.game_state.add_log_entry(f"Game ended in Turn {self.game_state.current_turn}. Status: {self.game_state.win_status}")
        elif not self.game_state.game_over:
            self.game_state.add_log_entry(f"Turn {self.game_state.current_turn} concluded. Ready for next turn.")


if __name__ == '__main__':
    print("TurnManager module: Manages the phases and progression of a game turn.")