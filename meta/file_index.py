"""
File Index with SHA256 Tracking for E1 V2

Implements lazy loading optimization by tracking file content changes.
Allows reuse of summaries for unchanged files.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List


class FileIndex:
    """
    Manages file index with SHA256 checksums for optimization
    
    Use case:
    - Before reading a file, check if SHA256 has changed
    - If unchanged, use cached summary instead of re-reading
    - Only load full content when editing or diagnosing
    """
    
    INDEX_PATH = Path("/app/meta/file_index.json")
    
    @staticmethod
    def load_index() -> Dict[str, Any]:
        """Load file index from disk"""
        if FileIndex.INDEX_PATH.exists():
            with open(FileIndex.INDEX_PATH) as f:
                return json.load(f)
        return {"files": {}, "last_updated": None}
    
    @staticmethod
    def save_index(index: Dict[str, Any]):
        """Save file index to disk"""
        from datetime import datetime, timezone
        index["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(FileIndex.INDEX_PATH, "w") as f:
            json.dump(index, f, indent=2)
    
    @staticmethod
    def compute_sha256(file_path: str) -> Optional[str]:
        """
        Compute SHA256 checksum of a file
        
        Returns:
            Hex digest of SHA256, or None if file doesn't exist
        """
        path = Path(file_path)
        if not path.exists():
            return None
        
        sha256 = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    @staticmethod
    def add_file(
        file_path: str,
        summary: str = None,
        tags: List[str] = None,
        dependencies: List[str] = None
    ):
        """
        Add or update file in index
        
        Args:
            file_path: Absolute path to file
            summary: Brief description of file's purpose
            tags: Categories (e.g., 'backend', 'service', 'route')
            dependencies: Other files this file depends on
        """
        index = FileIndex.load_index()
        
        sha256 = FileIndex.compute_sha256(file_path)
        if sha256 is None:
            return  # File doesn't exist
        
        # Relative path from /app
        rel_path = str(Path(file_path).relative_to("/app"))
        
        index["files"][rel_path] = {
            "sha256": sha256,
            "summary": summary or "No summary provided",
            "tags": tags or [],
            "dependencies": dependencies or [],
            "last_updated": None  # Will be set by save_index
        }
        
        FileIndex.save_index(index)
    
    @staticmethod
    def get_file_info(file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get cached information about a file
        
        Returns:
            File info dict or None if not in index
        """
        index = FileIndex.load_index()
        rel_path = str(Path(file_path).relative_to("/app"))
        return index["files"].get(rel_path)
    
    @staticmethod
    def has_changed(file_path: str) -> bool:
        """
        Check if file has changed since last indexed
        
        Returns:
            True if file changed or not in index
        """
        cached_info = FileIndex.get_file_info(file_path)
        if not cached_info:
            return True  # Not in index, consider it changed
        
        current_sha = FileIndex.compute_sha256(file_path)
        return current_sha != cached_info["sha256"]
    
    @staticmethod
    def update_file_summary(file_path: str, new_summary: str):
        """Update summary for a file (without recomputing SHA)"""
        index = FileIndex.load_index()
        rel_path = str(Path(file_path).relative_to("/app"))
        
        if rel_path in index["files"]:
            index["files"][rel_path]["summary"] = new_summary
            FileIndex.save_index(index)
    
    @staticmethod
    def bulk_index_directory(
        directory: str,
        extensions: List[str] = None,
        exclude_patterns: List[str] = None
    ) -> int:
        """
        Index all files in a directory
        
        Args:
            directory: Directory path to index
            extensions: File extensions to include (e.g., ['.py', '.js'])
            exclude_patterns: Patterns to exclude (e.g., ['node_modules', '__pycache__'])
        
        Returns:
            Number of files indexed
        """
        extensions = extensions or ['.py', '.js', '.jsx', '.ts', '.tsx']
        exclude_patterns = exclude_patterns or ['node_modules', '__pycache__', '.git', 'venv']
        
        dir_path = Path(directory)
        indexed_count = 0
        
        for file_path in dir_path.rglob('*'):
            # Skip if not a file
            if not file_path.is_file():
                continue
            
            # Check extension
            if file_path.suffix not in extensions:
                continue
            
            # Check exclude patterns
            if any(pattern in str(file_path) for pattern in exclude_patterns):
                continue
            
            # Auto-generate summary based on file type
            summary = FileIndex._auto_generate_summary(file_path)
            tags = FileIndex._auto_generate_tags(file_path)
            
            FileIndex.add_file(str(file_path), summary=summary, tags=tags)
            indexed_count += 1
        
        return indexed_count
    
    @staticmethod
    def _auto_generate_summary(file_path: Path) -> str:
        """Generate basic summary from file location and name"""
        parts = file_path.parts
        
        if 'backend' in parts:
            if 'services' in parts:
                return f"Backend service: {file_path.stem}"
            elif 'routers' in parts:
                return f"API router: {file_path.stem}"
            elif 'models' in parts:
                return f"Data model: {file_path.stem}"
        
        elif 'frontend' in parts:
            if 'components' in parts:
                return f"React component: {file_path.stem}"
            elif 'contexts' in parts:
                return f"React context: {file_path.stem}"
        
        return f"File: {file_path.name}"
    
    @staticmethod
    def _auto_generate_tags(file_path: Path) -> List[str]:
        """Generate tags based on file location"""
        tags = []
        parts = file_path.parts
        
        if 'backend' in parts:
            tags.append('backend')
            if 'services' in parts:
                tags.append('service')
            elif 'routers' in parts:
                tags.append('router')
            elif 'models' in parts:
                tags.append('model')
        
        elif 'frontend' in parts:
            tags.append('frontend')
            if 'components' in parts:
                tags.append('component')
        
        if file_path.suffix in ['.py']:
            tags.append('python')
        elif file_path.suffix in ['.js', '.jsx']:
            tags.append('javascript')
        
        return tags
    
    @staticmethod
    def find_files_by_tag(tag: str) -> List[str]:
        """Find all files with a specific tag"""
        index = FileIndex.load_index()
        return [
            f"/app/{path}" for path, info in index["files"].items()
            if tag in info.get("tags", [])
        ]
    
    @staticmethod
    def get_statistics() -> Dict[str, Any]:
        """Get index statistics"""
        index = FileIndex.load_index()
        
        total_files = len(index["files"])
        by_tag = {}
        
        for file_info in index["files"].values():
            for tag in file_info.get("tags", []):
                by_tag[tag] = by_tag.get(tag, 0) + 1
        
        return {
            "total_files": total_files,
            "by_tag": by_tag,
            "last_updated": index.get("last_updated")
        }


