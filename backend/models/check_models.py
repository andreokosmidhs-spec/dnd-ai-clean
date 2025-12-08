"""
Check Request/Resolution Pipeline Models
Formalizes the flow: CheckRequest → PlayerRoll → CheckResolution
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from enum import Enum


class AdvantageType(str, Enum):
    """Advantage/Disadvantage state"""
    NORMAL = "normal"
    ADVANTAGE = "advantage"
    DISADVANTAGE = "disadvantage"


class CheckOutcome(str, Enum):
    """Graded check outcomes"""
    CRITICAL_SUCCESS = "critical_success"  # Natural 20 or beat DC by 10+
    CLEAR_SUCCESS = "clear_success"        # Beat DC by 5-9
    MARGINAL_SUCCESS = "marginal_success"  # Beat DC by 1-4
    MARGINAL_FAILURE = "marginal_failure"  # Miss DC by 1-4
    CLEAR_FAILURE = "clear_failure"        # Miss DC by 5-9
    CRITICAL_FAILURE = "critical_failure"  # Natural 1 or miss DC by 10+


class CheckRequest(BaseModel):
    """
    Structured check request from DM
    Replaces freeform check requests
    """
    ability: str = Field(..., description="Ability to check (strength, dexterity, etc.)")
    skill: Optional[str] = Field(None, description="Skill proficiency if applicable")
    dc: int = Field(..., ge=5, le=30, description="Difficulty Class (5-30)")
    dc_band: str = Field(..., description="Difficulty band (easy, moderate, hard, etc.)")
    advantage_state: AdvantageType = Field(
        AdvantageType.NORMAL, 
        description="Advantage, disadvantage, or normal"
    )
    reason: str = Field(..., description="Why this check is needed (for player)")
    action_context: str = Field(..., description="What the player is trying to do")
    
    # Optional fields for complex checks
    opposed_check: bool = Field(False, description="Is this an opposed check?")
    group_check: bool = Field(False, description="Is this a group check?")
    
    # DC calculation metadata
    dc_reasoning: Optional[str] = Field(None, description="How DC was calculated")
    
    class Config:
        use_enum_values = True


class PlayerRoll(BaseModel):
    """
    Player's dice roll result
    """
    d20_roll: int = Field(..., ge=1, le=20, description="Raw d20 roll (1-20)")
    modifier: int = Field(..., description="Total modifier (ability + proficiency + bonuses)")
    total: int = Field(..., description="Final total (roll + modifier)")
    
    # Advantage/Disadvantage tracking
    advantage_state: AdvantageType = Field(
        AdvantageType.NORMAL,
        description="Was advantage/disadvantage applied?"
    )
    advantage_rolls: Optional[list[int]] = Field(
        None,
        description="Both rolls if advantage/disadvantage"
    )
    
    # Breakdown for UI
    ability_modifier: int = Field(..., description="Ability modifier portion")
    proficiency_bonus: int = Field(0, description="Proficiency bonus if skilled")
    other_bonuses: int = Field(0, description="Other bonuses/penalties")
    
    class Config:
        use_enum_values = True


class CheckResolution(BaseModel):
    """
    Resolved check outcome with graded result
    """
    success: bool = Field(..., description="Did the check succeed?")
    outcome: CheckOutcome = Field(..., description="Graded outcome")
    margin: int = Field(..., description="Difference between total and DC (positive = success)")
    
    # Original data
    check_request: CheckRequest
    player_roll: PlayerRoll
    
    # Narrative hooks for DM
    outcome_tier: Literal["critical", "clear", "marginal"] = Field(
        ..., 
        description="Outcome tier for DM narration guidance"
    )
    suggested_narration_style: str = Field(
        ...,
        description="Guidance for DM on how to narrate this outcome"
    )
    
    class Config:
        use_enum_values = True
    
    @staticmethod
    def from_roll_and_request(
        player_roll: PlayerRoll,
        check_request: CheckRequest
    ) -> "CheckResolution":
        """
        Create CheckResolution from roll and request
        """
        # Calculate margin
        margin = player_roll.total - check_request.dc
        success = margin >= 0
        
        # Determine outcome
        is_nat_20 = player_roll.d20_roll == 20
        is_nat_1 = player_roll.d20_roll == 1
        
        if is_nat_20 or margin >= 10:
            outcome = CheckOutcome.CRITICAL_SUCCESS
            outcome_tier = "critical"
            narration_style = "dramatic success with bonus benefit"
        elif margin >= 5:
            outcome = CheckOutcome.CLEAR_SUCCESS
            outcome_tier = "clear"
            narration_style = "clear success, player achieves goal cleanly"
        elif margin >= 0:
            outcome = CheckOutcome.MARGINAL_SUCCESS
            outcome_tier = "marginal"
            narration_style = "success but with complication or cost"
        elif margin >= -4:
            outcome = CheckOutcome.MARGINAL_FAILURE
            outcome_tier = "marginal"
            narration_style = "failure but not catastrophic, partial information"
        elif margin >= -9:
            outcome = CheckOutcome.CLEAR_FAILURE
            outcome_tier = "clear"
            narration_style = "clear failure, player does not achieve goal"
        else:  # margin <= -10 or nat 1
            outcome = CheckOutcome.CRITICAL_FAILURE
            outcome_tier = "critical"
            narration_style = "dramatic failure with consequence or complication"
        
        # Natural 1 overrides to critical failure
        if is_nat_1:
            outcome = CheckOutcome.CRITICAL_FAILURE
            outcome_tier = "critical"
            narration_style = "dramatic failure with consequence or complication"
        
        return CheckResolution(
            success=success,
            outcome=outcome,
            margin=margin,
            check_request=check_request,
            player_roll=player_roll,
            outcome_tier=outcome_tier,
            suggested_narration_style=narration_style
        )


class CheckRequestBuilder:
    """Helper to build CheckRequest from action context"""
    
    @staticmethod
    def build_from_action(
        action_type: str,
        dc: int,
        dc_band: str,
        dc_reasoning: str,
        player_action: str,
        ability: str,
        skill: Optional[str] = None,
        advantage_state: AdvantageType = AdvantageType.NORMAL,
        reason: Optional[str] = None
    ) -> CheckRequest:
        """
        Build a CheckRequest from action context
        """
        if reason is None:
            reason = f"Check required to {action_type.replace('_', ' ')}"
        
        return CheckRequest(
            ability=ability,
            skill=skill,
            dc=dc,
            dc_band=dc_band,
            advantage_state=advantage_state,
            reason=reason,
            action_context=player_action,
            dc_reasoning=dc_reasoning
        )
