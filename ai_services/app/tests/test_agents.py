import pytest
from app.agents.base_agent import BaseAgent
from app.models import User

@pytest.mark.asyncio
async def test_base_agent_initialization(test_session, test_user):
    """Test base agent initialization"""
    agent = BaseAgent(test_session, test_user)
    assert agent.session == test_session
    assert agent.user == test_user
    assert agent.agent_type == "BaseAgent"

@pytest.mark.asyncio
async def test_agent_detect_emotion(test_session, test_user):
    """Test emotion detection"""
    agent = BaseAgent(test_session, test_user)
    emotion = await agent.detect_emotion("I'm so happy today!")
    assert emotion in ["happy", "excited", "neutral"]  # Possible responses

@pytest.mark.asyncio
async def test_orchestrator_agent_detection(test_session, test_user):
    """Test orchestrator agent detection"""
    from app.services.orchestrator import Orchestrator
    
    orchestrator = Orchestrator(test_session, test_user)
    
    # Test habit-related message
    agent_name = await orchestrator.detect_agent("I want to start exercising daily")
    assert agent_name == "habit"
    
    # Test finance-related message
    agent_name = await orchestrator.detect_agent("How can I save more money?")
    assert agent_name == "finance"