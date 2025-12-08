# XP Bar UI Component Architecture
## Minecraft-Style XP Bar for DUNGEON FORGE

**Document Version:** 1.0  
**Date:** November 24, 2025  
**Component Type:** Visual Feedback / Progress Indicator

---

## 1. COMPONENT OVERVIEW

### Purpose
Display character progression in a visually engaging Minecraft-style XP bar that shows:
- Current level (centered number)
- XP progress to next level (segmented fill)
- Smooth animations on XP gain
- Glowing gradient effect

### Visual Reference
**Minecraft XP Bar Characteristics:**
- Horizontal segmented bar (appears as ~20 vertical segments)
- Emerald green gradient fill (#10b981 to #34d399)
- Yellow/gold glow effect on segments
- Centered level number in white text
- Dark border for contrast

---

## 2. COMPONENT SPECIFICATION

### File Location
```
/app/frontend/src/components/
├── ui/
│   └── (existing shadcn components)
└── XPBar.jsx  (NEW)
```

### Component Props
```javascript
XPBar.propTypes = {
  level: PropTypes.number.isRequired,        // Current character level
  currentXp: PropTypes.number.isRequired,    // Current XP count
  xpForNextLevel: PropTypes.number.isRequired, // XP required for next level
  className: PropTypes.string                // Optional additional classes
}
```

### Example Usage
```jsx
<XPBar 
  level={character.level} 
  currentXp={character.experience} 
  xpForNextLevel={calculateXpForLevel(character.level + 1)}
/>
```

---

## 3. VISUAL DESIGN

### Layout Structure
```
┌─────────────────────────────────────────────────────────┐
│ Narration Panel (Purple)                                │
│ "You enter the dark forest..."                          │
└─────────────────────────────────────────────────────────┘
         ▼
┌─────────────────────────────────────────────────────────┐
│ ░░▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░  [  3  ]                    │ ← XP Bar
└─────────────────────────────────────────────────────────┘
         ▼
┌─────────────────────────────────────────────────────────┐
│ [Look Around] [Search] [Inventory] [Character] [More]   │ ← Action Buttons
└─────────────────────────────────────────────────────────┘
```

### Styling Approach

**Container:**
- Full width of narration panel
- Height: 32px
- Margin: 8px 0 (spacing from narration and actions)
- Relative positioning for level number overlay

**Background Bar:**
- Dark gray/black (#1f2937 or #111827)
- Border: 2px solid #374151
- Rounded corners: 4px
- Box shadow for depth

**Progress Fill:**
- Segmented appearance (20 segments using repeating-linear-gradient)
- Gradient: emerald-500 (#10b981) to emerald-400 (#34d399)
- Glow effect: box-shadow with emerald color
- Smooth transition: transition-all duration-500
- Width: percentage based on (currentXp / xpForNextLevel * 100)%

**Level Number:**
- Absolute positioning, centered
- Font: text-xl font-bold
- Color: white with dark text-shadow for readability
- Z-index: 10 (above progress bar)

### TailwindCSS Implementation
```jsx
// Container
className="relative w-full h-8 bg-gray-900 border-2 border-gray-700 rounded overflow-hidden shadow-lg"

// Progress bar
className="absolute inset-0 bg-gradient-to-r from-emerald-500 to-emerald-400 transition-all duration-500 ease-out"
style={{
  width: `${progressPercent}%`,
  boxShadow: '0 0 20px rgba(16, 185, 129, 0.5)',
  backgroundImage: 'repeating-linear-gradient(90deg, transparent, transparent 4%, rgba(0,0,0,0.1) 4%, rgba(0,0,0,0.1) 5%)'
}}

// Level text
className="absolute inset-0 flex items-center justify-center z-10 text-xl font-bold text-white"
style={{ textShadow: '2px 2px 4px rgba(0,0,0,0.8)' }}
```

---

## 4. BEHAVIOR & ANIMATIONS

### Initial Render
- Calculate progress percentage
- Render bar with current XP fill
- Display level number

### XP Change Detection
```javascript
useEffect(() => {
  // Detect XP changes
  // Trigger smooth fill animation
  // Optional: Show +XP floating text
}, [currentXp]);
```

### Animation Timing
- **Fill transition:** 500ms ease-out
- **Glow pulse:** Optional 2s infinite pulse on level up
- **Level number:** Scale-up animation on level change

### Edge Cases
- **XP exceeds threshold:** Fill to 100%, trigger level up visual
- **Level up:** Brief glow flash, then reset bar for next level
- **Zero XP:** Show empty bar with level 1

---

## 5. INTEGRATION POINTS

### FocusedRPG.jsx Modification
**Location:** Between AdventureLogWithDM and ActionDock

**Before:**
```jsx
<AdventureLogWithDM ... />
<ActionDock ... />
```

**After:**
```jsx
<AdventureLogWithDM ... />

{/* XP Bar */}
<div className="w-full max-w-4xl mx-auto px-4 py-2">
  <XPBar 
    level={character?.level || 1}
    currentXp={character?.experience || 0}
    xpForNextLevel={calculateXpForLevel((character?.level || 1) + 1)}
  />
</div>

<ActionDock ... />
```

### Character State Integration
**Source:** character.level, character.experience  
**Update trigger:** When character state updates from API response

### XP Calculation Helper
```javascript
// Helper function to calculate XP threshold for level
const calculateXpForLevel = (level) => {
  // D&D 5e progression: roughly level * 300 XP
  const baseXp = 300;
  return baseXp * level;
};
```

---

## 6. RESPONSIVE DESIGN

### Desktop (≥768px)
- Full width of narration panel (~1024px max)
- Height: 32px
- Visible segments: 20

### Mobile (<768px)
- Full width minus padding
- Height: 28px
- Visible segments: 15 (adjusted for smaller screen)

### Tablet (768px-1024px)
- Full width
- Height: 30px
- Visible segments: 18

---

## 7. ACCESSIBILITY

### Screen Reader Support
```jsx
<div role="progressbar" 
     aria-valuenow={currentXp} 
     aria-valuemin={0} 
     aria-valuemax={xpForNextLevel}
     aria-label={`Level ${level}, ${currentXp} out of ${xpForNextLevel} XP`}>
```

### Visual Contrast
- Text shadow on level number for readability
- High contrast border (gray-700)
- Glow effect not essential for functionality

### Keyboard Navigation
- Not interactive, purely visual feedback
- No focus state needed

---

## 8. PERFORMANCE CONSIDERATIONS

### Optimization
- Memoize progress percentage calculation
- Use CSS transitions instead of JS animations
- Avoid re-renders on unrelated state changes

### Implementation
```javascript
const progressPercent = useMemo(() => {
  return Math.min((currentXp / xpForNextLevel) * 100, 100);
}, [currentXp, xpForNextLevel]);
```

---

## 9. TESTING CHECKLIST

- [ ] XP bar renders at correct location
- [ ] Progress fill matches XP percentage
- [ ] Level number displays correctly
- [ ] Smooth animation on XP change
- [ ] Responsive on mobile, tablet, desktop
- [ ] No visual overlap with narration or actions
- [ ] Glowing effect visible but not distracting
- [ ] Segmented appearance matches Minecraft style

---

## 10. FUTURE ENHANCEMENTS

**Phase 2 (Optional):**
- Floating +XP text on XP gain
- Sound effect on XP gain (subtle chime)
- Particle effect on level up
- Click to view detailed XP breakdown
- Tooltip showing exact XP numbers on hover

---

**Architecture Complete**  
**Next Phase:** UI-Engineer will implement component
