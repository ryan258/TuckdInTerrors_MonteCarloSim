# src/tuck_in_terrors_sim/game_logic/action_resolver.py
# Handles resolving player actions like playing cards, activating abilities

from typing import Dict, Optional, Any, List, TYPE_CHECKING # Added TYPE_CHECKING

from .game_state import GameState, PlayerState 
from tuck_in_terrors_sim.game_elements.card import Card, Toy, Spell, Ritual, Effect, CardInstance
from ..game_elements.enums import CardType, Zone, EffectTriggerType, EffectActivationCostType, ResourceType
from .effect_engine import EffectEngine 

if TYPE_CHECKING: # ADDED TYPE_CHECKING block
    from .win_loss_checker import WinLossChecker # ADDED import for type hint

class ActionResolver:
    def __init__(self, game_state: GameState, effect_engine: EffectEngine, win_loss_checker: 'WinLossChecker'): # MODIFIED signature
        self.game_state = game_state
        self.effect_engine = effect_engine 
        self.win_loss_checker = win_loss_checker # MODIFIED: Store win_loss_checker


    def _get_active_player(self) -> Optional[PlayerState]:
        """Helper to get the active player's state."""
        return self.game_state.get_active_player_state()

    def play_card(self, card_instance_id_in_hand: str, is_free_toy_play: bool = False, targets: Optional[List[Any]] = None) -> bool:
        gs = self.game_state
        active_player = self._get_active_player()

        if not active_player:
            gs.add_log_entry("Action Error: No active player found to play card.", level="ERROR")
            return False

        card_to_play_instance: Optional[CardInstance] = None
        card_hand_idx = -1
        for idx, inst in enumerate(active_player.zones[Zone.HAND]):
            if inst.instance_id == card_instance_id_in_hand:
                card_to_play_instance = inst
                card_hand_idx = idx
                break
        
        if not card_to_play_instance:
            gs.add_log_entry(f"Action Error: Card instance '{card_instance_id_in_hand}' not in P{active_player.player_id}'s hand.", level="ERROR")
            return False

        card_def = card_to_play_instance.definition

        if is_free_toy_play:
            if active_player.has_played_free_toy_this_turn:
                gs.add_log_entry(f"Action Error: Free Toy already played this turn. Cannot play '{card_def.name}'.", level="ERROR")
                return False
            if card_def.type != CardType.TOY:
                gs.add_log_entry(f"Action Error: '{card_def.name}' ({card_def.type.name}) is not a Toy for Free Toy Play.", level="ERROR")
                return False
            gs.add_log_entry(f"P{active_player.player_id} attempts Free Toy Play: '{card_def.name}'.")
        else: 
            if active_player.mana < card_def.cost_mana:
                gs.add_log_entry(f"Action Error: P{active_player.player_id} needs {card_def.cost_mana} mana for '{card_def.name}', has {active_player.mana}.", level="ERROR")
                return False
            gs.add_log_entry(f"P{active_player.player_id} attempts to play '{card_def.name}' for {card_def.cost_mana} mana.")
            active_player.mana -= card_def.cost_mana 
            gs.add_log_entry(f"P{active_player.player_id} spent {card_def.cost_mana} mana. Mana: {active_player.mana}.")

        original_hand_card = active_player.zones[Zone.HAND].pop(card_hand_idx)
        # card_to_play_instance is original_hand_card

        if card_def.type == CardType.TOY or card_def.type == CardType.RITUAL:
            gs.move_card_zone(card_to_play_instance, Zone.IN_PLAY, active_player.player_id)
            card_to_play_instance.turn_entered_play = gs.current_turn
            
            gs.add_log_entry(f"P{active_player.player_id} played {card_def.type.name} '{card_def.name}' ({card_to_play_instance.instance_id}) to play area.")
            
            if not gs.game_over: # Check if game ended before resolving effects (e.g. by a cost payment)
                for effect_obj in card_to_play_instance.definition.effects:
                    if effect_obj.trigger == EffectTriggerType.ON_PLAY:
                        self.effect_engine.resolve_effect(
                            effect=effect_obj,
                            game_state=gs,
                            player=active_player,
                            source_card_instance=card_to_play_instance,
                            triggering_event_context={'played_card_instance_id': card_to_play_instance.instance_id, 'targets': targets}
                        )
                    if gs.game_over: break # Stop resolving further effects if game ended

        elif card_def.type == CardType.SPELL:
            gs.add_log_entry(f"P{active_player.player_id} plays Spell '{card_def.name}'. Resolving...")
            
            if not gs.game_over:
                for effect_obj in card_to_play_instance.definition.effects:
                     if effect_obj.trigger == EffectTriggerType.ON_PLAY:
                        self.effect_engine.resolve_effect(
                            effect=effect_obj,
                            game_state=gs,
                            player=active_player, 
                            source_card_instance=card_to_play_instance, 
                            triggering_event_context={'played_spell_instance_id': card_to_play_instance.instance_id, 'targets': targets}
                        )
                     if gs.game_over: break
            
            if not gs.game_over: # Only increment if game is still on
                gs.storm_count_this_turn += 1
                gs.add_log_entry(f"Spell '{card_def.name}' cast. Storm count for this turn now: {gs.storm_count_this_turn}.")
            
            gs.move_card_zone(card_to_play_instance, Zone.DISCARD, active_player.player_id)
            gs.add_log_entry(f"Spell '{card_def.name}' ({card_to_play_instance.instance_id}) moved to P{active_player.player_id}'s discard pile.")

        if not gs.game_over: # Check win conditions only if game hasn't ended by an effect
            if self.win_loss_checker.check_all_conditions():
                gs.add_log_entry(f"Game end condition met after playing card '{card_def.name}'. Status: {gs.win_status or 'Unknown'}", level="GAME_END")
                # Game is now over, gs.game_over is True
        
        if is_free_toy_play and not gs.game_over : # only update flag if game not over
            active_player.has_played_free_toy_this_turn = True
            gs.add_log_entry(f"Free Toy play for P{active_player.player_id} used this turn.")
            
        return True

    def activate_ability(self, card_instance_id: str, effect_index: int, targets: Optional[List[Any]] = None) -> bool:
        gs = self.game_state
        active_player = self._get_active_player()
        card_instance = gs.get_card_instance(card_instance_id)

        if not active_player:
            gs.add_log_entry("Action Error: No active player to activate ability.", level="ERROR"); return False
        if not card_instance:
            gs.add_log_entry(f"Action Error: Card instance '{card_instance_id}' not found.", level="ERROR"); return False
        if card_instance.controller_id != active_player.player_id:
            gs.add_log_entry(f"Action Error: P{active_player.player_id} cannot activate ability of card '{card_instance.definition.name}' controlled by P{card_instance.controller_id}.", level="ERROR"); return False

        card_def = card_instance.definition
        if not (0 <= effect_index < len(card_def.effects)):
            gs.add_log_entry(f"Action Error: Invalid effect_index {effect_index} for '{card_def.name}'.", level="ERROR"); return False

        ability_effect_obj = card_def.effects[effect_index]
        
        if ability_effect_obj.trigger not in [EffectTriggerType.ACTIVATED_ABILITY, EffectTriggerType.TAP_ABILITY]:
            gs.add_log_entry(f"Action Error: Effect {effect_index} ('{ability_effect_obj.description}') on '{card_def.name}' is not an activatable type (Trigger: {ability_effect_obj.trigger.name}).", level="ERROR"); return False

        # Placeholder for detailed cost checking - assuming costs are met for now if ability is chosen
        if ability_effect_obj.trigger == EffectTriggerType.TAP_ABILITY:
            if card_instance.is_tapped:
                gs.add_log_entry(f"Action Error: Cannot activate tap ability of '{card_def.name}', already tapped.", level="ERROR"); return False
            card_instance.tap()
            gs.add_log_entry(f"Card '{card_def.name}' tapped for ability.")
        
        # Assume other costs are handled/checked before this point or are part of the effect resolution
        gs.add_log_entry(f"P{active_player.player_id} activating ability '{ability_effect_obj.description or effect_index}' of '{card_def.name}'.")

        if not gs.game_over: # Check if game ended before resolving effects
            self.effect_engine.resolve_effect(
                effect=ability_effect_obj,
                game_state=gs,
                player=active_player,
                source_card_instance=card_instance,
                triggering_event_context={'activated_ability_on_instance_id': card_instance.instance_id, 'targets': targets}
            )

        if not gs.game_over: # Check win conditions only if game hasn't ended by an effect
            if self.win_loss_checker.check_all_conditions():
                gs.add_log_entry(f"Game end condition met after activating ability on '{card_def.name}'. Status: {gs.win_status or 'Unknown'}", level="GAME_END")
        
        return True

if __name__ == '__main__':
    print("ActionResolver module: Handles player/AI actions and interfaces with EffectEngine.")