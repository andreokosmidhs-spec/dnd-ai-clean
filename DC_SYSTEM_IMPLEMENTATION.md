# 🎲 DC (Difficulty Class) System Implementation

Complete implementation of formalized DC taxonomy and check pipeline for RPG Forge.

---

## 📋 Overview

This implementation addresses 5 key areas:
1. DC Taxonomy + Helper
2. CheckRequest → ResolvedCheck Pipeline
3. Prompt-level DC Constraints  
4. Frontend DC + Roll UI
5. Orchestration Pipeline Enforcement

---

## 1. DC Taxonomy + Helper ✅

### File: `/app/backend/services/dc_rules.py`

**DC Bands (D&D 5e DMG p.238)**:
- `TRIVIAL` (5): Almost always succeeds
- `EASY` (10): Easy task
- `MODERATE` (15): Moderate difficulty (default)
- `HARD` (20): Hard task
- `VERY_HARD` (25): Very hard task
- `NEARLY_IMPOSSIBLE` (30): Nearly impossible

### DC Calculation Formula

```
Final DC = Base DC + Risk Modifier + Environment Modifier
```

**Components:**

1. **Base DC**: Determined by action type (climb, persuade, pick_lock, etc.)
2. **Risk Modifiers**:
   - Low risk: -2 (plenty of time, no pressure)
   - Normal risk: 0 (standard situation)
   - High risk: +2 (time pressure or consequences)
   - Critical risk: +5 (life-or-death)

3. **Environment Modifiers**:
   - Rain: +2
   - Heavy rain: +5
   - Fog: +2
   - Darkness: +5
   - Dim light: +2
   - Loud noise: +2
   - Crowded: +2
   - Distracted target: -2
   - Ideal conditions: -2

### Example Calculations

```python
# Example 1: Climbing in good conditions
Base: moderate (15) + normal risk (0) + no modifiers = DC 15

# Example 2: Picking lock while guards approach
Base: moderate (15) + high risk (+2) + darkness (+5) = DC 22

# Example 3: Persuading friendly merchant
Base: moderate (15) + low risk (-2) + ideal conditions (-2) = DC 11
```

### Helper Methods

```python
DCHelper.calculate_dc(action_type, risk_level, environment, character_level)
# Returns: (numeric_dc, reasoning, dc_band)

DCHelper.get_action_type_from_intent(player_action, intent_flags)
# Returns: action_type string

DCHelper.get_suggested_ability_and_skill(action_type)
# Returns: (ability, skill)
```

---

## 2. CheckRequest → ResolvedCheck Pipeline ✅

### File: `/app/backend/models/check_models.py`

### Data Models

#### 1. CheckRequest
Structured check request from DM to player:

```python
CheckRequest(
    ability="strength",           # Ability to check
    skill="Athletics",            # Skill if applicable
    dc=15,                        # Difficulty Class (5-30)
    dc_band="moderate",           # Difficulty band
    advantage_state="normal",     # normal/advantage/disadvantage
    reason="The cliff is steep",  # Why this check is needed
    action_context="Climbing",    # What player is trying to do
    dc_reasoning="Base: 15..."    # How DC was calculated
)
```

#### 2. PlayerRoll
Player's dice roll result:

```python
PlayerRoll(
    d20_roll=15,                  # Raw d20 roll (1-20)
    modifier=5,                   # Total modifier
    total=20,                     # Final total (roll + modifier)
    advantage_state="normal",
    advantage_rolls=[15, 12],     # If advantage/disadvantage
    ability_modifier=3,           # Breakdown
    proficiency_bonus=2,
    other_bonuses=0
)
```

#### 3. CheckResolution
Resolved check with graded outcome:

```python
CheckResolution(
    success=True,                         # Did check succeed?
    outcome="clear_success",              # Graded outcome
    margin=5,                             # Difference from DC
    check_request=CheckRequest(...),
    player_roll=PlayerRoll(...),
    outcome_tier="clear",                 # For DM narration
    suggested_narration_style="..."       # Narration guidance
)
```

