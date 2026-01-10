import httpx
import asyncio
import time
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from models import WAYResponse
from config import config
from connectors.mock_answers import get_mock_response

class WAYServiceException(Exception):
    """Custom exception for WAY service failures"""
    pass

class WAYClient:
    def __init__(self):
        self.base_url = config.WAY_API_URL
        self.timeout = config.WAY_TIMEOUT
        self.use_mock = config.USE_MOCK
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout, connect=5.0),
            follow_redirects=True
        )

    async def query(self, query_text: str, department: Optional[str] = None, trace_id: Optional[str] = None) -> WAYResponse:
        start_time = time.time()
        if self.use_mock:
            await asyncio.sleep(0.5)
            mock_data = get_mock_response(query_text, department)
            return self._parse_response(mock_data)

        try:
            data = await self._call_api_with_retry(query_text, department, trace_id)
            return self._parse_response(data)
        except Exception as e:
            print(f" [WAYClient] API failed: {type(e).__name__}. Falling back to MOCK.")
            mock_data = get_mock_response(query_text, department)
            mock_data["answer"] = f"⚠️ [โหมดสำรอง] \n\n{mock_data['answer']}"
            return self._parse_response(mock_data)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError)),
        reraise=True
    )
    async def _call_api_with_retry(self, query_text: str, department: Optional[str], trace_id: Optional[str]) -> dict:
        response = await self.client.post(
            f"{self.base_url}/rag/query",
            json={"query": query_text, "user_dept": department, "trace_id": trace_id}
        )
        if response.status_code == 200:
            return response.json()
        raise WAYServiceException(f"HTTP {response.status_code}")

    def _parse_response(self, data: dict) -> WAYResponse:
        return WAYResponse(
            answer=data.get("answer", "ไม่สามารถสร้างคำตอบได้"),
            confidence=data.get("confidence", 0.0),
            decision=data.get("decision", "low_confidence"),
            citations=data.get("citations", []),
            retrieved_docs=data.get("retrieved_docs", []),
            latency_ms=data.get("latency_ms", 0)
        )

    async def close(self):
        await self.client.aclose()
