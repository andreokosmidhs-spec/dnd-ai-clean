# Quest Detail UI Implementation Report

**Date:** 2025-01-XX  
**Status:** Completed  
**Purpose:** Document the implementation of Quest Detail Modal UI for the Campaign Log system

---

## Overview

This implementation adds a comprehensive Quest Detail UI to the PHANERON D&D app's Campaign Log system. When players view their Quests tab in the Campaign Log, they can now click "View Details" on any quest to see a full-screen modal with complete quest information, including objectives, rewards, origin information, and related entities.

---

## Changes Made

### 1. Backend Updates

#### Modified Files:
- `/app/backend/models/log_models.py`
- `/app/backend/services/campaign_log_service.py`

#### Changes:

**A. Added `source_lead_id` Field to QuestKnowledge Model**

Added a new optional field to track which Lead (quest hook) a quest originated from:

```python
class QuestKnowledge(BaseModel):
    # ... existing fields ...
    
    # Origin / Source
    source_lead_id: Optional[str] = None  # Lead that was converted to this quest (if any)
    
    # ... rest of fields ...
```

**B. Updated QuestDelta Model**

Added `source_lead_id` to the delta model for proper merging:

```python
class QuestDelta(BaseModel):
    # ... existing fields ...
    source_lead_id: Optional[str] = None
    # ... rest of fields ...
```

**C. Updated Campaign Log Service**

Modified the quest creation and merging logic in `campaign_log_service.py` to handle `source_lead_id`:

- Updated `apply_delta()` method to include `source_lead_id` when creating new quests
- Updated `_merge_quest()` method to merge `source_lead_id` when updating existing quests

**Backward Compatibility:** The `source_lead_id` field is optional, so existing quests without this field will continue to work normally.

---

### 2. Frontend Updates

#### New Files Created:

**A. `/app/frontend/src/hooks/useQuests.js`**

React Query hooks for quest data fetching:

```javascript
- useQuests(campaignId, characterId, status) - Fetch all quests with optional status filter
- useQuest(campaignId, questId, characterId) - Fetch single quest by ID
- useActiveQuests(campaignId, characterId) - Convenience hook for active quests
- useCompletedQuests(campaignId, characterId) - Convenience hook for completed quests
```

Follows the same pattern as `useLeads.js` for consistency.

**B. `/app/frontend/src/components/QuestDetailModal.jsx`**

Full-screen overlay modal component displaying comprehensive quest information:

**Features:**
- Quest title with status badge (Active/Completed/Failed/Rumored)
- Full description with proper formatting
- Motivation section (why the quest matters)
- Objectives list with completion checkboxes
- Promised rewards display
- Origin information:
  - Shows linked Lead details if `source_lead_id` present
  - Shows quest giver NPC if available
  - Displays "Direct quest" if no specific origin
- Related entities with proper icons:
  - Locations (with MapPin icon)
  - NPCs (with Users icon)
  - Factions (with Shield icon)
- Entity name resolution from Campaign Log
- Timestamps (discovered date, last updated)
- Responsive scrollable content area
- Consistent design with existing Campaign Log panels

**Props:**
```javascript
{
  quest: QuestKnowledge,        // Required quest data
  lead: LeadEntry,              // Optional linked lead
  onClose: Function,            // Close handler
  campaignLog: CampaignLog      // For entity name resolution
}
```

#### Modified Files:

**C. `/app/frontend/src/components/CampaignLogPanel.jsx`**

**Changes:**

1. **Added Imports:**
   - `Eye` icon from lucide-react
   - `QuestDetailModal` component

2. **Added State:**
   ```javascript
   const [selectedQuest, setSelectedQuest] = useState(null);
   const [selectedQuestLead, setSelectedQuestLead] = useState(null);
   const [showQuestModal, setShowQuestModal] = useState(false);
   const [fullLog, setFullLog] = useState(null);
   ```