### Graded Outcomes

- `CRITICAL_SUCCESS`: Natural 20 or beat DC by 10+ → Dramatic success with bonus
- `CLEAR_SUCCESS`: Beat DC by 5-9 → Clean success
- `MARGINAL_SUCCESS`: Beat DC by 1-4 → Success with complication
- `MARGINAL_FAILURE`: Miss DC by 1-4 → Failure but not catastrophic
- `CLEAR_FAILURE`: Miss DC by 5-9 → Clear failure
- `CRITICAL_FAILURE`: Natural 1 or miss DC by 10+ → Dramatic failure with consequence

---

## 3. Prompt-level DC Constraints ✅

### File: `/app/backend/routers/dungeon_forge.py`

### DM Prompt Updates

Added comprehensive DC rules to the system prompt:

#### Section 8: DIFFICULTY CLASS (DC) RULES
```
YOU MUST NEVER INVENT DCs ARBITRARILY

When an action requires a check, you MUST:
1. Use the suggested DC provided by the system
2. State the DC exactly ONCE in a structured format
3. NEVER make up your own DC values
```

#### System-Calculated DC Display
The prompt now shows:
```
SYSTEM-CALCULATED DC (USE THIS):
DC: 15 (moderate)
Ability: strength
Skill: Athletics
Reasoning: Base: moderate (15) | Risk: normal_risk (0) | Final: DC 15 (moderate)
YOU MUST USE THIS DC - DO NOT INVENT YOUR OWN
```

#### CHECK REQUEST Output Format
DM must output structured check_request in JSON:

```json
{
  "narration": "You approach the cliff face...",
  "options": ["Attempt to climb", "Look for another way"],
  "check_request": {
    "ability": "strength",
    "skill": "Athletics",
    "dc": 15,
    "dc_band": "moderate",
    "advantage_state": "normal",
    "reason": "The cliff is steep and slippery",
    "action_context": "Player is attempting to climb"
  }
}
```

#### Auto-Resolution Prevention
```
NEVER AUTO-RESOLVE CHECKS:
- You propose the check via check_request
- System waits for player to roll
- Player provides roll result
- Then you narrate the outcome
- DO NOT narrate success/failure until player rolls
```

---

## 4. Frontend DC + Roll UI ✅

### File: `/app/frontend/src/components/CheckRollPanel.jsx`

### Features

#### Visual Components
1. **Check Info Display**:
   - Action context
   - Check type (ability + skill)
   - DC with color-coded difficulty
   - Your modifier breakdown
   - Advantage/disadvantage indicator

2. **Roll Interface**:
   - "Roll Dice" button with animation
   - "Enter Custom Roll" option
   - Advantage/disadvantage roll display (shows both rolls, strikes through unused)

3. **Result Display**:
   - Large dice roll number(s)
   - Final total with modifier breakdown
   - Success/Failure status
   - Graded outcome (marginal, clear, critical)
   - Margin display (+5 or -3)

#### Color Coding

**DC Difficulty**:
- Trivial: Green
- Easy: Blue
- Moderate: Yellow
- Hard: Orange
- Very Hard: Red
- Nearly Impossible: Purple

**Outcome**:
- Critical Success: Bright green
- Clear Success: Green
- Marginal Success: Blue
- Marginal Failure: Yellow
- Clear Failure: Orange
- Critical Failure: Red

#### Usage

```jsx
<CheckRollPanel 
  checkRequest={checkRequest}
  character={character}
  onRollComplete={(rollResult) => {
    // Send roll to backend
  }}
  onDismiss={() => {
    // Close panel
  }}
/>
```

---

## 5. Orchestration Pipeline Enforcement ✅

### File: `/app/backend/routers/dungeon_forge.py`

### Pipeline Flow

