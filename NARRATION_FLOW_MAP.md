# Narration Flow Map - Dungeon Forge

## Complete Action-to-Narration Pipeline

### User Action Flow

```
User clicks "Look Around" button
    ↓
ActionDock.jsx → onActionSelect('look')
    ↓
FocusedRPG.jsx → handleActionSelect('look')
    ↓
Converts actionId to command text: "I look around carefully"
    ↓
Calls: adventureLogRef.current.sendMessage("I look around carefully")
    ↓
AdventureLogWithDM.jsx → sendPlayerMessage(playerMessage, messageType, checkResult)
    ↓
Creates player message object and adds to messages state
    ↓
Builds action payload using buildActionPayload() from GameStateContext
    ↓
Calls: sendToAPI(actionPayload)
    ↓
Makes fetch() POST to apiEndpoint (/api/rpg_dm/action)
    ↓
Backend processes action and returns response
    ↓
Response contains: {success, data: {narration, options, npc_mentions, world_state_update, ...}}
    ↓
Extracts narration from response.data.narration
    ↓
Creates DM message object with narration
    ↓
Calls: setMessages(prev => [...prev, dmMsg])
    ↓
React re-renders AdventureLogWithDM component
    ↓
Narration appears in Adventure Log UI
```

---

## Current Bug: Component Not Rendering

### Symptoms
1. ✅ Intro narration appears
2. ❌ Actions produce NO narration
3. ❌ Component logs never appear

### Root Cause
Component module loads but function never executes = **React not mounting component**

Possible reasons:
- Browser cache serving old bundle
- Hot reload failure
- React rendering issue

### Fix Strategy
1. Force clean build
2. Clear all caches
3. Verify component actually renders
4. Test with frontend agent

