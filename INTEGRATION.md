# 🔗 WUT ↔ WAY Integration Guide

## 👥 ทีมพัฒนา

| ชื่อ | Role | ความรับผิดชอบ |
|------|------|---------------|
| **WUT** | Backend Orchestrator | Classification, Decision, API Gateway |
| **WAY** | RAG Engine | Vector Search, LLM, Knowledge Base |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         User Browser                                │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Frontend (Port 5173)                           │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│              🔵 WUT Backend (Port 8001)                             │
│  ┌─────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  │
│  │ Classifier  │→ │ Decision Engine │→ │   WAY API Client        │  │
│  └─────────────┘  └─────────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│              🟢 WAY Backend (Port 8000)                             │
│  ┌─────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  │
│  │ RAG Engine  │→ │ Vector Search   │→ │    Gemini LLM           │  │
│  └─────────────┘  └─────────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   Qdrant Vector DB (Port 6333)                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📝 API Contract

### WUT → WAY Request

**Endpoint:** `POST http://way-backend:8000/rag/query`

```json
{
  "query": "รหัสผ่านอีเมลหาย ต้องทำอย่างไร",
  "user_dept": "IT",
  "trace_id": "abc-123-def-456",
  "max_results": 5,
  "temperature": 0.7
}
```

| Field | Type | Required | Owner | Description |
|-------|------|----------|-------|-------------|
| `query` | string | ✅ | WUT→WAY | คำถามของ User |
| `user_dept` | string | ❌ | WUT→WAY | แผนก (HR, IT, Accounting) |
| `trace_id` | string | ✅ | WUT→WAY | Request ID สำหรับ tracking |
| `max_results` | int | ❌ | WUT→WAY | จำนวน docs สูงสุด |
| `temperature` | float | ❌ | WUT→WAY | LLM temperature |

---

### WAY → WUT Response

```json
{
  "answer": "หากรหัสผ่านอีเมลหาย ให้ดำเนินการดังนี้...",
  "rag_confidence": 0.85,
  "suggested_action": "answer",
  "query": "รหัสผ่านอีเมลหาย",
  "business_signals": {
    "has_action_keywords": false,
    "has_urgent_keywords": false,
    "query_department_match": true
  },
  "citations": ["doc_it_001"],
  "retrieved_docs": [...],
  "debug_info": {...}
}
```

| Field | Type | Owner | Description |
|-------|------|-------|-------------|
| `answer` | string | WAY | คำตอบที่สร้างจาก RAG |
| `rag_confidence` | float | WAY | ความมั่นใจ (0.0-1.0) |
| `suggested_action` | string | WAY | "answer" หรือ "escalate" |
| `business_signals` | object | WAY | สัญญาณที่ตรวจพบ |
| `citations` | array | WAY | รายการ doc IDs |
| `retrieved_docs` | array | WAY | เอกสารที่ค้นพบ |
| `debug_info` | object | WAY | ข้อมูล debug |

---

## ⚠️ Critical Field Mappings

### Field Names ที่ WUT ต้องใช้ให้ถูกต้อง

| WAY ส่งมา | WUT ต้องใช้ | ❌ ห้ามใช้ |
|-----------|-------------|-----------|
| `rag_confidence` | `response.get("rag_confidence")` | `response.get("confidence")` |
| `suggested_action` | `response.get("suggested_action")` | `response.get("action")` |

### Code Example (WUT's way_api.py)

```python
def _parse_response(self, raw: Dict[str, Any]) -> Dict[str, Any]:
    return {
        # ✅ ถูกต้อง: ใช้ชื่อ field ตามที่ WAY ส่งมา
        "answer": raw.get("answer", ""),
        "rag_confidence": raw.get("rag_confidence", 0.0),      # ✅
        "suggested_action": raw.get("suggested_action", ""),    # ✅
        
        # ❌ ผิด: ชื่อ field ไม่ตรง
        # "confidence": raw.get("confidence", 0.0),            # ❌
        # "action": raw.get("action", ""),                     # ❌
    }
```

---

## 🎯 Decision Engine (WUT)

WUT ใช้ข้อมูลจาก WAY ในการตัดสินใจ:

