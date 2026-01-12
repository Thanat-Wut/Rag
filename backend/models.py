from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid


# =============================================================================
# Enums
# =============================================================================

class Department(str, Enum):
    """Valid department values matching WAY API"""
    HR = "HR"
    IT = "IT"
    ACCOUNTING = "Accounting"
    OTHER = "Other"


class ActionType(str, Enum):
    """Suggested action types"""
    ANSWER = "answer"
    ESCALATE = "escalate"
    CLARIFY = "clarify"
    TICKET = "ticket"


# =============================================================================
# Shared Models (matching WAY API exactly)
# =============================================================================

class ClassifiedQuery(BaseModel):
    """Result of query classification by WUT's classifier"""
    category: str = Field(
        default="Other",
        description="Detected category: HR, IT, Accounting, Other"
    )
    has_action: bool = Field(
        default=False,
        description="Whether query contains action keywords"
    )
    has_urgent: bool = Field(
        default=False,
        description="Whether query contains urgent keywords"
    )
    keywords: List[str] = Field(
        default_factory=list,
        description="Detected keywords"
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Classification confidence"
    )


class RetrievedDocument(BaseModel):
    """Document retrieved from vector search - matches WAY schema"""
    doc_id: str
    title: str
    url: str
    content_snippet: str
    similarity_score: float = Field(..., ge=0.0, le=1.0)
    category: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BusinessSignals(BaseModel):
    """Business signal detection results - matches WAY schema"""
    has_action_keywords: bool = False
    has_urgent_keywords: bool = False
    query_department_match: bool = False


class LatencyBreakdown(BaseModel):
    """Performance timing breakdown"""
    search_ms: float = 0.0
    llm_ms: float = 0.0
    total_ms: float = 0.0


class DebugInfo(BaseModel):
    """Debug information from WAY - matches WAY schema"""
    top_doc_score: float = Field(default=0.0, ge=0.0, le=1.0)
    num_relevant_docs: int = Field(default=0, ge=0)
    latency_breakdown: LatencyBreakdown = Field(default_factory=LatencyBreakdown)
    trace_id: str
    mock: bool = False
    fallback: bool = False
    error: Optional[str] = None


# =============================================================================
# Request Models
# =============================================================================

class HelpdeskRequest(BaseModel):
    """
    Incoming request to WUT orchestrator.
    
    Fields are aliased to support both WUT naming (message, department) 
    and WAY naming (query, user_dept) for flexibility.
    """
    # Primary field - accepts both 'message' and 'query'
    message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User's question or request"
    )
    
    # Alias for WAY compatibility
    query: Optional[str] = Field(
        None,
        description="Alias for message (WAY naming)"
    )
    
    # User identifier
    user_id: Optional[str] = Field(
        None,
        description="Unique identifier for the user"
    )
    
    # Department - accepts both 'department' and 'user_dept'
    department: Optional[str] = Field(
        None,
        description="User's department: HR, IT, Accounting, or Other"
    )
    
    # Alias for WAY compatibility
    user_dept: Optional[str] = Field(
        None,
        description="Alias for department (WAY naming)"
    )
    
    # Trace ID for request correlation
    trace_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique request ID for tracing"
    )
    
    # Optional context
    context: Optional[str] = Field(
        None,
        max_length=5000,
        description="Additional context for the query"
    )
    
    # RAG parameters (passed to WAY)
    max_results: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of documents to retrieve"
    )
    
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="LLM temperature for response generation"
    )

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "message": "How do I request annual leave?",
                "user_id": "user_123",
                "department": "HR",
                "trace_id": "abc-123-def"
            }
        }
    
    @field_validator("department", mode="before")
    @classmethod
    def validate_department(cls, v: Optional[str]) -> Optional[str]:
        """Validate department matches allowed values"""
        if v is None:
            return None
        
        # Normalize to title case
        normalized = v.strip().title()
        
        # Map common variations
        dept_mapping = {
            "Hr": "HR",
            "It": "IT",
            "Finance": "Accounting",
            "Accounts": "Accounting",
            "General": "Other",
            "Unknown": "Other"
        }
        
        normalized = dept_mapping.get(normalized, normalized)
        
        valid_depts = {"HR", "IT", "Accounting", "Other"}
        if normalized not in valid_depts:
            return "Other"  # Default to Other for unknown departments
        
        return normalized
    
    @model_validator(mode="after")
    def resolve_aliases(self) -> "HelpdeskRequest":
        """Resolve WAY-style field names to WUT-style"""
        # If query is provided but message is not, use query
        if self.query and not self.message:
            object.__setattr__(self, 'message', self.query)
        # If user_dept is provided but department is not, use user_dept
        if self.user_dept and not self.department:
            object.__setattr__(self, 'department', self.user_dept)
        return self
    
    def to_way_request(self) -> dict:
        """Convert to WAY API request format"""
        return {
            "query": self.message,
            "trace_id": self.trace_id,
            "user_dept": self.department,
            "context": self.context,
            "max_results": self.max_results,
            "temperature": self.temperature
        }


# =============================================================================
# Response Models
# =============================================================================

