import sqlite3
from datetime import datetime, timezone
import logging
from typing import List, Optional, Tuple, Any

from app.models import DB_SCHEMA, WebhookRequest, MessageResponse, SenderStats, StatsResponse
from app.config import settings

logger = logging.getLogger("api")

def get_db_connection():
    try:
        # Extract path from sqlite:////data/app.db -> /data/app.db
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise e

def init_db():
    conn = get_db_connection()
    try:
        conn.executescript(DB_SCHEMA)
        conn.commit()
    finally:
        conn.close()

def insert_message(msg: WebhookRequest) -> bool:
    """
    Inserts a message. Returns True if inserted, False if duplicate.
    """
    conn = get_db_connection()
    try:
        created_at = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        conn.execute(
            "INSERT INTO messages (message_id, from_msisdn, to_msisdn, ts, text, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (msg.message_id, msg.from_, msg.to, msg.ts, msg.text, created_at)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Duplicate message_id
        return False
    finally:
        conn.close()

def get_messages(limit: int, offset: int, from_filter: Optional[str], since_filter: Optional[str], q_filter: Optional[str]) -> Tuple[List[MessageResponse], int]:
    conn = get_db_connection()
    try:
        query = "SELECT * FROM messages WHERE 1=1"
        params: List[Any] = []
        
        if from_filter:
            query += " AND from_msisdn = ?"
            params.append(from_filter)
        if since_filter:
            query += " AND ts >= ?"
            params.append(since_filter)
        if q_filter:
            query += " AND text LIKE ?"
            params.append(f"%{q_filter}%")
            
        # Get total count first
        count_query = f"SELECT COUNT(*) as cnt FROM ({query})"
        cursor = conn.execute(count_query, params)
        total = cursor.fetchone()['cnt']
        
        # Get data
        query += " ORDER BY ts ASC, message_id ASC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
        
        results = [
            MessageResponse(
                message_id=row['message_id'],
                from_=row['from_msisdn'],
                to=row['to_msisdn'],
                ts=row['ts'],
                text=row['text']
            ) for row in rows
        ]
        
        return results, total
    finally:
        conn.close()

def get_stats() -> StatsResponse:
    conn = get_db_connection()
    try:
        # Total messages
        total_cursor = conn.execute("SELECT COUNT(*) as cnt, MIN(ts) as min_ts, MAX(ts) as max_ts FROM messages")
        total_row = total_cursor.fetchone()
        total_messages = total_row['cnt']
        first_ts = total_row['min_ts']
        last_ts = total_row['max_ts']

        # Messages per sender
        sender_cursor = conn.execute("""
            SELECT from_msisdn, COUNT(*) as cnt 
            FROM messages 
            GROUP BY from_msisdn 
            ORDER BY cnt DESC 
            LIMIT 10
        """)
        sender_rows = sender_cursor.fetchall()
        
        messages_per_sender = [
            SenderStats(from_=row['from_msisdn'], count=row['cnt']) 
            for row in sender_rows
        ]
        
        senders_count_cursor = conn.execute("SELECT COUNT(DISTINCT from_msisdn) as cnt FROM messages")
        senders_count = senders_count_cursor.fetchone()['cnt']
        
        return StatsResponse(
            total_messages=total_messages,
            senders_count=senders_count,
            messages_per_sender=messages_per_sender,
            first_message_ts=first_ts,
            last_message_ts=last_ts
        )
    finally:
        conn.close()
