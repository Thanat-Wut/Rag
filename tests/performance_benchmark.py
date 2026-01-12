"""performance_benchmark.py

Locust load testing script for WUT-WAY RAG Integration.

Usage:
    # Run with Locust Web UI
    locust -f tests/performance_benchmark.py --host=http://localhost:8001
    
    # Run headless mode with specific parameters
    locust -f tests/performance_benchmark.py --host=http://localhost:8001 \
        --users 50 --spawn-rate 10 --run-time 5m --headless
    
    # Run with HTML report
    locust -f tests/performance_benchmark.py --host=http://localhost:8001 \
        --users 100 --spawn-rate 20 --run-time 10m --headless \
        --html tests/performance_report.html

Environment Variables:
    WUT_URL: WUT service URL (default: http://localhost:8001)
    TEST_SCENARIOS_FILE: Path to test scenarios JSON (default: tests/test_scenarios.json)
"""

import json
import os
import random
import time
from typing import Dict, Any, List
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner

# =============================================================================
# Configuration
# =============================================================================

WUT_URL = os.getenv("WUT_URL", "http://localhost:8001")
TEST_SCENARIOS_FILE = os.getenv("TEST_SCENARIOS_FILE", "tests/test_scenarios.json")

# Load test scenarios
try:
    with open(TEST_SCENARIOS_FILE, "r", encoding="utf-8") as f:
        TEST_SCENARIOS = json.load(f)
except FileNotFoundError:
    print(f"Warning: {TEST_SCENARIOS_FILE} not found. Using default scenarios.")
    TEST_SCENARIOS = {
        "functional_tests": [
            {
                "id": "DEFAULT001",
                "input": {
                    "message": "How do I reset my password?",
                    "department": "IT",
                    "trace_id": "default-001"
                }
            }
        ]
    }

# =============================================================================
# Test Data Preparation
# =============================================================================

class TestDataPool:
    """Pool of test queries categorized by complexity."""
    
    def __init__(self, scenarios: Dict[str, Any]):
        self.quick_queries = []
        self.standard_queries = []
        self.complex_queries = []
        self.urgent_queries = []
        
        self._load_scenarios(scenarios)
    
    def _load_scenarios(self, scenarios: Dict[str, Any]):
        """Load and categorize test scenarios."""
        functional = scenarios.get("functional_tests", [])
        
        for scenario in functional:
            input_data = scenario.get("input", {})
            expected = scenario.get("expected", {})
            
            # Categorize based on expected signals and complexity
            signals = expected.get("business_signals", {})
            
            if signals.get("has_urgent_keywords"):
                self.urgent_queries.append(input_data)
            elif len(input_data.get("message", "")) > 50 or input_data.get("context"):
                self.complex_queries.append(input_data)
            elif len(input_data.get("message", "")) <= 20:
                self.quick_queries.append(input_data)
            else:
                self.standard_queries.append(input_data)
        
        # Add performance test scenarios
        perf_tests = scenarios.get("performance_tests", [])
        for scenario in perf_tests:
            input_data = scenario.get("input", {})
            if "PERF001" in scenario.get("id", ""):
                self.quick_queries.append(input_data)
            elif "PERF003" in scenario.get("id", ""):
                self.complex_queries.append(input_data)
            else:
                self.standard_queries.append(input_data)
        
        # Ensure we have at least some data in each category
        if not self.quick_queries:
            self.quick_queries = [{
                "message": "password",
                "department": "IT",
                "trace_id": "quick-default"
            }]
        
        if not self.standard_queries:
            self.standard_queries = [{
                "message": "How do I reset my password?",
                "department": "IT",
                "trace_id": "standard-default"
            }]
        
        if not self.complex_queries:
            self.complex_queries = [{
                "message": "I need help submitting travel expense claims",
                "department": "Accounting",
                "context": "Multiple receipts from business trip",
                "trace_id": "complex-default"
            }]
        
        if not self.urgent_queries:
            self.urgent_queries = [{
                "message": "URGENT: System crashed!",
                "department": "IT",
                "trace_id": "urgent-default"
            }]
    
    def get_quick_query(self) -> Dict[str, Any]:
        """Get a random quick query."""
        query = random.choice(self.quick_queries).copy()
        query["trace_id"] = f"load-quick-{int(time.time() * 1000)}"
        return query
    
    def get_standard_query(self) -> Dict[str, Any]:
        """Get a random standard query."""
        query = random.choice(self.standard_queries).copy()
        query["trace_id"] = f"load-standard-{int(time.time() * 1000)}"
        return query
    
    def get_complex_query(self) -> Dict[str, Any]:
        """Get a random complex query."""
        query = random.choice(self.complex_queries).copy()
        query["trace_id"] = f"load-complex-{int(time.time() * 1000)}"
        return query
    
    def get_urgent_query(self) -> Dict[str, Any]:
        """Get a random urgent query."""
        query = random.choice(self.urgent_queries).copy()
        query["trace_id"] = f"load-urgent-{int(time.time() * 1000)}"
        return query


