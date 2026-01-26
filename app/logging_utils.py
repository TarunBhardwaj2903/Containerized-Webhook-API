import logging
import json
import time
from datetime import datetime, timezone

# Configure logging
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "ts": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        
        # Add extra fields if they exist in valid json log keys
        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id
        if hasattr(record, "method"):
            log_record["method"] = record.method
        if hasattr(record, "path"):
            log_record["path"] = record.path
        if hasattr(record, "status"):
            log_record["status"] = record.status
        if hasattr(record, "latency_ms"):
            log_record["latency_ms"] = record.latency_ms
            
        # Specific for webhook
        if hasattr(record, "message_id"):
            log_record["message_id"] = record.message_id
        if hasattr(record, "dup"):
            log_record["dup"] = record.dup
        if hasattr(record, "result"):
            log_record["result"] = record.result

        return json.dumps(log_record)

def setup_logging(log_level: str):
    logger = logging.getLogger("api")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
    logger.setLevel(log_level.upper())
    return logger

logger = logging.getLogger("api")
