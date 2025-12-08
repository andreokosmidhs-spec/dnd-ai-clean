"""
E1 V2: Project State Manager
Manages normalized project state in /app/meta/
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

META_DIR = Path("/app/meta")
SCHEMAS_DIR = META_DIR / "schemas"
POLICIES_DIR = META_DIR / "policies"


class ProjectStateManager:
    """Manages project state files"""
    
    @staticmethod
    def load_project_state() -> Dict[str, Any]:
        """Load project_state.json"""
        with open(META_DIR / "project_state.json") as f:
            return json.load(f)
    
    @staticmethod
    def save_project_state(state: Dict[str, Any]):
        """Save project_state.json"""
        state["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(META_DIR / "project_state.json", "w") as f:
            json.dump(state, f, indent=2)
    
    @staticmethod
    def load_issues() -> Dict[str, Any]:
        """Load issues.json"""
        with open(META_DIR / "issues.json") as f:
            return json.load(f)
    
    @staticmethod
    def save_issues(issues: Dict[str, Any]):
        """Save issues.json"""
        with open(META_DIR / "issues.json", "w") as f:
            json.dump(issues, f, indent=2)
    
    @staticmethod
    def add_issue(issue: Dict[str, Any]):
        """Add new issue"""
        issues_data = ProjectStateManager.load_issues()
        issues_data["issues"].append(issue)
        
        # Update stats
        issues_data["issue_stats"]["total"] = len(issues_data["issues"])
        issues_data["issue_stats"]["open"] = sum(
            1 for i in issues_data["issues"] if i["status"] == "open"
        )
        issues_data["issue_stats"]["resolved"] = sum(
            1 for i in issues_data["issues"] if i["status"] == "resolved"
        )
        
        ProjectStateManager.save_issues(issues_data)
    
    @staticmethod
    def update_issue_status(issue_id: str, status: str, resolution: Optional[str] = None):
        """Update issue status"""
        issues_data = ProjectStateManager.load_issues()
        
        for issue in issues_data["issues"]:
            if issue["id"] == issue_id:
                issue["status"] = status
                if status == "resolved":
                    issue["resolved_at"] = datetime.now(timezone.utc).isoformat()
                    issue["resolution"] = resolution
                break
        
        # Update stats
        issues_data["issue_stats"]["open"] = sum(
            1 for i in issues_data["issues"] if i["status"] == "open"
        )
        issues_data["issue_stats"]["resolved"] = sum(
            1 for i in issues_data["issues"] if i["status"] == "resolved"
        )
        
        ProjectStateManager.save_issues(issues_data)
    
    @staticmethod
    def load_tasks() -> Dict[str, Any]:
        """Load tasks.json"""
        with open(META_DIR / "tasks.json") as f:
            return json.load(f)
    
    @staticmethod
    def save_tasks(tasks: Dict[str, Any]):
        """Save tasks.json"""
        with open(META_DIR / "tasks.json", "w") as f:
            json.dump(tasks, f, indent=2)
    
    @staticmethod
    def add_task(task: Dict[str, Any], task_type: str = "backlog"):
        """Add new task to appropriate list"""
        tasks_data = ProjectStateManager.load_tasks()
        
        if task_type == "active":
            tasks_data["active_tasks"].append(task)
        elif task_type == "in_progress":
            tasks_data["in_progress_tasks"].append(task)
        elif task_type == "completed":
            tasks_data["completed_tasks"].append(task)
        else:
            tasks_data["backlog"].append(task)
        
        # Update stats
        tasks_data["task_stats"]["total"] = (
            len(tasks_data["active_tasks"]) +
            len(tasks_data["in_progress_tasks"]) +
            len(tasks_data["completed_tasks"]) +
            len(tasks_data["backlog"])
        )
        tasks_data["task_stats"]["active"] = len(tasks_data["active_tasks"])
        tasks_data["task_stats"]["in_progress"] = len(tasks_data["in_progress_tasks"])
        tasks_data["task_stats"]["completed"] = len(tasks_data["completed_tasks"])
        tasks_data["task_stats"]["backlog"] = len(tasks_data["backlog"])
        
        ProjectStateManager.save_tasks(tasks_data)
    
    @staticmethod
    def move_task(task_id: str, from_list: str, to_list: str):
        """Move task between lists"""
        tasks_data = ProjectStateManager.load_tasks()
        
        # Find and remove from source
        task = None
        source_list = tasks_data[f"{from_list}_tasks" if from_list != "backlog" else "backlog"]
        for i, t in enumerate(source_list):
            if t["id"] == task_id:
                task = source_list.pop(i)
                break
        
        if not task:
            return False
        
        # Update status
        task["status"] = to_list
        if to_list == "completed":
            task["completed_at"] = datetime.now(timezone.utc).isoformat()
        
        # Add to destination
        dest_list = tasks_data[f"{to_list}_tasks" if to_list != "backlog" else "backlog"]
        dest_list.append(task)
        
        # Update stats
        tasks_data["task_stats"]["active"] = len(tasks_data["active_tasks"])
        tasks_data["task_stats"]["in_progress"] = len(tasks_data["in_progress_tasks"])
        tasks_data["task_stats"]["completed"] = len(tasks_data["completed_tasks"])
        tasks_data["task_stats"]["backlog"] = len(tasks_data["backlog"])
        
        ProjectStateManager.save_tasks(tasks_data)
        return True
    
    @staticmethod
    def load_testing_history() -> Dict[str, Any]:
        """Load testing_history.json"""
        with open(META_DIR / "testing_history.json") as f:
            return json.load(f)
    
    @staticmethod
    def save_testing_history(history: Dict[str, Any]):
        """Save testing_history.json"""
        with open(META_DIR / "testing_history.json", "w") as f:
            json.dump(history, f, indent=2)
    
    @staticmethod
    def add_test_run(test_run: Dict[str, Any]):
        """Add new test run"""
        history = ProjectStateManager.load_testing_history()
        history["test_runs"].append(test_run)
        
        # Update stats
        history["test_stats"]["total_runs"] = len(history["test_runs"])
        history["test_stats"]["total_tests"] = sum(
            run["results"]["total"] for run in history["test_runs"]
        )
        total_passed = sum(run["results"]["passed"] for run in history["test_runs"])
        total_tests = history["test_stats"]["total_tests"]
        history["test_stats"]["overall_pass_rate"] = (
            total_passed / total_tests if total_tests > 0 else 0
        )
        history["test_stats"]["last_run"] = test_run["timestamp"]
        
        ProjectStateManager.save_testing_history(history)
    
    @staticmethod
    def load_architecture() -> Dict[str, Any]:
        """Load architecture.json"""
        with open(META_DIR / "architecture.json") as f:
            return json.load(f)


class HandoffSummarizer:
    """Generates compact handoff summary from state files"""
    
    @staticmethod
    def generate_handoff_summary() -> str:
        """Generate handoff summary from meta files"""
        project_state = ProjectStateManager.load_project_state()
        issues = ProjectStateManager.load_issues()
        tasks = ProjectStateManager.load_tasks()
        testing = ProjectStateManager.load_testing_history()
        arch = ProjectStateManager.load_architecture()
        
        summary = f"""# HANDOFF SUMMARY V2 (Generated from /app/meta/)

