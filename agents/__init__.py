"""
MEP Ranking Application Sub-Agents System

A collection of specialized agents designed to enhance and maintain
the MEP Ranking application following Anthropic best practices.
"""

__version__ = "1.0.0"
__author__ = "MEP Ranking Development Team"

from .agent_manager import AgentManager
from .base_agent import BaseAgent

# Import all agents
from .data_pipeline_agent import DataPipelineAgent
from .data_validation_agent import DataValidationAgent
from .api_performance_agent import APIPerformanceAgent
from .frontend_enhancement_agent import FrontendEnhancementAgent
from .scoring_system_agent import ScoringSystemAgent
from .qa_agent import QAAgent

__all__ = [
    'AgentManager',
    'BaseAgent',
    'DataPipelineAgent',
    'DataValidationAgent', 
    'APIPerformanceAgent',
    'FrontendEnhancementAgent',
    'ScoringSystemAgent',
    'QAAgent'
]