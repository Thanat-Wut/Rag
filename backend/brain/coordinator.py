import time
from models import QueryRequest, HelpdeskResponse
from brain.classifier import classifier
from brain.decision import engine
from connectors.way_api import WAYClient
from utils.logger import setup_logger, log_with_context
from utils.ticket_helper import generate_ticket  # เพิ่มตัวช่วยสร้างตั๋ว

logger = setup_logger("wut.coordinator")

class Coordinator:
    def __init__(self):
        self.way_client = WAYClient()

    async def process_query(self, request: QueryRequest) -> HelpdeskResponse:
        start_time = time.time()
        trace_id = request.trace_id
        
        # Step 1: Classify
        classified = classifier.classify(request.query)

        # Step 2: Query WAY RAG (หรือ Mock)
        way_res = await self.way_client.query(request.query, classified["category"], trace_id)

        # Step 3: Decision
        final_action = engine.decide(classified, way_res.confidence)

        # Step 4: Generate Ticket if Escalate (เพิ่มส่วนนี้เข้าไป)
        ticket = None
        if final_action == "escalate":
            ticket = generate_ticket(
                category=classified["category"],
                query=request.query,
                urgency=classified["urgency"]
            )

        total_time = int((time.time() - start_time) * 1000)
        
        log_with_context(logger, "info", "Query processed", trace_id=trace_id, 
                         total_ms=total_time, dept=classified["category"], action=final_action)
        
        return HelpdeskResponse(
            query=request.query, 
            action=final_action, 
            answer=way_res.answer,
            confidence=way_res.confidence, 
            citations=way_res.citations,
            ticket=ticket,  # ส่งตั๋วกลับไป
            processing_time_ms=total_time, 
            trace_id=trace_id
        )

    async def shutdown(self):
        await self.way_client.close()
