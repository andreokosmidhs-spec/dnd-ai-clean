"""
Campaign Log Service - Storage and Delta Merging
Handles persistence and intelligent merging of campaign log updates.
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase

from models.log_models import (
    CampaignLog,
    LocationKnowledge,
    NpcKnowledge,
    FactionKnowledge,
    QuestKnowledge,
    RumorKnowledge,
    ItemKnowledge,
    DecisionKnowledge,
    LeadEntry,
    CampaignLogDelta,
    LocationDelta,
    NpcDelta,
    FactionDelta,
    QuestDelta,
    RumorDelta,
    ItemDelta,
    DecisionDelta,
    LeadDelta
)

logger = logging.getLogger(__name__)


class CampaignLogService:
    """Service for managing campaign logs"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.campaign_logs
    
    async def get_or_create_log(
        self, 
        campaign_id: str, 
        character_id: Optional[str] = None
    ) -> CampaignLog:
        """
        Get existing campaign log or create a new one.
        """
        query = {"campaign_id": campaign_id}
        if character_id:
            query["character_id"] = character_id
        
        log_doc = await self.collection.find_one(query, {"_id": 0})
        
        if log_doc:
            logger.info(f"📖 Found existing campaign log for {campaign_id}")
            return CampaignLog(**log_doc)
        else:
            logger.info(f"📖 Creating new campaign log for {campaign_id}")
            new_log = CampaignLog(
                campaign_id=campaign_id,
                character_id=character_id
            )
            await self.save_log(new_log)
            return new_log
    
    async def save_log(self, log: CampaignLog) -> None:
        """Save the entire log to MongoDB"""
        log.last_updated = datetime.now(timezone.utc)
        
        query = {"campaign_id": log.campaign_id}
        if log.character_id:
            query["character_id"] = log.character_id
        
        log_dict = log.model_dump()
        
        await self.collection.replace_one(
            query,
            log_dict,
            upsert=True
        )
        
        logger.info(f"💾 Saved campaign log for {log.campaign_id}")
    
    async def apply_delta(
        self, 
        campaign_id: str, 
        delta: CampaignLogDelta,
        character_id: Optional[str] = None
    ) -> CampaignLog:
        """
        Apply a delta update to the campaign log.
        Intelligently merges new information with existing data.
        """
        logger.info(f"🔄 Applying delta to campaign log {campaign_id}")
        
        # Get existing log
        log = await self.get_or_create_log(campaign_id, character_id)
        
        # Merge locations
        for loc_delta in delta.locations:
            if loc_delta.id in log.locations:
                existing = log.locations[loc_delta.id]
                self._merge_location(existing, loc_delta)
            else:
                # Create new location entry
                log.locations[loc_delta.id] = LocationKnowledge(
                    id=loc_delta.id,
                    name=loc_delta.name or loc_delta.id,
                    geography=loc_delta.geography or "",
                    climate=loc_delta.climate or "",
                    controlling_faction=loc_delta.controlling_faction,
                    notable_places=loc_delta.notable_places,
                    npcs_met_here=loc_delta.npcs_met_here,
                    architecture=loc_delta.architecture or "",
                    culture_notes=loc_delta.culture_notes or "",
                    history_snippet=loc_delta.history_snippet or ""
                )
        
        # Merge NPCs
        for npc_delta in delta.npcs:
            if npc_delta.id in log.npcs:
                existing = log.npcs[npc_delta.id]
                self._merge_npc(existing, npc_delta)
            else:
                log.npcs[npc_delta.id] = NpcKnowledge(
                    id=npc_delta.id,
                    name=npc_delta.name or npc_delta.id,
                    role=npc_delta.role or "",
                    location_id=npc_delta.location_id,
                    personality=npc_delta.personality or "",
                    appearance=npc_delta.appearance or "",
                    wants=npc_delta.wants or "",
                    offered=npc_delta.offered or "",
                    faction_id=npc_delta.faction_id,
                    relationship_to_party=npc_delta.relationship_to_party or "neutral"
                )
        
        # Merge Factions
        for faction_delta in delta.factions:
            if faction_delta.id in log.factions:
                existing = log.factions[faction_delta.id]
                self._merge_faction(existing, faction_delta)
            else:
                log.factions[faction_delta.id] = FactionKnowledge(
                    id=faction_delta.id,
                    name=faction_delta.name or faction_delta.id,
                    stated_purpose=faction_delta.stated_purpose or "",
                    suspected_purpose=faction_delta.suspected_purpose or "",
                    known_leader=faction_delta.known_leader,
                    base_location_id=faction_delta.base_location_id,
                    relationship_to_party=faction_delta.relationship_to_party or "neutral",
                    symbols=faction_delta.symbols or ""
                )
        
        # Merge Quests
        for quest_delta in delta.quests:
            if quest_delta.id in log.quests:
                existing = log.quests[quest_delta.id]
                self._merge_quest(existing, quest_delta)
            else:
                log.quests[quest_delta.id] = QuestKnowledge(
                    id=quest_delta.id,
                    title=quest_delta.title or quest_delta.id,
                    quest_giver_npc_id=quest_delta.quest_giver_npc_id,
                    description=quest_delta.description or "",
                    source_lead_id=quest_delta.source_lead_id,
                    status=quest_delta.status or "active",
                    objectives=quest_delta.new_objectives
                )
        
        # Add Rumors (always new entries)
        for rumor_delta in delta.rumors:
            log.rumors[rumor_delta.id] = RumorKnowledge(
                id=rumor_delta.id,
                content=rumor_delta.content,
                source_npc_id=rumor_delta.source_npc_id,
                source_location_id=rumor_delta.source_location_id,
                confirmed=rumor_delta.confirmed,
                contradicted=rumor_delta.contradicted
            )
        
        # Merge Items
        for item_delta in delta.items:
            if item_delta.id in log.items:
                existing = log.items[item_delta.id]
                self._merge_item(existing, item_delta)
            else:
                log.items[item_delta.id] = ItemKnowledge(
                    id=item_delta.id,
                    name=item_delta.name or item_delta.id,
                    appearance=item_delta.appearance or "",
                    known_properties=item_delta.known_properties or "",
                    suspected_properties=item_delta.suspected_properties or "",
                    found_where=item_delta.found_where,
                    received_from=item_delta.received_from,
                    currently_held=item_delta.currently_held or False
                )
        
        # Add Decisions (always new entries)
        for decision_delta in delta.decisions:
            log.decisions[decision_delta.id] = DecisionKnowledge(
                id=decision_delta.id,
                description=decision_delta.description,
                location_id=decision_delta.location_id,
                involved_npcs=decision_delta.involved_npcs,
                immediate_outcome=decision_delta.immediate_outcome or "",
                potential_consequences=decision_delta.potential_consequences
            )
        
        # Merge Leads (quest hooks/breadcrumbs)
        for lead_delta in delta.leads:
            if lead_delta.id in log.leads:
                # Update existing lead (status changes, notes additions)
                existing = log.leads[lead_delta.id]
                self._merge_lead(existing, lead_delta)
            else:
                # Create new lead entry
                log.leads[lead_delta.id] = LeadEntry(
                    id=lead_delta.id,
                    short_text=lead_delta.short_text,
                    location_id=lead_delta.location_id,
                    source_scene_id=lead_delta.source_scene_id,
                    source_type=lead_delta.source_type or "",
                    status=lead_delta.status,
                    related_npc_ids=lead_delta.related_npc_ids,
                    related_location_ids=lead_delta.related_location_ids,
                    related_faction_ids=lead_delta.related_faction_ids
                )
        
        # Save updated log
        await self.save_log(log)
        
        logger.info(f"✅ Delta applied successfully to campaign log {campaign_id}")
        return log
    
    def _merge_location(self, existing: LocationKnowledge, delta: LocationDelta) -> None:
        """Merge location delta into existing location (in-place)"""
        if delta.name:
            existing.name = delta.name
        if delta.geography:
            existing.geography = self._merge_text(existing.geography, delta.geography)
        if delta.climate:
            existing.climate = self._merge_text(existing.climate, delta.climate)
        if delta.controlling_faction:
            existing.controlling_faction = delta.controlling_faction
        if delta.notable_places:
            existing.notable_places = self._merge_list(existing.notable_places, delta.notable_places)
        if delta.npcs_met_here:
            existing.npcs_met_here = self._merge_list(existing.npcs_met_here, delta.npcs_met_here)
        if delta.architecture:
            existing.architecture = self._merge_text(existing.architecture, delta.architecture)
        if delta.culture_notes:
            existing.culture_notes = self._merge_text(existing.culture_notes, delta.culture_notes)
        if delta.history_snippet:
            existing.history_snippet = self._merge_text(existing.history_snippet, delta.history_snippet)
        
        existing.last_updated = datetime.now(timezone.utc)
    
    def _merge_npc(self, existing: NpcKnowledge, delta: NpcDelta) -> None:
        """Merge NPC delta into existing NPC (in-place)"""
        if delta.name:
            existing.name = delta.name
        if delta.role:
            existing.role = self._merge_text(existing.role, delta.role)
        if delta.location_id:
            existing.location_id = delta.location_id
        if delta.personality:
            existing.personality = self._merge_text(existing.personality, delta.personality)
        if delta.appearance:
            existing.appearance = self._merge_text(existing.appearance, delta.appearance)
        if delta.wants:
            existing.wants = self._merge_text(existing.wants, delta.wants)
        if delta.offered:
            existing.offered = self._merge_text(existing.offered, delta.offered)
        if delta.faction_id:
            existing.faction_id = delta.faction_id
        if delta.relationship_to_party:
            existing.relationship_to_party = delta.relationship_to_party
        
        existing.last_updated = datetime.now(timezone.utc)
    
    def _merge_faction(self, existing: FactionKnowledge, delta: FactionDelta) -> None:
        """Merge faction delta into existing faction (in-place)"""
        if delta.name:
            existing.name = delta.name
        if delta.stated_purpose:
            existing.stated_purpose = self._merge_text(existing.stated_purpose, delta.stated_purpose)
        if delta.suspected_purpose:
            existing.suspected_purpose = self._merge_text(existing.suspected_purpose, delta.suspected_purpose)
        if delta.known_leader:
            existing.known_leader = delta.known_leader
        if delta.base_location_id:
            existing.base_location_id = delta.base_location_id
        if delta.relationship_to_party:
            existing.relationship_to_party = delta.relationship_to_party
        if delta.symbols:
            existing.symbols = self._merge_text(existing.symbols, delta.symbols)
        
        existing.last_updated = datetime.now(timezone.utc)
    
    def _merge_quest(self, existing: QuestKnowledge, delta: QuestDelta) -> None:
        """Merge quest delta into existing quest (in-place)"""
        if delta.title:
            existing.title = delta.title
        if delta.quest_giver_npc_id:
            existing.quest_giver_npc_id = delta.quest_giver_npc_id
        if delta.description:
            existing.description = self._merge_text(existing.description, delta.description)
        if delta.source_lead_id:
            existing.source_lead_id = delta.source_lead_id
        if delta.status:
            existing.status = delta.status
        if delta.new_objectives:
            existing.objectives = self._merge_list(existing.objectives, delta.new_objectives)
        if delta.completed_objectives:
            existing.completed_objectives = self._merge_list(existing.completed_objectives, delta.completed_objectives)
        
        existing.last_updated = datetime.now(timezone.utc)
    
    def _merge_item(self, existing: ItemKnowledge, delta: ItemDelta) -> None:
        """Merge item delta into existing item (in-place)"""
        if delta.name:
            existing.name = delta.name
        if delta.appearance:
            existing.appearance = self._merge_text(existing.appearance, delta.appearance)
        if delta.known_properties:
            existing.known_properties = self._merge_text(existing.known_properties, delta.known_properties)
        if delta.suspected_properties:
            existing.suspected_properties = self._merge_text(existing.suspected_properties, delta.suspected_properties)
        if delta.found_where:
            existing.found_where = delta.found_where
        if delta.received_from:
            existing.received_from = delta.received_from
        if delta.currently_held is not None:
            existing.currently_held = delta.currently_held
        
        existing.last_updated = datetime.now(timezone.utc)
    
    def _merge_lead(self, existing: LeadEntry, delta: LeadDelta) -> None:
        """
        Merge lead delta into existing lead (in-place).
        Primary use case: updating lead status (unexplored -> active -> resolved)
        """
        # Update status if changed
        if delta.status and delta.status != existing.status:
            existing.status = delta.status
        
        # Merge related entities (add new ones, don't remove)
        if delta.related_npc_ids:
            existing.related_npc_ids = self._merge_list(existing.related_npc_ids, delta.related_npc_ids)
        if delta.related_location_ids:
            existing.related_location_ids = self._merge_list(existing.related_location_ids, delta.related_location_ids)
        if delta.related_faction_ids:
            existing.related_faction_ids = self._merge_list(existing.related_faction_ids, delta.related_faction_ids)
        
        existing.updated_at = datetime.now(timezone.utc)
    
    def _merge_text(self, existing: str, new: str) -> str:
        """
        Merge text fields intelligently.
        If existing is empty, use new. Otherwise, append if different.
        """
        if not existing:
            return new
        if not new:
            return existing
        
        # If new text is completely different, append with separator
        if new.lower() not in existing.lower():
            return f"{existing} {new}"
        
        return existing
    
    def _merge_list(self, existing: List[str], new: List[str]) -> List[str]:
        """
        Merge lists by adding unique items from new to existing.
        """
        combined = set(existing)
        combined.update(new)
        return list(combined)
    
    async def get_log(
        self, 
        campaign_id: str,
        character_id: Optional[str] = None
    ) -> Optional[CampaignLog]:
        """Get the full campaign log"""
        return await self.get_or_create_log(campaign_id, character_id)
    
    async def get_entity(
        self,
        campaign_id: str,
        entity_type: str,
        entity_id: str,
        character_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get a specific entity from the log"""
        log = await self.get_or_create_log(campaign_id, character_id)
        
        entity_map = {
            "location": log.locations,
            "npc": log.npcs,
            "faction": log.factions,
            "quest": log.quests,
            "rumor": log.rumors,
            "item": log.items,
            "decision": log.decisions,
            "lead": log.leads
        }
        
        collection = entity_map.get(entity_type)
        if not collection:
            return None
        
        entity = collection.get(entity_id)
        return entity.model_dump() if entity else None
    
    async def get_log_summary(
        self,
        campaign_id: str,
        character_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get summary counts for the campaign log"""
        log = await self.get_or_create_log(campaign_id, character_id)
        
        return {
            "campaign_id": campaign_id,
            "counts": {
                "locations": len(log.locations),
                "npcs": len(log.npcs),
                "factions": len(log.factions),
                "quests": len(log.quests),
                "rumors": len(log.rumors),
                "items": len(log.items),
                "decisions": len(log.decisions),
                "leads": len(log.leads)
            },
            "last_updated": log.last_updated
        }
    
    async def list_open_leads(
        self,
        campaign_id: str,
        character_id: Optional[str] = None,
        include_abandoned: bool = False
    ) -> List[LeadEntry]:
        """
        Return all leads with status != 'resolved' (and optionally != 'abandoned').
        
        Args:
            campaign_id: Campaign identifier
            character_id: Optional character identifier
            include_abandoned: If True, include abandoned leads. Default False.
            
        Returns:
            List of LeadEntry objects that are still open
        """
        log = await self.get_or_create_log(campaign_id, character_id)
        
        open_leads = []
        for lead in log.leads.values():
            # Always exclude resolved
            if lead.status == "resolved":
                continue
            
            # Exclude abandoned unless explicitly requested
            if lead.status == "abandoned" and not include_abandoned:
                continue
            
            open_leads.append(lead)
        
        # Sort by created_at (newest first)
        open_leads.sort(key=lambda x: x.created_at, reverse=True)
        
        logger.info(f"📋 Found {len(open_leads)} open leads for campaign {campaign_id}")
        return open_leads
    
    async def get_lead(
        self,
        campaign_id: str,
        lead_id: str,
        character_id: Optional[str] = None
    ) -> Optional[LeadEntry]:
        """
        Return a single LeadEntry by id, or None if not found.
        
        Args:
            campaign_id: Campaign identifier
            lead_id: Lead identifier
            character_id: Optional character identifier
            
        Returns:
            LeadEntry object or None
        """
        log = await self.get_or_create_log(campaign_id, character_id)
        return log.leads.get(lead_id)
    
    async def update_lead_status(
        self,
        campaign_id: str,
        lead_id: str,
        new_status: str,
        character_id: Optional[str] = None,
        player_notes: Optional[str] = None
    ) -> Optional[LeadEntry]:
        """
        Update the status of a lead (and optionally add player notes).
        
        Args:
            campaign_id: Campaign identifier
            lead_id: Lead identifier
            new_status: New status ("unexplored", "active", "resolved", "abandoned")
            character_id: Optional character identifier
            player_notes: Optional notes to append
            
        Returns:
            Updated LeadEntry or None if lead not found
        """
        log = await self.get_or_create_log(campaign_id, character_id)
        
        lead = log.leads.get(lead_id)
        if not lead:
            logger.warning(f"❌ Lead {lead_id} not found in campaign {campaign_id}")
            return None
        
        # Update status
        old_status = lead.status
        lead.status = new_status
        lead.updated_at = datetime.now(timezone.utc)
        
        # Append player notes if provided
        if player_notes:
            if lead.player_notes:
                lead.player_notes = f"{lead.player_notes}\n\n{player_notes}"
            else:
                lead.player_notes = player_notes
        
        # Save updated log
        await self.save_log(log)
        
        logger.info(f"✅ Updated lead {lead_id} status: {old_status} → {new_status}")
        return lead
