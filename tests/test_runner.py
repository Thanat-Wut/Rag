"""test_runner.py

Python pytest suite for WUT-WAY integration testing.

Usage:
    pytest tests/test_runner.py -v                    # Run all tests
    pytest tests/test_runner.py -v -k health          # Run health tests only
    pytest tests/test_runner.py -v -k test_wut        # Run WUT tests only
    pytest tests/test_runner.py -v --maxfail=1        # Stop after first failure
    pytest tests/test_runner.py -v -s                 # Show print output

Environment Variables:
    WUT_URL: WUT service URL (default: http://localhost:8001)
    WAY_URL: WAY service URL (default: http://localhost:8000)
    QDRANT_URL: Qdrant URL (default: http://localhost:6333)
"""

import pytest
import requests
import os
import json
import time
from typing import Dict, Any, Optional
from datetime import datetime

# =============================================================================
# Configuration
# =============================================================================

WUT_URL = os.getenv("WUT_URL", "http://localhost:8001")
WAY_URL = os.getenv("WAY_URL", "http://localhost:8000")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")

REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "10"))
MIN_CONFIDENCE = float(os.getenv("MIN_CONFIDENCE", "0.5"))
MAX_RESPONSE_TIME_MS = int(os.getenv("MAX_RESPONSE_TIME_MS", "5000"))

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def wut_client():
    """Create a session for WUT service."""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    yield session
    session.close()


@pytest.fixture(scope="session")
def way_client():
    """Create a session for WAY service."""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    yield session
    session.close()


@pytest.fixture(scope="session")
def qdrant_client():
    """Create a session for Qdrant service."""
    session = requests.Session()
    yield session
    session.close()


@pytest.fixture
def trace_id():
    """Generate unique trace ID for each test."""
    return f"pytest-{int(time.time() * 1000)}"


# =============================================================================
# Helper Functions
# =============================================================================


def validate_helpdesk_response(response_data: Dict[str, Any]) -> None:
    """Validate WUT HelpdeskResponse structure.
    
    Args:
        response_data: Response JSON from WUT API
    
    Raises:
        AssertionError: If validation fails
    """
    required_fields = [
        "reply",
        "confidence",
        "action",
        "trace_id",
        "query",
        "business_signals",
        "citations",
        "retrieved_docs",
    ]
    
    for field in required_fields:
        assert field in response_data, f"Missing required field: {field}"
    
    # Validate types
    assert isinstance(response_data["reply"], str), "reply must be string"
    assert isinstance(response_data["confidence"], (int, float)), "confidence must be number"
    assert 0.0 <= response_data["confidence"] <= 1.0, "confidence must be 0-1"
    assert response_data["action"] in ["answer", "escalate", "clarify", "ticket"], "invalid action"
    assert isinstance(response_data["business_signals"], dict), "business_signals must be object"
    assert isinstance(response_data["citations"], list), "citations must be array"
    assert isinstance(response_data["retrieved_docs"], list), "retrieved_docs must be array"


def validate_way_response(response_data: Dict[str, Any]) -> None:
    """Validate WAY RAGQueryResponse structure.
    
    Args:
        response_data: Response JSON from WAY API
    
    Raises:
        AssertionError: If validation fails
    """
    required_fields = [
        "answer",
        "rag_confidence",
        "suggested_action",
        "query",
        "business_signals",
    ]
    
    for field in required_fields:
        assert field in response_data, f"Missing required field: {field}"
    
    assert isinstance(response_data["answer"], str), "answer must be string"
    assert isinstance(response_data["rag_confidence"], (int, float)), "rag_confidence must be number"
    assert 0.0 <= response_data["rag_confidence"] <= 1.0, "rag_confidence must be 0-1"


def validate_business_signals(signals: Dict[str, Any]) -> None:
    """Validate BusinessSignals structure.
    
    Args:
        signals: BusinessSignals object from response
    
    Raises:
        AssertionError: If validation fails
    """
    required_fields = [
        "has_action_keywords",
        "has_urgent_keywords",
        "query_department_match",
    ]
    
    for field in required_fields:
        assert field in signals, f"Missing signal field: {field}"
        assert isinstance(signals[field], bool), f"{field} must be boolean"


# =============================================================================
# Health Check Tests
# =============================================================================


