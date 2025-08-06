
import streamlit as st
import psycopg2
import os
from PIL import Image

# --- データベース接続 (Renderデプロイ後に設定) ---
def get_db_connection():
    # Renderの環境変数からデータベースURLを取得
    # ローカルテスト用に、一時的なダミー値を設定
    db_url = os.environ.get("DATABASE_URL", "postgresql://user:password@host:port/database")
    try:
        conn = psycopg2.connect(db_url)
        return conn
    except psycopg2.OperationalError as e:
        st.error(f"データベースに接続できませんでした: {e}")
        st.info("Renderでデータベースをセットアップし、DATABASE_URL環境変数を設定してください。")
        return None

# --- テーブル初期化 ---
def init_db():
    conn = get_db_connection()
    if conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS votes (
                    id SERIAL PRIMARY KEY,
                    item_name VARCHAR(50) UNIQUE NOT NULL,
                    vote_count INTEGER DEFAULT 0
                );
            """)
            # 初期データの挿入 (存在しない場合のみ)
            cur.execute("INSERT INTO votes (item_name) VALUES ('fig01'), ('fig02'), ('fig03') ON CONFLICT (item_name) DO NOTHING;")
            conn.commit()
        conn.close()

# --- 投票データを取得 ---
def get_votes():
    conn = get_db_connection()
    if conn:
        with conn.cursor() as cur:
            cur.execute("SELECT item_name, vote_count FROM votes ORDER BY item_name;")
            votes = {row[0]: row[1] for row in cur.fetchall()}
            conn.close()
            return votes
    return {'fig01': 0, 'fig02': 0, 'fig03': 0} # DB接続失敗時のデフォルト値

# --- 投票を記録 ---
def add_vote(item_name):
    conn = get_db_connection()
    if conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE votes SET vote_count = vote_count + 1 WHERE item_name = %s;", (item_name,))
            conn.commit()
        conn.close()

# --- Streamlit アプリケーション --- 
st.set_page_config(layout="wide")
st.title("人気投票サイト")

# --- 初期化 ---
# アプリの初回起動時にデータベースを初期化
# (ローカルでは毎回実行されるが、Streamlitのセッション管理により問題ない)
# Render上ではデプロイ時に一度実行されるイメージ
init_db()

# --- 投票データの取得 ---
votes = get_votes()
total_votes = sum(votes.values())

# --- 画面レイアウト ---
col1, col2, col3 = st.columns(3)

with col1:
    st.header("候補1")
    try:
        img1 = Image.open("fig01.jpg")
        st.image(img1, use_column_width=True)
    except FileNotFoundError:
        st.error("fig01.jpg が見つかりません。")

    if st.button("投票する", key="btn1"):
        add_vote("fig01")
        st.rerun() # 画面を再読み込みして結果を即時反映

with col2:
    st.header("候補2")
    try:
        img2 = Image.open("fig02.jpg")
        st.image(img2, use_column_width=True)
    except FileNotFoundError:
        st.error("fig02.jpg が見つかりません。")

    if st.button("投票する", key="btn2"):
        add_vote("fig02")
        st.rerun()

with col3:
    st.header("候補3")
    try:
        img3 = Image.open("fig03.jpg")
        st.image(img3, use_column_width=True)
    except FileNotFoundError:
        st.error("fig03.jpg が見つかりません。")

    if st.button("投票する", key="btn3"):
        add_vote("fig03")
        st.rerun()

st.divider()

# --- 投票結果の表示 ---
st.header("現在の投票結果")

for item, count in votes.items():
    # ゼロ除算を避ける
    percentage = (count / total_votes * 100) if total_votes > 0 else 0
    st.write(f"**{item}:** {count} 票 ({percentage:.1f}%)")
    st.progress(percentage / 100)
