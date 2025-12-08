"""
Summary Layer Generator for E1 V2

Generates layered summaries for efficient context management:
- Project-level summary (1-2 pages)
- Per-task summaries (focused on specific work)
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime


class SummaryGenerator:
    """Generates multi-layered summaries from project state"""
    
    @staticmethod
    def generate_project_summary() -> str:
        """
        Generate concise 1-2 page project summary
        This is the primary context loaded by Coordinator
        """
        meta_dir = Path("/app/meta")
        
        # Load all state files
        with open(meta_dir / "project_state.json") as f:
            project_state = json.load(f)
        
        with open(meta_dir / "issues.json") as f:
            issues = json.load(f)
        
        with open(meta_dir / "tasks.json") as f:
            tasks = json.load(f)
        
        with open(meta_dir / "testing_history.json") as f:
            testing = json.load(f)
        
        with open(meta_dir / "architecture.json") as f:
            arch = json.load(f)
        
        # Build summary
        summary = f"""# {project_state['project_name']} - Project Summary

**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}  
**Health:** {project_state['health_status']} | **Phase:** {project_state['current_phase']}  
**Stack:** {project_state['stack']['frontend']['framework']} + {project_state['stack']['backend']['framework']} + {project_state['stack']['database']['type']}

---

## 🎯 Current Focus

"""
        
        # Active/In-progress tasks
        active_count = len(tasks['active_tasks']) + len(tasks['in_progress_tasks'])
        if active_count > 0:
            summary += f"**Active Work:** {active_count} task(s) in progress\n\n"
            for task in tasks['active_tasks'] + tasks['in_progress_tasks']:
                summary += f"- **{task['title']}** ({task['type']}, {task['status']})\n"
        else:
            summary += "**No active tasks.** Ready for new work.\n"
        
        summary += "\n---\n\n## 🐛 Open Issues\n\n"
        
        # Open issues by priority
        open_issues = [i for i in issues['issues'] if i['status'] == 'open']
        if open_issues:
            # Group by priority
            by_priority = {}
            for issue in open_issues:
                p = issue['priority']
                if p not in by_priority:
                    by_priority[p] = []
                by_priority[p].append(issue)
            
            for priority in ['P0', 'P1', 'P2', 'P3']:
                if priority in by_priority:
                    summary += f"### {priority} Issues\n"
                    for issue in by_priority[priority]:
                        summary += f"- **{issue['title']}** ({issue['type']})\n"
                        summary += f"  - Files: {', '.join(issue['files_affected'][:3])}\n"
                        if issue['recurrence_count'] > 0:
                            summary += f"  - ⚠️ Recurred {issue['recurrence_count']} time(s)\n"
        else:
            summary += "✅ No open issues\n"
        
        summary += "\n---\n\n## 📋 Recent Work\n\n"
        
        # Last 5 completed tasks
        recent_completed = tasks['completed_tasks'][-5:]
        for task in reversed(recent_completed):
            summary += f"- ✅ {task['title']} ({task.get('completed_at', 'N/A')[:10]})\n"
        
        summary += "\n---\n\n## 🧪 Testing Status\n\n"
        summary += f"- **Total Runs:** {testing['test_stats']['total_runs']}\n"
        summary += f"- **Overall Pass Rate:** {testing['test_stats']['overall_pass_rate']:.1%}\n"
        summary += f"- **Last Run:** {testing['test_stats'].get('last_run', 'N/A')[:10]}\n"
        
        if testing.get('known_test_gaps'):
            summary += f"\n**Known Gaps:**\n"
            for gap in testing['known_test_gaps'][:3]:
                summary += f"- {gap}\n"
        
        summary += "\n---\n\n## 🏗️ Architecture Overview\n\n"
        
        # Backend structure
        backend_services = arch['backend']['structure']['services']['categories']
        total_services = sum(len(services) for services in backend_services.values())
        summary += f"**Backend:**\n"
        summary += f"- {total_services} active services\n"
        summary += f"- {len(arch['backend']['key_endpoints'])} key endpoints\n"
        
        # Frontend structure
        summary += f"\n**Frontend:**\n"
        summary += f"- {len(arch['frontend']['structure']['components']['key_files'])} key components\n"
        
        summary += "\n---\n\n## ⚠️ Critical Constraints\n\n"
        
        constraints = project_state['critical_constraints']
        summary += f"**Protected:**\n"
        summary += f"- Directories: {', '.join(constraints['protected_dirs'])}\n"
        summary += f"- Env Vars: {', '.join(constraints['protected_env_vars'])}\n"
        summary += f"\n**Never Use:** {', '.join(constraints['never_use'])}\n"
        summary += f"**Always Use:** {', '.join(constraints['always_use'])}\n"
        
        summary += "\n---\n\n## 📦 Backlog\n\n"
        
        # Top priority backlog items
        priority_backlog = [t for t in tasks['backlog'] if t.get('priority', 'P3') in ['P1', 'P2']][:5]
        if priority_backlog:
            for task in priority_backlog:
                summary += f"- [{task.get('priority', 'P3')}] {task['title']}\n"
        
        summary += f"\n*({len(tasks['backlog'])} total backlog items)*\n"
        
        summary += "\n---\n\n"
        summary += "*For detailed state, see `/app/meta/` directory*\n"
        summary += f"*Agent Version: {project_state['agent_version']}*\n"
        
        return summary
    
    @staticmethod
    def save_project_summary():
        """Generate and save project summary"""
        summary = SummaryGenerator.generate_project_summary()
        output_path = Path("/app/meta/project_summary.md")
        with open(output_path, "w") as f:
            f.write(summary)
        return summary
    
    @staticmethod
    def generate_task_summary(task_id: str, task_data: Dict[str, Any]) -> str:
        """
        Generate per-task summary
        
        Args:
            task_id: Task identifier
            task_data: Task data from tasks.json
        """
        summary = f"""# Task Summary: {task_id}