3. **Added Handler Functions:**
   - `handleViewQuestDetails(quest)` - Opens modal, fetches full log and lead data
   - `handleCloseQuestModal()` - Closes modal and clears state

4. **Enhanced Quest Cards:**
   - Limited objectives display to 3 items (with "X more..." indicator)
   - Limited rewards display to 2 items (with "X more..." indicator)
   - Added line-clamp-2 to description for cleaner list view
   - Added "View Details" button with Eye icon

5. **Added Modal Rendering:**
   - Conditionally renders QuestDetailModal when showQuestModal is true
   - Passes quest, lead, and full campaign log as props

---

## How to Use

### For Players:

1. **Open Campaign Log:**
   - In-game, click the Campaign Log button (typically in the adventure screen)

2. **Navigate to Quests Tab:**
   - Click on the "Quests" tab in the Campaign Log panel

3. **View Quest Details:**
   - Click the "View Details" button on any quest card
   - A full-screen modal will appear with complete quest information

4. **Modal Features:**
   - Scroll through all quest details
   - See origin information (if quest came from a Lead)
   - View all objectives with completion status
   - See related locations, NPCs, and factions
   - Click "Close" or "X" to return to quest list

### Quest Information Displayed:

- **Header:**
  - Quest title
  - Status badge (color-coded)

- **Description Section:**
  - Full quest description
  - Motivation (why it matters)

- **Objectives:**
  - Complete list with checkboxes
  - Completed objectives shown with green checkmark
  - Incomplete objectives shown with gray circle

- **Rewards:**
  - All promised rewards listed

- **Origin:**
  - If from a Lead: Shows lead text and status
  - If from NPC: Shows quest giver name
  - If direct: Indicates no specific origin

- **Related Entities:**
  - Locations involved in the quest
  - NPCs related to the quest
  - Factions associated with the quest

- **Timestamps:**
  - When quest was discovered
  - When last updated

---

## Technical Details

### Data Flow:

1. **Quest List View (CampaignLogPanel):**
   ```
   User clicks "View Details"
     ↓
   handleViewQuestDetails(quest) called
     ↓
   Fetch full campaign log (if not cached)
     ↓
   Fetch lead details (if source_lead_id present)
     ↓
   Set modal state and render QuestDetailModal
   ```

2. **Modal Rendering:**
   ```
   QuestDetailModal receives props
     ↓
   Resolves entity IDs to names using campaignLog
     ↓
   Renders structured sections
     ↓
   User clicks Close
     ↓
   handleCloseQuestModal() called
     ↓
   Modal hidden, state cleared
   ```

### API Endpoints Used:

- `GET /api/campaign/log/quests?campaign_id={id}` - List all quests
- `GET /api/campaign/log/quests/{quest_id}?campaign_id={id}` - Get single quest
- `GET /api/campaign/log/leads/{lead_id}?campaign_id={id}` - Get linked lead
- `GET /api/campaign/log/full?campaign_id={id}` - Get full log for entity resolution

### Design Tokens Used:

- Colors: orange-400/600 (primary quest theme), green/red/purple for status
- Icons: lucide-react (Scroll, Target, Award, MapPin, Users, Shield, etc.)
- Layout: shadcn/ui Card, Badge, ScrollArea components
- Spacing: Consistent with Campaign Log panel design
- Typography: Proper hierarchy with uppercase section headers

---

## Testing

### Backend Tests:

✅ Quest endpoints return proper data structure  
✅ `source_lead_id` field properly saved and retrieved  
✅ Quest merging logic handles new field correctly  
✅ Backward compatibility maintained (existing quests work without source_lead_id)

### Frontend Tests:

✅ Quest list renders with "View Details" button  
✅ Modal opens when button clicked  
✅ Modal displays all quest information correctly  
✅ Lead details fetched and displayed when source_lead_id present  
✅ Entity names resolved from campaign log  
✅ Modal closes properly  
✅ No console errors or React warnings (except pre-existing ones)

