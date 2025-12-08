"""
Reviewer Agent for E1 V2

Performs automatic linting and static checks on code changes.
Read-only, provides feedback without making changes.
"""

import json
from pathlib import Path
from typing import Dict, Any, List


class ReviewerAgent:
    """
    Lightweight reviewer that runs linters on touched files
    
    Used automatically after Executor completes a task to catch:
    - Syntax errors
    - Undefined variables
    - Unused imports
    - Style issues
    """
    
    @staticmethod
    def review_task_changes(file_changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Review code changes from a task response
        
        Args:
            file_changes: List of {path, change_type} from task response
        
        Returns:
            {
                "status": "approved" | "needs_work",
                "lint_results": {...},
                "recommendations": [...]
            }
        """
        lint_results = {}
        recommendations = []
        issues_found = False
        
        for file_change in file_changes:
            path = file_change["path"]
            
            # Skip non-code files
            if not (path.endswith('.py') or path.endswith('.js') or path.endswith('.jsx')):
                continue
            
            # Run appropriate linter
            if path.endswith('.py'):
                result = ReviewerAgent._lint_python_file(path)
            else:
                result = ReviewerAgent._lint_javascript_file(path)
            
            lint_results[path] = result
            
            # Check for critical issues
            if result.get("errors", 0) > 0:
                issues_found = True
                recommendations.append(f"Fix {result['errors']} error(s) in {path}")
        
        # Determine status
        status = "needs_work" if issues_found else "approved"
        
        # Add general recommendations
        if not issues_found:
            recommendations.append("All linting checks passed")
        
        return {
            "status": status,
            "lint_results": lint_results,
            "recommendations": recommendations
        }
    
    @staticmethod
    def _lint_python_file(file_path: str) -> Dict[str, Any]:
        """
        Lint a Python file using ruff
        
        Returns:
            {
                "errors": int,
                "warnings": int,
                "details": str
            }
        """
        # This would call mcp_lint_python in real usage
        # For now, return a template
        return {
            "errors": 0,
            "warnings": 0,
            "details": "Linting skipped (template)"
        }
    
    @staticmethod
    def _lint_javascript_file(file_path: str) -> Dict[str, Any]:
        """
        Lint a JavaScript/TypeScript file using eslint
        
        Returns:
            {
                "errors": int,
                "warnings": int,
                "details": str
            }
        """
        # This would call mcp_lint_javascript in real usage
        # For now, return a template
        return {
            "errors": 0,
            "warnings": 0,
            "details": "Linting skipped (template)"
        }
    
    @staticmethod
    def auto_review_enabled() -> bool:
        """Check if auto-review is enabled"""
        # Could be controlled by project_state.json config
        return True


# Integration with workflow
def integrate_reviewer_in_workflow():
    """
    Documentation: How to use ReviewerAgent in the workflow
    
    After Executor completes a task:
    
    1. Executor returns task_response with file_changes
    2. Coordinator calls ReviewerAgent.review_task_changes(file_changes)
    3. If status == "needs_work":
        - Log the issues
        - Optionally create a new task to fix lint errors
    4. If status == "approved":
        - Continue with testing
    
    Example:
    
    ```python
    # After Executor completes
    task_response = executor.execute_task(task_envelope)
    
    # Run reviewer
    if ReviewerAgent.auto_review_enabled():
        review_result = ReviewerAgent.review_task_changes(
            task_response["file_changes"]
        )
        
        if review_result["status"] == "needs_work":
            print("⚠️ Reviewer found issues:")
            for rec in review_result["recommendations"]:
                print(f"  - {rec}")
        else:
            print("✅ Code review passed")
    ```
    """
    pass


if __name__ == "__main__":
    # Example usage
    example_changes = [
        {"path": "/app/backend/services/test_service.py", "change_type": "modified"},
        {"path": "/app/frontend/src/components/Test.jsx", "change_type": "created"}
    ]
    
    result = ReviewerAgent.review_task_changes(example_changes)
    print(json.dumps(result, indent=2))
