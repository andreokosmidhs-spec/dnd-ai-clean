"""
CONTEXT MEMORY SERVICE - Maintains narrative continuity

Prevents DM from losing track of:
- Current location
- Active NPCs in scene
- Recent actions and their outcomes
- Ongoing conflicts or situations

DMG p.140-145: Story cohesion and continuity
"""
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class ContextMemory:
    """
    Track and enforce narrative context to prevent DM hallucinations.
    """
    
    @staticmethod
    def build_recent_context(
        messages: List[Dict[str, Any]],
        max_messages: int = 3
    ) -> str:
        """
        Build a summary of recent actions for DM context.
        
        DMG p.140: "Keep track of what happened in previous sessions"
        
        Args:
            messages: List of recent message exchanges
            max_messages: How many recent messages to include
        
        Returns:
            Formatted context string
        """
        if not messages:
            return "No recent actions."
        
        recent = messages[-max_messages:]
        context_lines = []
        
        for i, msg in enumerate(recent, 1):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            
            if role == 'user':
                # Player action
                context_lines.append(f"  {i}. Player: {content[:100]}")
            elif role == 'assistant':
                # DM response (extract key info)
                if len(content) > 150:
                    content = content[:150] + "..."
                context_lines.append(f"     DM: {content}")
        
        return "RECENT ACTIONS:\n" + "\n".join(context_lines)
    
    @staticmethod
    def enforce_location_context(
        current_location: str,
        world_blueprint: Dict[str, Any]
    ) -> str:
        """
        Generate strict location enforcement guidance for DM.
        
        Returns location-specific constraints
        """
        location_lower = current_location.lower()
        
        # Identify location type
        if any(word in location_lower for word in ['ruin', 'tower', 'dungeon', 'cave', 'crypt']):
            location_type = "DANGEROUS RUINS"
            constraints = """
CRITICAL LOCATION CONSTRAINTS:
- You are at {location} (RUINS/DUNGEON)
- NO merchants, shopkeepers, or traders here
- Only monsters, undead, or dungeon inhabitants
- Atmosphere: Dark, dangerous, abandoned
- NPCs here: Enemies, explorers, or trapped victims
            """.format(location=current_location)
        
        elif any(word in location_lower for word in ['tavern', 'inn', 'bar']):
            location_type = "TAVERN/INN"
            constraints = """
CRITICAL LOCATION CONSTRAINTS:
- You are at {location} (TAVERN)
- NPCs: Innkeeper, patrons, travelers
- Atmosphere: Social, busy, public
- NO dungeon monsters or random merchants
            """.format(location=current_location)
        
        elif any(word in location_lower for word in ['market', 'shop', 'bazaar', 'store']):
            location_type = "MARKETPLACE"
            constraints = """
CRITICAL LOCATION CONSTRAINTS:
- You are at {location} (MARKET)
- NPCs: Merchants, shopkeepers, customers
- Atmosphere: Commercial, busy, public
- Focus on buying/selling
            """.format(location=current_location)
        
        elif any(word in location_lower for word in ['forest', 'woods', 'wilderness', 'road']):
            location_type = "WILDERNESS"
            constraints = """
CRITICAL LOCATION CONSTRAINTS:
- You are at {location} (WILDERNESS)
- NPCs: Travelers, bandits, druids, animals
- Atmosphere: Natural, isolated
- NO city NPCs or buildings
            """.format(location=current_location)
        
        else:
            location_type = "GENERAL LOCATION"
            constraints = """
CRITICAL LOCATION CONSTRAINTS:
- You are at {location}
- Stay consistent with this location type
- Only introduce NPCs appropriate for this setting
            """.format(location=current_location)
        
        logger.info(f"📍 Location enforcement: {location_type} - {current_location}")
        return constraints
    
    @staticmethod
    def enforce_active_npcs(
        active_npc_ids: List[str],
        world_blueprint: Dict[str, Any]
    ) -> str:
        """
        Create strict NPC constraints based on who's actually in the scene.
        
        DMG p.140: "Track NPCs and their current status"
        """
        if not active_npc_ids:
            return """
NPC CONSTRAINTS:
- NO NPCs are currently in this scene
- Do NOT introduce random NPCs unless the player explicitly seeks them
- If player wants to talk to someone, ask WHO they're looking for
            """
        
        # Get NPC names
        key_npcs = world_blueprint.get('key_npcs', [])
        active_npc_names = []
        
        for npc_id in active_npc_ids:
            for npc in key_npcs:
                if npc.get('id') == npc_id or npc.get('name', '').lower().replace(' ', '_') == npc_id:
                    active_npc_names.append(npc.get('name', npc_id))
                    break
        
        if not active_npc_names:
            active_npc_names = active_npc_ids  # Fallback to IDs
        
        return f"""
NPC CONSTRAINTS:
- ONLY these NPCs are in the scene: {', '.join(active_npc_names)}
- Do NOT introduce other NPCs without explicit player action
- If player talks, it's to one of these NPCs
- If they leave, remove from active_npcs
        """
    
    @staticmethod
    def check_dm_response_consistency(
        dm_narration: str,
        current_location: str,
        active_npc_ids: List[str],
        world_blueprint: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate DM response for narrative consistency.
        
        DMG p.145: "Catch continuity errors before they compound"
        
        Returns:
            {
                "consistent": bool,
                "issues": list of issues found,
                "warnings": list of warnings
            }
        """
        issues = []
        warnings = []
        
        narration_lower = dm_narration.lower()
        location_lower = current_location.lower()
        
        # Check 1: Location consistency
        if 'ruin' in location_lower or 'tower' in location_lower or 'dungeon' in location_lower:
            # Should NOT mention merchants, shops, taverns
            if any(word in narration_lower for word in ['merchant', 'shopkeeper', 'trader', 'shop', 'store']):
                issues.append(f"LOCATION ERROR: Mentioned merchant/shop at ruins ({current_location})")
            
            if 'tavern' in narration_lower or 'inn' in narration_lower:
                issues.append(f"LOCATION ERROR: Mentioned tavern at ruins ({current_location})")
        
        elif 'tavern' in location_lower or 'inn' in location_lower:
            # Should NOT mention monsters, dungeons
            if any(word in narration_lower for word in ['skeleton', 'zombie', 'undead', 'monster']):
                warnings.append(f"Warning: Mentioned monsters in tavern")
        
        # Check 2: NPC consistency
        key_npcs = world_blueprint.get('key_npcs', [])
        active_npc_names = []
        for npc_id in active_npc_ids:
            for npc in key_npcs:
                if npc.get('id') == npc_id:
                    active_npc_names.append(npc.get('name', '').lower())
                    break
        
        # Check if narration mentions NPCs not in active list
        all_npc_names = [npc.get('name', '').lower() for npc in key_npcs]
        for npc_name in all_npc_names:
            if npc_name and npc_name in narration_lower and npc_name not in active_npc_names:
                warnings.append(f"Warning: Mentioned NPC '{npc_name}' not in active scene")
        
        is_consistent = len(issues) == 0
        
        if issues:
            logger.error(f"❌ CONSISTENCY CHECK FAILED: {len(issues)} issues found")
            for issue in issues:
                logger.error(f"   - {issue}")
        
        if warnings:
            logger.warning(f"⚠️ Consistency warnings: {len(warnings)}")
            for warning in warnings:
                logger.warning(f"   - {warning}")
        
        return {
            "consistent": is_consistent,
            "issues": issues,
            "warnings": warnings
        }
    
    @staticmethod
    def get_ongoing_situation_summary(
        world_state: Dict[str, Any],
        combat_active: bool
    ) -> str:
        """
        Summarize any ongoing situations that must continue.
        
        Examples:
        - Combat in progress
        - NPC conversation happening
        - Plot armor consequences active
        - Pursuit by guards
        """
        situations = []
        
        if combat_active:
            situations.append("⚔️ COMBAT IS ACTIVE - Continue the fight")
        
        if world_state.get('guard_alert'):
            situations.append("👮 Guards are actively searching for you")
        
        if world_state.get('guards_hostile'):
            situations.append("⚠️ Guards will attack on sight")
        
        if world_state.get('bounties') and len(world_state['bounties']) > 0:
            active_bounties = [b for b in world_state['bounties'] if b.get('active')]
            if active_bounties:
                situations.append(f"💰 Bounty active: {active_bounties[0].get('amount')} gold")
        
        tension_state = world_state.get('tension_state', {})
        if tension_state.get('phase') == 'climax':
            situations.append("⚡ HIGH TENSION - Action is happening NOW")
        
        if situations:
            return "ONGOING SITUATIONS:\n" + "\n".join(f"  - {s}" for s in situations)
        
        return ""
