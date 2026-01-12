"""
Decision Engine - Makes decisions about how to handle queries

Responsibilities:
- Determine action (answer, escalate, clarify, ticket)
- Apply business rules based on confidence, signals, and policies
- Generate explanations for decisions
"""

import logging
from typing import Dict, Tuple
from config import settings
from models import ActionType, BusinessSignals

logger = logging.getLogger(__name__)


class DecisionEngine:
    """
    Decision engine that determines what action to take based on query analysis.
    
    Rules:
    1. If confidence >= HIGH_CONFIDENCE_THRESHOLD (0.85) → ANSWER
    2. If urgent keywords detected → ESCALATE
    3. If action keywords detected but confidence < THRESHOLD → CLARIFY
    4. If confidence >= THRESHOLD but < HIGH_CONFIDENCE → ANSWER (with caution)
    5. If confidence < THRESHOLD → ESCALATE or TICKET
    """
    
    def __init__(self):
        """Initialize decision engine with thresholds from config"""
        self.high_confidence_threshold = settings.HIGH_CONFIDENCE_THRESHOLD  # 0.85
        self.confidence_threshold = settings.CONFIDENCE_THRESHOLD  # 0.70
        self.escalation_threshold = settings.ESCALATION_CONFIDENCE_THRESHOLD  # 0.50
        logger.info(
            f"🤖 Decision Engine initialized with thresholds: "
            f"high={self.high_confidence_threshold}, "
            f"normal={self.confidence_threshold}, "
            f"escalate={self.escalation_threshold}"
        )
    
    def decide(self, confidence: float, signals: BusinessSignals, query: str) -> Tuple[ActionType, str]:
        """
        Make a decision based on confidence and signals.
        
        Args:
            confidence: Confidence score from RAG (0.0 to 1.0)
            signals: Business signals detected in query
            query: Original user query
        
        Returns:
            Tuple of (action, reason)
        """
        logger.debug(
            f"Decision Engine evaluating: confidence={confidence:.2f}, "
            f"urgent={signals.has_urgent_keywords}, "
            f"action={signals.has_action_keywords}"
        )
        
        # Rule 1: Urgent queries always escalate
        if signals.has_urgent_keywords:
            return ActionType.ESCALATE, "Urgent query detected - escalating to agent"
        
        # Rule 2: High confidence answers
        if confidence >= self.high_confidence_threshold:
            return ActionType.ANSWER, f"High confidence ({confidence:.1%}) - answering directly"
        
        # Rule 3: Action keywords with low confidence - clarify
        if signals.has_action_keywords and confidence < self.confidence_threshold:
            return ActionType.CLARIFY, f"Action needed but low confidence ({confidence:.1%}) - asking for clarification"
        
        # Rule 4: Normal confidence - answer
        if confidence >= self.confidence_threshold:
            return ActionType.ANSWER, f"Acceptable confidence ({confidence:.1%}) - answering"
        
        # Rule 5: Low confidence - escalate
        if confidence >= self.escalation_threshold:
            return ActionType.ESCALATE, f"Low confidence ({confidence:.1%}) - escalating to agent"
        
        # Rule 6: Very low confidence - create ticket
        return ActionType.TICKET, f"Very low confidence ({confidence:.1%}) - creating ticket for investigation"
    
    def get_confidence_status(self, confidence: float) -> str:
        """
        Get human-readable status for confidence level.
        
        Args:
            confidence: Confidence score (0.0 to 1.0)
        
        Returns:
            Status string (e.g., "High", "Medium", "Low")
        """
        if confidence >= self.high_confidence_threshold:
            return "🟢 High"
        elif confidence >= self.confidence_threshold:
            return "🟡 Medium"
        elif confidence >= self.escalation_threshold:
            return "🔴 Low"
        else:
            return "🔴🔴 Critical"
    
    def should_include_sources(self, action: ActionType, confidence: float) -> bool:
        """
        Determine if sources should be included in response.
        
        Sources are shown for answers but not for escalations or tickets.
        
        Args:
            action: Suggested action
            confidence: Confidence score
        
        Returns:
            True if sources should be included
        """
        # Include sources for answers and clarifications
        return action in [ActionType.ANSWER, ActionType.CLARIFY]
    
    def should_create_ticket(self, action: ActionType, department: str = None) -> bool:
        """
        Determine if a ticket should be automatically created.
        
        Args:
            action: Suggested action
            department: Department of the query
        
        Returns:
            True if ticket should be created
        """
        # Always create tickets for TICKET action
        if action == ActionType.TICKET:
            return True
        
        # Create tickets for escalations
        if action == ActionType.ESCALATE:
            return True
        
        return False
    
    def get_confidence_explanation(self, confidence: float) -> str:
        """
        Get a human-friendly explanation of the confidence score.
        
        Args:
            confidence: Confidence score (0.0 to 1.0)
        
        Returns:
            Explanation string
        """
        percentage = confidence * 100
        
        if confidence >= 0.95:
            return f"Very confident ({percentage:.0f}%) - this is a reliable answer"
        elif confidence >= 0.85:
            return f"Highly confident ({percentage:.0f}%) - this should be accurate"
        elif confidence >= 0.70:
            return f"Moderately confident ({percentage:.0f}%) - this is probably correct"
        elif confidence >= 0.50:
            return f"Somewhat confident ({percentage:.0f}%) - there might be better answers"
        else:
            return f"Low confidence ({percentage:.0f}%) - this query needs specialist review"
    
    def evaluate_response_quality(self, confidence: float, has_sources: bool) -> Dict[str, any]:
        """
        Evaluate the overall quality of the response.
        
        Args:
            confidence: Confidence score
            has_sources: Whether sources were retrieved
        
        Returns:
            Quality assessment dict
        """
        quality_score = confidence
        if has_sources:
            quality_score = min(quality_score * 1.1, 1.0)  # Boost if sources found
        
        is_high_quality = quality_score >= self.confidence_threshold
        
        return {
            "score": quality_score,
            "is_high_quality": is_high_quality,
            "explanation": self.get_confidence_explanation(confidence),
            "recommendation": "Present to user" if is_high_quality else "Review with caution"
        }


# =============================================================================
# Global decision engine instance
# =============================================================================

_decision_engine_instance: DecisionEngine = None


def get_decision_engine() -> DecisionEngine:
    """
    Get or create the global decision engine instance.
    Uses lazy initialization for efficiency.
    """
    global _decision_engine_instance
    if _decision_engine_instance is None:
        _decision_engine_instance = DecisionEngine()
    return _decision_engine_instance
def decide(way_response: Dict[str, any], classified: Dict[str, any]) -> str:
    """
    Convenience function to make decision without instantiating engine.
    
    Args:
        way_response: Response from WAY API
        classified: Classification results with category, has_action, has_urgent
        
    Returns:
        Action type as string (e.g., "answer", "escalate")
    """
    engine = get_decision_engine()
    
    # Extract confidence from WAY response
    confidence = way_response.get("rag_confidence", 0.0)
    
    # Build signals from classified data
    from models import BusinessSignals
    signals = BusinessSignals(
        has_action_keywords=classified.get("has_action", False),
        has_urgent_keywords=classified.get("has_urgent", False),
        query_department_match=True  # Assume match for now
    )
    
    # Get decision
    action, reason = engine.decide(
        confidence=confidence,
        signals=signals,
        query=way_response.get("query", "")
    )
    
    logger.info(f"Decision: {action} - {reason}")
    return action.value  # Return string value of ActionType enum
