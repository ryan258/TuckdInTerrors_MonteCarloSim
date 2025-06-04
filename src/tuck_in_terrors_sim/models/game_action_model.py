# src/tuck_in_terrors_sim/models/game_action_model.py
from typing import Dict, Any
from pydantic import BaseModel, Field

class GameAction(BaseModel):
    type: str = Field(..., description="The type of action, e.g., 'PLAY_CARD', 'ACTIVATE_ABILITY', 'PASS_TURN'")
    params: Dict[str, Any] = Field(default_factory=dict, description="Parameters specific to the action type")
    description: str = Field(..., description="Human-readable description of the action")