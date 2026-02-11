import json
import urllib.parse
from ..database import get_db_connection
from ..utils import send_json

def handle_get_threads(handler):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Join with users to get the author's name and avatar
        cursor.execute("""
            SELECT t.*, u.name as author_name, u.avatar_url as author_avatar
            FROM forum_threads t
            JOIN users u ON t.user_id = u.id
            ORDER BY t.created_at DESC
        """)
        threads = [dict(row) for row in cursor.fetchall()]
        
        # Count comments for each thread
        for thread in threads:
            cursor.execute("SELECT COUNT(*) as count FROM forum_comments WHERE thread_id = ?", (thread['id'],))
            row = cursor.fetchone()
            thread['comment_count'] = row['count'] if row else 0
            
        conn.close()
        send_json(handler, 200, threads)
    except Exception as e:
        print(f"Error fetching threads: {e}")
        send_json(handler, 500, {"error": str(e)})

def handle_create_thread(data, handler):
    user_id = data.get('user_id')
    title = data.get('title')
    content = data.get('content')
    
    if not user_id or not title or not content:
        send_json(handler, 400, {"error": "Missing required fields"})
        return
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO forum_threads (user_id, title, content)
            VALUES (?, ?, ?)
        """, (user_id, title, content))
        thread_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        send_json(handler, 201, {"status": "success", "thread_id": thread_id})
    except Exception as e:
        print(f"Error creating thread: {e}")
        send_json(handler, 500, {"error": str(e)})

def handle_get_comments(query_params, handler):
    thread_id = query_params.get('thread_id', [None])[0]
    if not thread_id:
        send_json(handler, 400, {"error": "Missing thread_id"})
        return
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.*, u.name as author_name, u.avatar_url as author_avatar
            FROM forum_comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.thread_id = ?
            ORDER BY c.created_at ASC
        """, (thread_id,))
        comments = [dict(row) for row in cursor.fetchall()]
        conn.close()
        send_json(handler, 200, comments)
    except Exception as e:
        print(f"Error fetching comments: {e}")
        send_json(handler, 500, {"error": str(e)})

def handle_create_comment(data, handler):
    thread_id = data.get('thread_id')
    user_id = data.get('user_id')
    content = data.get('content')
    
    if not thread_id or not user_id or not content:
        send_json(handler, 400, {"error": "Missing required fields"})
        return
        
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO forum_comments (thread_id, user_id, content)
            VALUES (?, ?, ?)
        """, (thread_id, user_id, content))
        comment_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        send_json(handler, 201, {"status": "success", "comment_id": comment_id})
    except Exception as e:
        print(f"Error creating comment: {e}")
        send_json(handler, 500, {"error": str(e)})