**Title:** {task_data['title']}  
**Type:** {task_data['type']}  
**Status:** {task_data['status']}  
**Created:** {task_data.get('created_at', 'N/A')}  
"""
        
        if task_data.get('completed_at'):
            summary += f"**Completed:** {task_data['completed_at']}\n"
        
        summary += "\n---\n\n## Goal\n\n"
        summary += task_data.get('description', task_data['title']) + "\n"
        
        if task_data.get('linked_issues'):
            summary += "\n## Linked Issues\n\n"
            for issue_id in task_data['linked_issues']:
                summary += f"- {issue_id}\n"
        
        summary += "\n## Files Affected\n\n"
        
        if task_data.get('files_created'):
            summary += "**Created:**\n"
            for file in task_data['files_created']:
                summary += f"- {file}\n"
        
        if task_data.get('files_modified'):
            summary += "\n**Modified:**\n"
            for file in task_data['files_modified']:
                summary += f"- {file}\n"
        
        if task_data.get('tests_run'):
            summary += "\n## Testing\n\n"
            summary += f"- **Tests Run:** {'Yes' if task_data['tests_run'] else 'No'}\n"
            if task_data.get('test_results'):
                summary += f"- **Results:** {task_data['test_results']}\n"
        
        if task_data.get('documentation'):
            summary += "\n## Documentation\n\n"
            for doc in task_data['documentation']:
                summary += f"- {doc}\n"
        
        summary += "\n---\n\n"
        summary += f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}*\n"
        
        return summary
    
    @staticmethod
    def save_task_summary(task_id: str, task_data: Dict[str, Any]):
        """Generate and save task summary"""
        summary = SummaryGenerator.generate_task_summary(task_id, task_data)
        
        tasks_dir = Path("/app/meta/tasks")
        tasks_dir.mkdir(exist_ok=True)
        
        output_path = tasks_dir / f"{task_id}.md"
        with open(output_path, "w") as f:
            f.write(summary)
        
        return summary
    
    @staticmethod
    def update_all_task_summaries():
        """Generate summaries for all completed tasks"""
        meta_dir = Path("/app/meta")
        with open(meta_dir / "tasks.json") as f:
            tasks_data = json.load(f)
        
        generated = []
        for task in tasks_data['completed_tasks']:
            task_id = task['id']
            SummaryGenerator.save_task_summary(task_id, task)
            generated.append(task_id)
        
        return generated


# CLI usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "project":
            summary = SummaryGenerator.save_project_summary()
            print("Generated project summary:")
            print(summary[:500] + "...")
        
        elif command == "all-tasks":
            generated = SummaryGenerator.update_all_task_summaries()
            print(f"Generated {len(generated)} task summaries")
        
        else:
            print(f"Unknown command: {command}")
            print("Available commands: project, all-tasks")
    else:
        print("Usage: python summary_generator.py [command]")