# Initialize test data pool
test_data = TestDataPool(TEST_SCENARIOS)

# =============================================================================
# Performance Metrics Collection
# =============================================================================

response_times = []
confidence_scores = []
error_count = 0


@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Track response times for analysis."""
    if exception is None:
        response_times.append(response_time)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Print summary statistics when test stops."""
    if response_times:
        response_times.sort()
        p50 = response_times[int(len(response_times) * 0.5)]
        p95 = response_times[int(len(response_times) * 0.95)]
        p99 = response_times[int(len(response_times) * 0.99)]
        avg = sum(response_times) / len(response_times)
        
        print("\n" + "="*60)
        print("PERFORMANCE SUMMARY")
        print("="*60)
        print(f"Total Requests: {len(response_times)}")
        print(f"Average Response Time: {avg:.0f}ms")
        print(f"P50 (Median): {p50:.0f}ms")
        print(f"P95: {p95:.0f}ms")
        print(f"P99: {p99:.0f}ms")
        print(f"Min: {min(response_times):.0f}ms")
        print(f"Max: {max(response_times):.0f}ms")
        
        if confidence_scores:
            avg_confidence = sum(confidence_scores) / len(confidence_scores)
            print(f"\nAverage Confidence Score: {avg_confidence:.3f}")
        
        print(f"\nErrors: {error_count}")
        print("="*60)


# =============================================================================
# Locust User Classes
# =============================================================================

