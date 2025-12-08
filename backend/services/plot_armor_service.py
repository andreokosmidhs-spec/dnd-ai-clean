"""
PLOT ARMOR SERVICE - Protects essential NPCs from campaign-breaking actions.

Prevents players from killing quest-critical NPCs while maintaining immersion
through realistic consequences (guards, reputation loss, arrest, etc.)
"""
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


def check_plot_armor(
    npc_data: Dict[str, Any],
    world_blueprint: Dict[str, Any],
    world_state: Dict[str, Any],
    action_type: str = "attack"
) -> Dict[str, Any]:
    """
    Check if an NPC has plot armor and what consequences should trigger.
    
    Args:
        npc_data: NPC data from world_blueprint
        world_blueprint: Full world blueprint
        world_state: Current world state
        action_type: Type of hostile action ("attack", "threaten", "steal_from", etc.)
    
    Returns:
        PlotArmorOutcome dict
    """
    npc_name = npc_data.get('name', 'Unknown')
    npc_role = npc_data.get('role', '').lower()
    
    # Determine if NPC is essential
    is_essential = is_npc_essential(npc_data, world_blueprint)
    
    # Get NPC attitude (default to neutral if not specified)
    npc_attitude = npc_data.get('attitude', 'neutral').lower()
    
    # Get current location context
    current_location = world_state.get('current_location', 'unknown').lower()
    location_type = get_location_type(current_location, world_blueprint)
    
    logger.info(f"🛡️ Plot armor check for {npc_name}:")
    logger.info(f"   Essential: {is_essential}")
    logger.info(f"   Attitude: {npc_attitude}")
    logger.info(f"   Location: {current_location} ({location_type})")
    logger.info(f"   Action: {action_type}")
    
    # Plot armor triggers if:
    # - NPC is essential
    # - AND (attitude is friendly/neutral OR location is civilized)
    should_protect = is_essential and (
        npc_attitude in ['friendly', 'neutral'] or 
        location_type in ['town', 'city', 'tavern', 'shop', 'temple']
    )
    
    if not should_protect:
        return {
            "handled": False,
            "allow_combat": True,
            "mechanical_override": "none",
            "consequences": [],
            "narrative_hint": None,
            "status": "no_protection"
        }
    
    # Plot armor activated - determine consequences
    logger.warning(f"🛡️ PLOT ARMOR ACTIVATED for {npc_name}")
    
    # Build consequences based on NPC role and location
    consequences = build_consequences(npc_data, location_type, action_type)
    
    # Get narrative hint
    narrative_hint = get_narrative_hint(npc_data, location_type, action_type, consequences)
    
    # Determine mechanical override
    mechanical_override = determine_mechanical_override(npc_data, location_type, action_type)
    
    return {
        "handled": True,
        "allow_combat": False,  # Never allow direct combat with protected NPCs
        "mechanical_override": mechanical_override,
        "consequences": consequences,
        "narrative_hint": narrative_hint,
        "status": "plot_armor_blocked"
    }


def is_npc_essential(npc_data: Dict[str, Any], world_blueprint: Dict[str, Any]) -> bool:
    """
    Determine if an NPC is essential to the campaign.
    """
    # Check explicit flag
    if npc_data.get('is_essential'):
        return True
    
    role = npc_data.get('role', '').lower()
    
    # Role-based essential detection
    essential_roles = [
        'quest giver', 'quest_giver', 'questgiver',
        'lord', 'ruler', 'king', 'queen', 'baron', 'duke',
        'faction leader', 'guild master', 'guildmaster',
        'high priest', 'archpriest',
        'mayor', 'elder', 'chief',
        'main contact', 'primary npc'
    ]
    
    if any(essential_role in role for essential_role in essential_roles):
        return True
    
    # Check if NPC is referenced in key world elements
    npc_name = npc_data.get('name', '')
    
    # Check if mentioned in macro_conflicts
    macro_conflicts = world_blueprint.get('macro_conflicts', {})
    all_conflicts = []
    all_conflicts.extend(macro_conflicts.get('local', []))
    all_conflicts.extend(macro_conflicts.get('realm', []))
    all_conflicts.extend(macro_conflicts.get('world', []))
    
    if any(npc_name.lower() in conflict.lower() for conflict in all_conflicts):
        return True
    
    # Check if they're a faction representative
    factions = world_blueprint.get('factions', [])
    for faction in factions:
        rep = faction.get('representative_npc_idea', '')
        if npc_name.lower() in rep.lower():
            return True
    
    return False


