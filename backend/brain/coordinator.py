"""
Coordinator - orchestrates the WUT backend flow
"""
import logging
from typing import Dict, Any, Optional
import uuid

try:
    from .classifier import get_classifier, ClassifiedQuery
    classifier = get_classifier()
    from .decision import decide
    from ..connectors.way_api import get_way_client, WAYAPIError, WAYConnectionError
    from ..models import HelpdeskRequest, HelpdeskResponse
    from ..config import settings
except ImportError:
    from brain.classifier import get_classifier, ClassifiedQuery
    classifier = get_classifier()
    from brain.decision import decide
    from connectors.way_api import get_way_client, WAYAPIError, WAYConnectionError
    from models import HelpdeskRequest, HelpdeskResponse, ClassifiedQuery
    from config import settings

logger = logging.getLogger(__name__)


class Coordinator:
    """
    Main orchestrator for WUT backend.
    Coordinates classifier, WAY API, and decision engine.
    """
    
    def __init__(self):
        self.way_client = get_way_client()
        self.use_mock = settings.USE_MOCK
    
    async def process_query(self, request: HelpdeskRequest) -> HelpdeskResponse:
        """
        Process a helpdesk query through the full pipeline.
        
        Flow:
        1. Classify the query (department, signals)
        2. Call WAY API for RAG response
        3. Apply decision engine rules
        4. Return final response
        """
        trace_id = request.trace_id or str(uuid.uuid4())
        logger.info(f"[{trace_id}] Processing query: {request.message[:50]}...")
        
        # Step 1: Classify the query
        classified = classifier.classify(request.message)
        logger.info(f"[{trace_id}] Classified: category={classified.category}, "
                   f"has_action={classified.has_action}, has_urgent={classified.has_urgent}")
        
        # Step 2: Call WAY API (or use mock)
        if self.use_mock:
            way_response = self._get_mock_response(request, classified, trace_id)
        else:
            try:
                way_response = await self.way_client.query(
                    query=request.message,
                    trace_id=trace_id,
                    user_dept=request.department or classified.category,
                    context=request.context,
                    max_results=request.max_results,
                    temperature=request.temperature
                )
            except (WAYAPIError, WAYConnectionError) as e:
                logger.error(f"[{trace_id}] WAY API error: {e}")
                way_response = self._get_fallback_response(request, classified, trace_id, str(e))
        
        # Step 3: Apply decision engine
        classified_dict = {
            "category": classified.category,
            "has_action": classified.has_action,
            "has_urgent": classified.has_urgent
        }
        final_action = decide(way_response, classified_dict)
        
        # Override action if decision engine changed it
        way_response["suggested_action"] = final_action
        
        # Step 4: Build response
        escalated = final_action == "escalate"
        ticket_id = self._create_ticket_if_needed(way_response, final_action, trace_id)
        
        response = HelpdeskResponse.from_way_response(
            way_response,
            escalated=escalated,
            ticket_id=ticket_id
        )
        
        logger.info(f"[{trace_id}] Response: action={final_action}, "
                   f"confidence={way_response.get('rag_confidence', 0):.2f}")
        
        return response
    
    def _get_mock_response(
        self,
        request: HelpdeskRequest,
        classified: ClassifiedQuery,
        trace_id: str
    ) -> Dict[str, Any]:
        """Generate mock response when WAY is unavailable"""
        logger.warning(f"[{trace_id}] Using MOCK response")
        
        return {
            "answer": f"[MOCK] คำถามของคุณเกี่ยวกับ {classified.category} ได้รับแล้ว กรุณารอการตอบกลับจากเจ้าหน้าที่",
            "rag_confidence": 0.5,
            "suggested_action": "escalate",
            "query": request.message,
            "business_signals": {
                "has_action_keywords": classified.has_action,
                "has_urgent_keywords": classified.has_urgent,
                "query_department_match": True
            },
            "citations": [],
            "retrieved_docs": [],
            "debug_info": {
                "top_doc_score": 0.0,
                "num_relevant_docs": 0,
                "latency_breakdown": {
                    "search_ms": 0.0,
                    "llm_ms": 0.0,
                    "total_ms": 0.0
                },
                "trace_id": trace_id,
                "mock": True,
                "fallback": False,
                "error": None
            },
            "timestamp": None
        }
    
    def _get_fallback_response(
        self,
        request: HelpdeskRequest,
        classified: ClassifiedQuery,
        trace_id: str,
        error: str
    ) -> Dict[str, Any]:
        """Generate fallback response when WAY fails"""
        logger.warning(f"[{trace_id}] Using FALLBACK response due to: {error}")
        
        response = self._get_mock_response(request, classified, trace_id)
        response["debug_info"]["mock"] = False
        response["debug_info"]["fallback"] = True
        response["debug_info"]["error"] = error
        response["answer"] = "ขออภัย ระบบไม่สามารถประมวลผลคำถามได้ในขณะนี้ กรุณาติดต่อเจ้าหน้าที่โดยตรง"
        
        return response
    
    def _create_ticket_if_needed(
        self,
        way_response: Dict[str, Any],
        final_action: str,
        trace_id: str
    ) -> Optional[str]:
        """Create support ticket if needed"""
        if final_action in ["escalate", "ticket"]:
            ticket_id = f"{settings.TICKET_PREFIX}-{trace_id[:8].upper()}"
            logger.info(f"[{trace_id}] Created ticket: {ticket_id}")
            return ticket_id
        return None


# Global coordinator instance
_coordinator: Optional[Coordinator] = None


def get_coordinator() -> Coordinator:
    """Get coordinator singleton"""
    global _coordinator
    if _coordinator is None:
        _coordinator = Coordinator()
    return _coordinator
