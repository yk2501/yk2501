import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import pandas as pd

# 管理者パスワード（実際の運用時は環境変数などで管理）
ADMIN_PASSWORD = "admin123"
SUBJECTS = [
    "国語表現", "古典探求", "日本史探求", "政治・経済",
    "生物基礎", "化学基礎", "保険", "英語コミュニケーション",
    "その他", "復習提案"
]

# データベース初期化
def init_db():
    conn = sqlite3.connect('flashcards.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT,
            answer TEXT,
            subject TEXT,
            created_at DATETIME,
            last_reviewed DATETIME,
            next_review DATETIME,
            stage INTEGER DEFAULT 0,
            correct_count INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    return conn

# 管理者認証
def authenticate_admin():
    if 'admin' not in st.session_state:
        password = st.text_input("管理者パスワードを入力してください（一般ユーザーはそのまま進んでください）:", type="password")
        if password == ADMIN_PASSWORD:
            st.session_state.admin = True
            st.success("管理者モードでログインしました")
        elif password != "":
            st.error("パスワードが間違っています")

# メインアプリ
def main():
    st.title("📚 科目別 復習管理アプリ")
    conn = init_db()
    authenticate_admin()

    # 管理者機能
    if st.session_state.get('admin'):
        with st.expander("🗃️ カード管理（管理者用）"):
            subject = st.selectbox("科目選択", SUBJECTS[:-1])
            question = st.text_input("問題文")
            answer = st.text_input("解答")
            if st.button("カード追加"):
                conn.execute('''
                    INSERT INTO cards (question, answer, subject, created_at, next_review)
                    VALUES (?,?,?,?,?)
                ''', (question, answer, subject, datetime.now(), datetime.now()))
                st.success("カードを追加しました！")

    # 復習モード選択
    mode = st.selectbox("モード選択", SUBJECTS)

    if mode == "復習提案":
        # 忘却曲線に基づく最適な問題の選択
        query = '''
            SELECT * FROM cards 
            WHERE next_review <= ?
            ORDER BY (1.0 / (stage + 1)) * (JULIANDAY(?) - JULIANDAY(last_reviewed)) DESC
            LIMIT 10
        '''
        due_cards = conn.execute(query, (datetime.now(), datetime.now())).fetchall()
    else:
        # 通常科目モード
        due_cards = conn.execute('''
            SELECT * FROM cards 
            WHERE subject = ? AND next_review <= ?
            ORDER BY next_review ASC
        ''', (mode, datetime.now())).fetchall()

    # カード表示
    if due_cards:
        st.subheader(f"📝 {mode} の問題 ({len(due_cards)}件)")
        for card in due_cards:
            with st.container(border=True):
                cols = st.columns([4,1])
                cols[0].write(f"**{card[1]}**")
                
                if cols[1].button("解答表示", key=f"show_{card[0]}"):
                    cols[0].success(f"**解答**: {card[2]}")
                    
                    # 正誤判定ボタン
                    col1, col2 = st.columns(2)
                    if col1.button("⭕ 正解", key=f"c_{card[0]}"):
                        update_card(conn, card[0], True)
                        st.rerun()
                    if col2.button("❌ 不正解", key=f"w_{card[0]}"):
                        update_card(conn, card[0], False)
                        st.rerun()
    else:
        st.success("🎉 現在復習が必要なカードはありません")

def update_card(conn, card_id, is_correct):
    # 更新ロジック（元のコードから流用）
    # ...

if __name__ == "__main__":
    main()
