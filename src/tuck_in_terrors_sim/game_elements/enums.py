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
    SET_ASIDE = auto() # For cards temporarily out of play but not in other zones

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
    BROWSE_SEARCH = auto() 
    MEMORY_TOKEN_INTERACT = auto()

class EffectTriggerType(Enum):
    ON_PLAY = auto()
    ON_LEAVE_PLAY = auto() 
    ON_DISCARD_THIS_CARD = auto()      
    ON_EXILE_THIS_CARD = auto()        
    ON_SACRIFICE_THIS_CARD = auto()    
    ON_ENTER_PLAY_FROM_DISCARD = auto()
    ACTIVATED_ABILITY = auto()         
    TAP_ABILITY = auto()               
    UNTAP_THIS_CARD = auto()
    BEGIN_PLAYER_TURN = auto()         
    END_PLAYER_TURN = auto()           
    WHEN_NIGHTMARE_CREEP_APPLIES_TO_PLAYER = auto() 
    ON_NIGHTMARE_CREEP_RESOLUTION_FOR_TURN = auto() 
    WHEN_OTHER_CARD_ENTERS_PLAY = auto()
    WHEN_OTHER_CARD_LEAVES_PLAY = auto()
    WHEN_SPIRIT_CREATED = auto()
    WHEN_MEMORY_TOKEN_CREATED = auto()
    WHEN_CARD_DRAWN = auto()
    BEFORE_THIS_CARD_MOVES_ZONES = auto() # New for Ghost Doll replacement effect
    # ... more specific triggers as game mechanics are implemented

class EffectConditionType(Enum):
    IS_FIRST_MEMORY = auto()            
    IS_FIRST_MEMORY_IN_PLAY = auto()    
    IS_FIRST_MEMORY_IN_DISCARD = auto() 
    PLAYER_HAS_RESOURCE = auto()        
    CARD_IN_ZONE = auto()               
    NIGHTMARE_CREEP_LEVEL_IS = auto()   
    CURRENT_TURN_IS = auto()            
    REANIMATED_TOY_IS_FIRST_MEMORY = auto()
    IS_MOVING_FROM_ZONE = auto()        # New for Ghost Doll
    IS_MOVING_TO_ZONE = auto()          # New for Ghost Doll
    # ... more conditions

class EffectActionType(Enum):
    DRAW_CARDS = auto()
    ADD_MANA = auto()
    CREATE_SPIRIT_TOKENS = auto()
    CREATE_MEMORY_TOKENS = auto()
    SACRIFICE_CARD_IN_PLAY = auto()     
    DISCARD_CARDS_RANDOM_FROM_HAND = auto()
    DISCARD_CARDS_CHOSEN_FROM_HAND = auto()
    RETURN_CARD_FROM_ZONE_TO_ZONE = auto() 
    RETURN_THIS_CARD_TO_HAND = auto()   
    EXILE_CARD_FROM_ZONE = auto()
    SEARCH_DECK_FOR_CARD = auto()       
    BROWSE_DECK = auto()                
    PLACE_COUNTER_ON_CARD = auto()
    REMOVE_COUNTER_FROM_CARD = auto()
    TAP_CARD_IN_PLAY = auto()
    UNTAP_CARD_IN_PLAY = auto()
    MODIFY_RESOURCE = auto()            
    PLAY_CARD_NO_COST = auto()
    TAKE_EXTRA_TURN = auto()
    SKIP_NIGHTMARE_CREEP_TURN = auto()  
    CANCEL_NIGHTMARE_CREEP_EFFECT = auto()
    DELAY_NIGHTMARE_CREEP_TURNS = auto()
    CONVERT_TOKENS = auto()
    TRANSFORM_TOY_TO_SPIRITS = auto()
    MILL_DECK = auto()
    ROLL_DICE = auto()
    PLAYER_CHOICE = auto()              
    CHOOSE_AND_REANIMATE_TOY_WITH_FM_BONUS = auto()
    CANCEL_IMPENDING_MOVE = auto()      # New for Ghost Doll
    # ... more actions

class EffectActivationCostType(Enum):
    PAY_MANA = auto()
    PAY_SPIRIT_TOKENS = auto()
    PAY_MEMORY_TOKENS = auto()
    TAP_THIS_CARD = auto()
    SACRIFICE_THIS_CARD = auto()
    SACRIFICE_FROM_PLAY = auto() 
    DISCARD_FROM_HAND = auto()
    EXILE_FROM_HAND = auto()
    EXILE_FROM_DISCARD = auto()
    
class PlayerChoiceType(Enum):
    CHOOSE_CARD_FROM_HAND = auto()
    CHOOSE_CARD_FROM_DISCARD = auto()
    CHOOSE_CARD_IN_PLAY = auto()        
    CHOOSE_TARGET_CARD_IN_PLAY = auto() 
    CHOOSE_YES_NO = auto()              
    CHOOSE_NUMBER_FROM_RANGE = auto()
    DISCARD_CARD_OR_SACRIFICE_SPIRIT = auto()