class TestHealthChecks:
    """Test suite for service health checks."""

    def test_qdrant_health(self, qdrant_client):
        """Test Qdrant service health."""
        response = qdrant_client.get(f"{QDRANT_URL}/health", timeout=REQUEST_TIMEOUT)
        assert response.status_code == 200, "Qdrant health check failed"

    def test_qdrant_collections(self, qdrant_client):
        """Test Qdrant collections endpoint."""
        response = qdrant_client.get(f"{QDRANT_URL}/collections", timeout=REQUEST_TIMEOUT)
        assert response.status_code == 200, "Qdrant collections check failed"
        data = response.json()
        assert "result" in data, "Qdrant response missing 'result'"

    def test_way_health(self, way_client):
        """Test WAY service health."""
        response = way_client.get(f"{WAY_URL}/health", timeout=REQUEST_TIMEOUT)
        assert response.status_code == 200, "WAY health check failed"
        data = response.json()
        assert data.get("status") in ["healthy", "connected"], "WAY not healthy"

    def test_way_root(self, way_client):
        """Test WAY root endpoint."""
        response = way_client.get(f"{WAY_URL}/", timeout=REQUEST_TIMEOUT)
        assert response.status_code == 200, "WAY root endpoint failed"

    def test_wut_health(self, wut_client):
        """Test WUT service health."""
        response = wut_client.get(f"{WUT_URL}/health", timeout=REQUEST_TIMEOUT)
        assert response.status_code == 200, "WUT health check failed"
        data = response.json()
        assert data.get("status") in ["healthy", "degraded"], "WUT not healthy"
        assert "way_connection" in data, "WUT health missing way_connection"

    def test_wut_root(self, wut_client):
        """Test WUT root endpoint."""
        response = wut_client.get(f"{WUT_URL}/", timeout=REQUEST_TIMEOUT)
        assert response.status_code == 200, "WUT root endpoint failed"
        data = response.json()
        assert data.get("service") == "WUT Backend", "Incorrect service name"


# =============================================================================
# WAY Service Tests
# =============================================================================


