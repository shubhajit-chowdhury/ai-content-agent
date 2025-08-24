from typing import Any, List, Optional
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from datetime import datetime
from all_models import get_model
from pydantic_ai.messages import ModelMessage
from pydantic_ai.common_tools.duckduckgo import duckduckgo_search_tool
import logging
import uuid



# Pydantic Models for data structures
class ContentPipeline(BaseModel):
    """Represents a content creation pipeline instance"""
    id: str = str(uuid.uuid4())
    status: str = "initiated"
    created_at: datetime = Field(default_factory=datetime.now)
    links: Optional[List[str]] = []
    content_strategy: Optional[str] = None
    generated_content: Optional[str] = None
    approval_status: str = "pending"



# Manager Agent Dependencies
class ResearcherDeps(BaseModel):
    id: str
    message: str



class GetTrendingTweetsDeps(BaseModel):
    topic: str
    count: int = 15


with open('context_files/system_prompt.md', 'r') as file:
    system_prompt = file.read()


async def keep_recent_messages(messages: list[ModelMessage]) -> list[ModelMessage]:
    """Keep only the last 10 messages to manage token usage."""
    return messages[-15:] if len(messages) > 5 else messages

research_agent = Agent(
    get_model,
    system_prompt=system_prompt,
    tools=[duckduckgo_search_tool()],
    history_processors=[keep_recent_messages]
    )


@research_agent.tool
async def read_system_files(
    ctx: RunContext[Any],  # Fixed: Changed from Any to RunContext[ResearcherDeps]
    file_name: str
) -> str:
    """Read a system file and return its content
    
    Args:
    file_name: Name of the file (e.g., 'audience_psychographics.json', 'system_prompt.md', etc.)
    Can include or exclude the 'context_files/' prefix
    
    Supported files:
    CORE CONTEXT:
    - business_context_profile.json
    - icp_profile.json  
    - brand_voice_profile.json
    - content_calendar.md
    
    CONDITIONAL CONTEXT:
    - personal_profile.json
    
    TWITTER ARCHITECTURES:
    - twitter_lead_magnet_prompt.md
    - twitter_ai_life_prompt.md
    
    TWITTER FORMATTING PATTERNS:
    - twitter_lead_magnet_examples.md
    - twitter_ai_life_examples.md
    
    ENHANCEMENT FRAMEWORKS:
    - neural_psychology_matrix.json
    - persuasion_amplifier.json
    - strategic_copy_architect.json
    """
    try:
        # Handle both cases: with or without context_files/ prefix
        if not file_name.startswith('context_files/'):
            file_path = f"context_files/{file_name}"
        else:
            file_path = file_name
            
        logging.info(f"Reading file: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
        # Log success with file type info
        file_type = "JSON" if file_name.endswith('.json') else "Markdown" if file_name.endswith('.md') else "Text"
        logging.info(f"Successfully read {len(content)} characters from {file_type} file: {file_path}")
        
        return content
        
    except FileNotFoundError:
        error_msg = f"File '{file_name}' not found in context_files directory."
        logging.error(error_msg)
        return error_msg
    except UnicodeDecodeError as e:
        error_msg = f"Error decoding file '{file_name}': {str(e)}"
        logging.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Error reading file '{file_name}': {str(e)}"
        logging.error(error_msg)
        return error_msg


# Optional: Add a helper tool to list available context files
@research_agent.tool  
async def list_context_files(
    ctx: RunContext[Any]
) -> str:
    """List all available context files organized by category"""
    import os
    try:
        files = os.listdir('context_files')
        
        # Organize files by category
        core_files = []
        conditional_files = []
        twitter_arch_files = []
        twitter_pattern_files = []
        enhancement_files = []
        other_files = []
        
        for file in files:
            if file in ['business_context_profile.json', 'icp_profile.json', 'brand_voice_profile.json', 'content_calendar.md']:
                core_files.append(file)
            elif file in ['product_strategy_profile.json', 'personal_profile.json']:
                conditional_files.append(file)
            elif 'prompt.md' in file:
                twitter_arch_files.append(file)
            elif 'examples.md' in file:
                twitter_pattern_files.append(file)
            elif file in ['neural_psychology_matrix.json', 'persuasion_amplifier.json', 'strategic_copy_architect.json']:
                enhancement_files.append(file)
            else:
                other_files.append(file)
        
        result = "📁 AVAILABLE CONTEXT FILES:\n\n"
        
        if core_files:
            result += "🔷 CORE CONTEXT (always active):\n"
            for file in core_files:
                result += f"  • {file}\n"
            result += "\n"
            
        if conditional_files:
            result += "🔶 CONDITIONAL CONTEXT (when relevant):\n"
            for file in conditional_files:
                result += f"  • {file}\n"
            result += "\n"
            
        if twitter_arch_files:
            result += "🐦 TWITTER ARCHITECTURES:\n"
            for file in twitter_arch_files:
                result += f"  • {file}\n"
            result += "\n"
            
        if twitter_pattern_files:
            result += "📝 TWITTER FORMATTING PATTERNS:\n"
            for file in twitter_pattern_files:
                result += f"  • {file}\n"
            result += "\n"
            
        if enhancement_files:
            result += "🚀 ENHANCEMENT FRAMEWORKS:\n"
            for file in enhancement_files:
                result += f"  • {file}\n"
            result += "\n"
            
        if other_files:
            result += "📄 OTHER FILES:\n"
            for file in other_files:
                result += f"  • {file}\n"
        
        return result
        
    except Exception as e:
        error_msg = f"Error listing context files: {str(e)}"
        logging.error(error_msg)
        return error_msg
