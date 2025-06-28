"""
Configuration loader for seeding system data.

This module provides utilities to load and validate configuration files
for agents, tools, and documents used in system seeding.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, ValidationError


class AgentPermissions(BaseModel):
    """Agent permission configuration"""
    web_search: bool = False
    file_system: bool = False
    shell_access: bool = False
    git_operations: bool = False
    database_write: bool = False
    spawn_agents: bool = True


class AgentConfig(BaseModel):
    """Agent configuration model"""
    name: str
    instruction: str
    context_documents: List[str] = Field(default_factory=list)
    available_tools: List[str] = Field(default_factory=list)
    permissions: AgentPermissions = Field(default_factory=AgentPermissions)


class ToolImplementation(BaseModel):
    """Tool implementation configuration"""
    type: str  # "python_class", "shell_command", "api_call", "mcp_server", "mcp_tool", "mcp_integration"
    module_path: Optional[str] = None
    class_name: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)


class ToolConfig(BaseModel):
    """Tool configuration model"""
    name: str
    description: str
    category: str
    implementation: ToolImplementation
    parameters: Dict[str, Any] = Field(default_factory=dict)
    permissions: List[str] = Field(default_factory=list)


class DocumentConfig(BaseModel):
    """Document configuration model"""
    name: str
    title: str
    category: str
    content: Optional[str] = None
    file_path: Optional[str] = None


class SeedConfiguration:
    """Main configuration loader and validator"""
    
    def __init__(self, config_dir: str = "config/seeds"):
        self.config_dir = Path(config_dir)
        self._agents: Optional[List[AgentConfig]] = None
        self._tools: Optional[List[ToolConfig]] = None
        self._documents: Optional[List[DocumentConfig]] = None
    
    def _load_yaml(self, filename: str) -> Dict[str, Any]:
        """Load and parse YAML configuration file"""
        config_path = self.config_dir / filename
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {filename}: {e}")
    
    @property
    def agents(self) -> List[AgentConfig]:
        """Load and validate agent configurations"""
        if self._agents is None:
            config_data = self._load_yaml("agents.yaml")
            self._agents = []
            
            for agent_data in config_data.get("agents", []):
                try:
                    agent_config = AgentConfig(**agent_data)
                    self._agents.append(agent_config)
                except ValidationError as e:
                    raise ValueError(f"Invalid agent configuration for '{agent_data.get('name', 'unknown')}': {e}")
        
        return self._agents
    
    @property
    def tools(self) -> List[ToolConfig]:
        """Load and validate tool configurations"""
        if self._tools is None:
            config_data = self._load_yaml("tools.yaml")
            self._tools = []
            
            for tool_data in config_data.get("tools", []):
                try:
                    # Convert implementation dict to ToolImplementation
                    if "implementation" in tool_data:
                        tool_data["implementation"] = ToolImplementation(**tool_data["implementation"])
                    
                    tool_config = ToolConfig(**tool_data)
                    self._tools.append(tool_config)
                except ValidationError as e:
                    raise ValueError(f"Invalid tool configuration for '{tool_data.get('name', 'unknown')}': {e}")
        
        return self._tools
    
    @property
    def documents(self) -> List[DocumentConfig]:
        """Load and validate document configurations"""
        if self._documents is None:
            config_data = self._load_yaml("documents.yaml")
            self._documents = []
            
            # Load filesystem docs
            filesystem_docs = config_data.get("filesystem_docs", {})
            if filesystem_docs:
                docs_dir = Path(self.config_dir / filesystem_docs.get("docs_directory", "../../../docs")).resolve()
                pattern = filesystem_docs.get("pattern", "*.md")
                category = filesystem_docs.get("category", "system")
                
                if docs_dir.exists():
                    for doc_file in docs_dir.glob(pattern):
                        doc_config = DocumentConfig(
                            name=doc_file.stem,
                            title=doc_file.name.replace('_', ' ').title(),
                            category=category,
                            file_path=str(doc_file)
                        )
                        self._documents.append(doc_config)
            
            # Load agent guide documents
            for guide_data in config_data.get("agent_guides", []):
                try:
                    # Resolve file path relative to config directory
                    if "file_path" in guide_data:
                        file_path = Path(self.config_dir / guide_data["file_path"]).resolve()
                        guide_data["file_path"] = str(file_path)
                    
                    guide_config = DocumentConfig(**guide_data)
                    self._documents.append(guide_config)
                except ValidationError as e:
                    raise ValueError(f"Invalid document configuration for '{guide_data.get('name', 'unknown')}': {e}")
            
            # Load system reference documents
            for ref_data in config_data.get("system_references", []):
                try:
                    ref_config = DocumentConfig(**ref_data)
                    self._documents.append(ref_config)
                except ValidationError as e:
                    raise ValueError(f"Invalid document configuration for '{ref_data.get('name', 'unknown')}': {e}")
        
        return self._documents
    
    def validate_all(self) -> bool:
        """Validate all configurations and return True if valid"""
        try:
            # Access all properties to trigger validation
            agents = self.agents
            tools = self.tools
            documents = self.documents
            
            print(f"✅ Configuration validation successful:")
            print(f"  - {len(agents)} agents configured")
            print(f"  - {len(tools)} tools configured")
            print(f"  - {len(documents)} documents configured")
            
            return True
        except Exception as e:
            print(f"❌ Configuration validation failed: {e}")
            return False
    
    def get_document_content(self, doc_config: DocumentConfig) -> str:
        """Get content for a document, either from inline content or file"""
        if doc_config.content:
            return doc_config.content
        elif doc_config.file_path:
            file_path = Path(doc_config.file_path)
            if file_path.exists():
                return file_path.read_text(encoding='utf-8')
            else:
                raise FileNotFoundError(f"Document file not found: {file_path}")
        else:
            raise ValueError(f"Document '{doc_config.name}' has no content or file_path")


def load_configuration(config_dir: str = "config/seeds") -> SeedConfiguration:
    """Factory function to create and validate configuration loader"""
    config = SeedConfiguration(config_dir)
    if not config.validate_all():
        raise ValueError("Configuration validation failed")
    return config