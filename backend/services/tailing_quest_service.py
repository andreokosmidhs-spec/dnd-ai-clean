"""
Tailing Quest Service
Automatically creates and manages quests when player tails/follows someone
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import random

logger = logging.getLogger(__name__)


class TailingQuestService:
    """Service for creating and managing tailing quests"""
    
    @staticmethod
    def detect_tailing_intent(action: str) -> Optional[Dict[str, str]]:
        """
        Detect if player is trying to tail/follow someone
        
        Returns:
            Dict with target info if tailing detected, None otherwise
        """
        action_lower = action.lower()
        
        # Tailing keywords
        tailing_keywords = [
            'follow', 'tail', 'track', 'shadow', 'pursue',
            'keep an eye on', 'watch where', 'see where',
            'trail', 'stalk', 'spy on'
        ]
        
        # Check if action contains tailing intent
        for keyword in tailing_keywords:
            if keyword in action_lower:
                # Extract target (simplified - could be enhanced)
                target = "the target"  # Default
                
                # Try to extract target name from action
                if 'the ' in action_lower:
                    parts = action_lower.split('the ')
                    if len(parts) > 1:
                        potential_target = parts[1].split(' ')[0:3]
                        target = ' '.join(potential_target).strip('.,!?')
                
                return {
                    "intent": "tailing",
                    "target": target,
                    "keyword": keyword
                }
        
        return None
    
    @staticmethod
    async def create_tailing_quest(
        campaign_id: str,
        character_id: str,
        target_name: str,
        location: str,
        world_state: Dict[str, Any],
        db
    ) -> Dict[str, Any]:
        """
        Create a new tailing quest
        
        Returns quest data with events
        """
        from services.quest_service import create_simple_quest
        
        quest_id = f"tail_{target_name.replace(' ', '_')}_{datetime.now(timezone.utc).timestamp()}"
        
        # Create quest
        quest_data = {
            "quest_id": quest_id,
            "title": f"Shadow {target_name.title()}",
            "description": f"Follow {target_name} discreetly and discover where they go and what they're planning.",
            "type": "investigation",
            "status": "active",
            "objectives": [
                {
                    "id": "stay_undetected",
                    "description": "Tail without being spotted",
                    "completed": False,
                    "required": True
                },
                {
                    "id": "discover_destination",
                    "description": "Find out where they're headed",
                    "completed": False,
                    "required": True
                },
                {
                    "id": "uncover_motive",
                    "description": "Learn what they're doing",
                    "completed": False,
                    "required": False
                }
            ],
            "information_gathered": [],
            "detection_level": 0,  # 0-100, if reaches 100, target knows they're being followed
            "events_completed": 0,
            "total_events": 3,
            "rewards": {
                "xp": 50,
                "information": "Valuable intelligence",
                "reputation": 1
            }
        }
        
        # Store quest in campaign log
        await create_simple_quest(
            campaign_id=campaign_id,
            quest_data=quest_data,
            db=db
        )
        
        logger.info(f"✨ Created tailing quest: {quest_id}")
        
        return quest_data
    
    @staticmethod
    def generate_tailing_event(
        detection_level: int,
        events_completed: int,
        location: str,
        target_name: str
    ) -> Dict[str, Any]:
        """
        Generate a tailing event that requires a check
        
        Returns event with check requirement and potential information
        """
        
        # Event templates based on detection level
        if events_completed == 0:
            # First event - initial tail
            events = [
                {
                    "check_type": "stealth",
                    "ability": "DEX",
                    "skill": "Stealth",
                    "dc": 13,
                    "reason": f"{target_name.title()} glances back while walking",
                    "on_success_info": f"{target_name.title()} heads toward the docks district, checking over shoulder frequently",
                    "on_fail_info": f"{target_name.title()} seems alert but continues moving",
                    "detection_gain_fail": 25
                },
                {
                    "check_type": "stealth",
                    "ability": "DEX",
                    "skill": "Stealth",
                    "dc": 12,
                    "reason": f"{target_name.title()} enters a crowded area - maintain distance",
                    "on_success_info": f"{target_name.title()} pushes through the crowd toward the market square",
                    "on_fail_info": "You lose sight momentarily in the crowd",
                    "detection_gain_fail": 20
                }
            ]
        elif events_completed == 1:
            # Mid-tail events - investigation/perception
            events = [
                {
                    "check_type": "perception",
                    "ability": "WIS",
                    "skill": "Perception",
                    "dc": 14,
                    "reason": f"{target_name.title()} meets someone - observe from distance",
                    "on_success_info": f"{target_name.title()} exchanges a sealed package with a hooded figure. You catch a glimpse of a red wax seal",
                    "on_fail_info": f"{target_name.title()} has a brief conversation with someone",
                    "detection_gain_fail": 15
                },
                {
                    "check_type": "investigation",
                    "ability": "INT",
                    "skill": "Investigation",
                    "dc": 13,
                    "reason": f"{target_name.title()} enters a building - study the surroundings",
                    "on_success_info": f"The building is a warehouse with 'Shipping Co.' on the door. Two guards posted outside. Loading bay in back",
                    "on_fail_info": "It's some kind of warehouse or shop",
                    "detection_gain_fail": 10
                }
            ]
        else:
            # Final event - crucial information
            events = [
                {
                    "check_type": "perception",
                    "ability": "WIS",
                    "skill": "Perception",
                    "dc": 15,
                    "reason": f"{target_name.title()} speaks in hushed tones - try to overhear",
                    "on_success_info": f"You overhear: '...midnight shipment...east gate...tell no one...' {target_name.title()} hands over a coin purse",
                    "on_fail_info": f"You can't make out the words but money changes hands",
                    "detection_gain_fail": 15
                },
                {
                    "check_type": "stealth",
                    "ability": "DEX",
                    "skill": "Stealth",
                    "dc": 16,
                    "reason": f"{target_name.title()} suddenly stops and looks around suspiciously",
                    "on_success_info": f"You duck into a doorway just in time. {target_name.title()} shrugs and continues to a basement entrance",
                    "on_fail_info": f"{target_name.title()}'s eyes narrow in your direction",
                    "detection_gain_fail": 35
                }
            ]
        
        return random.choice(events)
    
    @staticmethod
    async def process_tailing_check_result(
        campaign_id: str,
        quest_id: str,
        check_success: bool,
        event_data: Dict[str, Any],
        db
    ) -> Dict[str, Any]:
        """
        Process the result of a tailing check and update quest progress
        
        Returns updated quest data
        """
        # Fetch quest from campaign log
        campaign_doc = await db.campaigns.find_one({"campaign_id": campaign_id})
        if not campaign_doc:
            return {}
        
        world_state = campaign_doc.get("world_state", {})
        active_quests = world_state.get("active_quests", {})
        
        if quest_id not in active_quests:
            logger.warning(f"Quest {quest_id} not found in active quests")
            return {}
        
        quest = active_quests[quest_id]
        
        # Update detection level
        if not check_success:
            quest["detection_level"] = min(100, quest["detection_level"] + event_data.get("detection_gain_fail", 0))
        
        # Add information
        info_key = "on_success_info" if check_success else "on_fail_info"
        new_info = event_data.get(info_key, "")
        if new_info and new_info not in quest.get("information_gathered", []):
            quest.setdefault("information_gathered", []).append({
                "info": new_info,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "success": check_success
            })
        
        # Update events completed
        quest["events_completed"] = quest.get("events_completed", 0) + 1
        
        # Check if quest should complete
        if quest["detection_level"] >= 100:
            quest["status"] = "failed"
            quest["failure_reason"] = "Detected by target"
        elif quest["events_completed"] >= quest.get("total_events", 3):
            quest["status"] = "completed"
            # Mark objectives complete
            for obj in quest.get("objectives", []):
                if obj["id"] in ["stay_undetected", "discover_destination"]:
                    obj["completed"] = True
        
        # Save back to world state
        active_quests[quest_id] = quest
        world_state["active_quests"] = active_quests
        
        await db.campaigns.update_one(
            {"campaign_id": campaign_id},
            {"$set": {"world_state": world_state}}
        )
        
        logger.info(f"📊 Updated tailing quest: {quest_id}, detection: {quest['detection_level']}, events: {quest['events_completed']}")
        
        return quest
