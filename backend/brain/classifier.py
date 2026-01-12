"""
Query classifier for WUT Backend
Classifies user queries by department and detects keywords
"""
import re
from typing import Dict, List, Tuple
import logging

# Use relative import when running as package, absolute when running directly
try:
    from ..models import ClassifiedQuery
except ImportError:
    from models import ClassifiedQuery

logger = logging.getLogger(__name__)


class QueryClassifier:
    """Classifies user queries into departments and detects signals"""
    
    def __init__(self):
        # Department keywords
        self.department_keywords: Dict[str, List[str]] = {
            "HR": [
                "ลา", "พักร้อน", "ลาป่วย", "ลากิจ", "วันหยุด", "เงินเดือน", "salary",
                "สวัสดิการ", "benefit", "ประกัน", "insurance", "พนักงาน", "employee",
                "สัญญาจ้าง", "contract", "ลาออก", "resign", "สมัครงาน", "recruit",
                "ฝึกอบรม", "training", "ประเมิน", "evaluation", "โบนัส", "bonus",
                "leave", "vacation", "sick", "annual"
            ],
            "IT": [
                "รหัสผ่าน", "password", "อีเมล", "email", "คอมพิวเตอร์", "computer",
                "โน๊ตบุ๊ค", "laptop", "เครือข่าย", "network", "wifi", "vpn",
                "ระบบ", "system", "ล่ม", "down", "ช้า", "slow", "บัญชี", "account",
                "login", "ล็อกอิน", "software", "ซอฟต์แวร์", "printer", "เครื่องพิมพ์",
                "reset", "install", "ติดตั้ง", "virus", "ไวรัส", "backup"
            ],
            "Accounting": [
                "ใบเสร็จ", "receipt", "ใบกำกับ", "invoice", "ภาษี", "tax",
                "เบิก", "reimburse", "งบ", "budget", "ค่าใช้จ่าย", "expense",
                "โอนเงิน", "transfer", "บัญชี", "account", "การเงิน", "finance",
                "จ่าย", "payment", "เช็ค", "check", "supplier", "vendor"
            ]
        }
        
        # Action keywords
        self.action_keywords: List[str] = [
            "ต้องการ", "ขอ", "สมัคร", "ลง", "เปลี่ยน", "แก้ไข", "อัพเดท",
            "สร้าง", "ลบ", "เพิ่ม", "โอน", "จ่าย", "เบิก", "อนุมัติ",
            "request", "apply", "change", "update", "create", "delete",
            "add", "transfer", "pay", "approve", "submit", "cancel"
        ]
        
        # Urgent keywords
        self.urgent_keywords: List[str] = [
            "ด่วน", "urgent", "เร่ง", "ทันที", "immediately", "asap",
            "วิกฤต", "critical", "ล่ม", "down", "ไม่ได้", "cannot",
            "หยุด", "stop", "ค้าง", "stuck", "emergency", "ฉุกเฉิน"
        ]
    
    def classify(self, query: str) -> ClassifiedQuery:
        """
        Classify a user query.
        
        Args:
            query: User's question or request
        
        Returns:
            ClassifiedQuery with category, signals, and confidence
        """
        query_lower = query.lower()
        
        # Detect department
        category, dept_confidence = self._detect_department(query_lower)
        
        # Detect action keywords
        has_action, action_keywords = self._detect_keywords(query_lower, self.action_keywords)
        
        # Detect urgent keywords
        has_urgent, urgent_keywords = self._detect_keywords(query_lower, self.urgent_keywords)
        
        # Combine detected keywords
        all_keywords = action_keywords + urgent_keywords
        
        result = ClassifiedQuery(
            category=category,
            has_action=has_action,
            has_urgent=has_urgent,
            keywords=all_keywords,
            confidence=dept_confidence
        )
        
        logger.debug(f"Classified query: category={category}, "
                    f"has_action={has_action}, has_urgent={has_urgent}")
        
        return result
    
    def _detect_department(self, query: str) -> Tuple[str, float]:
        """Detect department from query"""
        scores: Dict[str, int] = {"HR": 0, "IT": 0, "Accounting": 0, "Other": 0}
        
        for dept, keywords in self.department_keywords.items():
            for keyword in keywords:
                if keyword.lower() in query:
                    scores[dept] += 1
        
        # Find max score
        max_dept = max(scores, key=scores.get)
        max_score = scores[max_dept]
        
        if max_score == 0:
            return "Other", 0.5
        
        # Calculate confidence based on keyword matches
        total_matches = sum(scores.values())
        confidence = min(0.5 + (max_score / max(total_matches, 1)) * 0.5, 1.0)
        
        return max_dept, confidence
    
    def _detect_keywords(self, query: str, keywords: List[str]) -> Tuple[bool, List[str]]:
        """Detect if any keywords are present"""
        found = []
        for keyword in keywords:
            if keyword.lower() in query:
                found.append(keyword)
        return len(found) > 0, found


# Global classifier instance
classifier = QueryClassifier()


def classify_query(query: str) -> ClassifiedQuery:
    """Convenience function for classification"""
    return classifier.classify(query)
