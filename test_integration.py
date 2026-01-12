#!/usr/bin/env python3
"""Integration tests for WAY + WUT system"""

import requests
import sys

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
RESET = '\033[0m'

class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
    
    def test_health(self, name, url):
        print(f"[Testing] {name}...", end=" ")
        try:
            r = requests.get(url, timeout=5)
            r.raise_for_status()
            print(f"{GREEN}✅ PASS{RESET}")
            self.passed += 1
        except Exception as e:
            print(f"{RED}❌ FAIL{RESET}")
            self.failed += 1
    
    def test_query(self, name, url, body, check_action=None):
        print(f"[Testing] {name}...", end=" ")
        try:
            r = requests.post(url, json=body, timeout=10)
            r.raise_for_status()
            data = r.json()
            
            action = data.get("action", data.get("suggested_action", "unknown"))
            confidence = data.get("confidence", data.get("rag_confidence", 0))
            
            if check_action and action != check_action:
                print(f"{RED}❌ FAIL{RESET} (expected={check_action}, got={action})")
                self.failed += 1
            else:
                print(f"{GREEN}✅ PASS{RESET} (action={action}, conf={confidence:.2f})")
                self.passed += 1
        except Exception as e:
            print(f"{RED}❌ FAIL{RESET} ({str(e)[:40]})")
            self.failed += 1
    
    def summary(self):
        print(f"\n{CYAN}=== Results ==={RESET}")
        print(f"{GREEN}Passed: {self.passed}{RESET}")
        if self.failed == 0:
            print(f"{GREEN}Failed: 0{RESET}")
            print(f"\n{GREEN}✅ All tests passed!{RESET}")
            return 0
        else:
            print(f"{RED}Failed: {self.failed}{RESET}")
            return 1

def main():
    runner = TestRunner()
    
    print(f"\n{CYAN}=== WAY + WUT Integration Tests ==={RESET}\n")
    
    # Health
    print(f"{YELLOW}--- Health Checks ---{RESET}")
    runner.test_health("Qdrant", "http://localhost:6333/healthz")
    runner.test_health("WAY", "http://localhost:8000/health")
    runner.test_health("WUT", "http://localhost:8001/health")
    
    # WAY Direct
    print(f"\n{YELLOW}--- WAY Direct ---{RESET}")
    runner.test_query(
        "WAY password reset",
        "http://localhost:8000/rag/query",
        {"query": "รหัสผ่านหาย", "user_dept": "IT", "trace_id": "t1"}
    )
    
    # WUT Integration
    print(f"\n{YELLOW}--- WUT Integration ---{RESET}")
    runner.test_query(
        "IT Query",
        "http://localhost:8001/api/internal-helpdesk/query",
        {"message": "รหัสผ่านอีเมลหาย", "department": "IT"}
    )
    
    runner.test_query(
        "HR Query",
        "http://localhost:8001/api/internal-helpdesk/query",
        {"message": "ขอลาพักร้อน"}
    )
    
    runner.test_query(
        "Accounting (should escalate)",
        "http://localhost:8001/api/internal-helpdesk/query",
        {"message": "อนุมัติงบประมาณ", "department": "Accounting"},
        check_action="escalate"
    )
    
    sys.exit(runner.summary())

if __name__ == "__main__":
    main()
