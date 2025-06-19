"""
Conversation Flow Management for Interview Sessions
Handles dynamic conversation steering, conditional responses, and interview progression
"""

import json
import re
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum


class InterviewPhase(Enum):
    """Interview phases for different interview types"""
    INTRODUCTION = "introduction"
    TECHNICAL = "technical" 
    PROBLEM_SOLVING = "problem_solving"
    BEHAVIORAL = "behavioral"
    CONCLUSION = "conclusion"
    GUESSTIMATE_STRUCTURE = "guesstimate_structure"
    GUESSTIMATE_CALCULATION = "guesstimate_calculation"
    GUESSTIMATE_SENSE_CHECK = "guesstimate_sense_check"


class ConversationState:
    """Tracks the current state of an interview conversation"""
    
    def __init__(self, session_id: str, interview_type: str, user_id: str):
        self.session_id = session_id
        self.interview_type = interview_type
        self.user_id = user_id
        self.phase = InterviewPhase.INTRODUCTION
        self.start_time = datetime.now()
        self.last_activity = datetime.now()
        
        # Conversation tracking
        self.topics_covered = []
        self.user_responses = []
        self.ai_questions = []
        self.conversation_quality = "good"
        
        # Interview-specific state
        self.difficulty_level = "medium"
        self.performance_indicators = []
        self.red_flags = []
        self.strengths_observed = []
        
        # Guesstimate-specific state
        self.guesstimate_problem = None
        self.assumptions_made = []
        self.calculation_steps = []
        self.framework_quality = "unknown"
        
    @property
    def duration_minutes(self) -> float:
        return (datetime.now() - self.start_time).total_seconds() / 60
    
    @property
    def time_in_current_phase(self) -> float:
        return (datetime.now() - self.last_activity).total_seconds() / 60


class ConversationRuleEngine:
    """Analyzes user responses and determines conversation flow"""
    
    def __init__(self):
        self.confidence_patterns = {
            "very_confident": ["I'm sure", "definitely", "absolutely", "certainly", "confident"],
            "somewhat_confident": ["I think", "probably", "likely", "I believe", "seems like"],
            "uncertain": ["maybe", "not sure", "I think maybe", "possibly", "unsure"],
            "struggling": ["don't know", "no idea", "can't remember", "struggling", "confused"]
        }
        
        self.technical_depth_patterns = {
            "surface_level": ["it works", "it's good", "I use it", "basic", "simple"],
            "intermediate": ["because", "the reason", "it handles", "implementation", "approach"],
            "deep": ["architecture", "performance", "trade-offs", "scalability", "optimization"]
        }
        
        self.guesstimate_patterns = {
            "framework_thinking": ["break down", "components", "factors", "structure", "approach"],
            "assumption_making": ["assume", "estimate", "roughly", "approximately", "let's say"],
            "calculation_mode": ["multiply", "divide", "calculate", "math", "numbers"],
            "sense_checking": ["reasonable", "realistic", "does this make sense", "sanity check"]
        }
    
    def analyze_user_response(self, user_text: str, conversation_state: ConversationState) -> Dict[str, Any]:
        """Analyze user response and return insights for conversation steering"""
        
        user_text_lower = user_text.lower()
        
        analysis = {
            "confidence_level": self._detect_confidence(user_text_lower),
            "technical_depth": self._detect_technical_depth(user_text_lower),
            "response_length": len(user_text.split()),
            "contains_questions": "?" in user_text,
            "off_topic_indicators": self._detect_off_topic(user_text_lower, conversation_state),
            "guesstimate_signals": self._detect_guesstimate_approach(user_text_lower),
            "recommended_action": None
        }
        
        # Determine recommended action based on analysis
        analysis["recommended_action"] = self._determine_next_action(analysis, conversation_state)
        
        return analysis
    
    def _detect_confidence(self, text: str) -> str:
        for level, patterns in self.confidence_patterns.items():
            if any(pattern in text for pattern in patterns):
                return level
        return "neutral"
    
    def _detect_technical_depth(self, text: str) -> str:
        for depth, patterns in self.technical_depth_patterns.items():
            if any(pattern in text for pattern in patterns):
                return depth
        return "intermediate"
    
    def _detect_off_topic(self, text: str, state: ConversationState) -> List[str]:
        """Detect if user is going off-topic based on interview type"""
        indicators = []
        
        if state.interview_type == "guesstimate_interviewer":
            # Off-topic for guesstimate interviews
            off_topic_keywords = ["coding", "algorithm", "programming", "backend", "frontend"]
            if any(keyword in text for keyword in off_topic_keywords):
                indicators.append("technical_tangent")
        
        elif "technical" in state.interview_type:
            # Off-topic for technical interviews
            off_topic_keywords = ["personal life", "hobbies", "family", "travel"]
            if any(keyword in text for keyword in off_topic_keywords):
                indicators.append("personal_tangent")
        
        return indicators
    
    def _detect_guesstimate_approach(self, text: str) -> Dict[str, bool]:
        """Detect guesstimate-specific approaches in user response"""
        signals = {}
        
        for approach, patterns in self.guesstimate_patterns.items():
            signals[approach] = any(pattern in text for pattern in patterns)
        
        return signals
    
    def _determine_next_action(self, analysis: Dict[str, Any], state: ConversationState) -> str:
        """Determine the recommended next action based on analysis"""
        
        # Handle struggling candidates
        if analysis["confidence_level"] == "struggling":
            return "provide_hint"
        
        # Handle off-topic responses
        if analysis["off_topic_indicators"]:
            return "redirect_to_topic"
        
        # Handle very short responses
        if analysis["response_length"] < 5:
            return "ask_for_elaboration"
        
        # Interview-specific logic
        if state.interview_type == "guesstimate_interviewer":
            return self._guesstimate_specific_action(analysis, state)
        
        # Default technical interview logic
        if analysis["technical_depth"] == "surface_level":
            return "probe_deeper"
        elif analysis["technical_depth"] == "deep" and analysis["confidence_level"] == "very_confident":
            return "increase_difficulty"
        
        return "continue_normal_flow"
    
    def _guesstimate_specific_action(self, analysis: Dict[str, Any], state: ConversationState) -> str:
        """Determine action for guesstimate interviews"""
        
        signals = analysis["guesstimate_signals"]
        
        if state.phase == InterviewPhase.GUESSTIMATE_STRUCTURE:
            if signals["framework_thinking"]:
                return "encourage_framework"
            elif signals["calculation_mode"]:
                return "slow_down_get_framework_first"
            else:
                return "guide_to_structure"
        
        elif state.phase == InterviewPhase.GUESSTIMATE_CALCULATION:
            if signals["assumption_making"]:
                return "challenge_assumptions"
            elif signals["calculation_mode"]:
                return "continue_calculation"
            else:
                return "encourage_calculation"
        
        elif state.phase == InterviewPhase.GUESSTIMATE_SENSE_CHECK:
            if signals["sense_checking"]:
                return "good_sense_check"
            else:
                return "prompt_sense_check"
        
        return "continue_normal_flow"


