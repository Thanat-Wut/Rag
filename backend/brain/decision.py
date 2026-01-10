class DecisionEngine:
    CONFIDENCE_THRESHOLD = 0.7
    # Intent ที่ต้องส่งต่อพนักงานเสมอ
    ESCALATE_INTENTS = ["action", "access_request"]

    def decide(self, classification: dict, confidence: float) -> str:
        # 1. ถ้าความมั่นใจต่ำ (Confidence < 0.7) -> Escalate
        if confidence < self.CONFIDENCE_THRESHOLD:
            return "escalate"
        
        # 2. ถ้าเป็นเรื่องบัญชี และมีความเร่งด่วนสูง -> Escalate
        if classification["category"] == "Accounting" and classification["urgency"] == "high":
            return "escalate"
            
        # 3. ถ้าเป็นเรื่อง IT แต่ความมั่นใจไม่สูงมาก (0.7 - 0.8) -> Escalate
        if classification["category"] == "IT" and confidence < 0.8:
            return "escalate"

        return "answer"

engine = DecisionEngine()
