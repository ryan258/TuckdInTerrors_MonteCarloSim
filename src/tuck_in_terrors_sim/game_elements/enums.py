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
    SET_ASIDE = auto() # For cards temporarily out of play (e.g., Dreamcatcher's exiled cards)
    BEING_CAST = auto() # For spells/rituals during resolution before going to discard/play

class TurnPhase(Enum):
    BEGIN_TURN = auto()
    MAIN_PHASE = auto()
    END_TURN = auto()
    GAME_SETUP = auto() # For effects during setup

class ResourceType(Enum):
    MANA = auto()
    SPIRIT = auto() # Spirit Tokens ✦
    MEMORY = auto() # Memory Tokens ❤

class CardSubType(Enum):
    LOOP = auto() # ↻
    HAUNT = auto() # ✦ (often associated with Spirit creation on leaving play)
    REANIMATE = auto() # ⚰️ (interactions with discard pile, bringing things back)
    SACRIFICE = auto() # ✂️ (involving sacrificing cards)
    DICE_ROLL = auto() # 🎲
    NIGHTMARE_INTERACT = auto() # 👁️ (interacting with Nightmare Creep)
    BROWSE_SEARCH = auto() # 🔍 (looking at or searching deck/zones)
    MEMORY_TOKEN_INTERACT = auto() # ❤ (specific interactions with Memory Tokens)

class EffectTriggerType(Enum):
    # Card State/Zone Changes
    ON_PLAY = auto()                            # When this card is played
    ON_LEAVE_PLAY = auto()                      # When this card leaves the play area
    ON_DISCARD_THIS_CARD = auto()               # When this card is discarded from hand
    ON_EXILE_THIS_CARD = auto()                 # When this card is exiled
    ON_SACRIFICE_THIS_CARD = auto()             # When this card is sacrificed
    ON_ENTER_PLAY_FROM_DISCARD = auto()         # When this card specifically enters play from discard
    BEFORE_THIS_CARD_MOVES_ZONES = auto()       # Replacement effect trigger for this card changing zones
    BEFORE_THIS_CARD_LEAVES_PLAY = auto()       # Replacement effect trigger before this card leaves play

    # Player Actions / Game Events
    ACTIVATED_ABILITY = auto()                  # Manually activated by player (cost may apply)
    TAP_ABILITY = auto()                        # Activated ability that inherently includes tapping this card
    UNTAP_THIS_CARD = auto()                    # When this card untaps
    WHEN_CARD_DRAWN = auto()                    # When any card is drawn by the player
    WHEN_NIGHTMARE_CREEP_APPLIES_TO_PLAYER = auto() # When NC objectives's general turn check passes
    ON_NIGHTMARE_CREEP_RESOLUTION_FOR_TURN = auto() # After a specific NC effect for the turn is resolved (used by NC effect logic itself)
    WHEN_OTHER_CARD_ENTERS_PLAY = auto()        # When another card enters play
    WHEN_OTHER_CARD_LEAVES_PLAY = auto()        # When another card leaves play
    WHEN_SPIRIT_CREATED = auto()                # When a Spirit token is created
    WHEN_MEMORY_TOKEN_CREATED = auto()          # When a Memory token is created
    WHEN_CARD_PLAYED_FROM_DISCARD_PILE = auto() # When a card is played from discard
    WHEN_CARD_PLAYED_FROM_EXILE = auto()        # When a card is played from exile
    WHEN_YOU_SACRIFICE_TOY = auto()             # When player sacrifices a Toy
    WHEN_COUNTER_REACHES_THRESHOLD = auto()     # E.g., Feeding Chair auto-sacrifices
    WHEN_PROTECTED_TOY_WOULD_LEAVE_PLAY = auto() # Specific event for Beloved Friend
    WHEN_CARD_EXILED_FROM_HAND = auto()         # When a card is exiled from hand

    # Turn Structure
    BEGIN_PLAYER_TURN = auto()
    BEGIN_PLAYER_TURN_EVERY_OTHER = auto()      # Special for Memory Loop of Scratched Records
    END_PLAYER_TURN = auto()
    ON_PLAY_AND_BEGIN_PLAYER_TURN = auto()      # Compound, likely handled by two effects in JSON

    # Continuous / State-Based (Engine needs to manage these)
    CONTINUOUS_WHILE_TAPPED = auto()            # For passive effects while tapped (e.g. Shadow Puppet)
    CONTINUOUS_WHILE_IN_PLAY = auto()           # General continuous effect