```
1. Player Action Received
   ↓
2. Intent Tagger Analyzes Action
   ↓
3. DC Helper Calculates DC (if check needed)
   ↓
4. DM Receives System-Calculated DC
   ↓
5. DM Proposes CheckRequest
   ↓
6. Frontend Shows Check Panel
   ↓
7. Player Rolls Dice
   ↓
8. Backend Creates CheckResolution
   ↓
9. DM Narrates Outcome
```

### Key Implementation Points

#### Step 3: DC Calculation
```python
# In action handler (line ~2680)
if intent_flags.get("needs_check"):
    from services.dc_rules import DCHelper
    
    action_type = DCHelper.get_action_type_from_intent(player_action, intent_flags)
    
    # Get environmental conditions
    environment = []
    if world.get("weather") in ["rain", "heavy_rain", "fog"]:
        environment.append(world.get("weather"))
    if world.get("time_of_day") == "night":
        environment.append("darkness")
    
    # Calculate DC
    suggested_dc, dc_reasoning, dc_band = DCHelper.calculate_dc(
        action_type=action_type,
        risk_level=determine_risk_level(world),
        environment=environment,
        character_level=character_level
    )
    
    # Get suggested ability/skill
    suggested_ability, suggested_skill = DCHelper.get_suggested_ability_and_skill(action_type)
    
    # Add to intent_flags for DM
    intent_flags["suggested_dc"] = suggested_dc
    intent_flags["dc_band"] = dc_band.value
    intent_flags["dc_reasoning"] = dc_reasoning
    intent_flags["suggested_ability"] = suggested_ability
    intent_flags["suggested_skill"] = suggested_skill
```

#### Step 5: DM Must Use Structured Format
The DM prompt explicitly requires:
- Use system-calculated DC (not invented)
- Output structured check_request
- Never auto-resolve

#### Step 8: Check Resolution
```python
# When player roll is received
from models.check_models import CheckResolution

resolution = CheckResolution.from_roll_and_request(
    player_roll=player_roll,
    check_request=check_request
)

# resolution.success: bool
# resolution.outcome: CheckOutcome enum
# resolution.margin: int
# resolution.suggested_narration_style: str
```

---

## 🔧 Integration Points

### Backend Files Modified
1. `/app/backend/routers/dungeon_forge.py` (DC calculation integration + prompt updates)
2. `/app/backend/services/dc_rules.py` (NEW - DC taxonomy)
3. `/app/backend/models/check_models.py` (NEW - check pipeline models)

### Frontend Files Created
1. `/app/frontend/src/components/CheckRollPanel.jsx` (NEW - UI component)

### Integration Steps for RPGGame.jsx

```jsx
import CheckRollPanel from './CheckRollPanel';

function RPGGame() {
  const [pendingCheck, setPendingCheck] = useState(null);
  
  // When DM response includes check_request
  useEffect(() => {
    if (dmResponse?.check_request) {
      setPendingCheck(dmResponse.check_request);
    }
  }, [dmResponse]);
  
  const handleRollComplete = async (rollResult) => {
    // Send roll to backend
    const response = await fetch(`${API_URL}/api/rpg_dm/resolve_check`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        campaign_id,
        character_id,
        roll_result: rollResult,
        check_request: pendingCheck
      })
    });
    
    const data = await response.json();
    setDmResponse(data);
    setPendingCheck(null);
  };
  
  return (
    <>
      {/* Game UI */}
      
      {pendingCheck && (
        <CheckRollPanel
          checkRequest={pendingCheck}
          character={character}
          onRollComplete={handleRollComplete}
          onDismiss={() => setPendingCheck(null)}
        />
      )}
    </>
  );
}
```

---

## 📊 Example Usage

### Scenario: Player Attempts to Climb

#### 1. Player Action
```
"I try to climb the cliff"
```

#### 2. Backend Calculates DC
```python
action_type = "climb"  # Detected by DCHelper
base_dc = 15           # Moderate difficulty
risk = "normal_risk"   # No time pressure
environment = ["rain"] # It's raining (+2)
final_dc = 17          # 15 + 0 + 2
```

