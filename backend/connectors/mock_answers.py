from typing import Optional

# Mock answers database organized by department/topic
MOCK_ANSWERS = {
    "leave": {
        "answer": "To request leave, please submit your application through the HR portal at least 3 days in advance. Annual leave entitlement is 20 days per year.",
        "confidence": 0.92,
        "citations": ["doc_hr_leave_001"],
        "retrieved_docs": [
            {
                "doc_id": "doc_hr_leave_001",
                "title": "Leave Policy Guide",
                "url": "https://kb.company.com/hr/leave-policy",
                "content_snippet": "Employees are entitled to 20 days of annual leave...",
                "similarity_score": 0.95,
                "category": "HR",
                "metadata": {"last_updated": "2024-01-15"}
            }
        ]
    },
    "password": {
        "answer": "To reset your password, go to the IT Self-Service Portal and click 'Forgot Password'. You'll receive a reset link via email within 5 minutes.",
        "confidence": 0.95,
        "citations": ["doc_it_password_001"],
        "retrieved_docs": [
            {
                "doc_id": "doc_it_password_001",
                "title": "Password Reset Guide",
                "url": "https://kb.company.com/it/password-reset",
                "content_snippet": "Use the self-service portal to reset your password...",
                "similarity_score": 0.97,
                "category": "IT",
                "metadata": {"last_updated": "2024-02-01"}
            }
        ]
    },
    "expense": {
        "answer": "Submit expense reports through the Finance Portal within 30 days of the expense. Attach receipts for amounts over $25. Reimbursement typically takes 5-7 business days.",
        "confidence": 0.88,
        "citations": ["doc_finance_expense_001"],
        "retrieved_docs": [
            {
                "doc_id": "doc_finance_expense_001",
                "title": "Expense Reimbursement Policy",
                "url": "https://kb.company.com/finance/expenses",
                "content_snippet": "All expenses must be submitted within 30 days...",
                "similarity_score": 0.91,
                "category": "Accounting",
                "metadata": {"last_updated": "2024-01-20"}
            }
        ]
    },
    "default": {
        "answer": "I found some relevant information, but I recommend verifying with your department manager for the most accurate guidance.",
        "confidence": 0.65,
        "citations": [],
        "retrieved_docs": []
    }
}


def get_mock_answer(query: str, user_dept: Optional[str] = None) -> dict:
    """
    Get a mock answer based on query keywords.
    
    Args:
        query: User's question
        user_dept: User's department (optional)
    
    Returns:
        dict: Mock answer with confidence, citations, and retrieved_docs
    """
    query_lower = query.lower()
    
    # Match keywords to mock answers
    if any(word in query_lower for word in ["leave", "vacation", "pto", "time off", "holiday"]):
        return MOCK_ANSWERS["leave"]
    
    if any(word in query_lower for word in ["password", "reset", "login", "access", "locked"]):
        return MOCK_ANSWERS["password"]
    
    if any(word in query_lower for word in ["expense", "reimburse", "receipt", "travel cost"]):
        return MOCK_ANSWERS["expense"]
    
    # Default low-confidence response
    return MOCK_ANSWERS["default"]