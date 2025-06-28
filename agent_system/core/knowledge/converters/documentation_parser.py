"""
Documentation parser for converting various documentation types to structured data.
"""

import logging
from pathlib import Path
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


class DocumentationParser:
    """Parses different types of documentation files."""
    
    def __init__(self, docs_dir: Path):
        """Initialize with documentation directory."""
        self.docs_dir = Path(docs_dir)
    
    def find_agent_guides(self) -> List[Path]:
        """Find all agent guide files."""
        agent_guides_dir = self.docs_dir / "context_documents"
        if not agent_guides_dir.exists():
            logger.warning(f"Agent guides directory not found: {agent_guides_dir}")
            return []
        
        return list(agent_guides_dir.glob("*_agent_guide.md"))
    
    def find_architecture_docs(self) -> List[Tuple[str, str, str]]:
        """Find architecture documentation files.
        
        Returns:
            List of tuples (filename, entity_id, display_name)
        """
        arch_docs = [
            ("entity_architecture.md", "system_entity_architecture", "Entity Framework Architecture"),
            ("process_architecture.md", "system_process_architecture", "Process Architecture"),
            ("event_system_guide.md", "system_event_architecture", "Event System Architecture"),
            ("runtime_specification.md", "system_runtime_architecture", "Runtime Architecture")
        ]
        
        return arch_docs
    
    def find_process_files(self) -> List[Path]:
        """Find process implementation files."""
        process_dir = self.docs_dir.parent / "core" / "processes"
        if not process_dir.exists():
            logger.warning(f"Process directory not found: {process_dir}")
            return []
        
        # Find specific process files
        process_files = []
        for pattern in ["*_process.py", "processes/*_process.py"]:
            process_files.extend(process_dir.glob(pattern))
        
        # Filter out base classes and tests
        return [
            f for f in process_files 
            if not any(skip in f.name for skip in ["base", "test", "__pycache__"])
        ]
    
    def find_tool_docs(self) -> List[Path]:
        """Find tool documentation files."""
        tool_patterns = [
            "context_documents/tools/*_tools.md",
            "docs/tools/*.md",
            "tools/*/README.md"
        ]
        
        tool_docs = []
        for pattern in tool_patterns:
            tool_docs.extend(self.docs_dir.glob(pattern))
        
        return tool_docs
    
    def read_file_safely(self, file_path: Path) -> Optional[str]:
        """Read a file safely with error handling.
        
        Args:
            file_path: Path to file to read
            
        Returns:
            File content or None if error
        """
        try:
            return file_path.read_text(encoding='utf-8')
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return None
    
    def extract_agent_name_from_guide(self, guide_path: Path) -> str:
        """Extract agent name from guide file path."""
        return guide_path.stem.replace("_guide", "")
    
    def extract_process_name_from_file(self, process_file: Path) -> str:
        """Extract process name from Python file."""
        return process_file.stem.replace("_process", "")
    
    def extract_tool_category_from_path(self, tool_path: Path) -> str:
        """Extract tool category from file path."""
        # If in a subdirectory, use that as category
        if tool_path.parent.name not in ["context_documents", "docs", "tools"]:
            return tool_path.parent.name
        
        # Otherwise infer from filename
        if "core" in tool_path.name:
            return "core"
        elif "system" in tool_path.name:
            return "system"
        elif "external" in tool_path.name:
            return "external"
        else:
            return "general"
    
    def find_or_create_architecture_doc(self, doc_name: str) -> Optional[Path]:
        """Find architecture document, checking for updated versions.
        
        Args:
            doc_name: Base document name
            
        Returns:
            Path to document if found, None otherwise
        """
        docs_dir = self.docs_dir / "docs"
        
        # Check original name
        doc_path = docs_dir / doc_name
        if doc_path.exists():
            return doc_path
        
        # Check with updated_ prefix
        updated_path = docs_dir / f"updated_{doc_name}"
        if updated_path.exists():
            return updated_path
        
        return None
    
    def parse_yaml_frontmatter(self, content: str) -> Tuple[dict, str]:
        """Parse YAML frontmatter from markdown content.
        
        Args:
            content: Markdown content with optional frontmatter
            
        Returns:
            Tuple of (metadata dict, content without frontmatter)
        """
        if not content.startswith("---"):
            return {}, content
        
        try:
            # Find end of frontmatter
            end_index = content.find("\n---\n", 4)
            if end_index == -1:
                return {}, content
            
            # Parse YAML (simplified - just extract key: value pairs)
            frontmatter = content[4:end_index]
            metadata = {}
            
            for line in frontmatter.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()
            
            # Return metadata and content without frontmatter
            return metadata, content[end_index + 5:]
            
        except Exception as e:
            logger.warning(f"Failed to parse frontmatter: {e}")
            return {}, content