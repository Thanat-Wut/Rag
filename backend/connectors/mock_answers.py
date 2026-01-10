MOCK_RESPONSES = {
    "รหัสผ่าน | password reset": {
        "answer": "การรีเซ็ตรหัสผ่านอีเมล สามารถทำได้โดยเข้าที่ portal.mango.internal/reset [1]",
        "confidence": 0.92,
        "decision": "answered",
        "citations": ["[1] IT Policy Manual"],
        "retrieved_docs": [{"doc_id": "IT-001", "score": 0.92}],
        "latency_ms": 850
    },
    "ลาป่วย | sick leave": {
        "answer": "การลาป่วยต้องแจ้งหัวหน้างานก่อน 9:00 น. และกรอกใบลาใน HR Portal [1]",
        "confidence": 0.88,
        "decision": "answered",
        "citations": ["[1] HR Handbook 2026"],
        "retrieved_docs": [{"doc_id": "HR-002", "score": 0.9}],
        "latency_ms": 920
    }
}

def get_mock_response(query: str):
    query_lower = query.lower()
    for keywords, response in MOCK_RESPONSES.items():
        for kw in keywords.split(" | "):
            if kw.lower() in query_lower:
                return response.copy()
    return {
        "answer": "ไม่พบข้อมูล กรุณาติดต่อเจ้าหน้าที่",
        "confidence": 0.25,
        "decision": "low_confidence",
        "citations": [],
        "retrieved_docs": [],
        "latency_ms": 500
    }