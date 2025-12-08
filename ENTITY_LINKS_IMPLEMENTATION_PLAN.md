# Clickable Entity Links + Player Knowledge System
## Implementation Plan

## Current State Analysis

### ✅ What Already Exists
1. **NPC Highlighting System**
   - `NPCMentionHighlighter.jsx` component that parses `[[npc_name]]` markup
   - Renders NPCs as clickable badges (purple for primary, gray for secondary)
   - `onNPCClick` handler that sets `selectedNpc` state
   - Currently shows a simple banner when NPC is selected

2. **Data Structure**
   - `npcMentions` array in narration responses: `{id, name, role}`
   - Message model includes `npcMentions` field

### ❌ What's Missing
1. **No Knowledge/Notebook System**
   - No database collection for player-known facts
   - No API to query what player knows about entities
   - No profile/info panel UI

2. **Limited Entity Types**
   - Only NPCs are highlighted
   - No support for locations, factions, items

3. **No Persistence**
   - No tracking of when entities are first revealed
   - No storage of player notes

---

## Phase 1: Knowledge System Foundation (Backend)

### 1.1 Database Schema

**New Collection: `knowledge_facts`**
```json
{
  "_id": "ObjectId",
  "campaign_id": "uuid",
  "character_id": "uuid",  // Optional: per-character knowledge
  "entity_type": "npc|location|faction|item",
  "entity_id": "string",
  "entity_name": "string",
  "fact_type": "introduction|interaction|description|quest_related|membership",
  "fact_text": "What the player learned",
  "revealed_at": "datetime",
  "source": "narration|player_note",
  "metadata": {}  // Additional context
}
```

**New Collection: `player_notes`**
```json
{
  "_id": "ObjectId",
  "campaign_id": "uuid",
  "character_id": "uuid",
  "entity_type": "npc|location|faction|item",
  "entity_id": "string",
  "note_text": "Player's personal note",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### 1.2 Backend Models

**File: `/app/backend/models/knowledge_models.py`**
```python
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime

class KnowledgeFact(BaseModel):
    campaign_id: str
    character_id: Optional[str] = None
    entity_type: Literal["npc", "location", "faction", "item"]
    entity_id: str
    entity_name: str
    fact_type: Literal["introduction", "interaction", "description", "quest_related", "membership"]
    fact_text: str
    revealed_at: datetime = Field(default_factory=datetime.utcnow)
    source: Literal["narration", "player_note"] = "narration"
    metadata: dict = {}

class PlayerNote(BaseModel):
    campaign_id: str
    character_id: Optional[str] = None
    entity_type: Literal["npc", "location", "faction", "item"]
    entity_id: str
    note_text: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class EntityProfile(BaseModel):
    """Player-facing entity profile built from knowledge facts"""
    entity_type: str
    entity_id: str
    name: str
    known_summary: str  # Concatenated facts
    first_seen: datetime
    important_interactions: List[str] = []
    quest_items_given: List[str] = []
    membership_info: List[str] = []
    player_notes: List[str] = []
    total_facts: int = 0
```

### 1.3 API Endpoints

**File: `/app/backend/routers/knowledge.py`**

```python
from fastapi import APIRouter, Query
from models.knowledge_models import KnowledgeFact, PlayerNote, EntityProfile

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])

@router.get("/entity-profile/{entity_type}/{entity_id}")
async def get_entity_profile(
    entity_type: str,
    entity_id: str,
    campaign_id: str = Query(...),
    character_id: Optional[str] = Query(None)
) -> EntityProfile:
    """
    Get player-known profile for an entity.
    ONLY returns information from KnowledgeFacts and PlayerNotes.
    """
    pass

@router.post("/facts")
async def create_knowledge_fact(fact: KnowledgeFact):
    """Record a new fact the player learned"""
    pass

@router.get("/facts")
async def get_knowledge_facts(
    campaign_id: str = Query(...),
    entity_id: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None)
):
    """Get all knowledge facts for a campaign"""
    pass

@router.post("/notes")
async def create_player_note(note: PlayerNote):
    """Player adds a personal note about an entity"""
    pass

@router.put("/notes/{note_id}")
async def update_player_note(note_id: str, note_text: str):
    """Update a player note"""
    pass
