import sqlite3
from datetime import datetime
import os

DB_PATH = 'marketing.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Создаем таблицу с колонками id, user_id, date, channel, roi, cpl, cpa
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,
            channel TEXT,
            roi REAL,
            cpl REAL,
            cpa REAL
        )
    ''')
    conn.commit()
    conn.close()

def save_analysis_results(user_id, df):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Ищем колонку с названием канала
    channel_col = next((col for col in df.columns if col in ['channel', 'канал', 'source']), None)

    for _, row in df.iterrows():
        channel_name = row[channel_col] if channel_col else 'Unknown'
        roi = row.get('roi', 0)
        cpl = row.get('cpl', 0)
        cpa = row.get('cpa', 0)

        cursor.execute('''
            INSERT INTO analyses (user_id, date, channel, roi, cpl, cpa)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, current_date, channel_name, roi, cpl, cpa))

    conn.commit()
    conn.close()

def get_latest_analysis(user_id):
    # Получает результаты анализа для конкретного пользователя.
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Ищем записи по ID пользователя, отфильтрованные по последней добавленной дате
    cursor.execute('''
        SELECT channel, roi, cpl, cpa
        FROM analyses
        WHERE user_id = ? AND date = (
            SELECT MAX(date) FROM analyses WHERE user_id = ?
        )
    ''', (user_id, user_id))
    
    results = cursor.fetchall()
    conn.close()
    return results    