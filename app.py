import streamlit as st
import psycopg2
import os
from PIL import Image

# --- アイテム設定 ---
ITEM_CONFIG = {
    'fig01': {'display_name': '01', 'image': 'fig01.jpg'},
    'fig02': {'display_name': '02', 'image': 'fig02.jpg'},
    'fig03': {'display_name': '03', 'image': 'fig03.jpg'},
    'fig04': {'display_name': '04', 'image': 'fig04.jpg'},
    'fig05': {'display_name': '05', 'image': 'fig05.jpg'},
}
ITEM_NAMES = list(ITEM_CONFIG.keys())

# --- データベース接続 ---
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
            args_str = ', '.join(cur.mogrify("(%s)", (name,)).decode('utf-8') for name in ITEM_NAMES)
            if args_str:
                cur.execute(f"INSERT INTO votes (item_name) VALUES {args_str} ON CONFLICT (item_name) DO NOTHING;")
            conn.commit()

# --- 投票データをDBから取得 ---
def fetch_votes_from_db():
    conn = get_db_connection()
    if conn:
        with conn.cursor() as cur:
            cur.execute("SELECT item_name, vote_count FROM votes;")
            db_votes = {row[0]: row[1] for row in cur.fetchall()}
            return {name: db_votes.get(name, 0) for name in ITEM_NAMES}
    return {name: 0 for name in ITEM_NAMES}

# --- 投票をDBに記録 ---
def add_vote_to_db(item_name):
    conn = get_db_connection()
    if conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE votes SET vote_count = vote_count + 1 WHERE item_name = %s;", (item_name,))
            conn.commit()

# --- Streamlit アプリケーション ---
st.set_page_config(layout="wide")

# タイトルを中央寄せ
st.markdown("<h1 style='text-align: center;'>人気投票サイト</h1>", unsafe_allow_html=True)

# --- 初期化 ---
init_db()

# --- Session Stateの初期化 ---
if 'votes' not in st.session_state:
    st.session_state.votes = fetch_votes_from_db()

# --- 投票ボタンのコールバック ---
def handle_vote(item_name):
    add_vote_to_db(item_name)
    st.session_state.votes[item_name] += 1

# --- 画面レイアウト ---
cols = st.columns(len(ITEM_NAMES))

# ボタンを中央寄せするためのCSSハック
st.markdown("""
<style>
div.stButton > button {
    display: block;
    margin: 0 auto;
}
</style>
""", unsafe_allow_html=True)

for i, (item_name, config) in enumerate(ITEM_CONFIG.items()):
    with cols[i]:
        st.header(config['display_name'])
        try:
            image = Image.open(config['image'])
            st.image(image, use_container_width=True)
        except FileNotFoundError:
            st.error(f"{config['image']} が見つかりません。")
        
        st.button("投票する", key=f"btn_{item_name}", on_click=handle_vote, args=(item_name,))

st.divider()

# --- 投票結果の表示 ---
st.header("現在の投票結果")

votes = st.session_state.votes
total_votes = sum(votes.values())

for item_name, config in ITEM_CONFIG.items():
    count = votes.get(item_name, 0)
    display_name = config['display_name']
    percentage = (count / total_votes * 100) if total_votes > 0 else 0
    st.write(f"**{display_name}:** {count} 票 ({percentage:.1f}%)")
    st.progress(percentage / 100)