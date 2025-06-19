"""
Integration module for conversation flows with the main backend
Handles the connection between WebSocket messages and conversation flow control
"""

import json
import asyncio
from typing import Dict, Any, Optional
from conversation_flows import conversation_flow_controller, ConversationState


class ConversationIntegrator:
    """Integrates conversation flow control with the main backend"""
    
    def __init__(self):
        self.flow_controller = conversation_flow_controller
    
    async def handle_session_start(self, session_id: str, interview_type: str, user_id: str) -> Dict[str, Any]:
        """Handle the start of a new interview session"""
        
        # Initialize conversation state
        conversation_state = self.flow_controller.start_conversation(session_id, interview_type, user_id)
        
        # Generate initial context for Gemini
        initial_context = self._generate_initial_context(conversation_state)
        
        return {
            "conversation_state": conversation_state,
            "initial_context": initial_context,
            "session_initialized": True
        }
    
    async def process_user_message(self, session_id: str, user_text: str) -> Optional[Dict[str, Any]]:
        """Process user message and generate conversation guidance"""
        
        if not user_text or not user_text.strip():
            return None
        
        # Process the user response through conversation flow controller
        guidance = self.flow_controller.process_user_response(session_id, user_text.strip())
        
        if not guidance:
            return None
        
        # Generate context injection for Gemini
        context_injection = self._generate_context_injection(guidance)
        
        return {
            "guidance": guidance,
            "context_injection": context_injection,
            "should_inject_context": True
        }
    
    def _generate_initial_context(self, state: ConversationState) -> str:
        """Generate initial context message for Gemini based on interview type"""
        
        if state.interview_type == "guesstimate_interviewer":
            return f"""
INTERVIEW SESSION INITIALIZED:
- Type: Guesstimate/Market Sizing Interview
- Session ID: {state.session_id}
- Current Phase: {state.phase.value}
- Duration: {state.duration_minutes:.1f} minutes

INITIAL GUIDANCE:
You are now conducting a guesstimate interview. Follow these steps:
1. Introduce yourself professionally
2. Present ONE specific market sizing problem
3. Emphasize that methodology matters more than the exact answer
4. Ask if they have any clarifying questions about the problem

Stay in character as a professional interviewer throughout the session.
Focus on guiding their thinking process rather than giving answers.
"""
        
        elif "technical" in state.interview_type:
            return f"""
INTERVIEW SESSION INITIALIZED:
- Type: Technical Interview ({state.interview_type})
- Session ID: {state.session_id}
- Current Phase: {state.phase.value}
- Duration: {state.duration_minutes:.1f} minutes

INITIAL GUIDANCE:
Start with a warm introduction and ask about their background.
Focus on their experience and technical skills.
Be friendly but professional throughout the interview.
"""
        
        else:
            return f"""
INTERVIEW SESSION INITIALIZED:
- Type: {state.interview_type}
- Session ID: {state.session_id}
- Current Phase: {state.phase.value}

Conduct this interview professionally and adapt to the candidate's responses.
"""
    
    def _generate_context_injection(self, guidance: Dict[str, Any]) -> str:
        """Generate context injection message for Gemini based on conversation guidance"""
        
        immediate_response = guidance.get("immediate_response", "")
        follow_up = guidance.get("follow_up", "")
        tone = guidance.get("tone", "neutral")
        context = guidance.get("conversation_context", {})
        next_steps = guidance.get("suggested_next_steps", [])
        time_guidance = guidance.get("time_management", {})
        
        context_message = f"""
CONVERSATION GUIDANCE UPDATE:

IMMEDIATE RESPONSE INSTRUCTION:
{immediate_response}

FOLLOW-UP QUESTION:
{follow_up}

TONE TO USE: {tone}

INTERVIEW CONTEXT:
- Current Phase: {context.get('current_phase', 'unknown')}
- Time Elapsed: {context.get('duration_minutes', 0):.1f} minutes
- Interview Type: {context.get('interview_type', 'unknown')}

NEXT STEPS:
{' | '.join(next_steps) if next_steps else 'Continue natural flow'}

TIME MANAGEMENT:
{time_guidance.get('message', 'On track')}

IMPORTANT: Make your response sound natural and conversational, not robotic.
Stay in character as the interviewer and make this guidance feel seamless.
"""
        
        # Add specific instructions based on analysis
        analysis = context.get("analysis_summary", {})
        if analysis:
            confidence = analysis.get("confidence_level", "neutral")
            technical_depth = analysis.get("technical_depth", "intermediate")
            
            context_message += f"""

CANDIDATE ANALYSIS:
- Confidence Level: {confidence}
- Technical Depth: {technical_depth}
- Response Length: {analysis.get('response_length', 0)} words

ADJUST YOUR RESPONSE ACCORDINGLY:
"""
            
            if confidence == "struggling":
                context_message += "- Be more supportive and provide hints\n"
            elif confidence == "very_confident":
                context_message += "- You can challenge them more\n"
            
            if technical_depth == "surface_level":
                context_message += "- Ask for more details and deeper explanation\n"
            elif technical_depth == "deep":
                context_message += "- Acknowledge their expertise and explore further\n"
        
        return context_message
    
    async def handle_session_end(self, session_id: str) -> Dict[str, Any]:
        """Handle the end of an interview session"""
        
        # Get final conversation state
        final_state = self.flow_controller.get_conversation_state(session_id)
        
        if final_state:
            # Generate session summary
            summary = {
                "session_id": session_id,
                "interview_type": final_state.interview_type,
                "total_duration_minutes": final_state.duration_minutes,
                "final_phase": final_state.phase.value,
                "topics_covered": final_state.topics_covered,
                "total_exchanges": len(final_state.user_responses),
                "performance_indicators": final_state.performance_indicators,
                "strengths_observed": final_state.strengths_observed
            }
            
            # Clean up conversation state
            self.flow_controller.end_conversation(session_id)
            
            return {
                "session_ended": True,
                "summary": summary
            }
        
        return {"session_ended": True, "summary": None}
    
    def get_conversation_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a conversation"""
        
        state = self.flow_controller.get_conversation_state(session_id)
        
        if not state:
            return None
        
        return {
            "session_id": session_id,
            "interview_type": state.interview_type,
            "current_phase": state.phase.value,
            "duration_minutes": state.duration_minutes,
            "is_active": True,
            "topics_covered": state.topics_covered,
            "conversation_quality": state.conversation_quality
        }


# Global instance for use in the main backend
conversation_integrator = ConversationIntegrator()