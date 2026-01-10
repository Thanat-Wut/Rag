from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from models import QueryRequest, HelpdeskResponse
from brain.coordinator import Coordinator
from config import config, validate_config
from utils.logger import setup_logger
import time

logger = setup_logger("wut.main")
coordinator: Coordinator = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global coordinator
    validate_config()
    coordinator = Coordinator()
    logger.info("✅ WUT Orchestrator Started")
    yield
    await coordinator.shutdown()
    logger.info("✅ Shutdown complete")

app = FastAPI(title="WUT Internal Helpdesk", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS, allow_methods=["*"], allow_headers=["*"])

# --- เพิ่มชุดนี้เข้าไปครับ ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # อนุญาตทุกเว็บ (สำหรับ Dev)
    allow_credentials=True,
    allow_methods=["*"],  # อนุญาตทุก Method (GET, POST, etc.)
    allow_headers=["*"],  # อนุญาตทุก Header
)
# -------------------------

@app.post("/api/internal-helpdesk/query", response_model=HelpdeskResponse)
async def query_helpdesk(request: QueryRequest):
    if not coordinator: raise HTTPException(status_code=503, detail="Service not ready")
    return await coordinator.process_query(request)

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": time.time()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=config.PORT, reload=True)