```python
def decide(way_response: dict, classified: dict) -> str:
    # ใช้ rag_confidence จาก WAY
    rag_confidence = way_response.get("rag_confidence", 0.0)
    suggested_action = way_response.get("suggested_action", "escalate")
    business_signals = way_response.get("business_signals", {})
    
    # WUT's Rules
    
    # Rule 1: Accounting + action → escalate (safety)
    if classified["category"] == "Accounting" and classified["has_action"]:
        return "escalate"
    
    # Rule 2: Low confidence → escalate
    if rag_confidence < 0.50:
        return "escalate"
    
    # Rule 3: Urgent → escalate
    if business_signals.get("has_urgent_keywords"):
        return "escalate"
    
    # Rule 4: Medium confidence → clarify
    if rag_confidence < 0.70:
        return "clarify"
    
    # Rule 5: High confidence → use WAY's suggestion
    return suggested_action
```

---

## 🌐 Environment Variables

### 🔵 WUT Backend

```bash
# .env ใน Rag/backend/
WAY_API_URL=http://localhost:8000      # URL ของ WAY
WAY_TIMEOUT=10                          # Timeout (seconds)
USE_MOCK=false                          # Mock mode
CONFIDENCE_THRESHOLD=0.70               # Threshold
```

### 🟢 WAY Backend

```bash
# .env ใน Rag_way/
GEMINI_API_KEY=your_api_key_here       # Required
QDRANT_URL=http://localhost:6333       # Qdrant URL
GEMINI_MODEL=gemini-1.5-flash          # Model
```

### Docker Compose (.env ใน Rag/)

```bash
# ใช้ร่วมกัน
GEMINI_API_KEY=your_api_key_here
LOG_LEVEL=INFO
```

---

## 🔧 Troubleshooting

### ❌ WUT: "rag_confidence not found"

**สาเหตุ:** WUT ใช้ field name ผิด

**แก้ไข:** ตรวจสอบ `Rag/backend/connectors/way_api.py`:
```python
# ❌ ผิด
confidence = response.get("confidence", 0.0)

# ✅ ถูก
confidence = response.get("rag_confidence", 0.0)
```

---

### ❌ WUT: "Connection refused to WAY"

**สาเหตุ:** WAY ไม่ทำงาน หรือ URL ผิด

**แก้ไข:**
```bash
# 1. ตรวจสอบ WAY running
docker-compose ps

# 2. ดู WAY logs
docker-compose logs way-backend

# 3. ตรวจสอบ URL
# Docker: http://way-backend:8000
# Local:  http://localhost:8000
```

---

### ❌ WAY: "GEMINI_API_KEY not set"

**สาเหตุ:** ไม่มี API key

**แก้ไข:**
```bash
# สร้าง .env ใน Rag/
echo "GEMINI_API_KEY=your_key_here" > .env
docker-compose up --build
```

---

### ❌ ได้ escalate ตลอด

**สาเหตุ:** rag_confidence ต่ำ หรือไม่มี documents

**ตรวจสอบ:**
```bash
# 1. Qdrant มี documents?
curl http://localhost:6333/collections | jq

# 2. WAY search ได้ผลลัพธ์?
docker-compose logs way-backend | grep "retrieved"

# 3. rag_confidence เท่าไหร่?
# ดูใน response จาก WAY
```

---

## 🧪 Testing

### ทดสอบ WUT → WAY Integration

```bash
# 1. Start services
docker-compose up -d

# 2. Test WUT health (ตรวจสอบ WAY connection)
curl http://localhost:8001/health | jq

# 3. Test full flow
curl -X POST http://localhost:8001/api/query \
  -H "Content-Type: application/json" \
  -d '{"message": "วิธีขอลาพักร้อน"}' | jq

# 4. ดู rag_confidence ใน response
# ถ้า >= 0.70 → action: "answer"
# ถ้า < 0.70 → action: "clarify" หรือ "escalate"
```

### ทดสอบ WAY โดยตรง

```bash
curl -X POST http://localhost:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "วิธีขอลาพักร้อน",
    "user_dept": "HR",
    "trace_id": "test-001"
  }' | jq
```

---

## 📊 Monitoring

### Log Correlation

ใช้ `trace_id` ติดตาม request ข้าม services:

```bash
# หา logs ทั้งหมดของ request นี้
docker-compose logs | grep "abc-123-def"
```

### Key Metrics

| Metric | Location | Owner |
|--------|----------|-------|
| Response Time | `debug_info.latency_breakdown` | WAY |
| Confidence | `rag_confidence` | WAY |
| Escalation Rate | Action counts | WUT |
| Error Rate | `debug_info.error` | Both |

---

<div align="center">

**🔵 WUT** ↔ **🟢 WAY**

Backend Orchestrator ↔ RAG Engine

</div>