class StandardUser(HttpUser):
    """Standard user simulating typical helpdesk queries."""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    weight = 6  # 60% of total users
    host = WUT_URL
    
    @task(6)  # 60% of user's tasks
    def query_standard(self):
        """Execute a standard query."""
        payload = test_data.get_standard_query()
        
        with self.client.post(
            "/api/query",
            json=payload,
            catch_response=True,
            name="Standard Query"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "confidence" in data:
                        confidence_scores.append(data["confidence"])
                    response.success()
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                global error_count
                error_count += 1
                response.failure(f"HTTP {response.status_code}")
    
    @task(3)  # 30% of user's tasks
    def query_quick(self):
        """Execute a quick query."""
        payload = test_data.get_quick_query()
        
        with self.client.post(
            "/api/query",
            json=payload,
            catch_response=True,
            name="Quick Query"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                global error_count
                error_count += 1
                response.failure(f"HTTP {response.status_code}")
    
    @task(1)  # 10% of user's tasks
    def health_check(self):
        """Check service health."""
        with self.client.get(
            "/health",
            catch_response=True,
            name="Health Check"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"HTTP {response.status_code}")


class PowerUser(HttpUser):
    """Power user simulating complex queries."""
    
    wait_time = between(2, 5)  # Wait 2-5 seconds between requests
    weight = 3  # 30% of total users
    host = WUT_URL
    
    @task(5)  # 50% of power user's tasks
    def query_complex(self):
        """Execute a complex query with context."""
        payload = test_data.get_complex_query()
        
        with self.client.post(
            "/api/query",
            json=payload,
            catch_response=True,
            name="Complex Query"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "confidence" in data:
                        confidence_scores.append(data["confidence"])
                    
                    # Verify retrieved documents
                    if "retrieved_docs" not in data:
                        response.failure("Missing retrieved_docs")
                    else:
                        response.success()
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                global error_count
                error_count += 1
                response.failure(f"HTTP {response.status_code}")
    
    @task(3)  # 30% of power user's tasks
    def query_standard(self):
        """Execute a standard query."""
        payload = test_data.get_standard_query()
        
        with self.client.post(
            "/api/query",
            json=payload,
            catch_response=True,
            name="Standard Query (Power)"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                global error_count
                error_count += 1
                response.failure(f"HTTP {response.status_code}")
    
    @task(2)  # 20% of power user's tasks
    def query_with_max_results(self):
        """Execute query with high max_results."""
        payload = test_data.get_standard_query()
        payload["max_results"] = 10
        
        with self.client.post(
            "/api/query",
            json=payload,
            catch_response=True,
            name="High Max Results Query"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                global error_count
                error_count += 1
                response.failure(f"HTTP {response.status_code}")


class UrgentUser(HttpUser):
    """User simulating urgent/critical queries."""
    
    wait_time = between(0.5, 2)  # Urgent users wait less
    weight = 1  # 10% of total users
    host = WUT_URL
    
    @task(8)  # 80% of urgent user's tasks
    def query_urgent(self):
        """Execute an urgent query."""
        payload = test_data.get_urgent_query()
        
        with self.client.post(
            "/api/query",
            json=payload,
            catch_response=True,
            name="Urgent Query"
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    
                    # Verify urgent detection
                    signals = data.get("business_signals", {})
                    if not signals.get("has_urgent_keywords") and \
                       not signals.get("has_action_keywords"):
                        response.failure("Failed to detect urgent keywords")
                    else:
                        response.success()
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                global error_count
                error_count += 1
                response.failure(f"HTTP {response.status_code}")
    
    @task(2)  # 20% of urgent user's tasks
    def query_standard_urgent(self):
        """Execute a standard query but with urgent expectations."""
        payload = test_data.get_standard_query()
        
        with self.client.post(
            "/api/query",
            json=payload,
            catch_response=True,
            name="Standard Query (Urgent User)"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                global error_count
                error_count += 1
                response.failure(f"HTTP {response.status_code}")


# =============================================================================
# Custom Shape (Optional)
# =============================================================================

from locust import LoadTestShape

class StepLoadShape(LoadTestShape):
    """
    A step load shape that increases users in steps.
    
    Stages:
    - 0-60s: 10 users
    - 60-120s: 25 users
    - 120-180s: 50 users
    - 180-240s: 75 users
    - 240-300s: 100 users
    """
    
    step_time = 60  # Duration of each step in seconds
    step_load = 15  # User increase per step
    spawn_rate = 5  # Users to spawn per second
    time_limit = 300  # Total test duration in seconds
    
    def tick(self):
        run_time = self.get_run_time()
        
        if run_time > self.time_limit:
            return None
        
        current_step = run_time // self.step_time
        user_count = 10 + (current_step * self.step_load)
        
        return (user_count, self.spawn_rate)


if __name__ == "__main__":
    print("\n" + "="*60)
    print("WUT-WAY Performance Benchmark")
    print("="*60)
    print(f"Host: {WUT_URL}")
    print(f"Test Scenarios: {TEST_SCENARIOS_FILE}")
    print(f"Quick Queries: {len(test_data.quick_queries)}")
    print(f"Standard Queries: {len(test_data.standard_queries)}")
    print(f"Complex Queries: {len(test_data.complex_queries)}")
    print(f"Urgent Queries: {len(test_data.urgent_queries)}")
    print("="*60)
    print("\nRun with: locust -f tests/performance_benchmark.py\n")
