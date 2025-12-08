# Intro Card Rendering Fix

## Summary
Fixed the "Adventure Begins" intro card bug where literal escape sequences (`\n\n`) were displaying as text instead of being rendered as proper paragraph breaks.

## Problem
The intro card was displaying:
- Literal `\n\n` characters visible in the UI
- No proper paragraph breaks
- Text appearing as one continuous block with visible escape sequences

Example of broken display:
```
Welcome to the kingdom...\n\nYou stand at the gates...\n\nWhat do you do?
```

## Root Cause
The `formatMessage()` function in `/app/frontend/src/components/AdventureLogWithDM.jsx` was only handling JavaScript string newlines (`\n`) but not literal backslash-n sequences that might come from the backend as string characters (`\\n`).

When the backend sends text with literal escape sequences (stored as `"\\n\\n"` in JSON), JavaScript interprets these as four characters: `\`, `n`, `\`, `n` - not as a newline escape sequence.

## Solution Implemented

### File Modified
`/app/frontend/src/components/AdventureLogWithDM.jsx` - `formatMessage()` function (lines 734-759)

### Before
```javascript
const formatMessage = (message) => {
  if (typeof message !== 'string') return message;
  
  const paragraphs = message.split('\n\n').filter(p => p.trim());
  if (paragraphs.length <= 1) return message;
  
  return paragraphs.map((paragraph, idx) => (
    <p key={idx} className={idx > 0 ? 'mt-3' : ''}>
      {paragraph}
    </p>
  ));
};
```

### After
```javascript
const formatMessage = (message) => {
  if (typeof message !== 'string') return message;
  
  // Handle both actual newlines and literal \n sequences
  // First, replace literal \n\n with actual newlines
  let cleanedMessage = message.replace(/\\n\\n/g, '\n\n').replace(/\\n/g, '\n');
  
  // Split on double newlines to create paragraphs
  const paragraphs = cleanedMessage.split(/\n\s*\n/).filter(p => p.trim());
  
  // If only one paragraph, just return it
  if (paragraphs.length <= 1) return cleanedMessage;
  
  // Return paragraphs with proper spacing
  return paragraphs.map((paragraph, idx) => (
    <p key={idx} className={idx > 0 ? 'mt-3' : ''}>
      {paragraph.split('\n').map((line, lineIdx) => (
        <React.Fragment key={lineIdx}>
          {lineIdx > 0 && <br />}
          {line}
        </React.Fragment>
      ))}
    </p>
  ));
};
```

## What Changed

### 1. Literal Escape Sequence Handling
```javascript
let cleanedMessage = message.replace(/\\n\\n/g, '\n\n').replace(/\\n/g, '\n');
```
- Converts literal `\n\n` (4 chars) → actual double newline
- Converts literal `\n` (2 chars) → actual single newline
- Handles text that comes pre-escaped from the backend

### 2. Improved Paragraph Splitting
```javascript
const paragraphs = cleanedMessage.split(/\n\s*\n/).filter(p => p.trim());
```
- Uses regex to split on double newlines with optional whitespace
- More robust than simple string split

### 3. Single Newline Handling
```javascript
{paragraph.split('\n').map((line, lineIdx) => (
  <React.Fragment key={lineIdx}>
    {lineIdx > 0 && <br />}
    {line}
  </React.Fragment>
))}
```
- Within paragraphs, renders single newlines as `<br />` tags
- Preserves line breaks within paragraphs
- Uses React.Fragment for clean rendering

## Expected Behavior After Fix

### Intro Card Display
✅ Proper paragraph breaks between sections
✅ No visible `\n` or `\n\n` characters
✅ Clean, readable text with appropriate spacing
✅ Line breaks within paragraphs rendered correctly

### Example Rendering
**Before:**
```
Welcome to the kingdom...\n\nYou stand at the gates...\n\nWhat do you do?
```

**After:**
```
Welcome to the kingdom...

You stand at the gates...

What do you do?
```

## Testing Instructions

### Manual Test
1. Start a new game → Generate character
2. View the intro card labeled "🎭 The Adventure Begins"
3. Verify:
   - ✅ No literal `\n` characters visible
   - ✅ Text is broken into proper paragraphs
   - ✅ Spacing between paragraphs is appropriate
   - ✅ No JSON fields visible (requested_check, entities, etc.)

### Comparison with DM Card
The "Dungeon Master" card (normal narration) should display identically to the intro card in terms of formatting and paragraph breaks.

### Test Cases
1. **Intro with multiple paragraphs**: Should display as separate `<p>` tags
2. **Intro with single newlines**: Should display as `<br />` within a paragraph
3. **Intro with double newlines**: Should create new paragraphs
4. **Mixed content**: Should handle both paragraph breaks and line breaks correctly

## Rollback Plan

If this change causes issues:

```javascript
// Revert to original formatMessage function
const formatMessage = (message) => {
  if (typeof message !== 'string') return message;
  
  const paragraphs = message.split('\n\n').filter(p => p.trim());
  if (paragraphs.length <= 1) return message;
  
  return paragraphs.map((paragraph, idx) => (
    <p key={idx} className={idx > 0 ? 'mt-3' : ''}>
      {paragraph}
    </p>
  ));
};
```

Then restart frontend:
```bash
sudo supervisorctl restart frontend
```

## Additional Context

### Why This Bug Occurred
- Backend sends JSON with properly escaped newlines
- JSON parser converts `"\\n"` → `\n` (2 characters: backslash + n)
- Old code only handled actual newline characters, not literal backslash-n
- Result: Text displayed with visible escape sequences

### Why This Fix Works
- Pre-processes text to convert literal escapes to actual newlines
- Handles both cases: proper newlines AND literal backslash-n sequences
- Ensures consistent rendering regardless of how text arrives from backend

### Affected Components
- ✅ Intro card ("The Adventure Begins")
- ✅ Regular DM narration (uses same formatMessage function)
- ✅ Any message with type 'dm' that goes through formatMessage

### Not Affected
- Player messages (different rendering path)
- Error messages (different rendering)
- Check/roll cards (separate components)

## Notes
- The fix is backward compatible - works with both properly formatted and escape-sequence text
- No backend changes required
- No API changes required
- No database changes required
- Frontend-only fix with zero side effects

## Verification

After applying this fix:
1. ✅ Frontend restarted successfully
2. ✅ No console errors
3. ✅ Ready for manual testing

Next steps:
1. Test intro generation with new character
2. Verify paragraph formatting
3. Check that regular DM narration still works correctly
4. Confirm no regression in other message types
