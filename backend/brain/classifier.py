from models import ClassifiedQuery
from typing import Dict, List, Tuple

class Classifier:
    # กฎ Tie-break: ถ้าคะแนนเท่ากัน ให้เรียงตามนี้ (Task B5 [cite: 520-522])
    PRIORITY_ORDER = ["IT", "HR", "Accounting", "General"]

    DEPT_KEYWORDS = {
        "IT": {
            "primary": ["password", "รหัสผ่าน", "email", "อีเมล", "vpn", "wifi", "internet", "ระบบ", "software"],
            "secondary": ["reset", "รีเซ็ต", "ลืม", "ช้า", "พัง", "error", "ติดตั้ง"]
        },
        "HR": {
            "primary": ["ลาป่วย", "ลาพักร้อน", "เงินเดือน", "สวัสดิการ", "ประกันสังคม", "pvd"],
            "secondary": ["ขอ", "เท่าไหร่", "ยังไง", "ระเบียบ"]
        },
        "Accounting": {
            "primary": ["เบิก", "invoice", "ใบกำกับภาษี", "ภาษี", "หัก ณ ที่จ่าย", "ชำระเงิน"],
            "secondary": ["รอบ", "กำหนด", "เอกสาร"]
        }
    }

    def classify(self, query: str) -> dict:
        query_low = query.lower()
        scores = {dept: 0 for dept in self.DEPT_KEYWORDS}
        
        for dept, keywords in self.DEPT_KEYWORDS.items():
            # Primary = 3 points
            for kw in keywords["primary"]:
                if kw in query_low: scores[dept] += 3
            # Secondary = 1 point
            for kw in keywords["secondary"]:
                if kw in query_low: scores[dept] += 1

        # เลือก Dept ที่คะแนนสูงสุด (ถ้าเท่ากันใช้ PRIORITY_ORDER)
        best_dept = "General"
        max_score = 0
        
        for dept in self.PRIORITY_ORDER:
            if dept in scores and scores[dept] > max_score:
                max_score = scores[dept]
                best_dept = dept
        
        # ตรวจสอบความเร่งด่วน (Urgency)
        is_urgent = any(kw in query_low for kw in ["ด่วน", "ทันที", "พัง", "urgent", "critical"])
        
        return {
            "category": best_dept,
            "urgency": "high" if is_urgent else "low",
            "score": max_score
        }

classifier = Classifier()