class LazyFileLoader:
    """
    Helper class to implement lazy loading with file index
    
    Usage:
        loader = LazyFileLoader()
        content = loader.load("/app/backend/services/some_service.py")
        # Returns summary if unchanged, full content if changed
    """
    
    def __init__(self, force_full_load: bool = False):
        """
        Args:
            force_full_load: If True, always load full content
        """
        self.force_full_load = force_full_load
    
    def load(self, file_path: str, context: str = "reading") -> str:
        """
        Load file with lazy loading optimization
        
        Args:
            file_path: Path to file
            context: "reading" (use summary if unchanged) or "editing" (always full)
        
        Returns:
            File content or cached summary
        """
        # Always load full content when editing
        if context == "editing" or self.force_full_load:
            return self._load_full_content(file_path)
        
        # Check if file has changed
        if not FileIndex.has_changed(file_path):
            # File unchanged, use cached summary
            info = FileIndex.get_file_info(file_path)
            if info and info.get("summary"):
                return f"[CACHED SUMMARY] {info['summary']}\n[File unchanged since last read]"
        
        # File changed or not in index, load full content
        return self._load_full_content(file_path)
    
    def _load_full_content(self, file_path: str) -> str:
        """Load full file content"""
        try:
            with open(file_path) as f:
                return f.read()
        except Exception as e:
            return f"[ERROR] Could not load file: {e}"


# CLI usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "index-backend":
            count = FileIndex.bulk_index_directory("/app/backend", extensions=['.py'])
            print(f"Indexed {count} backend files")
        
        elif command == "index-frontend":
            count = FileIndex.bulk_index_directory("/app/frontend/src", extensions=['.js', '.jsx', '.ts', '.tsx'])
            print(f"Indexed {count} frontend files")
        
        elif command == "stats":
            stats = FileIndex.get_statistics()
            print(f"Total files: {stats['total_files']}")
            print(f"By tag: {json.dumps(stats['by_tag'], indent=2)}")
        
        elif command == "check" and len(sys.argv) > 2:
            file_path = sys.argv[2]
            changed = FileIndex.has_changed(file_path)
            print(f"File changed: {changed}")
        
        else:
            print(f"Unknown command: {command}")
            print("Available commands: index-backend, index-frontend, stats, check <file>")
    else:
        print("Usage: python file_index.py [command]")
