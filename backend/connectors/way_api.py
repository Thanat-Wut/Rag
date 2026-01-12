import httpx
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import os

# Fix import - try relative first, then absolute
try:
    from ..config import settings
except ImportError:
    from config import settings

logger = logging.getLogger(__name__)


class WAYClient:
    """Client for communicating with WAY RAG API"""
    
    def __init__(self, base_url: Optional[str] = None, timeout: float = None):
        self.base_url = base_url or settings.WAY_API_URL
        self.timeout = timeout or settings.WAY_TIMEOUT
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout
            )
        return self._client
    
    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
    
    async def query(
        self,
        query: str,
        trace_id: str,
        user_dept: Optional[str] = None,
        context: Optional[str] = None,
        max_results: int = 5,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Send query to WAY RAG API"""
        client = await self._get_client()
        
        payload = {
            "query": query,
            "trace_id": trace_id,
            "user_dept": user_dept,
            "context": context,
            "max_results": max_results,
            "temperature": temperature
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        
        logger.info(f"[{trace_id}] Sending request to WAY: {self.base_url}/rag/query")
        
        try:
            response = await client.post("/rag/query", json=payload)
            response.raise_for_status()
            raw_response = response.json()
            logger.debug(f"[{trace_id}] WAY raw response keys: {raw_response.keys()}")
            return self._parse_response(raw_response, trace_id)
            
        except httpx.HTTPStatusError as e:
            logger.error(f"[{trace_id}] WAY HTTP error: {e.response.status_code}")
            raise WAYAPIError(f"WAY API returned {e.response.status_code}", e.response.status_code, trace_id)
        except httpx.RequestError as e:
            logger.error(f"[{trace_id}] WAY connection error: {str(e)}")
            raise WAYConnectionError(f"Failed to connect to WAY API: {str(e)}", trace_id)
    
    def _parse_response(self, raw: Dict[str, Any], trace_id: str) -> Dict[str, Any]:
        """
        Parse WAY response using CORRECT field names.
        
        ⚠️ CRITICAL MAPPINGS:
        - WAY uses 'rag_confidence' (NOT 'confidence')
        - WAY uses 'suggested_action' (NOT 'action')
        """
        # Log actual fields received for debugging
        logger.debug(f"[{trace_id}] WAY response fields: {list(raw.keys())}")
        
        # Verify critical fields exist
        if "rag_confidence" not in raw:
            logger.warning(f"[{trace_id}] 'rag_confidence' not in WAY response, checking 'confidence'")
            # Fallback: check if WAY sent 'confidence' instead
            rag_confidence = raw.get("confidence", raw.get("rag_confidence", 0.0))
        else:
            rag_confidence = raw.get("rag_confidence", 0.0)
        
        if "suggested_action" not in raw:
            logger.warning(f"[{trace_id}] 'suggested_action' not in WAY response, checking 'action'")
            suggested_action = raw.get("action", raw.get("suggested_action", "escalate"))
        else:
            suggested_action = raw.get("suggested_action", "escalate")
        
        parsed = {
            # Core fields - use WAY's naming (rag_confidence, suggested_action)
            "answer": raw.get("answer", ""),
            "rag_confidence": float(rag_confidence),  # ✅ CORRECT: rag_confidence
            "suggested_action": suggested_action,      # ✅ CORRECT: suggested_action
            "query": raw.get("query", ""),
            
            # Business signals
            "business_signals": self._parse_business_signals(raw.get("business_signals", {})),
            
            # Documents and citations
            "citations": raw.get("citations", []),
            "retrieved_docs": self._parse_retrieved_docs(raw.get("retrieved_docs", [])),
            
            # Debug info
            "debug_info": self._parse_debug_info(raw.get("debug_info", {}), trace_id),
            
            # Timestamp
            "timestamp": raw.get("timestamp", datetime.utcnow().isoformat())
        }
        
        logger.info(f"[{trace_id}] Parsed: rag_confidence={parsed['rag_confidence']:.2f}, "
                   f"suggested_action={parsed['suggested_action']}")
        
        return parsed
    
    def _parse_business_signals(self, signals: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "has_action_keywords": bool(signals.get("has_action_keywords", False)),
            "has_urgent_keywords": bool(signals.get("has_urgent_keywords", False)),
            "query_department_match": bool(signals.get("query_department_match", False))
        }
    
    def _parse_retrieved_docs(self, docs: list) -> list:
        parsed_docs = []
        for doc in docs:
            parsed_docs.append({
                "doc_id": doc.get("doc_id", ""),
                "title": doc.get("title", ""),
                "url": doc.get("url", ""),
                "content_snippet": doc.get("content_snippet", ""),
                "similarity_score": float(doc.get("similarity_score", 0.0)),
                "category": doc.get("category", ""),
                "metadata": doc.get("metadata", {})
            })
        return parsed_docs
    
    def _parse_debug_info(self, debug: Dict[str, Any], trace_id: str) -> Dict[str, Any]:
        latency = debug.get("latency_breakdown", {})
        return {
            "top_doc_score": float(debug.get("top_doc_score", 0.0)),
            "num_relevant_docs": int(debug.get("num_relevant_docs", 0)),
            "latency_breakdown": {
                "search_ms": float(latency.get("search_ms", 0.0)),
                "llm_ms": float(latency.get("llm_ms", 0.0)),
                "total_ms": float(latency.get("total_ms", 0.0))
            },
            "trace_id": debug.get("trace_id", trace_id),
            "mock": bool(debug.get("mock", False)),
            "fallback": bool(debug.get("fallback", False)),
            "error": debug.get("error")
        }
    
    async def health_check(self) -> Dict[str, Any]:
        client = await self._get_client()
        try:
            response = await client.get("/health")
            response.raise_for_status()
            return {"status": "connected", "url": self.base_url, "response": response.json()}
        except Exception as e:
            return {"status": "disconnected", "url": self.base_url, "error": str(e)}


class WAYAPIError(Exception):
    def __init__(self, message: str, status_code: int, trace_id: str):
        super().__init__(message)
        self.status_code = status_code
        self.trace_id = trace_id


class WAYConnectionError(Exception):
    def __init__(self, message: str, trace_id: str):
        super().__init__(message)
        self.trace_id = trace_id


_way_client: Optional[WAYClient] = None


def get_way_client() -> WAYClient:
    global _way_client
    if _way_client is None:
        _way_client = WAYClient()
    return _way_client


async def close_way_client():
    global _way_client
    if _way_client:
        await _way_client.close()
        _way_client = None
