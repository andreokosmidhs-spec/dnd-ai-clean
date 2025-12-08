"""
Agent Roles Definition for E1 V2

Defines Coordinator and Executor roles with clear separation of concerns.
This establishes behavioral patterns without requiring separate processes.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class AgentRole(Enum):
    """Agent operating modes"""
    COORDINATOR = "coordinator"
    EXECUTOR = "executor"
    REVIEWER = "reviewer"
    TESTER = "tester"


@dataclass
class RoleDefinition:
    """Defines capabilities and constraints for an agent role"""
    name: str
    goal: str
    allowed_tools: List[str]
    forbidden_tools: List[str]
    constraints: List[str]
    inputs: List[str]
    outputs: List[str]


class CoordinatorRole:
    """
    Coordinator: Planning and delegation only, no direct code changes
    
    Responsibilities:
    - Read user requests
    - Load project state (project_summary.md, issues.json, tasks.json)
    - Create execution plan
    - Generate task envelopes for sub-agents
    - Select appropriate testing levels
    - Update project state after task completion
    - Communicate with user
    
    Constraints:
    - NEVER edit code files directly
    - NEVER run build/install commands
    - Keep plans ≤ 5 steps per user request
    - Always validate against policies before creating tasks
    """
    
    DEFINITION = RoleDefinition(
        name="Coordinator",
        goal="Turn user requests into executable plans and task envelopes",
        allowed_tools=[
            "mcp_view_file",
            "view_bulk",
            "mcp_glob_files",
            "mcp_execute_bash (read-only: git log, ls, cat, grep)",
            "ask_human",
            "finish",
            # Sub-agent delegation
            "integration_playbook_expert_v2",
            "troubleshoot_agent",
            "support_agent",
            # State management
            "state_manager functions",
            "policy_checker functions"
        ],
        forbidden_tools=[
            "mcp_create_file",
            "mcp_search_replace",
            "mcp_insert_text",
            "mcp_bulk_file_writer",
            "mcp_execute_bash (write operations)",
            "pip install",
            "yarn add",
            "npm install",
            "supervisor restart"
        ],
        constraints=[
            "Never edit code directly",
            "Plans must be ≤ 5 steps",
            "Always check policies before task creation",
            "Must load project_summary.md before planning",
            "Must create task envelopes (not freeform instructions)",
            "Must select testing level for each task"
        ],
        inputs=[
            "User request",
            "project_summary.md",
            "issues.json",
            "tasks.json",
            "testing_history.json"
        ],
        outputs=[
            "Execution plan",
            "Task envelopes (JSON)",
            "Testing plans (JSON)",
            "Updated state files",
            "User communication"
        ]
    )
    
    @staticmethod
    def create_execution_plan(
        user_request: str,
        project_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create structured execution plan from user request
        
        Returns:
            {
                "plan_id": str,
                "steps": List[Dict],
                "task_envelopes": List[Dict],
                "testing_plan": Dict,
                "estimated_duration": str
            }
        """
        # Template for Coordinator behavior
        return {
            "plan_id": "plan-001",
            "steps": [],
            "task_envelopes": [],
            "testing_plan": {},
            "estimated_duration": "medium"
        }
    
    @staticmethod
    def validate_plan_against_policies(
        plan: Dict[str, Any],
        policies: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate execution plan against safety policies
        
        Returns:
            {
                "valid": bool,
                "violations": List[str],
                "warnings": List[str]
            }
        """
        from state_manager import PolicyChecker
        
        violations = []
        warnings = []
        
        # Check each task envelope
        for envelope in plan.get("task_envelopes", []):
            # Check for protected env vars
            if "env" in envelope.get("goal", "").lower():
                # Extract var names and check
                pass
            
            # Check for forbidden operations
            if any(forbidden in envelope.get("goal", "") for forbidden in ["npm install", "git reset"]):
                violations.append(f"Task {envelope.get('task_id')} contains forbidden operation")
        
        return {
            "valid": len(violations) == 0,
            "violations": violations,
            "warnings": warnings
        }


class ExecutorRole:
    """
    Executor: Code changes only, follows task envelope
    
    Responsibilities:
    - Receive task envelope (JSON)
    - Read related files
    - Make code changes to accomplish goal
    - Run tests as specified
    - Return task response (JSON)
    
    Constraints:
    - Only work on files specified in task envelope
    - Respect "must_not" constraints
    - Stay within max_steps limit
    - Only edit files, never plan or communicate with user directly
    """
    
    DEFINITION = RoleDefinition(
        name="Executor",
        goal="Implement code changes for a single task envelope",
        allowed_tools=[
            "mcp_view_file",
            "view_bulk",
            "mcp_glob_files",
            "mcp_create_file",
            "mcp_search_replace",
            "mcp_insert_text",
            "mcp_bulk_file_writer",
            "mcp_lint_python",
            "mcp_lint_javascript",
            "mcp_execute_bash (build/test commands)",
            # Testing
            "mcp_screenshot_tool",
            "deep_testing_backend_v2",
            "auto_frontend_testing_agent"
        ],
        forbidden_tools=[
            "ask_human",
            "finish",
            "integration_playbook_expert_v2 (Coordinator delegates this)",
            "troubleshoot_agent (escalate to Coordinator)",
            "support_agent"
        ],
        constraints=[
            "Only edit files in task envelope context.related_files",
            "Respect task envelope constraints.must_not",
            "Stay within constraints.max_steps",
            "Never communicate with user directly",
            "Always run linter after code changes",
            "Must follow testing plan provided by Coordinator"
        ],
        inputs=[
            "Task envelope (JSON)",
            "Related file paths",
            "Testing plan (JSON)"
        ],
        outputs=[
            "Task response (JSON)",
            "File changes list",
            "Test results",
            "Git diff"
        ]
    )
    
    @staticmethod
    def execute_task(envelope: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single task following the envelope
        
        Returns task response (JSON)
        """
        # Template for Executor behavior
        return {
            "task_id": envelope["task_id"],
            "status": "completed",
            "summary": "Task completed successfully",
            "file_changes": [],
            "test_results": {},
            "notes": []
        }


class ReviewerRole:
    """
    Reviewer: Static checks and linting (optional)
    
    Responsibilities:
    - Run linters on changed files
    - Check for common issues
    - Provide feedback (no changes)
    
    Constraints:
    - Read-only, never edit files
    - Focus on touched files only
    """
    
    DEFINITION = RoleDefinition(
        name="Reviewer",
        goal="Perform static checks on code changes",
        allowed_tools=[
            "mcp_view_file",
            "view_bulk",
            "mcp_lint_python",
            "mcp_lint_javascript"
        ],
        forbidden_tools=[
            "Any file editing tools",
            "mcp_execute_bash (write operations)"
        ],
        constraints=[
            "Read-only access",
            "Only review files in task response.file_changes",
            "Provide guidance, not fixes"
        ],
        inputs=[
            "Task response (JSON)",
            "List of changed files"
        ],
        outputs=[
            "Review report",
            "Lint findings",
            "Recommendations"
        ]
    )
    
    @staticmethod
    def review_changes(file_changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Review code changes and return findings
        
        Returns:
            {
                "status": "approved|needs_work",
                "lint_results": Dict,
                "recommendations": List[str]
            }
        """
        return {
            "status": "approved",
            "lint_results": {},
            "recommendations": []
        }


class TesterRole:
    """
    Tester: Execute testing plans
    
    Responsibilities:
    - Receive testing plan (JSON)
    - Execute tests at specified level
    - Log results
    - Return test response
    
    Constraints:
    - Follow testing plan exactly
    - Obey time budgets
    - Update testing_history.json
    """
    
    DEFINITION = RoleDefinition(
        name="Tester",
        goal="Execute structured testing plans",
        allowed_tools=[
            "mcp_execute_bash (curl, test scripts)",
            "mcp_screenshot_tool",
            "deep_testing_backend_v2",
            "auto_frontend_testing_agent"
        ],
        forbidden_tools=[
            "Any file editing tools",
            "ask_human"
        ],
        constraints=[
            "Follow testing plan constraints",
            "Respect max_duration_seconds",
            "Update testing_history.json with results"
        ],
        inputs=[
            "Testing plan (JSON)"
        ],
        outputs=[
            "Test results (JSON)",
            "Screenshots (paths)",
            "Updated testing_history.json"
        ]
    )


# Workflow orchestration logic
class WorkflowOrchestrator:
    """
    Manages workflow between Coordinator and Executors
    
    Typical flow:
    1. Coordinator receives user request
    2. Coordinator creates execution plan + task envelopes
    3. Coordinator validates against policies
    4. Coordinator hands off to Executor(s)
    5. Executor(s) implement changes, return responses
    6. Reviewer (optional) checks changes
    7. Tester executes testing plan
    8. Coordinator updates state, communicates results to user
    """
    
    @staticmethod
    def coordinator_to_executor_handoff(
        task_envelope: Dict[str, Any]
    ) -> str:
        """
        Generate handoff message from Coordinator to Executor
        
        Returns: Formatted instruction for Executor
        """
        return f"""
# EXECUTOR MODE: Task {task_envelope['task_id']}

You are now operating as an Executor. Your role is to implement code changes only.

## Task Envelope:
```json
{json.dumps(task_envelope, indent=2)}
```

## Your Constraints:
- Only edit files in context.related_files
- Respect constraints.must_not
- Stay within {task_envelope['constraints']['max_steps']} steps
- Do NOT communicate with user
- Return task response in JSON format

## Success Criteria:
{chr(10).join('- ' + c for c in task_envelope['success_criteria'])}

Begin implementation now.
"""
    
    @staticmethod
    def executor_to_coordinator_handoff(
        task_response: Dict[str, Any]
    ) -> str:
        """
        Process Executor response and return to Coordinator mode
        
        Returns: Summary for Coordinator
        """
        return f"""
# COORDINATOR MODE: Task {task_response['task_id']} Complete

Executor has completed task with status: {task_response['status']}

## Summary:
{task_response['summary']}

## Files Changed:
{chr(10).join('- ' + fc['path'] + ' (' + fc['change_type'] + ')' for fc in task_response.get('file_changes', []))}

## Next Steps:
1. Update task status in tasks.json
2. Run testing plan
3. Communicate results to user
"""


# Usage documentation
USAGE_GUIDE = """
# E1 V2 Agent Roles - Usage Guide

## Coordinator Mode (Default)

When receiving user request:
1. Load project_summary.md
2. Load relevant state files (issues, tasks)
3. Create execution plan (≤ 5 steps)
4. Generate task envelopes for each step
5. Validate against policies
6. Ask user for confirmation
7. Hand off to Executor

**Tools to use:**
- view_bulk (load multiple state files)
- PolicyChecker.check_* (validate operations)
- SchemaValidator.create_task_envelope (create envelopes)
- TestingLevels.recommend_level (choose test level)

## Executor Mode (During Implementation)

When implementing a task:
1. Receive task envelope (JSON)
2. Read related files
3. Make code changes
4. Run linter
5. Create task response (JSON)
6. Return to Coordinator

**Tools to use:**
- view_bulk (read files)
- mcp_bulk_file_writer (write multiple files)
- mcp_lint_* (run linters)
- Don't use ask_human or finish

## Reviewer Mode (Optional)

After Executor completes:
1. Receive file_changes list
2. Run linters on changed files
3. Provide recommendations
4. Return to Coordinator

## Tester Mode

When executing tests:
1. Receive testing plan (JSON)
2. Execute at specified level (L0-L3)
3. Log results to testing_history.json
4. Return test results to Coordinator
"""


if __name__ == "__main__":
    print("Agent Roles Defined:")
    print(f"- Coordinator: {CoordinatorRole.DEFINITION.goal}")
    print(f"- Executor: {ExecutorRole.DEFINITION.goal}")
    print(f"- Reviewer: {ReviewerRole.DEFINITION.goal}")
    print(f"- Tester: {TesterRole.DEFINITION.goal}")
    print("\nSee USAGE_GUIDE for implementation details")
