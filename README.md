# 🎯 WUT & WAY - Internal Helpdesk System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)
![React](https://img.shields.io/badge/React-18+-61DAFB.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**WUT** (Backend Orchestrator) & **WAY** (RAG Engine) - ระบบ Internal Helpdesk อัจฉริยะ
ขับเคลื่อนด้วยเทคโนโลยี RAG (Retrieval-Augmented Generation)

[Features](#-features) •
[Quick Start](#-quick-start) •
[Architecture](#-architecture) •
[API Reference](#-api-reference) •
[Configuration](#-configuration) •
[Troubleshooting](#-troubleshooting)

</div>

---

## 👥 ทีมพัฒนา

| ชื่อ | บทบาท | ความรับผิดชอบ |
|------|--------|---------------|
| **WUT** | Backend Orchestrator | จัดการ Flow, Classification, Decision Engine |
| **WAY** | RAG Engine Developer | Vector Search, LLM Integration, Knowledge Base |

---

## 📋 Overview

ระบบ Internal Helpdesk ประกอบด้วย 2 ส่วนหลัก:

### 🔵 WUT - Backend Orchestrator
- **Query Classification** - จัดหมวดหมู่คำถามตามแผนก (HR, IT, Accounting)
- **Decision Engine** - ตัดสินใจว่าจะตอบเอง หรือส่งต่อให้เจ้าหน้าที่
- **API Gateway** - เชื่อมต่อ Frontend กับ WAY RAG Engine

### 🟢 WAY - RAG Engine  
- **Vector Search** - ค้นหาเอกสารที่เกี่ยวข้องจาก Knowledge Base
- **LLM Integration** - สร้างคำตอบด้วย Gemini AI
- **Confidence Scoring** - ประเมินความมั่นใจในคำตอบ

---

## ✨ Features

| Feature | Owner | Description |
|---------|-------|-------------|
| 🧠 **Query Classification** | WUT | จัดหมวดหมู่คำถามอัตโนมัติ |
| 🎯 **Decision Engine** | WUT | กฎการตัดสินใจ answer/escalate/clarify |
| 🔍 **Vector Search** | WAY | ค้นหาเอกสารด้วย Semantic Search |
| 🤖 **LLM Response** | WAY | สร้างคำตอบด้วย Gemini |
| 📊 **Confidence Score** | WAY | คะแนนความมั่นใจ (rag_confidence) |
| 🔗 **API Integration** | WUT | เชื่อมต่อระหว่าง Services |
| 🎭 **Mock Mode** | WUT | โหมดพัฒนาเมื่อ WAY ไม่พร้อม |
| 🎫 **Ticket Creation** | WUT | สร้าง Ticket อัตโนมัติ |
| 🐳 **Docker Ready** | Both | Containerization พร้อมใช้งาน |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Gemini API Key (สำหรับ WAY)

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
cd AI_InternalHelpdesk/Rag

# Create environment file
cat > .env << EOF
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-1.5-flash
LOG_LEVEL=INFO
EOF

# Start all services
docker-compose up --build

# Services:
# - Frontend: http://localhost:5173
# - WUT Backend: http://localhost:8001
# - WAY Backend: http://localhost:8000
# - Qdrant: http://localhost:6333
```

### Option 2: Local Development

#### WUT Backend Setup

```bash
cd Rag/backend

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "WAY_API_URL=http://localhost:8000" > .env
echo "USE_MOCK=false" >> .env

# Run WUT server
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

#### WAY Backend Setup

```bash
cd Rag_way

# Create virtual environment  
python -m venv venv
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "GEMINI_API_KEY=your_key_here" > .env
echo "QDRANT_URL=http://localhost:6333" >> .env

# Run WAY server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

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
│                   React + Vite + TailwindCSS                        │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                 🔵 WUT Backend (Port 8001)                          │
│  ┌─────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  │
│  │ Classifier  │→ │ Decision Engine │→ │   WAY API Client        │  │
│  │             │  │                 │  │                         │  │
│  │ • Category  │  │ • Thresholds    │  │ • HTTP Client           │  │
│  │ • Keywords  │  │ • Safety Rules  │  │ • Response Parsing      │  │
│  └─────────────┘  └─────────────────┘  └─────────────────────────┘  │
│                         by WUT                                      │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                 🟢 WAY Backend (Port 8000)                          │
│  ┌─────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  │
│  │ RAG Engine  │→ │ Vector Search   │→ │    Gemini LLM           │  │
│  │             │  │                 │  │                         │  │
│  │ • Query     │  │ • Qdrant        │  │ • Response Gen          │  │
│  │ • Context   │  │ • Embeddings    │  │ • Confidence            │  │
│  └─────────────┘  └─────────────────┘  └─────────────────────────┘  │
│                         by WAY                                      │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   Qdrant Vector DB (Port 6333)                      │
│                   Knowledge Base Storage                            │
└─────────────────────────────────────────────────────────────────────┘
```

### Project Structure

```
AI_InternalHelpdesk/
├── Rag/                        # 🔵 WUT's Domain
│   ├── backend/                # WUT Backend (FastAPI)
│   │   ├── brain/              # Core Logic
│   │   │   ├── classifier.py   # Query Classification
│   │   │   ├── coordinator.py  # Main Orchestrator
│   │   │   └── decision.py     # Decision Engine
│   │   ├── connectors/         # External Services
│   │   │   └── way_api.py      # WAY API Client
│   │   ├── config.py           # Configuration
│   │   ├── models.py           # Pydantic Models
│   │   └── main.py             # FastAPI App
│   │
│   ├── frontend/               # Frontend (React)
│   │   └── src/
│   │
│   └── docker-compose.yml      # All Services
│
└── Rag_way/                    # 🟢 WAY's Domain
    ├── main.py                 # FastAPI App
    ├── rag_engine.py           # RAG Logic
    ├── vector_store.py         # Qdrant Client
    └── llm_client.py           # Gemini Integration
```

---

## 📡 API Reference

### WUT → WAY Communication

#### Request (WUT sends to WAY)
```http
POST http://way-backend:8000/rag/query
Content-Type: application/json

{
  "query": "รหัสผ่านอีเมลหาย",
  "user_dept": "IT",
  "trace_id": "abc-123"
}
```

#### Response (WAY returns to WUT)
```json
{
  "answer": "หากรหัสผ่านอีเมลหาย ให้ดำเนินการดังนี้...",
  "rag_confidence": 0.85,
  "suggested_action": "answer",
  "business_signals": {
    "has_action_keywords": false,
    "has_urgent_keywords": false
  },
  "citations": ["doc_it_001"],
  "retrieved_docs": [...]
}
```

### ⚠️ Critical Field Names

| WAY Returns | WUT Uses As | Notes |
|-------------|-------------|-------|
| `rag_confidence` | `confidence` | ไม่ใช่ "confidence" |
| `suggested_action` | `action` | ไม่ใช่ "action" |
| `business_signals` | `business_signals` | Object |

---

## 🔄 Data Flow

```
1. User ส่งคำถาม → Frontend
                      ↓
2. Frontend → WUT Backend (POST /api/query)
                      ↓
3. WUT: Classifier จัดหมวดหมู่ (HR/IT/Accounting)
                      ↓
4. WUT → WAY Backend (POST /rag/query)
                      ↓
5. WAY: Vector Search หาเอกสารที่เกี่ยวข้อง
                      ↓
6. WAY: Gemini สร้างคำตอบ + rag_confidence
                      ↓
7. WAY → WUT (Response with rag_confidence)
                      ↓
8. WUT: Decision Engine ตัดสินใจ
   • rag_confidence >= 0.70 → answer
   • rag_confidence < 0.50 → escalate
   • urgent keywords → escalate
                      ↓
9. WUT → Frontend (Final Response)
                      ↓
10. User เห็นคำตอบ
```

---

## ⚙️ Configuration

### 🔵 WUT Backend Environment

| Variable | Default | Owner | Description |
|----------|---------|-------|-------------|
| `WAY_API_URL` | `http://localhost:8000` | WUT | URL ของ WAY |
| `WAY_TIMEOUT` | `10` | WUT | Timeout (seconds) |
| `USE_MOCK` | `false` | WUT | Mock mode |
| `CONFIDENCE_THRESHOLD` | `0.70` | WUT | Threshold ขั้นต่ำ |

### 🟢 WAY Backend Environment

| Variable | Default | Owner | Description |
|----------|---------|-------|-------------|
| `GEMINI_API_KEY` | - | WAY | Google AI API Key |
| `QDRANT_URL` | - | WAY | Qdrant URL |
| `GEMINI_MODEL` | `gemini-1.5-flash` | WAY | Model name |

---

## 🧪 Testing

### ทดสอบ WUT Backend
```bash
# Health check
curl http://localhost:8001/health

# Query test
curl -X POST http://localhost:8001/api/query \
  -H "Content-Type: application/json" \
  -d '{"message": "วิธีขอลาพักร้อน"}'
```

### ทดสอบ WAY Backend โดยตรง
```bash
# Health check
curl http://localhost:8000/health

# RAG query
curl -X POST http://localhost:8000/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query": "วิธีขอลาพักร้อน", "trace_id": "test-001"}'
```

### Integration Test
```bash
cd Rag
./test_way_integration.sh
```

---

## 🔧 Troubleshooting

### ❌ WUT ไม่สามารถเชื่อมต่อ WAY

```bash
# ตรวจสอบ WAY running
docker-compose ps

# ดู logs ของ WAY
docker-compose logs way-backend

# ตรวจสอบ URL
# Docker: WAY_API_URL=http://way-backend:8000
# Local:  WAY_API_URL=http://localhost:8000
```

### ❌ rag_confidence not found

**สาเหตุ:** WUT ใช้ field name ผิด

```python
# ❌ ผิด
confidence = response.get("confidence")

# ✅ ถูก
confidence = response.get("rag_confidence")
```

### ❌ ได้ escalate ตลอด

1. ตรวจสอบว่า Qdrant มี documents
2. ดู WAY logs ว่า search ได้ผลลัพธ์ไหม
3. ตรวจสอบ rag_confidence ที่ WAY ส่งกลับ

---

## 📚 Documentation

- [INTEGRATION.md](./INTEGRATION.md) - รายละเอียดการเชื่อมต่อ WUT ↔ WAY
- [WUT API Docs](http://localhost:8001/docs) - Swagger Documentation
- [WAY API Docs](http://localhost:8000/docs) - Swagger Documentation

---

## 🤝 Team Collaboration

### WUT's Responsibilities
- [ ] Query Classification
- [ ] Decision Engine Rules
- [ ] WAY API Client
- [ ] Frontend Integration
- [ ] Error Handling & Fallback

### WAY's Responsibilities
- [ ] RAG Engine
- [ ] Vector Search (Qdrant)
- [ ] LLM Integration (Gemini)
- [ ] Confidence Scoring
- [ ] Document Ingestion

### Shared Responsibilities
- [ ] API Contract Definition
- [ ] Integration Testing
- [ ] Docker Compose Setup
- [ ] Documentation

---

<div align="center">

**Built with ❤️ by WUT & WAY**

🔵 WUT - Backend Orchestrator | 🟢 WAY - RAG Engine

</div>