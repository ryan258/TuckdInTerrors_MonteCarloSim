# src/tuck_in_terrors_sim/game_logic/action_resolver.py
# Handles resolving player actions like playing cards, activating abilities

from typing import TYPE_CHECKING, List, Optional, Any, Dict, Tuple # Added Tuple
from .game_state import GameState, PlayerState 
from tuck_in_terrors_sim.game_elements.card import Card, Toy, Spell, Ritual, Effect, CardInstance
from ..game_elements.enums import CardType, Zone, EffectTriggerType, EffectActivationCostType, ResourceType
from .effect_engine import EffectEngine 

if TYPE_CHECKING:
    from .game_state import GameState, PlayerState
    from .effect_engine import EffectEngine
    from .win_loss_checker import WinLossChecker
    from ..game_elements.card import CardInstance, Effect # Make sure Effect is here if used in Tuple

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

        card_def = card_to_play_instance.definition # type: ignore
        played_card_instance = card_to_play_instance # Keep a reference

        # 1. Cost Payment & Initial Checks
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

        # 2. Move Card from Hand
        # The card_to_play_instance is removed from hand and becomes 'played_card_instance'
        active_player.zones[Zone.HAND].pop(card_hand_idx) # type: ignore
        gs.add_log_entry(f"'{played_card_instance.definition.name}' ({played_card_instance.instance_id}) removed from hand.", "ACTION_DETAIL") # type: ignore

        # 3. Gather Triggered Effects
        pending_effects_to_resolve: List[Tuple[CardInstance, Effect, Dict[str, Any]]] = []
        
        # Event context for this play event
        play_event_context = {
            'event_type': 'CARD_PLAYED', # Generic event type
            'played_card_instance_id': played_card_instance.instance_id, # type: ignore
            'played_card_definition_id': played_card_instance.definition.card_id, # type: ignore
            'played_card_type': played_card_instance.definition.type, # type: ignore
            'played_card_subtypes': played_card_instance.definition.subtypes, # type: ignore
            'player_id': active_player.player_id,
            'targets': targets # If any targets were chosen for the play itself
        }

        # a. Triggers from other cards already in play
        #    (e.g., "Whenever a Toy is played...")
        cards_in_play_sorted = sorted(
            [c for c in gs.cards_in_play.values() if c.instance_id != played_card_instance.instance_id], # type: ignore
            key=lambda c: (c.turn_entered_play if c.turn_entered_play is not None else float('inf'), c.instance_id)
        )

        for other_card_in_play in cards_in_play_sorted:
            for effect_obj in other_card_in_play.definition.effects:
                # Example: Check for a specific trigger type like WHEN_CARD_TYPE_PLAYED
                if effect_obj.trigger == EffectTriggerType.WHEN_CARD_TYPE_PLAYED:
                    # Check if the condition of this effect matches the played card
                    # This condition check is simplified here; real conditions are in effect_obj.condition
                    # For WHEN_CARD_TYPE_PLAYED, the effect's own conditions might check params.card_type
                    # Here, we assume the effect itself will check its specific conditions via self.effect_engine.check_condition
                    # We just need to identify that it *could* trigger.
                    # A more robust way is if effect_obj.condition could use play_event_context.
                    
                    # Simplified: if a card in play has a WHEN_CARD_TYPE_PLAYED trigger, queue it.
                    # The EffectEngine's check_condition will ultimately determine if it resolves.
                    pending_effects_to_resolve.append(
                        (other_card_in_play, effect_obj, play_event_context)
                    )
        
        # b. ON_PLAY Triggers from the card just played
        #    These should resolve *after* triggers from cards already in play.
        #    We will add them to the list and rely on sorting or add them last.
        #    For now, we'll add them and ensure they are marked as "just played" for sorting.
        
        # Temporarily assign current turn for sorting purposes if it's entering play
        # If it's a spell, it doesn't truly "enter play" in the same way.
        original_turn_entered_play = played_card_instance.turn_entered_play # type: ignore
        if card_def.type == CardType.TOY or card_def.type == CardType.RITUAL:
            played_card_instance.turn_entered_play = gs.current_turn # type: ignore
            # This also marks it as the "newest" for sorting if instance_id is used as tie-breaker

        for effect_obj in played_card_instance.definition.effects: # type: ignore
            if effect_obj.trigger == EffectTriggerType.ON_PLAY:
                # Mark these as "just_played" for sorting if needed, or handle by adding last
                # The sort key will handle this if `turn_entered_play` is now current_turn
                pending_effects_to_resolve.append(
                    (played_card_instance, effect_obj, play_event_context) # type: ignore
                )

        # 4. Sort all pending effects
        #    - Primary sort: effects from cards "just played" go last.
        #    - Secondary sort (for cards already in play): oldest first.
        def sort_effects_key(item: Tuple[CardInstance, Effect, Dict[str, Any]]):
            card_inst, effect_obj, _ = item
            is_just_played = (card_inst.instance_id == played_card_instance.instance_id) # type: ignore
            
            turn_entered = card_inst.turn_entered_play if card_inst.turn_entered_play is not None else float('inf')
            # if is_just_played, turn_entered might be the current turn.
            
            return (
                is_just_played,  # False (0) for already in play, True (1) for just played
                turn_entered,    # Sort by when the source card entered play (oldest first)
                card_inst.instance_id # Tie-breaker
            )

        pending_effects_to_resolve.sort(key=sort_effects_key)

        # 5. Move card to its final zone *before* resolving sorted effects that might depend on its location
        if card_def.type == CardType.TOY or card_def.type == CardType.RITUAL:
            gs.move_card_zone(played_card_instance, Zone.IN_PLAY, active_player.player_id) # type: ignore
            # played_card_instance.turn_entered_play was already set for sorting
            gs.add_log_entry(f"P{active_player.player_id} played {card_def.type.name} '{card_def.name}' ({played_card_instance.instance_id}) to play area.") # type: ignore
        elif card_def.type == CardType.SPELL:
            gs.add_log_entry(f"P{active_player.player_id} casting Spell '{card_def.name}'. Effects will resolve, then it goes to discard.")
            # Spells resolve then go to discard. Zone change happens after effects.
            pass # Spell zone change handled after effects

        # 6. Resolve sorted effects
        if not gs.game_over:
            for card_source_instance, effect_to_resolve, event_ctx in pending_effects_to_resolve:
                if gs.game_over: break
                self.effect_engine.resolve_effect(
                    effect=effect_to_resolve,
                    game_state=gs,
                    player=active_player, # The player whose action triggered these effects
                    source_card_instance=card_source_instance,
                    triggering_event_context=event_ctx # Pass the specific context
                )
        
        # Restore original turn_entered_play if it was temporarily changed for a non-permanent card
        if card_def.type != CardType.TOY and card_def.type != CardType.RITUAL:
             played_card_instance.turn_entered_play = original_turn_entered_play # type: ignore


        # 7. Post-effect actions (e.g., moving spell to discard, storm count)
        if card_def.type == CardType.SPELL:
            if not gs.game_over: # Only increment if game is still on
                gs.storm_count_this_turn += 1
                gs.add_log_entry(f"Spell '{card_def.name}' cast. Storm count for this turn now: {gs.storm_count_this_turn}.")
            
            gs.move_card_zone(played_card_instance, Zone.DISCARD, active_player.player_id) # type: ignore
            gs.add_log_entry(f"Spell '{card_def.name}' ({played_card_instance.instance_id}) moved to P{active_player.player_id}'s discard pile.") # type: ignore


        # 8. Final win condition check and flag updates
        if not gs.game_over:
            if self.win_loss_checker.check_all_conditions():
                gs.add_log_entry(f"Game end condition met after playing card '{card_def.name}'. Status: {gs.win_status or 'Unknown'}", level="GAME_END")
        
        if is_free_toy_play and not gs.game_over :
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