class EffectConditionType(Enum):
    # Card Properties / State
    IS_FIRST_MEMORY = auto()                    # Checks if the source card of the effect is the First Memory
    IS_FIRST_MEMORY_IN_PLAY = auto()
    IS_FIRST_MEMORY_IN_DISCARD = auto()
    REANIMATED_TOY_IS_FIRST_MEMORY = auto()     # Specific check for reanimation target
    THIS_CARD_IS_TAPPED = auto()                # Checks if the source card instance is tapped
    HAS_COUNTER_TYPE_VALUE_GE = auto()          # Card has >= X of a counter type (e.g. Feeding Chair)
    CARD_HAS_BEEN_IN_PLAY_FOR_X_TURNS_GE = auto() # Card has been in play for X or more turns

    # Player / Game State
    PLAYER_HAS_RESOURCE = auto()                # Player has X amount of Mana, Spirits, Memory
    DECK_SIZE_LE = auto()                       # Player's deck has X or fewer cards
    NIGHTMARE_CREEP_LEVEL_IS = auto()           # Current NC level/turn implies certain state
    NIGHTMARE_CREEP_IS_ACTIVE = auto()          # Has NC started affecting the game?
    CURRENT_TURN_IS = auto()                    # Current game turn is X / >=X / <=X

    # Event-Based Conditions (contextual, checked when an event triggers an effect)
    EVENT_CARD_IS_TYPE = auto()                 # Card involved in trigger is of specific CardType (e.g. another Toy left play)
    EVENT_CARD_IS_FM = auto()                   # Card involved in trigger is the First Memory
    EVENT_SOURCE_IS_SELF = auto()               # Helps differentiate self-triggers vs "other card" triggers
    IS_MOVING_FROM_ZONE = auto()                # Card is moving from a specific zone
    IS_MOVING_TO_ZONE = auto()                  # Card is moving to a specific zone
    CHOICE_WAS_MADE_IN_EVENT = auto()           # Check if a specific player choice was made as part of the trigger or cost

