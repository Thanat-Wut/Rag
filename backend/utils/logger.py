import json
import os
from datetime import datetime
from perplexity.backend.config import config

def log_interaction(request_data: dict, response_data: dict):
    log_file = os.path.join(config.LOG_DIR, "wut_app.jsonl")
    
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "request": request_data,
        "response": response_data
    }
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
