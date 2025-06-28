from typing import Dict, Any, List, Optional, AsyncGenerator
from abc import ABC, abstractmethod
import asyncio
import json
import re
from datetime import datetime

from config.settings import settings
from typing import Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

# Temporary compatibility models - these should be migrated to proper entities
class ModelConfig(BaseModel):
    provider: str = "google"
    model_name: str = "gemini-2.5-flash-preview-05-20"
    temperature: float = 0.1
    max_tokens: int = 4000
    api_key: Optional[str] = None
    
    class Config:
        protected_namespaces = ()

class MCPToolCall(BaseModel):
    tool_name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    call_id: Optional[str] = None


class AIModelProvider(ABC):
    """Abstract base class for AI model providers"""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.client = None
    
    @abstractmethod
    async def initialize(self):
        """Initialize the AI model client"""
        pass
    
    @abstractmethod
    async def generate_response(self, 
                              messages: List[Dict[str, str]], 
                              tools: List[Dict[str, Any]] = None,
                              **kwargs) -> Dict[str, Any]:
        """Generate a response from the AI model"""
        pass
    
    @abstractmethod
    def parse_tool_calls(self, response: str) -> List[MCPToolCall]:
        """Parse tool calls from the model response"""
        pass


class AnthropicProvider(AIModelProvider):
    """Anthropic Claude model provider"""
    
    async def initialize(self):
        try:
            import anthropic
            self.client = anthropic.AsyncAnthropic(
                api_key=self.config.api_key or settings.anthropic_api_key
            )
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")
    
    async def generate_response(self, 
                              messages: List[Dict[str, str]], 
                              tools: List[Dict[str, Any]] = None,
                              **kwargs) -> Dict[str, Any]:
        """Generate response using Anthropic Claude"""
        
        # Convert messages to Anthropic format
        anthropic_messages = []
        system_message = ""
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # Prepare request parameters
        request_params = {
            "model": self.config.model_name,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "messages": anthropic_messages
        }
        
        if system_message:
            request_params["system"] = system_message
        
        if tools:
            request_params["tools"] = tools
        
        # Add any additional parameters
        request_params.update(kwargs)
        
        try:
            response = await self.client.messages.create(**request_params)
            
            return {
                "content": response.content[0].text if response.content else "",
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                },
                "model": response.model,
                "stop_reason": response.stop_reason,
                "tool_calls": self._extract_tool_calls(response)
            }
            
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")
    
    def _extract_tool_calls(self, response) -> List[MCPToolCall]:
        """Extract tool calls from Anthropic response"""
        tool_calls = []
        
        if hasattr(response, 'content'):
            for content_block in response.content:
                if hasattr(content_block, 'type') and content_block.type == 'tool_use':
                    tool_calls.append(MCPToolCall(
                        tool_name=content_block.name,
                        parameters=content_block.input,
                        call_id=content_block.id
                    ))
        
        return tool_calls
    
    def parse_tool_calls(self, response: str) -> List[MCPToolCall]:
        """Parse tool calls from response text (fallback method)"""
        tool_calls = []
        
        # Look for tool call patterns in the response
        tool_pattern = r'<tool_call>\s*(\{[^}]+\})\s*</tool_call>'
        matches = re.findall(tool_pattern, response, re.DOTALL)
        
        for match in matches:
            try:
                tool_data = json.loads(match)
                tool_calls.append(MCPToolCall(
                    tool_name=tool_data.get("name", ""),
                    parameters=tool_data.get("parameters", {}),
                    call_id=tool_data.get("id")
                ))
            except json.JSONDecodeError:
                continue
        
        return tool_calls


