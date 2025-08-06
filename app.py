import streamlit as st
import psycopg2
import os
from PIL import Image

# --- データベース接続 ---
# st.cache_resourceは、アプリ全体で一度だけ実行されるように関数をキャッシュする
@st.cache_resource
def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        st.error("DATABASE_URLが設定されていません。Renderの環境変数を確認してください。")
        return None
    try:
        conn = psycopg2.connect(db_url)
        return conn
    except psycopg2.OperationalError as e:
        st.error(f"データベース接続エラー: {e}")
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
            cur.execute("INSERT INTO votes (item_name) VALUES ('fig01'), ('fig02'), ('fig03') ON CONFLICT (item_name) DO NOTHING;")
            conn.commit()
        # この接続はキャッシュされているので閉じない

# --- 投票データをDBから取得 ---
def fetch_votes_from_db():
    conn = get_db_connection()
    if conn:
        with conn.cursor() as cur:
            cur.execute("SELECT item_name, vote_count FROM votes ORDER BY item_name;")
            return {row[0]: row[1] for row in cur.fetchall()}
    return {'fig01': 0, 'fig02': 0, 'fig03': 0}

# --- 投票をDBに記録 ---
def add_vote_to_db(item_name):
    conn = get_db_connection()
    if conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE votes SET vote_count = vote_count + 1 WHERE item_name = %s;", (item_name,))
            conn.commit()

# --- Streamlit アプリケーション ---
st.set_page_config(layout="wide")
st.title("人気投票サイト")

# --- 初期化 ---
init_db()

# --- Session Stateの初期化 ---
# st.session_stateに'votes'がなければ、DBから読み込んで初期化
if 'votes' not in st.session_state:
    st.session_state.votes = fetch_votes_from_db()

# --- 投票ボタンが押されたときのコールバック関数 ---
def handle_vote(item_name):
    # まずDBを更新
    add_vote_to_db(item_name)
    # 次にSession Stateを更新
    st.session_state.votes[item_name] += 1

# --- 画面レイアウト ---
col1, col2, col3 = st.columns(3)
image_files = {'fig01': "fig01.jpg", 'fig02': "fig02.jpg", 'fig03': "fig03.jpg"}
cols = {'fig01': col1, 'fig02': col2, 'fig03': col3}

for i, (item_name, image_file) in enumerate(image_files.items()):
    with cols[item_name]:
        st.header(f"候補{i+1}")
        try:
            image = Image.open(image_file)
            st.image(image, use_container_width=True)
        except FileNotFoundError:
            st.error(f"{image_file} が見つかりません。")
        
        # ボタンが押されたらhandle_voteを呼び出す
        st.button("投票する", key=f"btn_{item_name}", on_click=handle_vote, args=(item_name,))

st.divider()

# --- 投票結果の表示 (Session Stateから) ---
st.header("現在の投票結果")

# Session Stateから票数を取得
votes = st.session_state.votes
total_votes = sum(votes.values())

for item, count in votes.items():
    percentage = (count / total_votes * 100) if total_votes > 0 else 0
    st.write(f"**{item}:** {count} 票 ({percentage:.1f}%)")
    st.progress(percentage / 100)