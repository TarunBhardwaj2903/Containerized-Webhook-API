from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
import re

# Pydantic Models

class WebhookRequest(BaseModel):
    message_id: str = Field(..., min_length=1)
    from_: str = Field(..., alias="from")
    to: str
    ts: str
    text: Optional[str] = Field(None, max_length=4096)

    @field_validator('from_', 'to')
    def validate_e164(cls, v):
        # Simple E.164-like validation: start with +, then digits
        if not re.match(r'^\+\d+$', v):
            raise ValueError('Must be in E.164 format (e.g. +1234567890)')
        return v
    
    @field_validator('ts')
    def validate_iso8601(cls, v):
         if not v.endswith('Z'):
             raise ValueError('Timestamp must be UTC and end with Z')
         return v

class MessageResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    message_id: str
    from_: str = Field(..., alias="from")
    to: str
    ts: str
    text: Optional[str]

class MessageListResponse(BaseModel):
    data: List[MessageResponse]
    total: int
    limit: int
    offset: int

class SenderStats(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    from_: str = Field(..., alias="from")
    count: int

class StatsResponse(BaseModel):
    total_messages: int
    senders_count: int
    messages_per_sender: List[SenderStats]
    first_message_ts: Optional[str]
    last_message_ts: Optional[str]

# DB Schema (Raw SQL)
DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS messages (
    message_id TEXT PRIMARY KEY,
    from_msisdn TEXT NOT NULL,
    to_msisdn TEXT NOT NULL,
    ts TEXT NOT NULL,
    text TEXT,
    created_at TEXT NOT NULL
);
"""