### Edge Cases Handled:

✅ Quest without source_lead_id (shows "Direct quest")  
✅ Quest without quest_giver_npc_id (graceful fallback)  
✅ Empty objectives list (section not shown)  
✅ Empty rewards list (section not shown)  
✅ Missing related entities (empty arrays handled)  
✅ Failed lead fetch (modal still displays without lead info)  
✅ Entity ID that doesn't exist in campaign log (shows ID as fallback)

---

## Future Enhancements

### Potential Improvements:

1. **Quest Progress Indicators:**
   - Add visual progress bar based on completed objectives
   - Show percentage complete

2. **Quest Actions:**
   - "Mark as Priority" button
   - "Abandon Quest" button
   - "Share with Party" button (for multiplayer)

3. **Quest History:**
   - Timeline of quest events
   - Log of objective completions
   - Notes/journal entries per quest

4. **Quest Filtering:**
   - Filter by status (active/completed/failed)
   - Filter by location
   - Filter by faction
   - Search by quest title/description

5. **Quest Map Integration:**
   - Show quest locations on world map
   - Mark quest objectives on map
   - Visual quest route/path

6. **Reward Preview:**
   - Show item tooltips for rewards
   - Preview XP/gold amounts
   - Display reward rarity/quality

7. **Related Quest Chains:**
   - Show prerequisite quests
   - Display follow-up quests
   - Visualize quest dependencies

---

## Known Limitations

1. **Entity Resolution:**
   - Requires full campaign log fetch for name resolution
   - May be slow for large campaign logs (optimization needed)

2. **Real-time Updates:**
   - Modal doesn't auto-refresh if quest updates during viewing
   - User must close and reopen to see changes

3. **Lead Details:**
   - Separate API call needed for lead information
   - Could be optimized with server-side join/populate

4. **No Quest Editing:**
   - Modal is read-only (by design)
   - Quest updates must come through gameplay/DM

---

## Files Reference

### Backend Files:
- `/app/backend/models/log_models.py` - QuestKnowledge, QuestDelta models
- `/app/backend/services/campaign_log_service.py` - Quest merging logic
- `/app/backend/routers/campaign_log.py` - Quest API endpoints (existing)

### Frontend Files:
- `/app/frontend/src/hooks/useQuests.js` - React Query hooks (NEW)
- `/app/frontend/src/components/QuestDetailModal.jsx` - Modal component (NEW)
- `/app/frontend/src/components/CampaignLogPanel.jsx` - Integration point (MODIFIED)

### Documentation:
- `/app/meta/QUEST_UI_IMPLEMENTATION.md` - This document (NEW)
- `/app/meta/SCENE_GENERATION_ARCHITECTURE.md` - Context (existing)
- `/app/meta/MISSIONS_ARCHITECTURE.md` - Quest system context (existing)

---

## Summary

The Quest Detail UI implementation provides players with a comprehensive view of their quests within the Campaign Log system. The modal follows existing design patterns, integrates seamlessly with the Leads system, and maintains backward compatibility with existing quest data.

**Key Achievements:**
- ✅ Full quest detail modal with all information
- ✅ Lead-to-Quest origin tracking via `source_lead_id`
- ✅ Entity name resolution for better UX
- ✅ Consistent design with Campaign Log
- ✅ React Query patterns for data fetching
- ✅ Proper error handling and edge cases
- ✅ No breaking changes to existing code

**Next Steps:**
- Test with actual gameplay to create quests from leads
- Gather user feedback on modal UX
- Consider implementing suggested enhancements
- Optimize entity resolution for large campaign logs

---

**Implementation Complete:** 2025-01-XX  
**Developer Notes:** Implementation focused on read-only quest viewing. Quest creation, modification, and lead-to-quest conversion are handled by existing backend systems. This UI is purely for display and does not modify quest data.
