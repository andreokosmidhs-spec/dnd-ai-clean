"""
Campaign Log Extractor - Hybrid LLM + Deterministic Extraction
Uses existing entity_mentions for first pass, then LLM for structured delta extraction.
"""
import logging
import json
import re
from typing import Dict, Any, List, Optional
from litellm import acompletion

from models.log_models import CampaignLogDelta, LeadDelta
from utils.entity_mentions import EntityMention

logger = logging.getLogger(__name__)


class CampaignLogExtractor:
    """
    Extracts structured campaign log deltas from narration.
    HYBRID APPROACH:
    1. Deterministic: Uses entity_mentions to detect which entities appear
    2. LLM-powered: Extracts structured details about those entities
    """
    
    def __init__(self, openai_api_key: str):
        self.api_key = openai_api_key
    
    async def extract_from_narration(
        self,
        narration: str,
        entity_mentions: List[EntityMention],
        existing_log_context: Optional[Dict[str, Any]] = None,
        current_location: Optional[str] = None,
        quest_hooks: Optional[List[Dict[str, Any]]] = None,
        scene_id: Optional[str] = None
    ) -> CampaignLogDelta:
        """
        Extract campaign log delta from a scene narration.
        
        Args:
            narration: The DM's narration text
            entity_mentions: Pre-detected entities (from entity_mentions.py)
            existing_log_context: Optional context about what's already known
            current_location: The current location ID
            quest_hooks: Optional list of hooks from scene_generator to convert to leads
            scene_id: Optional scene identifier for lead tracking
        
        Returns:
            CampaignLogDelta with structured updates (including leads from hooks)
        """
        logger.info(f"🔍 Extracting campaign log from narration ({len(narration)} chars, {len(entity_mentions)} entities, {len(quest_hooks or [])} hooks)")
        
        # Convert quest hooks to LeadDeltas
        lead_deltas = []
        if quest_hooks:
            lead_deltas = self._convert_hooks_to_leads(
                quest_hooks,
                current_location,
                scene_id
            )
            logger.info(f"🎣 Converted {len(lead_deltas)} hooks → LeadDeltas")
        
        # Build extraction prompt
        prompt = self._build_extraction_prompt(
            narration,
            entity_mentions,
            existing_log_context,
            current_location
        )
        
        try:
            response = await acompletion(
                model="gpt-4o-mini",  # Fast and cost-effective for extraction
                messages=[
                    {
                        "role": "system",
                        "content": "You are a Campaign Log Extractor. Extract only player-knowable information from D&D narration."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                api_key=self.api_key,
                temperature=0.1  # Low temp for consistent extraction
            )
            
            content = response.choices[0].message.content.strip()
            
            # Remove markdown code blocks if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            delta_json = json.loads(content)
            
            # Validate and create CampaignLogDelta
            delta = CampaignLogDelta(**delta_json)
            
            # Add converted leads from hooks
            delta.leads.extend(lead_deltas)
            
            logger.info(f"✅ Extracted delta: {len(delta.locations)} locs, {len(delta.npcs)} npcs, {len(delta.quests)} quests, {len(delta.leads)} leads")
            
            return delta
            
        except Exception as e:
            logger.error(f"❌ Campaign log extraction failed: {e}")
            # Return delta with leads even on LLM extraction failure
            return CampaignLogDelta(leads=lead_deltas)
    
    def _convert_hooks_to_leads(
        self,
        quest_hooks: List[Dict[str, Any]],
        current_location: Optional[str],
        scene_id: Optional[str]
    ) -> List[LeadDelta]:
        """
        Convert quest hooks from scene_generator into LeadDelta entries.
        
        Args:
            quest_hooks: List of hooks with type, description, source, difficulty
            current_location: Current location ID
            scene_id: Scene identifier
            
        Returns:
            List of LeadDelta objects
        """
        lead_deltas = []
        
        for hook in quest_hooks:
            hook_text = hook.get("description", "")
            hook_type = hook.get("type", "observation")
            hook_source = hook.get("source", "")
            
            # Create stable ID from hook text (slugified)
            lead_id = self._slugify_hook_text(hook_text)
            
            # Extract related entity IDs from source
            related_npcs = []
            related_locations = []
            related_factions = []
            
            if hook_source.startswith("npc:"):
                related_npcs.append(hook_source.split(":", 1)[1])
            elif hook_source.startswith("poi:"):
                related_locations.append(hook_source.split(":", 1)[1])
            elif hook_source.startswith("faction:"):
                related_factions.append(hook_source.split(":", 1)[1])
            
            # Create LeadDelta
            lead_delta = LeadDelta(
                id=lead_id,
                short_text=hook_text,
                location_id=current_location,
                source_scene_id=scene_id,
                source_type=hook_type,
                status="unexplored",
                related_npc_ids=related_npcs,
                related_location_ids=related_locations,
                related_faction_ids=related_factions
            )
            
            lead_deltas.append(lead_delta)
            logger.debug(f"🎣 Created lead: {lead_id} - {hook_text[:50]}...")
        
        return lead_deltas
    
    def _slugify_hook_text(self, text: str) -> str:
        """
        Convert hook text to stable ID.
        Example: "Strange noises near the Old Barracks" -> "lead_strange_noises_near_old_barracks"
        """
        # Take first 6 words max
        words = text.lower().split()[:6]
        # Remove punctuation and special chars
        clean_words = [re.sub(r'[^a-z0-9]', '', w) for w in words]
        # Filter empty strings
        clean_words = [w for w in clean_words if w]
        # Join with underscore
        slug = "_".join(clean_words)
        # Prepend lead_ prefix
        return f"lead_{slug}"
    
    def _build_extraction_prompt(
        self,
        narration: str,
        entity_mentions: List[EntityMention],
        existing_log_context: Optional[Dict[str, Any]],
        current_location: Optional[str]
    ) -> str:
        """Build the LLM prompt for extraction"""
        
        # Format entity mentions for context
        mentioned_entities = []
        for mention in entity_mentions:
            mentioned_entities.append({
                "type": mention["entity_type"],
                "id": mention["entity_id"],
                "name": mention["display_text"]
            })
        
        existing_context_str = ""
        if existing_log_context:
            existing_context_str = f"""
EXISTING KNOWLEDGE (what the party already knows):
{json.dumps(existing_log_context, indent=2)}
"""
        
        prompt = f"""You are a Campaign Log Extractor for a D&D 5e game.

TASK: Extract player-knowable information from this narration scene and output structured deltas.

CRITICAL RULES:
1. ONLY extract information the PLAYER CHARACTER could reasonably know from this scene
2. NO GM secrets, hidden motivations, or spoilers
3. NO speculation beyond what's stated or strongly implied
4. Use the pre-detected entity IDs provided below
5. For locations: extract geography, climate, notable places, architecture, culture
6. For NPCs: extract role, personality, appearance, wants, offers, relationships
7. For factions: extract purpose, symbols, leaders, territory
8. For quests: extract objectives, quest giver, rewards
9. For rumors: extract unconfirmed info the party heard
10. For items: extract appearance, properties (known or suspected)
11. For decisions: track major choices the party made

---
CURRENT LOCATION: {current_location or "Unknown"}

PRE-DETECTED ENTITIES (use these IDs):
{json.dumps(mentioned_entities, indent=2)}

{existing_context_str}

NARRATION:
"{narration}"

---

OUTPUT FORMAT (valid JSON only):
{{
  "locations": [
    {{
      "id": "location_rusty_anchor",
      "name": "The Rusty Anchor",
      "geography": "Coastal tavern",
      "climate": "Salty sea air",
      "notable_places": ["Main hall", "Upstairs rooms"],
      "npcs_met_here": ["npc_gregor"],
      "architecture": "Weathered wood building",
      "culture_notes": "Popular with sailors"
    }}
  ],
  "npcs": [
    {{
      "id": "npc_gregor",
      "name": "Gregor",
      "role": "Innkeeper",
      "location_id": "location_rusty_anchor",
      "personality": "Gruff but welcoming",
      "appearance": "Bald dwarf with thick beard",
      "wants": "Wants to find his missing daughter",
      "offered": "Offered free room and board",
      "relationship_to_party": "friendly"
    }}
  ],
  "factions": [
    {{
      "id": "faction_thieves_guild",
      "name": "The Shadow Syndicate",
      "stated_purpose": "Merchants guild",
      "suspected_purpose": "Actually a thieves guild",
      "symbols": "Red crow emblem"
    }}
  ],
  "quests": [
    {{
      "id": "quest_find_daughter",
      "title": "Find Gregor's Daughter",
      "quest_giver_npc_id": "npc_gregor",
      "description": "Search the eastern woods for Gregor's missing daughter",
      "status": "active",
      "new_objectives": ["Search eastern woods", "Ask the ranger"]
    }}
  ],
  "rumors": [
    {{
      "id": "rumor_haunted_woods",
      "content": "The eastern woods are haunted by spirits",
      "source_npc_id": "npc_gregor",
      "confirmed": false
    }}
  ],
  "items": [
    {{
      "id": "item_silver_locket",
      "name": "Silver Locket",
      "appearance": "Tarnished silver with a portrait inside",
      "known_properties": "Belonged to Gregor's daughter",
      "found_where": "location_eastern_woods",
      "currently_held": true
    }}
  ],
  "decisions": [
    {{
      "id": "decision_accepted_gregor_quest",
      "description": "Agreed to help Gregor find his daughter",
      "location_id": "location_rusty_anchor",
      "involved_npcs": ["npc_gregor"],
      "immediate_outcome": "Gregor is grateful and offers free lodging",
      "potential_consequences": ["Might gain a loyal ally", "Could be walking into danger"]
    }}
  ]
}}

IMPORTANT:
- If no new information for a category, use empty array []
- Use the exact IDs from PRE-DETECTED ENTITIES when they match
- For new entities not in the list, create IDs like: "location_[name_lowercase]", "npc_[name_lowercase]"
- Keep descriptions concise (1-2 sentences max)
- Only include what the PLAYER knows from THIS scene (plus existing context if provided)

Output ONLY valid JSON, no explanation."""
        
        return prompt


# Convenience function for integration
async def extract_campaign_log_from_scene(
    narration: str,
    entity_mentions: List[EntityMention],
    openai_api_key: str,
    existing_log_context: Optional[Dict[str, Any]] = None,
    current_location: Optional[str] = None,
    quest_hooks: Optional[List[Dict[str, Any]]] = None,
    scene_id: Optional[str] = None
) -> CampaignLogDelta:
    """
    Convenience function for extracting campaign log from a scene.
    Includes conversion of quest hooks to leads.
    """
    extractor = CampaignLogExtractor(openai_api_key)
    return await extractor.extract_from_narration(
        narration,
        entity_mentions,
        existing_log_context,
        current_location,
        quest_hooks,
        scene_id
    )
