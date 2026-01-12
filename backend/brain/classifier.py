"""
Query Classifier - Classifies user queries into departments and detects signals

Responsibilities:
- Categorize queries (HR, IT, Accounting, Other)
- Extract keywords
- Detect action and urgent keywords
- Assess classification confidence
"""

import logging
from typing import List, Tuple, Dict
from models import ClassifiedQuery

logger = logging.getLogger(__name__)

# =============================================================================
# Department-specific Keywords
# =============================================================================

DEPARTMENT_KEYWORDS = {
    "HR": {
        "keywords": [
            "leave", "vacation", "holiday", "absent", "sick", "ลา", "วันลา",
            "salary", "wage", "payroll", "เงินเดือน", "อัตราเงินเดือน",
            "contract", "employment", "hire", "recruit", "สัญญา", "จ้าง",
            "benefit", "insurance", "health", "ประกันสุขภาพ", "สวัสดิการ",
            "appraisal", "review", "performance", "evaluation", "ประเมินผล",
            "policy", "rule", "guideline", "code of conduct", "นโยบาย",
            "resign", "terminate", "retirement", "ลาออก", "เกษียณ",
        ],
        "confidence_weight": 1.0,
    },
    "IT": {
        "keywords": [
            "password", "email", "login", "account", "access", "รหัสผ่าน", "บัญชี",
            "software", "application", "app", "install", "download", "application",
            "computer", "laptop", "pc", "device", "hardware", "เครื่องคอมพิวเตอร์",
            "network", "wifi", "internet", "connection", "vpn", "เน็ตเวิร์ก",
            "server", "database", "system", "downtime", "bug", "error",
            "backup", "recovery", "data", "file", "storage", "ข้อมูล",
            "security", "virus", "malware", "antivirus", "firewall",
            "support", "ticket", "issue", "problem", "helpdesk",
        ],
        "confidence_weight": 1.0,
    },
    "Accounting": {
        "keywords": [
            "invoice", "receipt", "bill", "payment", "ใบแจ้งหนี้", "ใบเสร็จ", "ชำระเงิน",
            "expense", "cost", "budget", "expense claim", "ค่าใช้จ่าย", "งบประมาณ",
            "tax", "vat", "withholding", "ภาษี", "vat", "ภาษีอากร",
            "financial", "report", "statement", "ledger", "account", "บัญชี",
            "audit", "compliance", "reconciliation", "รับรอง",
            "purchase", "order", "po", "supplier", "vendor", "ผู้จัดจำหน่าย",
            "refund", "deduction", "allowance", "compensation", "เงินคืน",
            "investment", "profit", "revenue", "expense", "income", "รายได้",
        ],
        "confidence_weight": 1.0,
    },
}

# =============================================================================
# Action Keywords - Indicates query needs immediate action/escalation
# =============================================================================

ACTION_KEYWORDS = {
    "urgent_action": [
        "error", "crash", "down", "broken", "lost", "missing", "ผิดพลาด",
        "cannot access", "ไม่สามารถ", "ไม่ได้", "ไม่เข้า",
        "blocked", "locked", "failed", "ล็อก", "ล้มเหลว",
    ],
    "urgent_temporal": [
        "asap", "urgent", "emergency", "immediately", "now", "ด่วน",
        "เร่งด่วน", "ทันที", "โดยด่วน",
    ],
}


class Classifier:
    """
    Classifies queries into departments and extracts business signals.
    
    Example:
        classifier = Classifier()
        result = classifier.classify("I lost my password")
        # Returns ClassifiedQuery with category="IT", confidence=0.95
    """
    
    def __init__(self):
        """Initialize classifier with department keywords"""
        self.departments = DEPARTMENT_KEYWORDS
        self.action_keywords = ACTION_KEYWORDS
        logger.info("✅ Classifier initialized")
    
    def classify(self, query: str) -> ClassifiedQuery:
        """
        Classify a query into a department and extract signals.
        
        Args:
            query: User's input query
        
        Returns:
            ClassifiedQuery with classification results
        """
        query_lower = query.lower()
        
        # Find matching department
        category, confidence, matched_keywords = self._find_department(query_lower)
        
        # Detect action signals
        has_action, has_urgent = self._detect_signals(query_lower)
        
        logger.info(
            f"Classification: query='{query[:50]}...' category={category} "
            f"confidence={confidence:.2f} action={has_action} urgent={has_urgent}"
        )
        
        return ClassifiedQuery(
            category=category,
            has_action=has_action,
            has_urgent=has_urgent,
            keywords=matched_keywords,
            confidence=confidence,
        )
    
    def _find_department(self, query_lower: str) -> Tuple[str, float, List[str]]:
        """
        Find the best matching department for the query.
        
        Args:
            query_lower: Lowercased query string
        
        Returns:
            Tuple of (department, confidence, matched_keywords)
        """
        scores = {}
        all_matched = {}
        
        for dept, dept_info in self.departments.items():
            matched = self._extract_keywords(query_lower, dept_info["keywords"])
            all_matched[dept] = matched
            
            if matched:
                # Confidence based on number of matches
                # More matches = higher confidence
                score = min(len(matched) * 0.15, 1.0)
                scores[dept] = score
        
        if not scores:
            logger.debug(f"No department match, defaulting to 'Other'")
            return "Other", 0.0, []
        
        # Get department with highest score
        best_dept = max(scores, key=scores.get)
        best_score = scores[best_dept]
        matched_keywords = all_matched[best_dept]
        
        return best_dept, best_score, matched_keywords
    
    def _extract_keywords(self, query: str, keywords: List[str]) -> List[str]:
        """
        Extract matched keywords from query.
        
        Args:
            query: Lowercased query string
            keywords: List of keywords to match
        
        Returns:
            List of matched keywords
        """
        matched = []
        for keyword in keywords:
            # Simple substring matching (could be upgraded to word boundaries)
            if keyword in query:
                matched.append(keyword)
        return matched
    
    def _detect_signals(self, query_lower: str) -> Tuple[bool, bool]:
        """
        Detect action and urgent signals in query.
        
        Args:
            query_lower: Lowercased query string
        
        Returns:
            Tuple of (has_action, has_urgent)
        """
        has_action = any(
            kw in query_lower for kw in self.action_keywords.get("urgent_action", [])
        )
        
        has_urgent = any(
            kw in query_lower for kw in self.action_keywords.get("urgent_temporal", [])
        )
        
        return has_action or has_urgent, has_urgent


# =============================================================================
# Global classifier instance
# =============================================================================

_classifier_instance: Classifier = None


def get_classifier() -> Classifier:
    """
    Get or create the global classifier instance.
    Uses lazy initialization for efficiency.
    """
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = Classifier() 
    return _classifier_instance

classifier = get_classifier()