# AdventureLogWithDM.jsx - Zustand Migration Test Checklist

## ✅ Manual Testing Checklist

### 1. New Game Flow
- [ ] Start a new campaign
- [ ] Character creation completes successfully
- [ ] Cinematic intro plays automatically
- [ ] First DM narration appears
- [ ] Action options are displayed

### 2. Send Action Flow
- [ ] Type a custom action in the input field
- [ ] Action appears in the adventure log
- [ ] DM responds with narration
- [ ] New options or checks appear

### 3. Ability Check Flow
- [ ] DM requests an ability check
- [ ] Check request card displays correctly with:
  - Ability name (e.g., Stealth)
  - DC value
  - Character modifiers
- [ ] Click "Roll" button
- [ ] Dice roll result appears
- [ ] DM continues narration based on outcome

### 4. Combat Flow
- [ ] Trigger combat (e.g., "I attack the goblin")
- [ ] Combat HUD appears showing:
  - Character HP
  - Enemy HP
  - Turn order
- [ ] Take combat actions
- [ ] Combat continues through multiple rounds
- [ ] Combat ends (victory or defeat)
- [ ] Combat HUD disappears

### 5. Defeat Modal
- [ ] Reduce character HP to 0
- [ ] Defeat modal appears showing:
  - Injury count
  - Restored HP
  - XP penalty (if any)
- [ ] Click "Continue Adventure"
- [ ] Modal closes
- [ ] Game continues

### 6. Reload/Persistence Flow
- [ ] Play for a few turns
- [ ] Refresh the browser page
- [ ] Click "Continue Campaign"
- [ ] All messages reload correctly
- [ ] Combat state persists (if in combat)
- [ ] Pending checks persist (if any)
- [ ] Character stats are accurate

### 7. TTS (Text-to-Speech)
- [ ] Enable TTS toggle
- [ ] DM narration auto-generates audio
- [ ] Audio player appears on DM messages
- [ ] Click play on audio player
- [ ] Audio plays correctly
- [ ] Disable TTS toggle
- [ ] New narrations don't auto-generate audio

### 8. Intent Mode Toggle
- [ ] Toggle between "Action", "Say", and "DM?" modes
- [ ] Messages send with correct intent type
- [ ] Player messages display correct badges
- [ ] Keyboard shortcuts work (Alt+A, Alt+S, Alt+D)

## 🔍 What to Look For

### Expected Behaviors
- No console errors related to state management
- Smooth transitions between game states
- All UI elements render correctly
- No flickering or duplicate messages
- Loading states appear/disappear correctly

### State Persistence
- Zustand store persists to localStorage automatically
- Page refresh doesn't lose game progress
- Campaign ID and character ID are preserved
- Combat state survives refresh

### Performance
- No lag when adding messages
- Smooth scrolling in adventure log
- Fast response to user actions

## 🚨 Known Issues to Watch

1. **Background Variant Selector** - Still broken (separate issue)
2. **First Load** - May need to create new character if no campaign exists
3. **Audio Generation** - Requires OPENAI_TTS_KEY in backend/.env

## 📊 Testing Status

- [ ] All flows tested
- [ ] No critical bugs found
- [ ] Ready for production

---

**Migration Date:** ${new Date().toISOString().split('T')[0]}
**Component:** AdventureLogWithDM.jsx
**Store:** useDungeonStore.js (Zustand)
**Status:** Ready for Manual Testing
