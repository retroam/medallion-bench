"""MedallionBench solver using multi-agent architecture."""

from typing import Dict, List, Optional

from inspect_ai.solver import Solver, solver
from inspect_ai.tool import Tool

from .agents import DataAgent, ModelAgent, SubmissionAgent
from .tools import (
    BusinessSimTool,
    KVTool,
    ModelTrainingTool,
    NumeraiDataTool,
    ScratchpadTool,
    SubmissionSimulatorTool,
    VectorMemoryTool,
)


@solver
def medallion_solver(
    phase: int = 1,
    max_steps: int = 50,
) -> Solver:
    """MedallionBench solver using multi-agent architecture.
    
    Creates a multi-agent system with specialized sub-agents:
    - DataAgent: Handles EDA and feature engineering
    - ModelAgent: Develops and trains models
    - SubmissionAgent: Manages submissions and risk
    
    Args:
        phase: Which evaluation phase (determines available tools)
        max_steps: Maximum steps for the main solver
        
    Returns:
        Solver: Configured multi-agent solver
    """
    # Get tools based on phase
    tools = _get_phase_tools(phase)
    
    # TODO: Use multiagent-inspect patterns here
    # For now, create a basic solver with all tools
    from inspect_ai.solver import basic_agent
    
    return basic_agent(
        tools=tools,
        max_steps=max_steps,
    )


def _get_phase_tools(phase: int) -> List[Tool]:
    """Get available tools based on evaluation phase."""
    # Core tools available in all phases
    core_tools = [
        NumeraiDataTool(),
        ScratchpadTool(),
        KVTool(),
    ]
    
    # Phase 1-2: Basic model development
    if phase >= 1:
        core_tools.extend([
            ModelTrainingTool(),
            SubmissionSimulatorTool(),
        ])
    
    # Phase 2+: Advanced risk management
    if phase >= 2:
        core_tools.extend([
            BusinessSimTool(),
        ])
    
    # Phase 4: Advanced memory tools
    if phase >= 4:
        core_tools.extend([
            VectorMemoryTool(),
        ])
    
    return core_tools


# TODO: Implement proper multi-agent architecture using multiagent-inspect
# This would involve:
# 1. SubAgentConfig for each agent type
# 2. Agent coordination and communication
# 3. Tool specialization per agent
# 4. Memory sharing between agents

def _create_multi_agent_solver(phase: int) -> Solver:
    """Create multi-agent solver (placeholder for future implementation)."""
    # from multiagent_inspect import SubAgentConfig, basic_agent, init_sub_agents
    
    # data_agent = SubAgentConfig(
    #     tools=[NumeraiDataTool(), ScratchpadTool()],
    #     max_steps=20,
    # )
    
    # model_agent = SubAgentConfig(
    #     tools=[ModelTrainingTool(), KVTool()],
    #     max_steps=30,
    # )
    
    # submission_agent = SubAgentConfig(
    #     tools=[SubmissionSimulatorTool(), BusinessSimTool()],
    #     max_steps=15,
    # )
    
    # return basic_agent(
    #     init=init_sub_agents([data_agent, model_agent, submission_agent]),
    #     tools=[],  # Main agent uses sub-agents
    # )
    
    pass