class EffectActionType(Enum):
    # Basic Resource & Card Manipulation
    DRAW_CARDS = auto()
    ADD_MANA = auto()
    CREATE_SPIRIT_TOKENS = auto()
    CREATE_MEMORY_TOKENS = auto()
    PLACE_COUNTER_ON_CARD = auto()
    REMOVE_COUNTER_FROM_CARD = auto()
    MILL_DECK = auto()

    # Card Movement & Zone Changes
    RETURN_CARD_FROM_ZONE_TO_ZONE = auto()      # Generic: needs params for card, from_zone, to_zone
    RETURN_THIS_CARD_TO_HAND = auto()
    EXILE_CARD_FROM_ZONE = auto()               # Generic: needs params for card/filter, from_zone
    SACRIFICE_CARD_IN_PLAY = auto()             # Generic: needs params for card/filter to sacrifice
    DISCARD_CARDS_RANDOM_FROM_HAND = auto()
    DISCARD_CARDS_CHOSEN_FROM_HAND = auto()     # Links to PLAYER_CHOICE
    REANIMATE_CARD = auto()                     # Specific: Play card from discard, params for modifiers
    PLAY_CARD_NO_COST = auto()                  # Play a specific card (usually from hand/search) for free
    PLAY_RANDOM_CARD_FROM_SET_ASIDE = auto()    # For Dreamcatcher
    CANCEL_IMPENDING_MOVE = auto()              # Stop a card from moving zones (replacement effect part)
    CANCEL_IMPENDING_LEAVE_PLAY = auto()        # Stop a card from leaving play

    # Searches & Deck Interaction
    BROWSE_DECK = auto()                        # Look at top X cards, reorder/put bottom (params define specifics)
    SEARCH_DECK = auto()                        # Search deck for card(s) matching filter (params define what happens - to hand, play, top)

    # Game State & Turn Structure
    TAKE_EXTRA_TURN = auto()
    ADVANCE_NIGHTMARE_CREEP_TRACK = auto()      # Manually progress NC (e.g., Memory Loop)
    SKIP_NIGHTMARE_CREEP_EFFECTS = auto()       # Skip next X NC effects
    DELAY_NIGHTMARE_CREEP_TURNS = auto()        # NC doesn't apply for X turns
    CANCEL_NIGHTMARE_CREEP_EFFECT = auto()      # Cancel a currently resolving/imminent NC effect
    MODIFY_NEXT_NIGHTMARE_CREEP_EFFECT = auto() # Change what the next NC effect does
    INCREASE_CARD_COSTS_IN_HAND = auto()        # For NC effect

    # Complex / Meta Actions
    PLAYER_CHOICE = auto()                      # Triggers a player decision (params define choice type and outcomes)
    CONDITIONAL_EFFECT = auto()                 # Executes sub-actions based on a condition (meta-action or engine logic)
    APPLY_TEMPORARY_EFFECT_PLAYER = auto()      # Grants player a temporary triggered/static ability (e.g. Nightlight Glimmer)
    ADD_REPLACEMENT_EFFECT = auto()             # Adds a temporary replacement effect to the game
    GRANT_TEMPORARY_ABILITY_TO_CARDS = auto()   # E.g. Midnight Animator makes toys tappable for spirits
    EMPOWER_TOKENS = auto()                     # E.g. Fluffstorm gives first spirit an ability
    CONVERT_RESOURCES = auto()                  # E.g. Laughter Preserved in Amber (Memory to Spirits + Draw)
    TRANSFORM_CARD = auto()                     # E.g. Last Goodbye (Toy to Spirits + other effects)
    ROLL_DICE_AND_APPLY_MAPPED_EFFECT = auto()  # For complex dice roll cards, maps results to actions

    # Specific Named Actions from Cards (Consider if they can be generalized over time)
    SACRIFICE_RANDOM_CARD = auto()              # E.g. Midnight Animator outcome (could be SACRIFICE_CARD_IN_PLAY with random target)
    SACRIFICE_RESOURCE = auto()                 # E.g. Nightmare Creep makes player sacrifice a Spirit token

class EffectActivationCostType(Enum):
    PAY_MANA = auto()
    PAY_SPIRIT_TOKENS = auto()
    PAY_MEMORY_TOKENS = auto()
    TAP_THIS_CARD = auto()                      # Cost is to tap the card with the ability
    TAP_OTHER_CARD = auto()                     # Cost is to tap another specified card
    SACRIFICE_THIS_CARD = auto()                # Cost is to sacrifice the card with the ability
    SACRIFICE_FROM_PLAY = auto()                # Cost is to sacrifice other card(s) from play (params specify filter)
    DISCARD_FROM_HAND = auto()                  # Cost is to discard card(s) from hand (params specify filter/count)
    EXILE_FROM_HAND = auto()
    EXILE_FROM_DISCARD = auto()
    CHOOSE_AND_PAY_COST = auto()                # If the cost itself is a choice (e.g. "Pay X or Discard Y")

class PlayerChoiceType(Enum):
    # General Choices
    CHOOSE_YES_NO = auto()
    CHOOSE_NUMBER_FROM_RANGE = auto()
    CHOOSE_MODAL_EFFECT = auto()                # Player chooses between 2+ effect options on a card

    # Card Choices
    CHOOSE_CARD_FROM_HAND = auto()
    CHOOSE_CARD_FROM_DISCARD = auto()
    CHOOSE_CARD_IN_PLAY = auto()                # General choice of a card in play
    CHOOSE_TARGET_CARD_IN_PLAY = auto()         # For effects that need a target

    # Specific Game Action Choices
    DISCARD_CARD_OR_SACRIFICE_SPIRIT = auto()   # Common NC choice
    CHOOSE_TOY_TO_SACRIFICE = auto()
    CHOOSE_TOY_TO_SACRIFICE_OPTIONAL = auto()   # Option to not sacrifice if "may"
    CHOOSE_YES_NO_PAY_COST = auto()             # Yes/No choice that also involves paying a cost if "Yes"
    CHOOSE_CARD_FROM_ZONE_FILTERED = auto()     # Generic, params: zone, card_filter, purpose_text