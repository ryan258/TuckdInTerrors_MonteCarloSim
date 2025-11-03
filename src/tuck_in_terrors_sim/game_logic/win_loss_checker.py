# src/tuck_in_terrors_sim/game_logic/win_loss_checker.py
# Functions to check objective completion & Nightfall

from typing import TYPE_CHECKING, Optional
from ..game_elements.enums import Zone

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

        elif component_type == "CONTROL_X_SPIRITS_AT_ONCE":
            # OBJ03: Control 7+ Spirits at once
            spirits_needed = params.get("spirits_needed", 0)
            active_player = gs.get_active_player_state()
            current_spirits = active_player.spirit_tokens if active_player else 0

            gs.add_log_entry(f"  CONTROL_X_SPIRITS_AT_ONCE check: Have {current_spirits}/{spirits_needed} spirits.", level="DEBUG")
            if current_spirits >= spirits_needed:
                condition_met = True

        elif component_type == "CONTROL_X_DIFFERENT_SPIRIT_GENERATING_CARDS_IN_PLAY":
            # OBJ03 alt: Have 3+ different cards that generate Spirits in play
            cards_needed = params.get("cards_needed", 0)
            spirit_generating_cards = gs.objective_progress.get("spirit_generating_cards_in_play", set())

            gs.add_log_entry(f"  CONTROL_X_DIFFERENT_SPIRIT_GENERATING_CARDS_IN_PLAY check: Have {len(spirit_generating_cards)}/{cards_needed} cards.", level="DEBUG")
            if len(spirit_generating_cards) >= cards_needed:
                condition_met = True

        elif component_type == "LOOP_TOY_X_TIMES_IN_TURN":
            # OBJ04: Loop one Toy 5+ times in a single turn
            loops_needed = params.get("toy_loops_needed", 0)
            max_loops_this_turn = gs.objective_progress.get("max_toy_loops_this_turn", 0)

            gs.add_log_entry(f"  LOOP_TOY_X_TIMES_IN_TURN check: Max loops this turn {max_loops_this_turn}/{loops_needed}.", level="DEBUG")
            if max_loops_this_turn >= loops_needed:
                condition_met = True

        elif component_type == "RETURN_X_DIFFERENT_TOYS_FROM_DISCARD_TO_HAND_GAME":
            # OBJ04 alt: Return 6 different Toys from discard to hand during game
            toys_needed = params.get("toys_needed", 0)
            toys_returned = gs.objective_progress.get("different_toys_returned_from_discard", set())

            gs.add_log_entry(f"  RETURN_X_DIFFERENT_TOYS_FROM_DISCARD_TO_HAND_GAME check: Returned {len(toys_returned)}/{toys_needed} toys.", level="DEBUG")
            if len(toys_returned) >= toys_needed:
                condition_met = True

        elif component_type == "REANIMATE_FIRST_MEMORY_X_TIMES":
            # OBJ05: Reanimate your First Memory 3 times
            reanimations_needed = params.get("reanimations_needed", 0)
            fm_reanimations = gs.objective_progress.get("first_memory_reanimations", 0)

            gs.add_log_entry(f"  REANIMATE_FIRST_MEMORY_X_TIMES check: Reanimated FM {fm_reanimations}/{reanimations_needed} times.", level="DEBUG")
            if fm_reanimations >= reanimations_needed:
                condition_met = True

        elif component_type == "REANIMATE_X_DIFFERENT_TOYS_GAME":
            # OBJ05 alt: Reanimate 4 different Toys over the game
            toys_needed = params.get("toys_needed", 0)
            toys_reanimated = gs.objective_progress.get("different_toys_reanimated", set())

            gs.add_log_entry(f"  REANIMATE_X_DIFFERENT_TOYS_GAME check: Reanimated {len(toys_reanimated)}/{toys_needed} different toys.", level="DEBUG")
            if len(toys_reanimated) >= toys_needed:
                condition_met = True

        elif component_type == "CAST_X_DIFFERENT_NON_TOY_SPELLS_IN_TURN":
            # OBJ06: Cast 5 different non-Toy spells in a single turn
            spells_needed = params.get("spells_needed", 0)
            spells_this_turn = gs.objective_progress.get("different_spells_cast_this_turn", set())

            gs.add_log_entry(f"  CAST_X_DIFFERENT_NON_TOY_SPELLS_IN_TURN check: Cast {len(spells_this_turn)}/{spells_needed} spells this turn.", level="DEBUG")
            if len(spells_this_turn) >= spells_needed:
                condition_met = True

        elif component_type == "PLAY_X_DIFFERENT_NON_TOY_SPELLS_GAME":
            # OBJ06 alt: Play 8 different non-Toy spells over the game
            spells_needed = params.get("spells_needed", 0)
            spells_played = gs.objective_progress.get("different_spells_played_game", set())

            gs.add_log_entry(f"  PLAY_X_DIFFERENT_NON_TOY_SPELLS_GAME check: Played {len(spells_played)}/{spells_needed} different spells.", level="DEBUG")
            if len(spells_played) >= spells_needed:
                condition_met = True

        elif component_type == "EMPTY_DECK_WITH_CARDS_IN_PLAY":
            # OBJ07: Empty your deck with 3+ Toys and 2+ Rituals in play
            min_toys = params.get("min_toys_in_play", 0)
            min_rituals = params.get("min_rituals_in_play", 0)

            active_player = gs.get_active_player_state()
            if active_player:
                deck_empty = len(active_player.zones[Zone.DECK]) == 0

                from ..game_elements.enums import CardType
                toys_in_play = sum(1 for card in gs.cards_in_play.values()
                                  if card.definition.type == CardType.TOY
                                  and card.controller_id == active_player.player_id)
                rituals_in_play = sum(1 for card in gs.cards_in_play.values()
                                     if card.definition.type == CardType.RITUAL
                                     and card.controller_id == active_player.player_id)

                gs.add_log_entry(f"  EMPTY_DECK_WITH_CARDS_IN_PLAY check: Deck empty={deck_empty}, Toys={toys_in_play}/{min_toys}, Rituals={rituals_in_play}/{min_rituals}.", level="DEBUG")
                if deck_empty and toys_in_play >= min_toys and rituals_in_play >= min_rituals:
                    condition_met = True

        elif component_type == "SACRIFICE_X_TOYS_GAME":
            # OBJ07 alt: Sacrifice 8+ Toys over the game
            toys_needed = params.get("toys_needed", 0)
            toys_sacrificed = gs.objective_progress.get("toys_sacrificed_game", 0)

            gs.add_log_entry(f"  SACRIFICE_X_TOYS_GAME check: Sacrificed {toys_sacrificed}/{toys_needed} toys.", level="DEBUG")
            if toys_sacrificed >= toys_needed:
                condition_met = True

        elif component_type == "ROLL_TOTAL_X_ON_CARD_AND_HAVE_Y_MEMORY_TOKENS":
            # OBJ08: Roll total of 10+ on specific card AND have 1+ Memory Token
            total_roll_needed = params.get("total_roll_needed", 0)
            memory_tokens_needed = params.get("memory_tokens_needed", 0)

            total_rolls = gs.objective_progress.get("whispering_doll_total_rolls", 0)
            active_player = gs.get_active_player_state()
            memory_tokens = active_player.memory_tokens if active_player else 0

            # Also count spent tokens if configured
            if params.get("memory_tokens_spent_count", False):
                memory_tokens += gs.objective_progress.get("memory_tokens_spent_game", 0)

            gs.add_log_entry(f"  ROLL_TOTAL_X_ON_CARD_AND_HAVE_Y_MEMORY_TOKENS check: Rolls={total_rolls}/{total_roll_needed}, Memory={memory_tokens}/{memory_tokens_needed}.", level="DEBUG")
            if total_rolls >= total_roll_needed and memory_tokens >= memory_tokens_needed:
                condition_met = True

        elif component_type == "PLAY_X_CARDS_FROM_EXILE_GAME":
            # OBJ08 alt: Play 5+ cards from exile during the game
            cards_needed = params.get("cards_needed", 0)
            cards_played = gs.objective_progress.get("cards_played_from_exile", 0)

            gs.add_log_entry(f"  PLAY_X_CARDS_FROM_EXILE_GAME check: Played {cards_played}/{cards_needed} cards from exile.", level="DEBUG")
            if cards_played >= cards_needed:
                condition_met = True

        # Add more win condition handlers here for future objectives
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