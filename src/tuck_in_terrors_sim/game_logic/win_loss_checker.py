# src/tuck_in_terrors_sim/game_logic/win_loss_checker.py
# Functions to check objective completion & Nightfall

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .game_state import GameState
    from ..game_elements.objective import ObjectiveLogicComponent

class WinLossChecker:
    def __init__(self, game_state: 'GameState'):
        self.game_state = game_state

    def check_all_conditions(self) -> bool:
        """
        Checks all win and loss conditions.
        Updates game_state.game_over and game_state.win_status.
        Returns True if the game has ended, False otherwise.
        """
        gs = self.game_state

        if gs.game_over: # If game already ended (e.g., by an effect)
            return True

        # 1. Check Primary Win Condition
        if self._check_win_condition(gs.current_objective.primary_win_condition, "PRIMARY_WIN"):
            return True

        # 2. Check Alternative Win Condition (if it exists and primary not met)
        if gs.current_objective.alternative_win_condition and \
           self._check_win_condition(gs.current_objective.alternative_win_condition, "ALTERNATIVE_WIN"):
            return True

        # 3. Check Loss Conditions (Nightfall is the primary one for now)
        if gs.current_turn > gs.current_objective.nightfall_turn:
            gs.add_log_entry(f"Nightfall reached at Turn {gs.current_turn} (Limit: {gs.current_objective.nightfall_turn}). Game Over.", level="GAME_END")
            gs.game_over = True
            gs.win_status = "LOSS_NIGHTFALL"
            return True
        
        # TODO: Add other loss conditions if any (e.g., deck out if objective specifies, specific card effects)

        return False # Game continues

    def _check_win_condition(self, win_con: Optional['ObjectiveLogicComponent'], status_on_win: str) -> bool:
        """
        Checks a single win condition component.
        """
        gs = self.game_state
        if not win_con:
            return False

        component_type = win_con.component_type
        params = win_con.params
        condition_met = False

        gs.add_log_entry(f"Checking win condition: {component_type} with params {params}", level="DEBUG")

        # Implement logic for different component_types based on your objectives.json examples
        if component_type == "PLAY_X_DIFFERENT_TOYS_AND_CREATE_Y_SPIRITS":
            # Needs GameState.objective_progress to track:
            # 'distinct_toys_played_ids': set()
            # 'spirits_created_total_game': int
            toys_needed = params.get("toys_needed", 0)
            spirits_needed = params.get("spirits_needed", 0)
            
            # Ensure objective_progress has these keys, initialized by game_setup or updated by game logic
            distinct_toys_played_count = len(gs.objective_progress.get("distinct_toys_played_ids", set()))
            total_spirits_created = gs.objective_progress.get("spirits_created_total_game", 0)
            
            gs.add_log_entry(f"  PLAY_X_DIFFERENT_TOYS_AND_CREATE_Y_SPIRITS check: Played {distinct_toys_played_count}/{toys_needed} distinct toys, Created {total_spirits_created}/{spirits_needed} spirits.", level="DEBUG")
            if distinct_toys_played_count >= toys_needed and total_spirits_created >= spirits_needed:
                condition_met = True

        elif component_type == "GENERATE_X_MANA_FROM_CARD_EFFECTS":
            # Needs GameState.objective_progress to track:
            # 'mana_from_card_effects_total_game': int
            mana_needed = params.get("mana_needed", 0)
            total_mana_from_effects = gs.objective_progress.get("mana_from_card_effects_total_game", 0)
            
            gs.add_log_entry(f"  GENERATE_X_MANA_FROM_CARD_EFFECTS check: Generated {total_mana_from_effects}/{mana_needed} mana from effects.", level="DEBUG")
            if total_mana_from_effects >= mana_needed:
                condition_met = True
        
        elif component_type == "CAST_SPELL_WITH_STORM_COUNT":
            # This is more complex as it's an event, not just a state.
            # GameState.objective_progress would need a flag set by EffectEngine/ActionResolver
            # when this specific event (casting the spell with sufficient storm) occurs.
            # e.g., gs.objective_progress.get("FLUFFSTORM_CAST_WITH_STORM_5_PLUS", False)
            spell_id_or_name = params.get("spell_card_id_or_name") # e.g. "TCSPL_FLUFFSTORM_PLACEHOLDER"
            min_storm = params.get("min_storm_count")
            min_spirits = params.get("min_spirits_to_create_by_spell") # This part is harder to generically check here, effect should confirm
            
            # Example: a flag set when the specific spell resolves with enough storm
            # This flag would be set by the EffectEngine when Fluffstorm's ON_PLAY effect resolves.
            # Let's assume a structure like: objective_progress["CAST_SPELL_EVENT_MET"][spell_id_or_name] = True
            event_key = f"CAST_SPELL_EVENT_MET_{spell_id_or_name}_STORM_{min_storm}"
            if gs.objective_progress.get(event_key, False):
                gs.add_log_entry(f"  CAST_SPELL_WITH_STORM_COUNT check: Event for {spell_id_or_name} with storm >={min_storm} MET.", level="DEBUG")
                condition_met = True
            else:
                gs.add_log_entry(f"  CAST_SPELL_WITH_STORM_COUNT check: Event for {spell_id_or_name} with storm >={min_storm} NOT YET MET.", level="DEBUG")


        elif component_type == "CREATE_TOTAL_X_SPIRITS_GAME":
            # Needs GameState.objective_progress to track:
            # 'spirits_created_total_game': int (same as above)
            spirits_needed = params.get("spirits_needed", 0)
            total_spirits_created = gs.objective_progress.get("spirits_created_total_game", 0)

            gs.add_log_entry(f"  CREATE_TOTAL_X_SPIRITS_GAME check: Created {total_spirits_created}/{spirits_needed} total spirits.", level="DEBUG")
            if total_spirits_created >= spirits_needed:
                condition_met = True
        
        # Add more win condition handlers here for other component_types (Phase 4)
        else:
            gs.add_log_entry(f"Win condition type '{component_type}' not yet implemented in WinLossChecker.", level="WARNING")


        if condition_met:
            gs.add_log_entry(f"Objective Win Condition Met: {win_con.description or component_type}! Status: {status_on_win}", level="GAME_END")
            gs.game_over = True
            gs.win_status = status_on_win
            return True
            
        return False

if __name__ == '__main__':
    print("WinLossChecker module: Checks for game end conditions based on objectives.")
    # Testing this module requires a fully set up GameState.