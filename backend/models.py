from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Literal
from uuid import uuid4

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    department: Optional[Literal["IT", "HR", "Accounting"]] = None
    trace_id: Optional[str] = Field(default_factory=lambda: str(uuid4()))

    @field_validator('query')
    @classmethod
    def query_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()

class ClassifiedQuery(BaseModel):
    category: Literal["IT", "HR", "Accounting", "General"]
    urgency: Literal["low", "medium", "high"]
    intent: str = "information_retrieval"
    score: float = 0.0

# เพิ่ม RetrievedDoc สำหรับเก็บข้อมูลเอกสารที่ค้นหาได้
class RetrievedDoc(BaseModel):
    doc_id: str
    score: float
    text: Optional[str] = None
    metadata: Optional[dict] = None

# เพิ่ม WAYResponse สำหรับรับค่าจาก WAY API (Task B7)
class WAYResponse(BaseModel):
    answer: str
    confidence: float
    decision: str
    citations: List[str] = Field(default_factory=list)
    retrieved_docs: List[RetrievedDoc] = Field(default_factory=list)
    latency_ms: int = 0

class TicketTemplate(BaseModel):
    department: str
    subject: str
    contact_email: str
    message_template: str
    priority: Literal["low", "medium", "high"]

class HelpdeskResponse(BaseModel):
    query: str
    action: Literal["answer", "escalate"]
    answer: Optional[str] = None
    confidence: float
    citations: List[str] = Field(default_factory=list)
    ticket: Optional[TicketTemplate] = None
    processing_time_ms: int
    trace_id: str