def get_location_type(location_name: str, world_blueprint: Dict[str, Any]) -> str:
    """
    Determine the type of location (town, wilderness, dungeon, etc.)
    """
    location_lower = location_name.lower()
    
    # Check starting town
    starting_town = world_blueprint.get('starting_town', {})
    if starting_town.get('name', '').lower() in location_lower:
        return 'town'
    
    # Check POIs
    pois = world_blueprint.get('points_of_interest', [])
    for poi in pois:
        if poi.get('name', '').lower() in location_lower:
            poi_type = poi.get('type', '').lower()
            if 'tavern' in poi_type or 'inn' in poi_type:
                return 'tavern'
            elif 'shop' in poi_type or 'store' in poi_type:
                return 'shop'
            elif 'temple' in poi_type or 'shrine' in poi_type:
                return 'temple'
            elif 'dungeon' in poi_type or 'ruins' in poi_type:
                return 'dungeon'
            return poi_type
    
    # Default classification based on keywords
    if any(word in location_lower for word in ['tavern', 'inn', 'bar']):
        return 'tavern'
    elif any(word in location_lower for word in ['shop', 'store', 'market']):
        return 'shop'
    elif any(word in location_lower for word in ['temple', 'church', 'shrine']):
        return 'temple'
    elif any(word in location_lower for word in ['town', 'city', 'village']):
        return 'town'
    elif any(word in location_lower for word in ['dungeon', 'cave', 'ruins']):
        return 'dungeon'
    
    return 'wilderness'


def build_consequences(
    npc_data: Dict[str, Any],
    location_type: str,
    action_type: str
) -> List[Dict[str, Any]]:
    """
    Build a list of consequences for violating plot armor.
    """
    consequences = []
    npc_role = npc_data.get('role', '').lower()
    
    # Reputation loss (always applies in civilized areas)
    if location_type in ['town', 'city', 'tavern', 'shop', 'temple']:
        consequences.append({
            "type": "reputation_change",
            "faction": "Local Citizens",
            "amount": -15,
            "description": "Word spreads of your violent outburst"
        })
    
    # Guard intervention (in towns/cities)
    if location_type in ['town', 'city']:
        if 'lord' in npc_role or 'ruler' in npc_role or 'mayor' in npc_role:
            consequences.append({
                "type": "guard_intervention",
                "severity": "arrest",
                "description": "Elite guards immediately restrain you"
            })
            consequences.append({
                "type": "bounty_added",
                "amount": 100,
                "description": "Wanted for assault on nobility"
            })
        else:
            consequences.append({
                "type": "guard_intervention",
                "severity": "warning",
                "description": "Town guards rush to intervene"
            })
    
    # Bodyguard protection (for nobility and faction leaders)
    if any(role in npc_role for role in ['lord', 'leader', 'master', 'priest']):
        consequences.append({
            "type": "bodyguard_protection",
            "description": "Personal bodyguards intercept the attack"
        })
    
    # Witness reactions (in public places)
    if location_type in ['tavern', 'shop', 'town', 'city']:
        consequences.append({
            "type": "witness_alarm",
            "description": "Bystanders cry out in shock and horror"
        })
    
    # NPC-specific consequences
    if 'quest' in npc_role:
        consequences.append({
            "type": "quest_blocked",
            "description": "The NPC refuses to work with you now"
        })
    
    return consequences


def get_narrative_hint(
    npc_data: Dict[str, Any],
    location_type: str,
    action_type: str,
    consequences: List[Dict[str, Any]]
) -> str:
    """
    Generate a narrative hint for the DM based on consequences.
    """
    npc_name = npc_data.get('name', 'the NPC')
    npc_role = npc_data.get('role', '').lower()
    
    # Check for bodyguard protection
    has_bodyguards = any(c['type'] == 'bodyguard_protection' for c in consequences)
    has_guards = any(c['type'] == 'guard_intervention' for c in consequences)
    
    if has_bodyguards:
        return f"As you move to strike {npc_name}, armored bodyguards step between you with weapons drawn. 'Stand down,' one commands coldly."
    
    if has_guards:
        guard_severity = next((c['severity'] for c in consequences if c['type'] == 'guard_intervention'), 'warning')
        if guard_severity == 'arrest':
            return f"Before your blow lands, city guards rush in and forcibly restrain you. '{npc_name} is under the protection of the crown!' one shouts."
        else:
            return f"Town guards quickly intervene, stepping between you and {npc_name}. 'That's enough!' one barks."
    
    # Generic protection
    if location_type == 'tavern':
        return f"The tavern erupts in chaos as patrons grab your arms. 'Not here!' the barkeep shouts, moving to protect {npc_name}."
    elif location_type == 'temple':
        return f"A divine force seems to deflect your attack. The priests move to shield {npc_name}, their eyes burning with righteous anger."
    elif location_type == 'town' or location_type == 'city':
        return f"Bystanders cry out and several brave citizens move to protect {npc_name}. 'Get the guards!' someone shouts."
    
    return f"{npc_name} deftly avoids your attack, and the situation escalates dangerously."


