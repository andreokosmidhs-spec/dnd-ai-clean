"""
Testing Levels Framework for E1 V2

Defines tiered testing approach (L0-L3) to avoid timeout issues
and ensure appropriate test coverage.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import json
from pathlib import Path


class TestingLevels:
    """
    Defines testing levels and their characteristics
    
    L0: No tests (only if user explicitly waives)
    L1: Smoke tests (<15s) - 1-3 key endpoints, 1-2 UI flows
    L2: Focused suite (per feature/bug) - targeted testing
    L3: Full regression - only for major refactors or phase completion
    """
    
    LEVELS = {
        0: {
            "name": "No Tests",
            "max_duration": 0,
            "when_to_use": "Only if user explicitly says 'I'll test manually'",
            "must_log": True,
            "description": "No automated testing performed"
        },
        1: {
            "name": "Smoke Tests",
            "max_duration": 15,
            "when_to_use": "Always run after any non-trivial change",
            "methods": ["curl", "quick_playwright", "screenshot"],
            "description": "Fast validation of key functionality"
        },
        2: {
            "name": "Focused Suite",
            "max_duration": 60,
            "when_to_use": "Changes touching specific endpoints/components",
            "methods": ["testing_agent", "curl", "playwright"],
            "description": "Targeted testing of affected areas"
        },
        3: {
            "name": "Full Regression",
            "max_duration": 180,
            "when_to_use": "Major refactor, phase complete, or user request",
            "methods": ["testing_agent", "comprehensive_suite"],
            "description": "Complete test suite across all features"
        }
    }
    
    @staticmethod
    def get_level_info(level: int) -> Dict[str, Any]:
        """Get information about a testing level"""
        return TestingLevels.LEVELS.get(level, {})
    
    @staticmethod
    def recommend_level(
        change_type: str,
        files_changed: int,
        endpoints_affected: List[str],
        is_phase_complete: bool = False,
        user_requested_full: bool = False
    ) -> int:
        """
        Recommend appropriate testing level based on change characteristics
        
        Args:
            change_type: "bug_fix", "feature", "refactor", "config", etc.
            files_changed: Number of files modified
            endpoints_affected: List of API endpoints touched
            is_phase_complete: True if completing a major phase
            user_requested_full: True if user explicitly requested full testing
        
        Returns:
            Recommended testing level (0-3)
        """
        # User explicit request
        if user_requested_full:
            return 3
        
        # Phase completion
        if is_phase_complete:
            return 3
        
        # Major refactor with many files
        if change_type == "refactor" and files_changed >= 5:
            return 3
        
        # Feature with multiple endpoints or components
        if change_type == "feature" and (files_changed >= 3 or len(endpoints_affected) >= 3):
            return 2
        
        # Bug fix with specific scope
        if change_type == "bug_fix" and files_changed <= 3:
            return 2
        
        # Config changes, small fixes
        if change_type in ["config", "docs"] or files_changed <= 2:
            return 1
        
        # Default to focused testing
        return 2


class TestingPlanGenerator:
    """Generates structured testing plans based on context"""
    
    @staticmethod
    def generate_plan_id() -> str:
        """Generate unique plan ID: test-YYYY-MM-DD-NNN"""
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")
        
        # Load existing plans to get next sequence number
        meta_dir = Path("/app/meta")
        history_file = meta_dir / "testing_history.json"
        
        if history_file.exists():
            with open(history_file) as f:
                history = json.load(f)
                today_plans = [
                    run for run in history.get("test_runs", [])
                    if run.get("timestamp", "").startswith(date_str)
                ]
                seq = len(today_plans) + 1
        else:
            seq = 1
        
        return f"test-{date_str}-{seq:03d}"
    
    @staticmethod
    def create_smoke_test_plan(
        endpoints: List[str] = None,
        ui_flows: List[str] = None,
        reason: str = "Standard smoke test after code change"
    ) -> Dict[str, Any]:
        """
        Create L1 smoke test plan
        
        Args:
            endpoints: 1-3 key backend endpoints to test
            ui_flows: 1-2 key UI flows to test
            reason: Why this test is being run
        """
        plan_id = TestingPlanGenerator.generate_plan_id()
        
        return {
            "plan_id": plan_id,
            "level": 1,
            "scope": {
                "endpoints": endpoints or [],
                "ui_flows": ui_flows or []
            },
            "reason": reason,
            "constraints": {
                "max_duration_seconds": 15
            },
            "test_methods": ["curl", "screenshot"]
        }
    
    @staticmethod
    def create_focused_test_plan(
        task_id: str,
        endpoints: List[str],
        ui_flows: List[str] = None,
        services: List[str] = None,
        reason: str = None
    ) -> Dict[str, Any]:
        """
        Create L2 focused test plan for specific task
        
        Args:
            task_id: ID of task being tested
            endpoints: Backend endpoints touched by this task
            ui_flows: Frontend flows affected
            services: Backend services to validate
            reason: Why this level of testing is appropriate
        """
        plan_id = TestingPlanGenerator.generate_plan_id()
        
        default_reason = f"Focused testing for {task_id}: {len(endpoints)} endpoints, {len(ui_flows or [])} UI flows affected"
        
        return {
            "plan_id": plan_id,
            "level": 2,
            "scope": {
                "endpoints": endpoints,
                "ui_flows": ui_flows or [],
                "services": services or []
            },
            "reason": reason or default_reason,
            "constraints": {
                "max_duration_seconds": 60
            },
            "test_methods": ["testing_agent", "curl"]
        }
    
    @staticmethod
    def create_regression_plan(
        reason: str = "Full regression suite"
    ) -> Dict[str, Any]:
        """
        Create L3 full regression plan
        
        Args:
            reason: Why full regression is needed
        """
        plan_id = TestingPlanGenerator.generate_plan_id()
        
        return {
            "plan_id": plan_id,
            "level": 3,
            "scope": {
                "endpoints": ["all"],
                "ui_flows": ["all"],
                "services": ["all"]
            },
            "reason": reason,
            "constraints": {
                "max_duration_seconds": 180
            },
            "test_methods": ["testing_agent", "comprehensive_suite"]
        }


class SmokeTestHelper:
    """Helper functions for quick L1 smoke tests"""
    
    @staticmethod
    def backend_health_check() -> str:
        """Returns curl command to check backend health"""
        return "curl -s -o /dev/null -w '%{http_code}' http://localhost:8001/docs"
    
    @staticmethod
    def frontend_health_check() -> str:
        """Returns curl command to check frontend health"""
        return "curl -s -o /dev/null -w '%{http_code}' http://localhost:3000"
    
    @staticmethod
    def test_endpoint(endpoint: str, method: str = "GET", data: str = None) -> str:
        """
        Generate curl command for testing an endpoint
        
        Args:
            endpoint: API endpoint path (e.g., '/api/campaigns')
            method: HTTP method (GET, POST, etc.)
            data: JSON data for POST/PUT requests
        """
        backend_url = "http://localhost:8001"
        
        if method == "GET":
            return f"curl -s -w '\\nStatus: %{{http_code}}' {backend_url}{endpoint}"
        elif method == "POST" and data:
            return f"curl -s -X POST -H 'Content-Type: application/json' -d '{data}' -w '\\nStatus: %{{http_code}}' {backend_url}{endpoint}"
        else:
            return f"curl -s -X {method} -w '\\nStatus: %{{http_code}}' {backend_url}{endpoint}"
    
    @staticmethod
    def quick_playwright_template(url: str, action: str) -> str:
        """
        Generate quick Playwright script for simple UI test
        
        Args:
            url: Page URL to test
            action: Action to perform (e.g., 'click button', 'check text')
        """
        return f'''
try:
    await page.set_viewport_size({{"width": 1920, "height": 800}})
    await page.goto("{url}")
    await page.wait_for_load_state("networkidle", timeout=5000)
    
    # {action}
    
    await page.screenshot(path="/tmp/smoke_test.png", quality=20, full_page=False)
    print("✓ Smoke test passed")
except Exception as e:
    print(f"✗ Smoke test failed: {{str(e)}}")
    await page.screenshot(path="/tmp/smoke_test_error.png", quality=20, full_page=False)
'''


# Example usage
if __name__ == "__main__":
    # Demonstrate level recommendation
    level = TestingLevels.recommend_level(
        change_type="feature",
        files_changed=4,
        endpoints_affected=["/api/campaigns", "/api/characters"],
        is_phase_complete=False
    )
    print(f"Recommended level: L{level} - {TestingLevels.get_level_info(level)['name']}")
    
    # Generate smoke test plan
    smoke_plan = TestingPlanGenerator.create_smoke_test_plan(
        endpoints=["/api/campaigns"],
        ui_flows=["load_home_page"]
    )
    print(f"\nSmoke test plan: {json.dumps(smoke_plan, indent=2)}")
    
    # Generate backend health check
    health_cmd = SmokeTestHelper.backend_health_check()
    print(f"\nBackend health check: {health_cmd}")
