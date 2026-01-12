import logging
from typing import Dict, Any, Optional

# Fix import - try relative first, then absolute
try:
    from ..config import settings
except ImportError:
    from config import settings

logger = logging.getLogger(__name__)


class DecisionEngine:
    """Decision engine using WAY's rag_confidence and suggested_action"""
    
    def __init__(self, confidence_threshold: float = None, escalation_threshold: float = None):
        self.confidence_threshold = confidence_threshold or settings.CONFIDENCE_THRESHOLD
        self.escalation_threshold = escalation_threshold or settings.ESCALATION_CONFIDENCE_THRESHOLD
    
    def decide(self, way_response: Dict[str, Any], classified: Optional[Dict[str, Any]] = None) -> str:
        """
        Make final decision based on WAY response and business rules.
        
        ⚠️ CRITICAL: Uses WAY's field names:
        - way_response['rag_confidence'] (NOT 'confidence')
        - way_response['suggested_action'] (NOT 'action')
        """
        # ✅ CORRECT: Use 'rag_confidence' from WAY
        rag_confidence = way_response.get("rag_confidence", 0.0)
        
        # ✅ CORRECT: Use 'suggested_action' from WAY
        suggested_action = way_response.get("suggested_action", "escalate")
        
        # Business signals from WAY
        business_signals = way_response.get("business_signals", {})
        retrieved_docs = way_response.get("retrieved_docs", [])
        
        has_urgent_keywords = business_signals.get("has_urgent_keywords", False)
        has_action_keywords = business_signals.get("has_action_keywords", False)
        
        category = classified.get("category", "Other") if classified else "Other"
        has_action = classified.get("has_action", False) if classified else has_action_keywords
        
        trace_id = way_response.get("debug_info", {}).get("trace_id", "unknown")
        
        logger.info(f"[{trace_id}] Decision inputs: "
                   f"rag_confidence={rag_confidence:.2f}, "  # ✅ Logged correctly
                   f"suggested_action={suggested_action}, "   # ✅ Logged correctly
                   f"category={category}, urgent={has_urgent_keywords}")
        
        # Rule 1: Safety override for Accounting + action
        if category == "Accounting" and has_action:
            logger.info(f"[{trace_id}] Rule 1: Accounting + action → escalate")
            return "escalate"
        
        # Rule 2: Very low confidence → escalate
        if rag_confidence < self.escalation_threshold:
            logger.info(f"[{trace_id}] Rule 2: Low rag_confidence ({rag_confidence:.2f}) → escalate")
            return "escalate"
        
        # Rule 3: Urgent keywords → escalate
        if has_urgent_keywords:
            logger.info(f"[{trace_id}] Rule 3: Urgent keywords → escalate")
            return "escalate"
        
        # Rule 4: Medium confidence → check docs or clarify
        if rag_confidence < self.confidence_threshold:
            if not retrieved_docs:
                logger.info(f"[{trace_id}] Rule 4: Medium rag_confidence, no docs → escalate")
                return "escalate"
            
            top_score = way_response.get("debug_info", {}).get("top_doc_score", 0.0)
            if top_score < 0.6:
                logger.info(f"[{trace_id}] Rule 4: Medium rag_confidence, weak docs → clarify")
                return "clarify"
        
        # Rule 5: Action keywords in sensitive categories
        if has_action_keywords and category in ["HR", "Accounting"]:
            if rag_confidence < 0.85:
                logger.info(f"[{trace_id}] Rule 5: Action + sensitive → clarify")
                return "clarify"
        
        # Rule 6: High confidence → use WAY's suggested_action
        if rag_confidence >= self.confidence_threshold:
            logger.info(f"[{trace_id}] Rule 6: High rag_confidence → {suggested_action}")
            return suggested_action
        
        # Fallback
        logger.info(f"[{trace_id}] Fallback: {suggested_action}")
        return suggested_action
    
    def should_create_ticket(
        self,
        way_response: Dict[str, Any],
        final_action: str
    ) -> bool:
        """
        Determine if a support ticket should be created.
        
        Args:
            way_response: Parsed WAY response
            final_action: Final decision from decide()
        
        Returns:
            True if ticket should be created
        """
        # Create ticket for escalations
        if final_action == "escalate":
            return True
        
        # Create ticket if explicitly requested
        if final_action == "ticket":
            return True
        
        # Create ticket for very low confidence answers
        rag_confidence = way_response.get("rag_confidence", 0.0)
        if final_action == "answer" and rag_confidence < 0.5:
            return True
        
        return False
    
    def get_escalation_reason(
        self,
        way_response: Dict[str, Any],
        final_action: str,
        classified: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Get human-readable reason for escalation.
        
        Returns None if not escalated.
        """
        if final_action not in ["escalate", "ticket"]:
            return None
        
        rag_confidence = way_response.get("rag_confidence", 0.0)
        business_signals = way_response.get("business_signals", {})
        category = classified.get("category", "Other") if classified else "Other"
        
        reasons = []
        
        if rag_confidence < self.escalation_threshold:
            reasons.append(f"Low confidence ({rag_confidence:.0%})")
        
        if business_signals.get("has_urgent_keywords"):
            reasons.append("Urgent request detected")
        
        if category == "Accounting" and classified and classified.get("has_action"):
            reasons.append("Financial action requires human review")
        
        if not way_response.get("retrieved_docs"):
            reasons.append("No relevant documents found")
        
        if not reasons:
            reasons.append("Manual review recommended")
        
        return "; ".join(reasons)


# Singleton instance
_decision_engine: Optional[DecisionEngine] = None


def get_decision_engine() -> DecisionEngine:
    """Get decision engine singleton"""
    global _decision_engine
    if _decision_engine is None:
        _decision_engine = DecisionEngine()
    return _decision_engine


def decide(way_response: Dict[str, Any], classified: Optional[Dict[str, Any]] = None) -> str:
    """Convenience function using correct WAY field names (rag_confidence, suggested_action)"""
    engine = get_decision_engine()
    return engine.decide(way_response, classified)