def determine_mechanical_override(
    npc_data: Dict[str, Any],
    location_type: str,
    action_type: str
) -> str:
    """
    Determine what mechanical override to apply.
    
    Returns:
        - "forced_non_lethal": Allow attack but force unconscious instead of death
        - "forced_miss": Attack automatically misses
        - "none": No mechanical override (plot armor handled narratively only)
    """
    npc_role = npc_data.get('role', '').lower()
    
    # High-importance NPCs: forced miss
    if any(role in npc_role for role in ['lord', 'ruler', 'king', 'queen', 'faction leader']):
        return "forced_miss"
    
    # Quest givers and important NPCs: forced non-lethal if hit lands
    if any(role in npc_role for role in ['quest', 'elder', 'master']):
        return "forced_non_lethal"
    
    # In civilized areas: generally forced miss due to intervention
    if location_type in ['town', 'city']:
        return "forced_miss"
    
    # Default: allow mechanical resolution but force non-lethal
    return "forced_non_lethal"


def apply_plot_armor_consequences(
    world_state: Dict[str, Any],
    character_state: Dict[str, Any],
    consequences: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Apply plot armor consequences to world state and character state.
    
    DMG p.32, p.74: Apply consequences and track for escalation
    
    Returns:
        {
            "world_state_update": dict,
            "character_state_update": dict,
            "applied_consequences": list of strings
        }
    """
    from services.consequence_service import ConsequenceEscalation
    
    world_state_update = {}
    character_state_update = {}
    applied_consequences = []
    
    for consequence in consequences:
        consequence_type = consequence.get('type')
        
        if consequence_type == 'reputation_change':
            # Update reputation
            faction = consequence.get('faction', 'Local Citizens')
            amount = consequence.get('amount', -10)
            
            reputation = character_state.get('reputation', {})
            current_rep = reputation.get(faction, 0)
            reputation[faction] = current_rep + amount
            character_state_update['reputation'] = reputation
            
            applied_consequences.append(f"Reputation with {faction}: {amount:+d}")
            
            # Track transgression for escalation (DMG p.74)
            ConsequenceEscalation.track_transgression(
                world_state,
                target_id=faction,
                action="reputation_damage",
                severity="minor"
            )
        
        elif consequence_type == 'bounty_added':
            # Add bounty flag to world state
            bounties = world_state.get('bounties', [])
            bounty_amount = consequence.get('amount', 50)
            bounties.append({
                "amount": bounty_amount,
                "reason": consequence.get('description', 'Criminal act'),
                "active": True
            })
            world_state_update['bounties'] = bounties
            
            applied_consequences.append(f"Bounty added: {bounty_amount} gold")
            
            # Track as severe transgression (DMG p.32)
            ConsequenceEscalation.track_transgression(
                world_state,
                target_id="city_authority",
                action="bounty_posted",
                severity="severe"
            )
        
        elif consequence_type == 'guard_intervention':
            # Set world state flag
            world_state_update['guard_alert'] = True
            world_state_update['last_offense'] = 'assault'
            
            applied_consequences.append("Guards are now hostile")
            
            # Track as moderate transgression (DMG p.32)
            ConsequenceEscalation.track_transgression(
                world_state,
                target_id="city_guard",
                action="guard_intervention",
                severity="moderate"
            )
        
        elif consequence_type == 'quest_blocked':
            # Mark quest giver as hostile
            applied_consequences.append("Quest giver refuses to work with you")
            
            # Track transgression
            ConsequenceEscalation.track_transgression(
                world_state,
                target_id="quest_giver",
                action="relationship_broken",
                severity="moderate"
            )
    
    return {
        "world_state_update": world_state_update,
        "character_state_update": character_state_update,
        "applied_consequences": applied_consequences
    }
