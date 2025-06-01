# src/tuck_in_terrors_sim/game_elements/enums.py
from enum import Enum, auto

class CardType(Enum):
    TOY = auto()
    RITUAL = auto()
    SPELL = auto()

class Zone(Enum):
    DECK = auto()
    HAND = auto()
    IN_PLAY = auto()
    DISCARD = auto()
    EXILE = auto()
    SET_ASIDE = auto()

class TurnPhase(Enum):
    BEGIN_TURN = auto()
    MAIN_PHASE = auto()
    END_TURN = auto()

class ResourceType(Enum):
    MANA = auto()
    SPIRIT = auto() # ✦
    MEMORY = auto() # ❤

class CardSubType(Enum):
    LOOP = auto()
    HAUNT = auto()
    REANIMATE = auto()
    SACRIFICE = auto()
    DICE_ROLL = auto()
    NIGHTMARE_INTERACT = auto()
    BROWSE_SEARCH = auto() # Combined for 🔍, specific actions will differentiate
    MEMORY_TOKEN_INTERACT = auto()

class EffectTriggerType(Enum):
    ON_PLAY = auto()                        # When this card itself enters play
    ON_LEAVE_PLAY = auto()                  # When this card leaves play
    ON_DISCARD_THIS_CARD = auto()           # When this card is discarded from hand
    ON_EXILE_THIS_CARD = auto()             # When this card is exiled
    ON_SACRIFICE_THIS_CARD = auto()         # When this specific card is sacrificed
    ON_ENTER_PLAY_FROM_DISCARD = auto()     # For "Toy Cow..." - when this card specifically enters play from discard
    ACTIVATED_ABILITY = auto()              # For player-activated abilities on cards in play
    TAP_ABILITY = auto()                    # A specific kind of activated ability requiring tap
    UNTAP_THIS_CARD = auto()
    BEGIN_PLAYER_TURN = auto()              # At the beginning of the card controller's turn
    END_PLAYER_TURN = auto()                # At the end of the card controller's turn
    WHEN_NIGHTMARE_CREEP_APPLIES_TO_PLAYER = auto() # For card effects reacting to the game's NC event ("Toy Cow...")
    ON_NIGHTMARE_CREEP_RESOLUTION_FOR_TURN = auto() # For the NC effect itself specified in an Objective
    WHEN_OTHER_CARD_ENTERS_PLAY = auto()    # When any other card enters play (can be filtered by type/zone)
    WHEN_OTHER_CARD_LEAVES_PLAY = auto()    # When any other card leaves play
    WHEN_SPIRIT_CREATED = auto()
    WHEN_MEMORY_TOKEN_CREATED = auto()
    WHEN_CARD_DRAWN = auto()
    # ... more specific triggers as game mechanics are implemented

class EffectConditionType(Enum):
    IS_FIRST_MEMORY = auto()                # Is this card the First Memory?
    IS_FIRST_MEMORY_IN_PLAY = auto()        # Is the game's First Memory currently in the IN_PLAY zone?
    IS_FIRST_MEMORY_IN_DISCARD = auto()     # Is the game's First Memory currently in the DISCARD zone?
    PLAYER_HAS_RESOURCE = auto()            # e.g., {type: PLAYER_HAS_RESOURCE, resource: ResourceType.SPIRIT, amount: 3, comparison: 'GE'}
    CARD_IN_ZONE = auto()                   # Generic check for a card (by ID, name, or properties) in a specific zone
    NIGHTMARE_CREEP_LEVEL_IS = auto()       # Check current NC intensity/level
    CURRENT_TURN_IS = auto()                # e.g., {type: CURRENT_TURN_IS, turn: 5, comparison: 'EQ'/'LE'/'GE'}
    REANIMATED_TOY_IS_FIRST_MEMORY = auto() # Contextual: True if the toy just reanimated by an effect was the First Memory
    # ... more conditions

class EffectActionType(Enum):
    DRAW_CARDS = auto()
    ADD_MANA = auto()
    CREATE_SPIRIT_TOKENS = auto()
    CREATE_MEMORY_TOKENS = auto()
    SACRIFICE_CARD_IN_PLAY = auto()         # Player chooses a card in play that meets criteria
    DISCARD_CARDS_RANDOM_FROM_HAND = auto()
    DISCARD_CARDS_CHOSEN_FROM_HAND = auto()
    RETURN_CARD_FROM_ZONE_TO_ZONE = auto()  # Generic movement
    RETURN_THIS_CARD_TO_HAND = auto()       # Specific to the card resolving the effect
    EXILE_CARD_FROM_ZONE = auto()
    SEARCH_DECK_FOR_CARD = auto()           # For specific tutor effects like "Forgotten Storybook"
    BROWSE_DECK = auto()                    # For "Browse X" or "🔍X" effects (look at top X, reorder/put back)
    PLACE_COUNTER_ON_CARD = auto()
    REMOVE_COUNTER_FROM_CARD = auto()
    TAP_CARD_IN_PLAY = auto()
    UNTAP_CARD_IN_PLAY = auto()
    MODIFY_RESOURCE = auto()                # Generic gain/lose for mana, spirits, memory_tokens (player's pool)
    PLAY_CARD_NO_COST = auto()
    TAKE_EXTRA_TURN = auto()
    SKIP_NIGHTMARE_CREEP_TURN = auto()      # Skips the next NC application for the turn
    CANCEL_NIGHTMARE_CREEP_EFFECT = auto()  # Cancels an already triggered NC effect
    DELAY_NIGHTMARE_CREEP_TURNS = auto()    # Postpones NC
    CONVERT_TOKENS = auto()
    TRANSFORM_TOY_TO_SPIRITS = auto()
    MILL_DECK = auto()
    ROLL_DICE = auto()
    PLAYER_CHOICE = auto()                  # Presents a choice to the AI (defined by PlayerChoiceType)
    CHOOSE_AND_REANIMATE_TOY_WITH_FM_BONUS = auto() # For "Recurring Cuddles..."
    # ... more actions

class EffectActivationCostType(Enum):
    PAY_MANA = auto()
    PAY_SPIRIT_TOKENS = auto()
    PAY_MEMORY_TOKENS = auto()
    TAP_THIS_CARD = auto()
    SACRIFICE_THIS_CARD = auto()
    SACRIFICE_FROM_PLAY = auto() # Sacrifice another card from play meeting criteria
    DISCARD_FROM_HAND = auto()
    EXILE_FROM_HAND = auto()
    EXILE_FROM_DISCARD = auto()
    # ... other potential costs to activate an ability

class PlayerChoiceType(Enum):
    CHOOSE_CARD_FROM_HAND = auto()
    CHOOSE_CARD_FROM_DISCARD = auto()
    CHOOSE_CARD_IN_PLAY = auto()            # Player chooses one of their cards in play
    CHOOSE_TARGET_CARD_IN_PLAY = auto()     # Player chooses any card in play (e.g., for an effect that targets)
    CHOOSE_YES_NO = auto()                  # For "may" effects or simple decisions
    CHOOSE_NUMBER_FROM_RANGE = auto()
    DISCARD_CARD_OR_SACRIFICE_SPIRIT = auto() # Specific choice for "The First Night" NC
    # ... more choice types as needed by card/objective effects