class GoogleProvider(AIModelProvider):
    """Google Gemini model provider"""
    
    async def initialize(self):
        try:
            import google.generativeai as genai
            self.genai = genai  # Store the module reference
            
            api_key = self.config.api_key or settings.google_api_key
            if not api_key:
                raise ValueError("Google API key not found. Set GOOGLE_API_KEY environment variable.")
            
            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel(self.config.model_name)
            
        except ImportError:
            raise ImportError("google-generativeai package not installed. Run: pip install google-generativeai")
    
    async def generate_response(self, 
                              messages: List[Dict[str, str]], 
                              tools: List[Dict[str, Any]] = None,
                              **kwargs) -> Dict[str, Any]:
        """Generate response using Google Gemini"""
        
        # Convert messages to Gemini format
        gemini_messages = []
        system_instruction = ""
        
        for msg in messages:
            if msg["role"] == "system":
                system_instruction = msg["content"]
            elif msg["role"] == "user":
                gemini_messages.append({"role": "user", "parts": [msg["content"]]})
            elif msg["role"] == "assistant":
                gemini_messages.append({"role": "model", "parts": [msg["content"]]})
        
        # Prepare generation config
        generation_config = {
            "temperature": self.config.temperature,
            "max_output_tokens": self.config.max_tokens,
        }
        
        try:
            # Create model with system instruction if provided
            if system_instruction:
                model = self.genai.GenerativeModel(
                    self.config.model_name,
                    system_instruction=system_instruction
                )
            else:
                model = self.client
            
            # Convert messages to Gemini chat history format
            if len(gemini_messages) > 1:
                # Start chat with history
                chat = model.start_chat(history=gemini_messages[:-1])
                response = await asyncio.to_thread(
                    chat.send_message,
                    gemini_messages[-1]["parts"][0],
                    generation_config=generation_config
                )
            else:
                # Single message
                response = await asyncio.to_thread(
                    model.generate_content,
                    gemini_messages[0]["parts"][0] if gemini_messages else "",
                    generation_config=generation_config
                )
            
            return {
                "content": response.text if response.text else "",
                "usage": {
                    "input_tokens": getattr(response.usage_metadata, 'prompt_token_count', 0),
                    "output_tokens": getattr(response.usage_metadata, 'candidates_token_count', 0),
                    "total_tokens": getattr(response.usage_metadata, 'total_token_count', 0)
                },
                "model": self.config.model_name,
                "stop_reason": response.candidates[0].finish_reason.name if response.candidates else "stop",
                "tool_calls": self._extract_tool_calls(response)
            }
            
        except Exception as e:
            raise Exception(f"Google API error: {str(e)}")
    
    def _extract_tool_calls(self, response) -> List[MCPToolCall]:
        """Extract tool calls from Google response"""
        tool_calls = []
        
        # Google Gemini doesn't have built-in tool calling like Anthropic/OpenAI
        # We'll need to parse from text response if tools are needed
        if hasattr(response, 'text') and response.text:
            tool_calls = self.parse_tool_calls(response.text)
        
        return tool_calls
    
    def parse_tool_calls(self, response: str) -> List[MCPToolCall]:
        """Parse tool calls from response text"""
        tool_calls = []
        
        # Look for tool call patterns in the response
        tool_pattern = r'<tool_call>\s*(\{[^}]+\})\s*</tool_call>'
        matches = re.findall(tool_pattern, response, re.DOTALL)
        
        for match in matches:
            try:
                tool_data = json.loads(match)
                tool_calls.append(MCPToolCall(
                    tool_name=tool_data.get("name", ""),
                    parameters=tool_data.get("parameters", {}),
                    call_id=tool_data.get("id", f"call_{len(tool_calls)}")
                ))
            except json.JSONDecodeError:
                continue
        
        return tool_calls


class OpenAIProvider(AIModelProvider):
    """OpenAI GPT model provider"""
    
    async def initialize(self):
        try:
            import openai
            self.client = openai.AsyncOpenAI(
                api_key=self.config.api_key or settings.openai_api_key
            )
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
    
    async def generate_response(self, 
                              messages: List[Dict[str, str]], 
                              tools: List[Dict[str, Any]] = None,
                              **kwargs) -> Dict[str, Any]:
        """Generate response using OpenAI GPT"""
        
        # Prepare request parameters
        request_params = {
            "model": self.config.model_name,
            "messages": messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature
        }
        
        if tools:
            request_params["tools"] = [{"type": "function", "function": tool} for tool in tools]
            request_params["tool_choice"] = "auto"
        
        # Add any additional parameters
        request_params.update(kwargs)
        
        try:
            response = await self.client.chat.completions.create(**request_params)
            
            return {
                "content": response.choices[0].message.content or "",
                "usage": {
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "model": response.model,
                "stop_reason": response.choices[0].finish_reason,
                "tool_calls": self._extract_tool_calls(response.choices[0].message)
            }
            
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def _extract_tool_calls(self, message) -> List[MCPToolCall]:
        """Extract tool calls from OpenAI response"""
        tool_calls = []
        
        if hasattr(message, 'tool_calls') and message.tool_calls:
            for tool_call in message.tool_calls:
                try:
                    parameters = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    parameters = {}
                
                tool_calls.append(MCPToolCall(
                    tool_name=tool_call.function.name,
                    parameters=parameters,
                    call_id=tool_call.id
                ))
        
        return tool_calls
    
    def parse_tool_calls(self, response: str) -> List[MCPToolCall]:
        """Parse tool calls from response text (fallback method)"""
        return []  # OpenAI handles tool calls differently


class AIModelManager:
    """Manager for AI model providers"""
    
    def __init__(self):
        self._providers = {
            "anthropic": AnthropicProvider,
            "openai": OpenAIProvider,
            "google": GoogleProvider
        }
        self._instances: Dict[str, AIModelProvider] = {}
    
    async def get_provider(self, config: ModelConfig) -> AIModelProvider:
        """Get or create an AI model provider instance"""
        provider_key = f"{config.provider}:{config.model_name}"
        
        if provider_key not in self._instances:
            if config.provider not in self._providers:
                raise ValueError(f"Unsupported AI provider: {config.provider}")
            
            provider_class = self._providers[config.provider]
            provider = provider_class(config)
            await provider.initialize()
            self._instances[provider_key] = provider
        
        return self._instances[provider_key]
    
    def register_provider(self, name: str, provider_class: type):
        """Register a new AI model provider"""
        self._providers[name] = provider_class
    
    async def close_all(self):
        """Close all provider connections"""
        for provider in self._instances.values():
            if hasattr(provider, 'close'):
                await provider.close()
        self._instances.clear()


# Global AI model manager instance
ai_model_manager = AIModelManager()