```

---

## Phase 2: Enhanced Entity Markup (Backend)

### 2.1 Extend Narration Response

**Current**: `npcMentions: [{id, name, role}]`

**Enhanced**: 
```json
{
  "narration": "You meet [[npc:eldric]]Eldric the Whisper[[/npc]] at [[loc:tavern]]The Rusty Anchor[[/loc]].",
  "entity_mentions": [
    {
      "type": "npc",
      "id": "npc_eldric_001",
      "name": "Eldric the Whisper",
      "role": "primary",
      "first_mention": true
    },
    {
      "type": "location",
      "id": "loc_rusty_anchor",
      "name": "The Rusty Anchor",
      "first_mention": false
    }
  ]
}
```

### 2.2 Auto-Create Knowledge Facts

When narration mentions an entity:
1. Check if KnowledgeFact exists for this entity + campaign
2. If `first_mention: true`, create introduction fact
3. Add interaction/description facts based on narration context

---

## Phase 3: Frontend Entity Link Component

### 3.1 Generic Entity Link Component

**File: `/app/frontend/src/components/EntityLink.jsx`**

```jsx
import React from 'react';
import { Badge } from './ui/badge';

const ENTITY_STYLES = {
  npc: {
    color: 'text-orange-400',
    border: 'border-orange-400/50',
    hover: 'hover:bg-orange-600/20',
    glow: 'hover:shadow-orange-400/50'
  },
  location: {
    color: 'text-blue-400',
    border: 'border-blue-400/50',
    hover: 'hover:bg-blue-600/20',
    glow: 'hover:shadow-blue-400/50'
  },
  faction: {
    color: 'text-purple-400',
    border: 'border-purple-400/50',
    hover: 'hover:bg-purple-600/20',
    glow: 'hover:shadow-purple-400/50'
  },
  item: {
    color: 'text-green-400',
    border: 'border-green-400/50',
    hover: 'hover:bg-green-600/20',
    glow: 'hover:shadow-green-400/50'
  }
};

export const EntityLink = ({ 
  entityType, 
  entityId, 
  name, 
  onClick,
  children 
}) => {
  const styles = ENTITY_STYLES[entityType] || ENTITY_STYLES.npc;
  
  return (
    <span
      className={`
        ${styles.color} ${styles.border} ${styles.hover}
        cursor-pointer inline-block mx-0.5 px-1.5 py-0.5 rounded
        border-b-2 transition-all duration-200
        hover:shadow-sm ${styles.glow}
      `}
      onClick={() => onClick({ type: entityType, id: entityId, name })}
      title={`View ${entityType}: ${name}`}
    >
      {children || name}
    </span>
  );
};
```

### 3.2 Enhanced Narration Parser

**File: `/app/frontend/src/components/EntityNarrationParser.jsx`**

```jsx
/**
 * Parses entity markup in narration:
 * [[npc:id]]Name[[/npc]]
 * [[loc:id]]Name[[/loc]]
 * [[faction:id]]Name[[/faction]]
 * [[item:id]]Name[[/item]]
 */
export const EntityNarrationParser = ({ 
  text, 
  entityMentions = [], 
  onEntityClick 
}) => {
  const pattern = /\[\[([a-z]+):([^\]]+)\]\]([^\[]+)\[\[\/\1\]\]/g;
  // Parse and render with EntityLink components
  // ...
};
```

---

## Phase 4: Entity Profile Panel UI

### 4.1 Profile Panel Component

**File: `/app/frontend/src/components/EntityProfilePanel.jsx`**

```jsx
import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { X, BookOpen, MessageSquare, Package, Users } from 'lucide-react';
import { apiClient } from '../api/rpgClient';