class HelpdeskResponse(BaseModel):
    """
    Response from WUT orchestrator.
    
    Contains both WUT-style fields (reply, confidence, action) and 
    full WAY response data for transparency.
    """
    # -------------------------------------------------------------------------
    # Core response fields (WUT naming)
    # -------------------------------------------------------------------------
    reply: str = Field(
        ...,
        alias="answer",
        description="Generated answer to the user's question"
    )
    
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        alias="rag_confidence",
        description="Confidence score from RAG engine (0.0 to 1.0)"
    )
    
    action: str = Field(
        ...,
        alias="suggested_action",
        description="Suggested action: 'answer', 'escalate', 'clarify', or 'ticket'"
    )
    
    trace_id: str = Field(
        ...,
        description="Request trace ID for correlation"
    )
    
    # -------------------------------------------------------------------------
    # Extended fields from WAY
    # -------------------------------------------------------------------------
    query: str = Field(
        ...,
        description="Original user query"
    )
    
    business_signals: BusinessSignals = Field(
        default_factory=BusinessSignals,
        description="Detected business signals in the query"
    )
    
    citations: List[str] = Field(
        default_factory=list,
        description="List of document IDs used for the answer"
    )
    
    retrieved_docs: List[RetrievedDocument] = Field(
        default_factory=list,
        description="Source documents retrieved from knowledge base"
    )
    
    debug_info: Optional[DebugInfo] = Field(
        None,
        description="Debug information (latency, scores, etc.)"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Response timestamp"
    )
    
    # -------------------------------------------------------------------------
    # WUT-specific fields
    # -------------------------------------------------------------------------
    escalated: bool = Field(
        default=False,
        description="Whether the request was escalated to human agent"
    )
    
    ticket_id: Optional[str] = Field(
        None,
        description="Ticket ID if a ticket was created"
    )

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "reply": "To request annual leave, submit your application through the HR portal.",
                "confidence": 0.92,
                "action": "answer",
                "trace_id": "abc-123-def",
                "query": "How do I request annual leave?",
                "business_signals": {
                    "has_action_keywords": True,
                    "has_urgent_keywords": False,
                    "query_department_match": True
                },
                "citations": ["doc_hr_001"],
                "retrieved_docs": [],
                "escalated": False,
                "timestamp": "2024-01-10T12:00:00Z"
            }
        }
    
    @classmethod
    def from_way_response(cls, way_response: dict, escalated: bool = False, ticket_id: Optional[str] = None) -> "HelpdeskResponse":
        """
        Create HelpdeskResponse from WAY API response.
        
        Args:
            way_response: Raw response dict from WAY API
            escalated: Whether request was escalated
            ticket_id: Ticket ID if created
        
        Returns:
            HelpdeskResponse instance
        """
        # Parse business signals
        signals_data = way_response.get("business_signals", {})
        business_signals = BusinessSignals(
            has_action_keywords=signals_data.get("has_action_keywords", False),
            has_urgent_keywords=signals_data.get("has_urgent_keywords", False),
            query_department_match=signals_data.get("query_department_match", False)
        )
        
        # Parse retrieved documents
        retrieved_docs = []
        for doc in way_response.get("retrieved_docs", []):
            retrieved_docs.append(RetrievedDocument(
                doc_id=doc.get("doc_id", ""),
                title=doc.get("title", ""),
                url=doc.get("url", ""),
                content_snippet=doc.get("content_snippet", ""),
                similarity_score=doc.get("similarity_score", 0.0),
                category=doc.get("category", ""),
                metadata=doc.get("metadata", {})
            ))
        
        # Parse debug info
        debug_data = way_response.get("debug_info", {})
        latency_data = debug_data.get("latency_breakdown", {})
        debug_info = DebugInfo(
            top_doc_score=debug_data.get("top_doc_score", 0.0),
            num_relevant_docs=debug_data.get("num_relevant_docs", 0),
            latency_breakdown=LatencyBreakdown(
                search_ms=latency_data.get("search_ms", 0.0),
                llm_ms=latency_data.get("llm_ms", 0.0),
                total_ms=latency_data.get("total_ms", 0.0)
            ),
            trace_id=debug_data.get("trace_id", ""),
            mock=debug_data.get("mock", False),
            fallback=debug_data.get("fallback", False),
            error=debug_data.get("error")
        )
        
        # Parse timestamp
        timestamp_str = way_response.get("timestamp")
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                timestamp = datetime.utcnow()
        else:
            timestamp = datetime.utcnow()
        
        return cls(
            reply=way_response.get("answer", ""),
            confidence=way_response.get("rag_confidence", 0.0),
            action=way_response.get("suggested_action", "escalate"),
            trace_id=debug_data.get("trace_id", ""),
            query=way_response.get("query", ""),
            business_signals=business_signals,
            citations=way_response.get("citations", []),
            retrieved_docs=retrieved_docs,
            debug_info=debug_info,
            timestamp=timestamp,
            escalated=escalated,
            ticket_id=ticket_id
        )


# =============================================================================
# Health Check Models
# =============================================================================

class HealthStatus(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Overall status: 'healthy' or 'unhealthy'")
    version: str = Field(default="1.0.0", description="API version")
    way_connection: dict = Field(
        default_factory=dict,
        description="WAY API connection status"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# Error Models
# =============================================================================

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    trace_id: Optional[str] = Field(None, description="Request trace ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
