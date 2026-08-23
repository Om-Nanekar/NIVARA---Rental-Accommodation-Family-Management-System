from contextlib import contextmanager
import mysql.connector
from mysql.connector import Error
from config import Config

@contextmanager
def get_connection():
    conn = mysql.connector.connect(**Config.DB_CONFIG)
    try:
        yield conn
    finally:
        if conn.is_connected():
            conn.close()
    return mysql.connector.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DATABASE
    )

def fetch_all(query, params=None):
    with get_connection() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(query, params or ())
        rows = cur.fetchall()
        cur.close()
        return rows

def fetch_one(query, params=None):
    with get_connection() as conn:
        cur = conn.cursor(dictionary=True)
        cur.execute(query, params or ())
        row = cur.fetchone()
        cur.close()
        return row

def execute(query, params=None, many=False):
    with get_connection() as conn:
        cur = conn.cursor()
        if many:
            cur.executemany(query, params or [])
        else:
            cur.execute(query, params or ())
        conn.commit()
        last_id = cur.lastrowid
        affected = cur.rowcount
        cur.close()
        return last_id, affected

def transaction(callback):
    with get_connection() as conn:
        try:
            result = callback(conn)
            conn.commit()
            return result
        except Exception:
            conn.rollback()
            raise