class InterviewFlowController:
    """Controls the flow and progression of different interview types"""
    
    def __init__(self):
        self.rule_engine = ConversationRuleEngine()
        self.active_conversations = {}  # session_id -> ConversationState
        
        # Load interview flow configurations
        self.interview_flows = self._load_interview_flows()
    
    def _load_interview_flows(self) -> Dict[str, Dict]:
        """Load interview flow configurations for different interview types"""
        return {
            "guesstimate_interviewer": {
                "phases": [
                    {
                        "name": InterviewPhase.INTRODUCTION,
                        "duration_minutes": 2,
                        "goals": ["establish_rapport", "present_problem", "clarify_scope"]
                    },
                    {
                        "name": InterviewPhase.GUESSTIMATE_STRUCTURE,
                        "duration_minutes": 5,
                        "goals": ["framework_development", "component_identification"]
                    },
                    {
                        "name": InterviewPhase.GUESSTIMATE_CALCULATION,
                        "duration_minutes": 15,
                        "goals": ["assumption_making", "mathematical_calculation"]
                    },
                    {
                        "name": InterviewPhase.GUESSTIMATE_SENSE_CHECK,
                        "duration_minutes": 3,
                        "goals": ["result_validation", "benchmarking"]
                    }
                ]
            },
            "technical_screening": {
                "phases": [
                    {
                        "name": InterviewPhase.INTRODUCTION,
                        "duration_minutes": 3,
                        "goals": ["background_discussion", "experience_overview"]
                    },
                    {
                        "name": InterviewPhase.TECHNICAL,
                        "duration_minutes": 20,
                        "goals": ["coding_problems", "algorithm_discussion"]
                    },
                    {
                        "name": InterviewPhase.CONCLUSION,
                        "duration_minutes": 2,
                        "goals": ["candidate_questions", "next_steps"]
                    }
                ]
            }
        }
    
    def start_conversation(self, session_id: str, interview_type: str, user_id: str) -> ConversationState:
        """Initialize a new conversation state"""
        state = ConversationState(session_id, interview_type, user_id)
        self.active_conversations[session_id] = state
        return state
    
    def process_user_response(self, session_id: str, user_text: str) -> Optional[Dict[str, Any]]:
        """Process user response and generate conversation guidance"""
        
        if session_id not in self.active_conversations:
            return None
        
        state = self.active_conversations[session_id]
        
        # Analyze the user response
        analysis = self.rule_engine.analyze_user_response(user_text, state)
        
        # Update conversation state
        state.user_responses.append({
            "text": user_text,
            "timestamp": datetime.now(),
            "analysis": analysis
        })
        state.last_activity = datetime.now()
        
        # Generate conversation guidance
        guidance = self._generate_conversation_guidance(analysis, state)
        
        # Update phase if needed
        self._update_phase_if_needed(state)
        
        return guidance
    
    def _generate_conversation_guidance(self, analysis: Dict[str, Any], state: ConversationState) -> Dict[str, Any]:
        """Generate specific guidance for the interviewer AI"""
        
        action = analysis["recommended_action"]
        
        guidance_map = {
            "provide_hint": {
                "immediate_response": f"That's okay! Let me give you a hint to help you think through this.",
                "follow_up": "Does that help you think of an approach?",
                "tone": "supportive"
            },
            
            "redirect_to_topic": {
                "immediate_response": f"That's interesting, but let's bring this back to our main topic.",
                "follow_up": "How would you approach [current topic]?",
                "tone": "gentle_redirect"
            },
            
            "ask_for_elaboration": {
                "immediate_response": "Could you elaborate on that? I'd love to hear more details about your thinking.",
                "follow_up": "What led you to that conclusion?",
                "tone": "encouraging"
            },
            
            "encourage_framework": {
                "immediate_response": "Excellent structure! I like how you're breaking this down systematically.",
                "follow_up": "Now let's work through each component. Where would you like to start?",
                "tone": "positive_reinforcement"
            },
            
            "challenge_assumptions": {
                "immediate_response": "Interesting assumption. Can you walk me through your reasoning for that number?",
                "follow_up": "Does that seem realistic when you think about [relevant context]?",
                "tone": "constructive_challenge"
            },
            
            "slow_down_get_framework_first": {
                "immediate_response": "Hold on - before we get to numbers, let's make sure we have a clear framework.",
                "follow_up": "What are the key components we need to estimate here?",
                "tone": "guided_structure"
            },
            
            "probe_deeper": {
                "immediate_response": "That's a good start. Can you dive deeper into how that works?",
                "follow_up": "What are the technical details behind that approach?",
                "tone": "probing"
            },
            
            "increase_difficulty": {
                "immediate_response": "Great answer! Let me push this a bit further.",
                "follow_up": "How would you handle [more complex scenario]?",
                "tone": "challenging"
            }
        }
        
        base_guidance = guidance_map.get(action, {
            "immediate_response": "I see. Can you tell me more about that?",
            "follow_up": "What's your reasoning behind that approach?",
            "tone": "neutral"
        })
        
        # Add context-specific information
        guidance = {
            **base_guidance,
            "conversation_context": {
                "session_id": state.session_id,
                "current_phase": state.phase.value,
                "duration_minutes": round(state.duration_minutes, 1),
                "interview_type": state.interview_type,
                "analysis_summary": analysis
            },
            "suggested_next_steps": self._get_next_steps(state),
            "time_management": self._get_time_guidance(state)
        }
        
        return guidance
    
    def _update_phase_if_needed(self, state: ConversationState) -> None:
        """Update interview phase based on time and progress"""
        
        current_flow = self.interview_flows.get(state.interview_type, {})
        phases = current_flow.get("phases", [])
        
        if not phases:
            return
        
        # Find current phase in flow
        current_phase_index = next(
            (i for i, phase in enumerate(phases) if phase["name"] == state.phase),
            0
        )
        
        # Check if we should move to next phase
        current_phase_config = phases[current_phase_index]
        time_in_phase = state.time_in_current_phase
        
        if time_in_phase > current_phase_config["duration_minutes"]:
            # Move to next phase if available
            if current_phase_index + 1 < len(phases):
                next_phase = phases[current_phase_index + 1]
                state.phase = next_phase["name"]
                state.last_activity = datetime.now()
    
    def _get_next_steps(self, state: ConversationState) -> List[str]:
        """Get suggested next steps based on current state"""
        
        if state.interview_type == "guesstimate_interviewer":
            if state.phase == InterviewPhase.INTRODUCTION:
                return ["Present the guesstimate problem clearly", "Ask for clarifying questions"]
            elif state.phase == InterviewPhase.GUESSTIMATE_STRUCTURE:
                return ["Guide them to create a framework", "Don't let them jump to numbers yet"]
            elif state.phase == InterviewPhase.GUESSTIMATE_CALCULATION:
                return ["Work through assumptions systematically", "Challenge unrealistic numbers"]
            elif state.phase == InterviewPhase.GUESSTIMATE_SENSE_CHECK:
                return ["Ask them to evaluate their answer", "Guide comparison to benchmarks"]
        
        return ["Continue with natural conversation flow"]
    
    def _get_time_guidance(self, state: ConversationState) -> Dict[str, Any]:
        """Provide time management guidance"""
        
        total_duration = state.duration_minutes
        
        if total_duration > 25:  # Interview getting long
            return {
                "status": "overtime",
                "message": "Interview is running long, consider wrapping up",
                "suggested_action": "move_to_conclusion"
            }
        elif total_duration > 20:  # Approaching end
            return {
                "status": "nearing_end", 
                "message": "About 5 minutes left, start thinking about conclusion",
                "suggested_action": "prepare_for_wrap_up"
            }
        else:
            return {
                "status": "on_track",
                "message": "Good pace, continue as planned",
                "suggested_action": "continue_current_phase"
            }
    
    def get_conversation_state(self, session_id: str) -> Optional[ConversationState]:
        """Get current conversation state"""
        return self.active_conversations.get(session_id)
    
    def end_conversation(self, session_id: str) -> None:
        """Clean up conversation state"""
        if session_id in self.active_conversations:
            del self.active_conversations[session_id]


# Global instance for use across the application
conversation_flow_controller = InterviewFlowController()