export const EntityProfilePanel = ({ 
  entity, // {type, id, name}
  campaignId,
  characterId,
  onClose 
}) => {
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    loadProfile();
  }, [entity.id]);
  
  const loadProfile = async () => {
    const response = await apiClient.get(
      `/api/knowledge/entity-profile/${entity.type}/${entity.id}`,
      { params: { campaign_id: campaignId, character_id: characterId }}
    );
    setProfile(response.data);
    setLoading(false);
  };
  
  if (!entity) return null;
  
  return (
    <div className="fixed right-4 top-20 bottom-4 w-96 z-50">
      <Card className="h-full bg-gray-900/95 border-amber-600/30 backdrop-blur-sm flex flex-col">
        <CardHeader className="border-b border-amber-600/20">
          <div className="flex items-center justify-between">
            <CardTitle className="text-amber-400">{entity.name}</CardTitle>
            <Button
              onClick={onClose}
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
          <p className="text-sm text-gray-400 capitalize">{entity.type}</p>
        </CardHeader>
        
        <CardContent className="flex-1 overflow-y-auto p-4">
          {loading ? (
            <div>Loading...</div>
          ) : (
            <Tabs defaultValue="overview" className="w-full">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="overview">
                  <BookOpen className="h-4 w-4" />
                </TabsTrigger>
                <TabsTrigger value="interactions">
                  <MessageSquare className="h-4 w-4" />
                </TabsTrigger>
                <TabsTrigger value="items">
                  <Package className="h-4 w-4" />
                </TabsTrigger>
                <TabsTrigger value="notes">
                  <Users className="h-4 w-4" />
                </TabsTrigger>
              </TabsList>
              
              <TabsContent value="overview">
                <div className="space-y-3">
                  <div>
                    <h4 className="text-sm font-semibold text-amber-400 mb-2">What You Know</h4>
                    <p className="text-sm text-gray-300">{profile.known_summary}</p>
                  </div>
                  <div className="text-xs text-gray-500">
                    First seen: {new Date(profile.first_seen).toLocaleDateString()}
                  </div>
                </div>
              </TabsContent>
              
              {/* Other tabs... */}
            </Tabs>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
```

---

## Phase 5: Integration & Testing

### 5.1 Update AdventureLogWithDM.jsx

```jsx
import { EntityNarrationParser } from './EntityNarrationParser';
import { EntityProfilePanel } from './EntityProfilePanel';

const [selectedEntity, setSelectedEntity] = useState(null);

// In render:
{entry.entity_mentions && entry.entity_mentions.length > 0 ? (
  <EntityNarrationParser
    text={entry.text}
    entityMentions={entry.entity_mentions}
    onEntityClick={(entity) => setSelectedEntity(entity)}
  />
) : (
  formatMessage(entry.text)
)}

{/* Entity Profile Panel */}
{selectedEntity && (
  <EntityProfilePanel
    entity={selectedEntity}
    campaignId={campaignId}
    characterId={characterState?.id}
    onClose={() => setSelectedEntity(null)}
  />
)}
```

### 5.2 Knowledge Guard Checks

```python
def get_entity_profile(entity_type, entity_id, campaign_id, character_id):
    """
    CRITICAL: Only return player-known information.
    Do NOT query world_npcs, world_locations, etc. directly.
    ONLY aggregate from knowledge_facts and player_notes.
    """
    facts = db.knowledge_facts.find({
        "campaign_id": campaign_id,
        "entity_id": entity_id,
        "entity_type": entity_type
    })
    
    # Build profile ONLY from facts
    # NO access to world entity collections
```

---

## Implementation Order

1. **Backend Models** (1 hr)
   - Create `knowledge_models.py`
   - Add MongoDB indexes

2. **Backend API** (2 hrs)
   - Create `/api/knowledge` router
   - Implement profile endpoint with guard

3. **Frontend EntityLink** (1 hr)
   - Generic component
   - Enhanced parser

4. **Frontend Profile Panel** (2 hrs)
   - UI with tabs
   - API integration

5. **Integration** (1 hr)
   - Update AdventureLogWithDM
   - Test with existing [[npc:name]] markup

6. **Auto-Fact Creation** (1 hr)
   - Modify narration endpoint
   - Create facts on first mention

7. **Testing** (1 hr)
   - Manual test all entity types
   - Verify no data leaks

**Total: ~9 hours**

---

## Success Metrics

✅ Orange clickable links appear for all entity types
✅ Profile panel shows ONLY player-known info
✅ No console errors
✅ Multiple entities in same sentence work
✅ Profile updates as new facts are revealed
✅ Player can add personal notes
✅ Knowledge Guard verification passes