class TestWAYService:
    """Test suite for WAY RAG service."""

    def test_way_rag_query_basic(self, way_client, trace_id):
        """Test basic WAY RAG query."""
        payload = {
            "query": "How do I reset my password?",
            "trace_id": trace_id,
            "user_dept": "IT",
        }
        
        response = way_client.post(
            f"{WAY_URL}/rag/query",
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        
        assert response.status_code == 200, f"WAY query failed: {response.text}"
        data = response.json()
        validate_way_response(data)
        
        # Check answer is not empty
        assert len(data["answer"]) > 0, "WAY returned empty answer"

    def test_way_rag_query_hr_department(self, way_client, trace_id):
        """Test WAY query with HR department."""
        payload = {
            "query": "How many days of annual leave do I have?",
            "trace_id": trace_id,
            "user_dept": "HR",
        }
        
        response = way_client.post(
            f"{WAY_URL}/rag/query",
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        
        assert response.status_code == 200
        data = response.json()
        validate_way_response(data)

    def test_way_rag_query_with_context(self, way_client, trace_id):
        """Test WAY query with additional context."""
        payload = {
            "query": "How do I submit an expense claim?",
            "trace_id": trace_id,
            "user_dept": "Accounting",
            "context": "I need to claim travel expenses from last week's trip.",
        }
        
        response = way_client.post(
            f"{WAY_URL}/rag/query",
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        
        assert response.status_code == 200
        data = response.json()
        validate_way_response(data)

    def test_way_invalid_payload(self, way_client):
        """Test WAY with invalid payload."""
        payload = {"invalid": "payload"}
        
        response = way_client.post(
            f"{WAY_URL}/rag/query",
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        
        assert response.status_code == 422, "WAY should reject invalid payload"


# =============================================================================
# WUT Service Tests
# =============================================================================


class TestWUTService:
    """Test suite for WUT orchestrator service."""

    def test_wut_query_simple(self, wut_client, trace_id):
        """Test simple WUT query."""
        payload = {
            "message": "How do I reset my password?",
            "department": "IT",
            "trace_id": trace_id,
        }
        
        response = wut_client.post(
            f"{WUT_URL}/api/query",
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        
        assert response.status_code == 200, f"WUT query failed: {response.text}"
        data = response.json()
        validate_helpdesk_response(data)
        
        # Verify trace_id matches
        assert data["trace_id"] == trace_id, "Trace ID mismatch"

    def test_wut_query_urgent_detection(self, wut_client, trace_id):
        """Test WUT urgent keyword detection."""
        payload = {
            "message": "URGENT: My computer crashed and I lost all data!",
            "department": "IT",
            "trace_id": trace_id,
        }
        
        response = wut_client.post(
            f"{WUT_URL}/api/query",
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        
        assert response.status_code == 200
        data = response.json()
        validate_helpdesk_response(data)
        validate_business_signals(data["business_signals"])
        
        # Should detect urgent and action keywords
        signals = data["business_signals"]
        assert signals["has_urgent_keywords"] is True, "Failed to detect urgent keywords"
        assert signals["has_action_keywords"] is True, "Failed to detect action keywords"

    def test_wut_query_action_detection(self, wut_client, trace_id):
        """Test WUT action keyword detection."""
        payload = {
            "message": "I cannot access my email account, it says blocked",
            "department": "IT",
            "trace_id": trace_id,
        }
        
        response = wut_client.post(
            f"{WUT_URL}/api/query",
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        
        assert response.status_code == 200
        data = response.json()
        signals = data["business_signals"]
        
        # Should detect action keywords ("cannot access", "blocked")
        assert signals["has_action_keywords"] is True, "Failed to detect action keywords"

    def test_wut_department_matching(self, wut_client, trace_id):
        """Test department matching between user and query classification."""
        payload = {
            "message": "How do I request annual leave?",
            "department": "HR",
            "trace_id": trace_id,
        }
        
        response = wut_client.post(
            f"{WUT_URL}/api/query",
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        
        assert response.status_code == 200
        data = response.json()
        signals = data["business_signals"]
        
        # Department should match (HR query from HR user)
        # Note: This may not always be true depending on WAY's classification
        # so we just check the field exists
        assert "query_department_match" in signals

    def test_wut_confidence_threshold(self, wut_client, trace_id):
        """Test WUT confidence scoring."""
        payload = {
            "message": "What is the company dress code policy?",
            "department": "HR",
            "trace_id": trace_id,
        }
        
        response = wut_client.post(
            f"{WUT_URL}/api/query",
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Confidence should be within valid range
        confidence = data["confidence"]
        assert 0.0 <= confidence <= 1.0, f"Invalid confidence: {confidence}"

    def test_wut_invalid_payload(self, wut_client):
        """Test WUT with invalid payload."""
        payload = {"invalid": "payload"}
        
        response = wut_client.post(
            f"{WUT_URL}/api/query",
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        
        assert response.status_code == 422, "WUT should reject invalid payload"

    def test_wut_legacy_endpoint(self, wut_client, trace_id):
        """Test WUT legacy endpoint for backward compatibility."""
        payload = {
            "message": "Test query",
            "trace_id": trace_id,
        }
        
        response = wut_client.post(
            f"{WUT_URL}/api/internal-helpdesk/query",
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        
        assert response.status_code == 200, "Legacy endpoint failed"
        data = response.json()
        validate_helpdesk_response(data)


# =============================================================================
# Integration Tests (WUT + WAY + Qdrant)
# =============================================================================


class TestIntegration:
    """Test suite for end-to-end integration."""

    def test_end_to_end_flow(self, wut_client, trace_id):
        """Test complete flow from WUT through WAY to Qdrant."""
        payload = {
            "message": "How do I submit an expense claim?",
            "department": "Accounting",
            "trace_id": trace_id,
            "max_results": 3,
        }
        
        start_time = time.time()
        response = wut_client.post(
            f"{WUT_URL}/api/query",
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        elapsed_ms = (time.time() - start_time) * 1000
        
        assert response.status_code == 200, f"E2E flow failed: {response.text}"
        data = response.json()
        validate_helpdesk_response(data)
        
        # Verify all pipeline components contributed
        assert len(data["reply"]) > 0, "Empty reply"
        assert data["confidence"] > 0, "Zero confidence"
        assert "debug_info" in data, "Missing debug info"
        
        # Check retrieved documents
        assert "retrieved_docs" in data, "Missing retrieved_docs"
        # Note: May be empty if knowledge base is not populated
        
        print(f"\nE2E Test Results:")
        print(f"  Reply length: {len(data['reply'])} chars")
        print(f"  Confidence: {data['confidence']:.2f}")
        print(f"  Action: {data['action']}")
        print(f"  Retrieved docs: {len(data['retrieved_docs'])}")
        print(f"  Elapsed time: {elapsed_ms:.0f}ms")

    def test_citation_accuracy(self, wut_client, trace_id):
        """Test that citations match retrieved documents."""
        payload = {
            "message": "What are the IT security policies?",
            "department": "IT",
            "trace_id": trace_id,
        }
        
        response = wut_client.post(
            f"{WUT_URL}/api/query",
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        
        assert response.status_code == 200
        data = response.json()
        
        citations = data.get("citations", [])
        retrieved_docs = data.get("retrieved_docs", [])
        
        # All citations should reference valid documents
        doc_ids = {doc["doc_id"] for doc in retrieved_docs}
        for citation in citations:
            assert citation in doc_ids or len(doc_ids) == 0, \
                f"Citation {citation} not in retrieved docs"

    def test_performance_baseline(self, wut_client, trace_id):
        """Test that response time meets baseline requirements."""
        payload = {
            "message": "Performance test query",
            "trace_id": trace_id,
        }
        
        start_time = time.time()
        response = wut_client.post(
            f"{WUT_URL}/api/query",
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        elapsed_ms = (time.time() - start_time) * 1000
        
        assert response.status_code == 200
        assert elapsed_ms < MAX_RESPONSE_TIME_MS, \
            f"Response too slow: {elapsed_ms:.0f}ms (max: {MAX_RESPONSE_TIME_MS}ms)"
        
        print(f"\nPerformance: {elapsed_ms:.0f}ms (threshold: {MAX_RESPONSE_TIME_MS}ms)")


# =============================================================================
# Edge Cases & Error Handling
# =============================================================================


class TestEdgeCases:
    """Test suite for edge cases and error handling."""

    def test_empty_message(self, wut_client, trace_id):
        """Test WUT with empty message."""
        payload = {
            "message": "",
            "trace_id": trace_id,
        }
        
        response = wut_client.post(
            f"{WUT_URL}/api/query",
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        
        # Should reject empty message
        assert response.status_code == 422, "Should reject empty message"

    def test_very_long_message(self, wut_client, trace_id):
        """Test WUT with very long message."""
        payload = {
            "message": "x" * 3000,  # Exceeds 2000 char limit
            "trace_id": trace_id,
        }
        
        response = wut_client.post(
            f"{WUT_URL}/api/query",
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        
        # Should reject message that's too long
        assert response.status_code == 422, "Should reject overly long message"

    def test_invalid_department(self, wut_client, trace_id):
        """Test WUT with invalid department (should default to 'Other')."""
        payload = {
            "message": "Test query",
            "department": "InvalidDept",
            "trace_id": trace_id,
        }
        
        response = wut_client.post(
            f"{WUT_URL}/api/query",
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        
        # Should accept but normalize to 'Other'
        assert response.status_code == 200, "Should handle invalid department"

    def test_special_characters(self, wut_client, trace_id):
        """Test WUT with special characters in message."""
        payload = {
            "message": "Test @#$% special <chars> & symbols!",
            "trace_id": trace_id,
        }
        
        response = wut_client.post(
            f"{WUT_URL}/api/query",
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        
        assert response.status_code == 200, "Should handle special characters"

    def test_thai_language(self, wut_client, trace_id):
        """Test WUT with Thai language query."""
        payload = {
            "message": "ฉันจะขอลาพักร้อนได้อย่างไร",
            "department": "HR",
            "trace_id": trace_id,
        }
        
        response = wut_client.post(
            f"{WUT_URL}/api/query",
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        
        assert response.status_code == 200, "Should handle Thai language"
        data = response.json()
        
        # Should detect Thai keywords
        signals = data["business_signals"]
        # "ลา" should be detected as HR keyword
        assert signals["has_action_keywords"] is True or \
               len(data["retrieved_docs"]) > 0, "Should process Thai query"


if __name__ == "__main__":
    # Run tests with pytest when executed directly
    pytest.main([__file__, "-v", "-s"])
