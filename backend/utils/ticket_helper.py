from models import TicketTemplate

# คลังข้อมูลสำหรับสร้างร่างตั๋วตามแผนก (Task B8)
TICKET_TEMPLATES = {
    "IT": {
        "subject": "แจ้งปัญหา/ขอรับบริการด้าน IT",
        "email": "it.support@mango.com",
        "template": "พบปัญหาการใช้งาน: {query}\nประเภท: Support Request"
    },
    "HR": {
        "subject": "ติดต่อสอบถามงานบุคคล/สวัสดิการ",
        "email": "hr.center@mango.com",
        "template": "รายละเอียดคำร้อง: {query}"
    },
    "Accounting": {
        "subject": "แจ้งเรื่องการเบิกจ่าย/ใบกำกับภาษี",
        "email": "account.pay@mango.com",
        "template": "รายละเอียดคำร้อง: {query}"
    }
}

def generate_ticket(category: str, query: str, urgency: str) -> TicketTemplate:
    # เลือก Template ตามแผนก (Default เป็น IT ถ้าหาไม่เจอ)
    info = TICKET_TEMPLATES.get(category, TICKET_TEMPLATES["IT"])
    
    return TicketTemplate(
        department=category,
        subject=info["subject"],
        contact_email=info["email"],
        message_template=info["template"].format(query=query),
        priority=urgency
    )