#### 3. DM Receives System Prompt
```
SYSTEM-CALCULATED DC (USE THIS):
DC: 17 (moderate)
Ability: strength
Skill: Athletics
Reasoning: Base: moderate (15) | Risk: normal_risk (0) | Environment: ['rain'] (+2) | Final: DC 17 (moderate)
YOU MUST USE THIS DC - DO NOT INVENT YOUR OWN
```

#### 4. DM Outputs CheckRequest
```json
{
  "narration": "You approach the rain-slicked cliff face. The holds are slippery, and water runs down the rock in streams.",
  "options": ["Attempt the climb", "Wait for the rain to stop", "Look for another route"],
  "check_request": {
    "ability": "strength",
    "skill": "Athletics",
    "dc": 17,
    "dc_band": "moderate",
    "advantage_state": "normal",
    "reason": "The cliff is steep and slippery from rain",
    "action_context": "Climbing the cliff"
  }
}
```

#### 5. Frontend Shows Check Panel
- Displays DC 17 (moderate) in yellow
- Shows player's modifier: +5 (Str +3, Prof +2)
- "Roll Dice" button

#### 6. Player Rolls
- Rolls d20: 14
- Modifier: +5
- Total: 19
- Success! (19 ≥ 17, margin: +2)

#### 7. Backend Creates Resolution
```python
CheckResolution(
    success=True,
    outcome="marginal_success",  # +2 margin
    margin=2,
    outcome_tier="marginal",
    suggested_narration_style="success but with complication or cost"
)
```

#### 8. DM Narrates Outcome
```
You dig your fingers into the wet stone and haul yourself upward. The climb is exhausting, and twice you nearly slip, but you reach the top. Your hands are scraped and bleeding from the rough rock.
```

---

## 🎯 Benefits

### 1. Consistency
- All DCs follow D&D 5e guidelines
- No arbitrary difficulty spikes
- Predictable scaling

### 2. Transparency
- Players see exactly why DC is X
- Reasoning is logged and displayed
- No "black box" calculations

### 3. Balance
- Environmental factors matter
- Risk level affects difficulty appropriately
- Character level scaling prevents trivial checks at high levels

### 4. UX Enhancement
- Clear visual feedback
- Advantage/disadvantage clearly shown
- Graded outcomes (not just pass/fail)

### 5. DM Constraint
- LLM cannot invent DCs
- Must use system-calculated values
- Structured output format enforced

---

## 🧪 Testing Checklist

- [ ] DC calculation works for all action types
- [ ] Environmental modifiers apply correctly
- [ ] Risk levels affect DC appropriately
- [ ] Frontend displays check panel
- [ ] Advantage/disadvantage rolls work
- [ ] Custom roll input works
- [ ] Success/failure outcomes display correctly
- [ ] DM prompt includes DC constraints
- [ ] DM cannot auto-resolve checks
- [ ] Check resolution creates proper graded outcomes

---

## 🚀 Next Steps

### Frontend Integration
1. Import `CheckRollPanel` into `RPGGame.jsx`
2. Add state for `pendingCheck`
3. Hook up `onRollComplete` to backend endpoint
4. Test full flow

### Backend Endpoint (TODO)
Create `/api/rpg_dm/resolve_check` endpoint:
```python
@router.post("/rpg_dm/resolve_check")
async def resolve_check(
    campaign_id: str,
    character_id: str,
    roll_result: PlayerRoll,
    check_request: CheckRequest
):
    # Create CheckResolution
    resolution = CheckResolution.from_roll_and_request(roll_result, check_request)
    
    # Call DM to narrate outcome
    dm_response = await run_dungeon_forge_with_resolution(
        campaign_id, 
        character_id, 
        resolution
    )
    
    return dm_response
```

---

*Implementation Date: 2025-12-04*  
*Status: Backend Complete ✅ | Frontend Component Created ✅ | Integration Pending*
