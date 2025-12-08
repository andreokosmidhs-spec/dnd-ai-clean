"""
CONSEQUENCE ESCALATION SERVICE - DMG p.32, p.74, p.98-99

Implements consequence tracking and escalation system:
- DMG p.74: "Success earns rewards, failure introduces complications"
- DMG p.32: "Address problem behaviors with consequences"
- DMG p.98-99: "Fixing Problems" - consequences guide players back on track

Tracks player transgressions and escalates consequences progressively.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class ConsequenceEscalation:
    """
    Track and escalate consequences of player actions.
    
    DMG Principle: Consequences should escalate from warnings to serious repercussions.
    """
    
    SEVERITY_LEVELS = {
        "minor": {
            "examples": ["NPC annoyed", "small reputation loss", "warning given"],
            "escalation_threshold": 3,  # 3 minor offenses = 1 moderate
            "next_level": "moderate",
            "description": "Minor transgression with light consequences"
        },
        "moderate": {
            "examples": ["Guards investigate", "quest giver refuses help", "disadvantage on social checks"],
            "escalation_threshold": 2,  # 2 moderate offenses = 1 severe
            "next_level": "severe",
            "description": "Moderate transgression requiring attention"
        },
        "severe": {
            "examples": ["Bounty posted", "guards attack on sight", "faction turns hostile"],
            "escalation_threshold": 1,  # 1 severe offense = critical
            "next_level": "critical",
            "description": "Severe transgression with major repercussions"
        },
        "critical": {
            "examples": ["City-wide manhunt", "war declared", "exile enforced"],
            "escalation_threshold": None,  # No further escalation
            "next_level": None,
            "description": "Critical transgression - maximum consequences"
        }
    }
    
    @staticmethod
    def track_transgression(
        world_state: Dict[str, Any],
        target_id: str,
        action: str,
        severity: str = "minor",
        is_violent: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Record a player transgression and check if escalation is needed.
        
        DMG p.32: Track problem behaviors
        DMG p.74: Failure introduces complications
        
        Args:
            world_state: Current world state (will be modified)
            target_id: ID of affected NPC or faction
            action: Description of transgression
            severity: "minor", "moderate", "severe", "critical"
            is_violent: True if action involves violence (triggers faster escalation)
        
        Returns:
            Escalation dict if threshold met, None otherwise
        """
        # Initialize transgressions dict if needed
        if 'transgressions' not in world_state:
            world_state['transgressions'] = {}
        
        if target_id not in world_state['transgressions']:
            world_state['transgressions'][target_id] = []
        
        # Record transgression
        transgression = {
            "action": action,
            "severity": severity,
            "is_violent": is_violent,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "escalation_triggered": False
        }
        
        world_state['transgressions'][target_id].append(transgression)
        
        logger.info(f"⚠️ Transgression recorded: {target_id} - {action} (severity: {severity}, violent: {is_violent})")
        
        # Count total transgressions for this target (any severity)
        total_transgressions = len(world_state['transgressions'][target_id])
        
        # Check if escalation threshold met
        transgressions_of_severity = [
            t for t in world_state['transgressions'][target_id]
            if t['severity'] == severity and not t.get('escalation_triggered', False)
        ]
        
        threshold = ConsequenceEscalation.SEVERITY_LEVELS[severity]['escalation_threshold']
        
        if threshold and len(transgressions_of_severity) >= threshold:
            logger.warning(f"🚨 ESCALATION THRESHOLD MET: {len(transgressions_of_severity)} {severity} transgressions against {target_id}")
            
            # Mark transgressions as processed
            for t in transgressions_of_severity:
                t['escalation_triggered'] = True
            
            # Escalate to next level
            escalation = ConsequenceEscalation.escalate_consequence(
                world_state,
                target_id,
                severity,
                is_violent=any(t.get('is_violent', False) for t in transgressions_of_severity)
            )
            
            return escalation
        
        # CRITICAL: If 3+ violent transgressions regardless of threshold, force combat
        violent_transgressions = [
            t for t in world_state['transgressions'][target_id]
            if t.get('is_violent', False)
        ]
        
        if len(violent_transgressions) >= 3:
            logger.error(f"🔥 AUTO-COMBAT TRIGGER: {len(violent_transgressions)} violent actions against {target_id}")
            return {
                "escalated": True,
                "from_severity": severity,
                "to_severity": "severe",
                "type": "auto_combat",
                "should_trigger_combat": True,
                "should_alert_guards": True,
                "should_issue_bounty": True,
                "severity_level": "severe",
                "description": f"Your repeated violent actions have forced guards to respond with lethal force.",
                "mechanical_effect": {
                    "guards_hostile": True,
                    "combat_initiated": True
                },
                "narrative_hint": "Guards draw weapons and attack!",
                "escalation_timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        return None
    
    @staticmethod
    def escalate_consequence(
        world_state: Dict[str, Any],
        target_id: str,
        current_severity: str,
        is_violent: bool = False
    ) -> Dict[str, Any]:
        """
        Escalate to the next severity level.
        
        DMG p.98-99: "Fixing Problems" - escalating consequences guide behavior
        
        Escalation path:
        - minor (3x) → moderate: Investigation, social disadvantage
        - moderate (2x) → severe: Bounty, guards hostile, COMBAT
        - severe (1x) → critical: Manhunt, war, exile
        
        Args:
            world_state: Current world state
            target_id: ID of affected NPC or faction
            current_severity: Current severity level
            is_violent: True if escalation involves violent actions
        
        Returns:
            Escalation consequence dict with combat trigger flags
        """
        next_level = ConsequenceEscalation.SEVERITY_LEVELS[current_severity]['next_level']
        
        if not next_level:
            logger.error("❌ Already at maximum severity level")
            return {
                "escalated": False,
                "reason": "Maximum severity already reached",
                "should_trigger_combat": False,
                "should_alert_guards": False,
                "should_issue_bounty": False,
                "severity_level": current_severity
            }
        
        logger.warning(f"📈 ESCALATING: {current_severity} → {next_level} for {target_id}")
        
        # Generate appropriate consequence for next level
        if next_level == "moderate":
            consequence = {
                "escalated": True,
                "from_severity": current_severity,
                "to_severity": next_level,
                "type": "investigation",
                "description": f"Guards start asking questions about your actions involving {target_id}.",
                "mechanical_effect": {
                    "charisma_disadvantage": True,
                    "guard_suspicion": True,
                    "location": "town"
                },
                "narrative_hint": "Your repeated offenses have attracted official attention. Guards are now investigating your activities.",
                "escalation_timestamp": datetime.now(timezone.utc).isoformat(),
                "should_trigger_combat": False,
                "should_alert_guards": True,
                "should_issue_bounty": False,
                "severity_level": "moderate"
            }
            
            # Apply mechanical effect
            world_state['guard_suspicion'] = True
            
        elif next_level == "severe":
            # Calculate bounty amount based on target importance
            bounty_amounts = {
                "city_guard": 100,
                "city_authority": 200,
                "quest_giver": 50,
                "faction_leader": 300,
                "default": 100
            }
            bounty_amount = bounty_amounts.get(target_id, bounty_amounts["default"])
            
            # CRITICAL: Severe level ALWAYS triggers combat if violent
            should_combat = is_violent
            
            consequence = {
                "escalated": True,
                "from_severity": current_severity,
                "to_severity": next_level,
                "type": "bounty_and_combat" if should_combat else "bounty",
                "description": f"A bounty of {bounty_amount} gold is posted for your capture.",
                "mechanical_effect": {
                    "bounty_amount": bounty_amount,
                    "guards_hostile": True,
                    "bounty_hunters_active": True,
                    "combat_initiated": should_combat
                },
                "narrative_hint": f"Your continued transgressions have resulted in a {bounty_amount} gold bounty. Guards attack on sight, and bounty hunters are searching for you." + (" Guards draw weapons and attack!" if should_combat else ""),
                "escalation_timestamp": datetime.now(timezone.utc).isoformat(),
                "should_trigger_combat": should_combat,
                "should_alert_guards": True,
                "should_issue_bounty": True,
                "severity_level": "severe"
            }
            
            # Apply mechanical effect
            if 'bounties' not in world_state:
                world_state['bounties'] = []
            
            world_state['bounties'].append({
                "amount": bounty_amount,
                "target": target_id,
                "reason": "Repeated offenses",
                "active": True,
                "posted_at": datetime.now(timezone.utc).isoformat()
            })
            
            world_state['guard_alert'] = True
            world_state['guards_hostile'] = True
            
        elif next_level == "critical":
            consequence = {
                "escalated": True,
                "from_severity": current_severity,
                "to_severity": next_level,
                "type": "faction_war",
                "description": f"The entire faction mobilizes against you. You are declared an enemy of the state.",
                "mechanical_effect": {
                    "city_hostile": True,
                    "must_flee": True,
                    "permanent_enemy": target_id,
                    "overwhelming_force": True
                },
                "narrative_hint": "Your actions have escalated beyond redemption. The city is now completely hostile. You must flee or face overwhelming force. This has permanent campaign consequences.",
                "escalation_timestamp": datetime.now(timezone.utc).isoformat(),
                "should_trigger_combat": True,
                "should_alert_guards": True,
                "should_issue_bounty": True,
                "severity_level": "critical"
            }
            
            # Apply mechanical effect
            world_state['city_hostile'] = True
            world_state['permanent_enemies'] = world_state.get('permanent_enemies', [])
            if target_id not in world_state['permanent_enemies']:
                world_state['permanent_enemies'].append(target_id)
        
        else:
            # Fallback
            consequence = {
                "escalated": True,
                "from_severity": current_severity,
                "to_severity": next_level,
                "type": "generic_escalation",
                "description": "Your actions have serious consequences.",
                "mechanical_effect": {},
                "narrative_hint": "The situation has escalated.",
                "escalation_timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        # Record escalation in world state
        if 'consequence_escalations' not in world_state:
            world_state['consequence_escalations'] = []
        
        world_state['consequence_escalations'].append(consequence)
        
        logger.info(f"✅ Escalation applied: {consequence['type']}")
        
        return consequence
    
    @staticmethod
    def get_transgression_summary(
        world_state: Dict[str, Any],
        target_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get summary of all transgressions, optionally filtered by target.
        
        Returns:
            {
                "total_transgressions": int,
                "by_severity": {"minor": int, "moderate": int, ...},
                "by_target": {"npc_id": count, ...},
                "escalations": int,
                "current_status": str
            }
        """
        transgressions = world_state.get('transgressions', {})
        
        if target_id:
            # Filter to specific target
            target_transgressions = transgressions.get(target_id, [])
            data = {target_id: target_transgressions}
        else:
            # All targets
            data = transgressions
        
        # Count by severity
        by_severity = {"minor": 0, "moderate": 0, "severe": 0, "critical": 0}
        total = 0
        
        for target, trans_list in data.items():
            for trans in trans_list:
                severity = trans.get('severity', 'minor')
                by_severity[severity] += 1
                total += 1
        
        # Count escalations
        escalations = len(world_state.get('consequence_escalations', []))
        
        # Determine current status
        if by_severity['critical'] > 0:
            status = "CRITICAL - City-wide hostility"
        elif by_severity['severe'] > 0:
            status = "SEVERE - Wanted, bounty active"
        elif by_severity['moderate'] > 0:
            status = "MODERATE - Under investigation"
        elif by_severity['minor'] > 0:
            status = "MINOR - Some NPCs annoyed"
        else:
            status = "CLEAN - No transgressions"
        
        return {
            "total_transgressions": total,
            "by_severity": by_severity,
            "by_target": {t: len(tlist) for t, tlist in data.items()},
            "escalations": escalations,
            "current_status": status
        }
    
    @staticmethod
    def check_if_weakens_plot_armor(
        world_state: Dict[str, Any],
        npc_id: str
    ) -> bool:
        """
        DMG principle: Repeated attempts should eventually overcome protection.
        
        Check if repeated transgressions against an NPC have weakened their plot armor.
        After sufficient transgressions, even essential NPCs can be harmed.
        
        Args:
            world_state: Current world state
            npc_id: ID of NPC to check
        
        Returns:
            True if plot armor should be weakened/removed
        """
        transgressions = world_state.get('transgressions', {}).get(npc_id, [])
        
        # Count transgressions of all types against this NPC
        total_attempts = len(transgressions)
        
        # After 5 attempts, plot armor weakens (allows forced non-lethal)
        # After 10 attempts, plot armor breaks completely
        
        if total_attempts >= 10:
            logger.warning(f"🛡️💥 PLOT ARMOR BROKEN: {npc_id} has been attacked {total_attempts} times")
            return True
        elif total_attempts >= 5:
            logger.warning(f"🛡️⚠️ PLOT ARMOR WEAKENING: {npc_id} has been attacked {total_attempts} times")
            return True  # Still protected but can be fought (forced non-lethal)
        
        return False
    
    @staticmethod
    def get_escalation_warning(
        world_state: Dict[str, Any],
        target_id: str,
        current_severity: str
    ) -> Optional[str]:
        """
        DMG p.26: Give players information they need to make smart choices.
        
        Warn players before escalation occurs.
        
        Returns warning message if near escalation, None otherwise
        """
        transgressions = world_state.get('transgressions', {}).get(target_id, [])
        unprocessed = [t for t in transgressions if t['severity'] == current_severity and not t.get('escalation_triggered', False)]
        
        threshold = ConsequenceEscalation.SEVERITY_LEVELS[current_severity]['escalation_threshold']
        
        if threshold and len(unprocessed) == threshold - 1:
            next_level = ConsequenceEscalation.SEVERITY_LEVELS[current_severity]['next_level']
            warning = f"⚠️ WARNING: One more {current_severity} offense will escalate to {next_level} consequences!"
            logger.warning(warning)
            return warning
        
        return None