## PROJECT OVERVIEW
- **Name:** {project_state['project_name']}
- **Health:** {project_state['health_status']}
- **Phase:** {project_state['current_phase']}
- **Stack:** {project_state['stack']['frontend']['framework']} + {project_state['stack']['backend']['framework']} + {project_state['stack']['database']['type']}

## CURRENT STATUS

### Open Issues ({issues['issue_stats']['open']} total)
"""
        
        # Add open issues
        open_issues = [i for i in issues['issues'] if i['status'] == 'open']
        for issue in sorted(open_issues, key=lambda x: x['priority']):
            summary += f"- **[{issue['priority']}] {issue['title']}** ({issue['type']})\n"
            summary += f"  Files: {', '.join(issue['files_affected'])}\n"
        
        summary += f"\n### Active Tasks ({tasks['task_stats']['active']} active, {tasks['task_stats']['in_progress']} in progress)\n"
        
        # Add active/in-progress tasks
        for task in tasks['active_tasks'] + tasks['in_progress_tasks']:
            summary += f"- **{task['title']}** ({task['status']})\n"
        
        summary += f"\n### Recently Completed ({len(tasks['completed_tasks'][-3:])} last 3)\n"
        
        # Add last 3 completed
        for task in tasks['completed_tasks'][-3:]:
            summary += f"- {task['title']} (completed {task['completed_at'][:10]})\n"
        
        summary += f"\n### Backlog ({tasks['task_stats']['backlog']} items)\n"
        
        # Add high-priority backlog items
        for task in [t for t in tasks['backlog'] if t.get('priority', 'P3') in ['P1', 'P2']][:3]:
            summary += f"- [{task.get('priority', 'P3')}] {task['title']}\n"
        
        summary += f"\n## TESTING STATUS\n"
        summary += f"- **Total Runs:** {testing['test_stats']['total_runs']}\n"
        summary += f"- **Pass Rate:** {testing['test_stats']['overall_pass_rate']:.1%}\n"
        summary += f"- **Last Run:** {testing['test_stats']['last_run'][:10]}\n"
        
        # Add known test gaps
        if testing['known_test_gaps']:
            summary += f"\n**Test Gaps:**\n"
            for gap in testing['known_test_gaps'][:3]:
                summary += f"- {gap}\n"
        
        summary += f"\n## ARCHITECTURE\n"
        summary += f"**Backend Services:** {len(arch['backend']['structure']['services']['categories']['phase1_dmg_systems']) + len(arch['backend']['structure']['services']['categories']['phase2_aversion_systems'])} active\n"
        summary += f"**Key Endpoints:** {len(arch['backend']['key_endpoints'])}\n"
        summary += f"**Frontend Components:** {len(arch['frontend']['structure']['components']['key_files'])}\n"
        
        summary += f"\n## CRITICAL CONSTRAINTS\n"
        for constraint, items in project_state['critical_constraints'].items():
            if isinstance(items, list):
                summary += f"- **{constraint.replace('_', ' ').title()}:** {', '.join(items)}\n"
        
        summary += f"\n---\n**Full state available in /app/meta/**\n"
        summary += f"**Last Updated:** {project_state['last_updated']}\n"
        
        return summary
    
    @staticmethod
    def save_handoff_summary():
        """Generate and save handoff summary"""
        summary = HandoffSummarizer.generate_handoff_summary()
        with open("/app/HANDOFF_SUMMARY_V2.md", "w") as f:
            f.write(summary)
        return summary



class PolicyChecker:
    """Validates operations against safety policies"""
    
    @staticmethod
    def load_env_policy() -> Dict[str, Any]:
        """Load environment variable policy"""
        with open(META_DIR / "policies" / "env_policy.json") as f:
            return json.load(f)
    
    @staticmethod
    def load_deps_policy() -> Dict[str, Any]:
        """Load dependency management policy"""
        with open(META_DIR / "policies" / "deps_policy.json") as f:
            return json.load(f)
    
    @staticmethod
    def check_env_modification(var_name: str, file_path: str = None) -> Dict[str, Any]:
        """
        Check if environment variable can be modified
        Returns: {"allowed": bool, "reason": str, "suggestion": str}
        """
        policy = PolicyChecker.load_env_policy()
        
        # Check protected variables
        all_protected = []
        for env_type, vars_list in policy["protected_variables"].items():
            if env_type != "description":
                all_protected.extend(vars_list)
        
        if var_name in all_protected:
            return {
                "allowed": False,
                "reason": f"{var_name} is a protected variable configured for Kubernetes",
                "suggestion": "This variable must not be modified. Use a different variable name."
            }
        
        # Check forbidden patterns
        import fnmatch
        for pattern in policy["forbidden_patterns"]:
            if fnmatch.fnmatch(var_name, pattern):
                # Check if it's in allowed modifications
                allowed_patterns = policy["allowed_modifications"]["patterns"]
                is_allowed = any(fnmatch.fnmatch(var_name, ap) for ap in allowed_patterns)
                
                if not is_allowed:
                    return {
                        "allowed": False,
                        "reason": f"{var_name} matches forbidden pattern {pattern}",
                        "suggestion": "Sensitive variables should be handled carefully. Use approved patterns only."
                    }
        
        return {
            "allowed": True,
            "reason": "Variable is not protected",
            "suggestion": "Ensure value is not hardcoded in source files"
        }
    
    @staticmethod
    def check_dependency_operation(command: str) -> Dict[str, Any]:
        """
        Check if dependency operation is allowed
        Returns: {"allowed": bool, "reason": str, "correct_command": str}
        """
        policy = PolicyChecker.load_deps_policy()
        
        # Check forbidden operations
        for forbidden_op in policy["forbidden_operations"]:
            if forbidden_op in command:
                # Suggest correct alternative
                if "npm" in command:
                    return {
                        "allowed": False,
                        "reason": "npm is forbidden - use yarn instead",
                        "correct_command": command.replace("npm install", "yarn add").replace("npm i", "yarn add")
                    }
                elif "pip install" in command and "pip freeze" not in command:
                    pkg = command.replace("pip install", "").strip()
                    return {
                        "allowed": False,
                        "reason": "pip install must update requirements.txt",
                        "correct_command": f"pip install {pkg} && pip freeze > /app/backend/requirements.txt"
                    }
        
        # Check allowed operations
        for allowed_op in policy["allowed_operations"]:
            if any(allowed_part in command for allowed_part in allowed_op.split()):
                return {
                    "allowed": True,
                    "reason": "Operation follows dependency policy",
                    "correct_command": command
                }
        
        return {
            "allowed": False,
            "reason": "Command does not match allowed operations",
            "correct_command": "Use 'yarn add <pkg>' or 'pip install <pkg> && pip freeze > requirements.txt'"
        }
    
    @staticmethod
    def check_rollback_intent(user_message: str) -> bool:
        """
        Check if user is requesting a rollback
        Returns: True if rollback phrases detected
        """
        rollback_phrases = [
            "revert", "rollback", "go back", "undo",
            "restore", "previous version", "last working",
            "undo all changes", "revert everything"
        ]
        
        message_lower = user_message.lower()
        return any(phrase in message_lower for phrase in rollback_phrases)
    
    @staticmethod
    def check_git_operation(command: str) -> Dict[str, Any]:
        """
        Check if git operation is safe
        Returns: {"allowed": bool, "reason": str, "suggestion": str}
        """
        forbidden_git_ops = [
            "git reset", "git revert", "git checkout",
            "rm -rf .git", "git clean -fd", "git reset --hard"
        ]
        
        for forbidden_op in forbidden_git_ops:
            if forbidden_op in command:
                return {
                    "allowed": False,
                    "reason": f"'{forbidden_op}' is forbidden - may cause environment issues",
                    "suggestion": "Use platform Rollback feature instead. See /app/meta/ROLLBACK_GUIDE.md"
                }
        
        # Allowed git operations
        allowed_git_ops = ["git status", "git log", "git diff", "git commit", "git branch"]
        if any(allowed_op in command for allowed_op in allowed_git_ops):
            return {
                "allowed": True,
                "reason": "Safe git operation",
                "suggestion": None
            }
        
        return {
            "allowed": False,
            "reason": "Unknown git operation",
            "suggestion": "Only use git status, log, diff, commit, branch"
        }



class SchemaValidator:
    """Validates task envelopes, responses, and testing plans against JSON schemas"""
    
    @staticmethod
    def load_schema(schema_name: str) -> Dict[str, Any]:
        """Load a JSON schema"""
        schema_path = SCHEMAS_DIR / f"{schema_name}.json"
        with open(schema_path) as f:
            return json.load(f)
    
    @staticmethod
    def validate_task_envelope(envelope: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate task envelope against schema
        Returns: {"valid": bool, "errors": List[str]}
        """
        errors = []
        
        # Required fields
        required = ["task_id", "task_type", "goal", "context", "constraints", "success_criteria", "expected_outputs"]
        for field in required:
            if field not in envelope:
                errors.append(f"Missing required field: {field}")
        
        if not errors and "task_id" in envelope:
            # Validate task_id format (e.g., 'bug-123')
            if not re.match(r"^[a-z]+-[0-9]+$", envelope["task_id"]):
                errors.append(f"task_id must match pattern '[type]-[number]' (e.g., 'bug-123')")
        
        if not errors and "task_type" in envelope:
            valid_types = ["feature", "bug_fix", "integration", "deployment", "exploration", "refactor", "test"]
            if envelope["task_type"] not in valid_types:
                errors.append(f"task_type must be one of: {valid_types}")
        
        if not errors and "goal" in envelope:
            if len(envelope["goal"]) < 10 or len(envelope["goal"]) > 500:
                errors.append("goal must be between 10 and 500 characters")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    @staticmethod
    def validate_task_response(response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate task response against schema
        Returns: {"valid": bool, "errors": List[str]}
        """
        errors = []
        
        # Required fields
        required = ["task_id", "status", "summary"]
        for field in required:
            if field not in response:
                errors.append(f"Missing required field: {field}")
        
        if not errors and "status" in response:
            valid_statuses = ["completed", "failed", "partial", "blocked"]
            if response["status"] not in valid_statuses:
                errors.append(f"status must be one of: {valid_statuses}")
        
        if not errors and "summary" in response:
            if len(response["summary"]) < 20 or len(response["summary"]) > 1000:
                errors.append("summary must be between 20 and 1000 characters")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    @staticmethod
    def validate_testing_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate testing plan against schema
        Returns: {"valid": bool, "errors": List[str]}
        """
        errors = []
        
        # Required fields
        required = ["plan_id", "level", "scope", "reason"]
        for field in required:
            if field not in plan:
                errors.append(f"Missing required field: {field}")
        
        if not errors and "plan_id" in plan:
            # Validate plan_id format (e.g., 'test-2025-11-24-001')
            if not re.match(r"^test-[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{3}$", plan["plan_id"]):
                errors.append("plan_id must match pattern 'test-YYYY-MM-DD-NNN'")
        
        if not errors and "level" in plan:
            if plan["level"] not in [0, 1, 2, 3]:
                errors.append("level must be 0, 1, 2, or 3")
        
        if not errors and "reason" in plan:
            if len(plan["reason"]) < 10:
                errors.append("reason must be at least 10 characters")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    @staticmethod
    def create_task_envelope(
        task_id: str,
        task_type: str,
        goal: str,
        related_files: List[str] = None,
        related_issues: List[str] = None,
        max_steps: int = 10,
        time_budget: str = "medium",
        must_not: List[str] = None,
        success_criteria: List[str] = None,
        expected_outputs: List[str] = None
    ) -> Dict[str, Any]:
        """
        Helper to create a valid task envelope
        """
        envelope = {
            "task_id": task_id,
            "task_type": task_type,
            "goal": goal,
            "context": {
                "project_state_path": "/app/meta/project_state.json",
                "related_files": related_files or [],
                "related_issues": related_issues or []
            },
            "constraints": {
                "max_steps": max_steps,
                "time_budget": time_budget,
                "must_not": must_not or []
            },
            "success_criteria": success_criteria or [goal],
            "expected_outputs": expected_outputs or ["summary", "file_changes", "test_results"]
        }
        
        validation = SchemaValidator.validate_task_envelope(envelope)
        if not validation["valid"]:
            raise ValueError(f"Invalid task envelope: {validation['errors']}")
        
        return envelope
    
    @staticmethod
    def create_testing_plan(
        plan_id: str,
        level: int,
        reason: str,
        endpoints: List[str] = None,
        ui_flows: List[str] = None,
        max_duration: int = 60,
        test_methods: List[str] = None
    ) -> Dict[str, Any]:
        """
        Helper to create a valid testing plan
        """
        plan = {
            "plan_id": plan_id,
            "level": level,
            "scope": {
                "endpoints": endpoints or [],
                "ui_flows": ui_flows or []
            },
            "reason": reason,
            "constraints": {
                "max_duration_seconds": max_duration
            },
            "test_methods": test_methods or (["curl"] if level <= 1 else ["testing_agent"])
        }
        
        validation = SchemaValidator.validate_testing_plan(plan)
        if not validation["valid"]:
            raise ValueError(f"Invalid testing plan: {validation['errors']}")
        
        return plan


# CLI usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "generate-handoff":
            summary = HandoffSummarizer.save_handoff_summary()
            print("Generated handoff summary:")
            print(summary)
        
        elif command == "show-issues":
            issues = ProjectStateManager.load_issues()
            print(json.dumps(issues, indent=2))
        
        elif command == "show-tasks":
            tasks = ProjectStateManager.load_tasks()
            print(json.dumps(tasks, indent=2))
        
        else:
            print(f"Unknown command: {command}")
            print("Available commands: generate-handoff, show-issues, show-tasks")
    else:
        print("Usage: python state_manager.py [command]")
