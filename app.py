import streamlit as st
import pandas as pd
import pytz
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
from streamlit_gsheets import GSheetsConnection

# --- [0. 설정 정보] ---
SHEET_ID = "1nf0XEDSj5kc0k29pWKaCa345aUG0-3RmofWqd4bRZ9M"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"
ADMIN_PASSWORD = "plave123"
PLLI_LOGO = "https://pbs.twimg.com/profile_images/1982462665361330176/xHkk84gA.jpg"

st.set_page_config(page_title="PLAVE PLLI CONNECT", page_icon="💙🩷", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

# --- [1. 세련된 다크 네온 디자인 CSS] ---
st.markdown(f"""
    <style>
    /* 기본 배경 및 폰트 */
    .stApp {{ background-color: #0B0E14; color: #E6EDF3 !important; font-family: 'Pretendard', sans-serif; }}
    
    /* 사이드바 */
    section[data-testid="stSidebar"] {{ background-color: #12161D !important; border-right: 1px solid #30363D; }}
    section[data-testid="stSidebar"] .stRadio label {{
        background-color: transparent !important; color: #8B949E !important;
        padding: 12px 15px !important; border-radius: 10px !important; margin-bottom: 8px !important;
        transition: 0.2s; cursor: pointer;
    }}
    section[data-testid="stSidebar"] div[aria-checked="true"] label {{
        background-color: rgba(162, 210, 255, 0.1) !important;
        color: #A2D2FF !important; border: 1px solid rgba(162, 210, 255, 0.5); font-weight: 700;
    }}

    /* 메인 타이틀 */
    .main-title {{
        text-align: center; font-size: 2.5rem; font-weight: 900;
        background: linear-gradient(90deg, #A2D2FF, #FFB7D5);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 40px; filter: drop-shadow(0 0 10px rgba(162, 210, 255, 0.3));
    }}

    /* 카드 디자인 */
    .tweet-card {{
        background-color: #161B22; border: 1px solid #30363D; border-radius: 16px;
        padding: 24px; margin-bottom: 20px !important; transition: 0.3s;
    }}
    .tweet-card:hover {{ border-color: #A2D2FF; box-shadow: 0 0 15px rgba(162, 210, 255, 0.1); }}

    /* 태그 및 텍스트 */
    .category-tag {{ background: rgba(162, 210, 255, 0.15); color: #A2D2FF; padding: 3px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 600; }}
    .d-day-tag {{ float: right; color: #FF7B72; font-weight: 800; font-size: 0.9rem; }}
    .card-text {{ font-size: 1.15rem; font-weight: 600; color: #FFFFFF; margin-top: 15px; line-height: 1.6; }}

    /* 버튼 디자인 - 배경과 조화롭게 */
    div.stButton > button, .stLinkButton > a {{
        background: transparent !important; color: #A2D2FF !important;
        border: 1px solid rgba(162, 210, 255, 0.5) !important;
        border-radius: 10px !important; font-weight: 600 !important;
        transition: 0.3s !important; text-decoration: none !important;
        display: flex; justify-content: center; width: 100%;
    }}
    div.stButton > button:hover, .stLinkButton > a:hover {{
        background: rgba(162, 210, 255, 0.1) !important;
        border-color: #A2D2FF !important; transform: translateY(-2px);
    }}

    /* 입력창 및 익스팬더 */
    .stExpander {{ background-color: #161B22 !important; border: 1px solid #30363D !important; border-radius: 12px !important; }}
    input, textarea {{ background-color: #0D1117 !important; color: #FFFFFF !important; border: 1px solid #30363D !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- [2. 유틸리티 함수] ---
def auto_categorize(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=3)
        soup = BeautifulSoup(res.text, 'html.parser')
        title = soup.title.string if soup.title else ""
        url_l = str(url).lower()
        if any(k in title or k in url_l for k in ["M카", "음방", "인가", "Mcountdown"]): return "🎙️ 음악방송"
        if any(k in title or k in url_l for k in ["시상식", "Awards", "ASEA", "SMA", "MAMA"]): return "🏆 시상식"
        if any(k in title or k in url_l for k in ["생일", "Birthday", "AD", "광고"]): return "🎨 광고/시안"
        return "🗳️ 일반 투표"
    except: return "🗳️ 일반 투표"

def get_app_icon_html(url):
    safe_url = str(url).lower() if pd.notna(url) else ""
    if "x.com" in safe_url or "twitter.com" in safe_url: return "🐦 "
    icons = {"podoal": "🍇", "fanplus": "🏆", "idolchamp": "🎙️", "duckad": "🦆", "mnet": "🌟", "mubeat": "💓"}
    for key, icon in icons.items():
        if key in safe_url: return f"<span style='font-size:1.1rem; margin-right:5px;'>{icon}</span>"
    return "🔹 "

# --- [3. 사이드바 메뉴] ---
with st.sidebar:
    st.markdown(f'<img src="{PLLI_LOGO}" style="border-radius:50%; width:100px; margin: 0 auto; display:block; border: 2px solid #A2D2FF;">', unsafe_allow_html=True)
    st.markdown("<div style='text-align:center; font-weight:800; font-size:1.2rem; margin:15px 0;'>PLLI CONNECT</div>", unsafe_allow_html=True)
    menu = st.radio("MENU", ["📊 전체 보드", "🎨 광고/시안", "📻 라디오 신청", "💬 커뮤니티"], label_visibility="collapsed")

st.markdown("<h1 class='main-title'>PLLI CONNECT</h1>", unsafe_allow_html=True)

# --- [4. 메인 로직] ---
if menu in ["📊 전체 보드", "🎨 광고/시안"]:
    try:
        raw_df = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1", ttl="5m")
        today = datetime.now().date()
        raw_df['end_dt'] = pd.to_datetime(raw_df['end_date'], errors='coerce').dt.date
        active_df = raw_df[raw_df['end_dt'] >= today].copy()

        # 정보 등록 폼 (관리자 암호 확인 추가)
        with st.expander("➕ 새로운 정보 등록하기"):
            with st.form("vote_form", clear_on_submit=True):
                f_pwd = st.text_input("관리자 암호", type="password")
                f_cat = st.selectbox("분류", ["🗳️ 일반 투표", "🎙️ 음악방송", "🏆 시상식", "🎨 광고/시안", "🗓️ 스케줄"])
                f_text = st.text_area("내용 (X 링크 포함 가능)")
                f_end = st.date_input("종료 날짜")
                f_img = st.text_input("이미지 주소 (선택사항)")
                if st.form_submit_button("등록하기"):
                    if f_pwd == ADMIN_PASSWORD:
                        urls = re.findall(r'(https?://\S+)', f_text)
                        final_link = urls[0] if urls else ""
                        suggested = auto_categorize(final_link) if final_link else f_cat
                        new_row = pd.DataFrame([{
                            "category": suggested, "importance": 1, 
                            "text": f_text.split('http')[0].strip(), 
                            "end_date": f_end.strftime('%Y-%m-%d'), 
                            "link": final_link, "images": f_img
                        }])
                        conn.update(spreadsheet=SHEET_URL, worksheet="Sheet1", data=pd.concat([raw_df, new_row], ignore_index=True))
                        st.success("등록되었습니다!"); st.rerun()
                    else: st.error("암호가 틀렸습니다.")

        # 필터링
        display_df = active_df[active_df['category'].str.contains("광고|시안")].copy() if menu == "🎨 광고/시안" else active_df.copy()
        df_sorted = display_df.sort_values(by='end_dt', ascending=True)

        # 카드 출력
        cols = st.columns(2)
        for idx, row in df_sorted.reset_index().iterrows():
            with cols[idx % 2]:
                d_day = (row['end_dt'] - today).days
                d_day_txt = f"D-{d_day}" if d_day > 0 else "🔥 오늘마감"
                
                st.markdown(f"""<div class="tweet-card">
                    <div><span class="category-tag">{row['category']}</span><span class="d-day-tag">{d_day_txt}</span></div>
                    <div class="card-text">{row['text']}</div>
                </div>""", unsafe_allow_html=True)
                
                if pd.notna(row['images']) and str(row['images']).strip():
                    st.image(row['images'], use_container_width=True)
                if row['link']:
                    st.link_button(f"{get_app_icon_html(row['link'])} 자세히 보기", row['link'], use_container_width=True)
    except Exception as e: st.error(f"데이터 로드 실패: {e}")

# --- 라디오 신청 ---
elif menu == "📻 라디오 신청":
    try:
        rdf = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet2", ttl="5m")
        st.info("💡 플레이브의 노래를 라디오에 신청해 보아요!")
        for _, row in rdf.iterrows():
            st.markdown(f"""<div class="tweet-card">
                <span class="category-tag">{row['type']}</span>
                <div class="card-text">{row['name']}</div>
            </div>""", unsafe_allow_html=True)
            st.link_button("신청하러 가기", row['link'], use_container_width=True)
    except: st.info("라디오 정보를 불러올 수 없습니다.")

# --- 커뮤니티 ---
elif menu == "💬 커뮤니티":
    try:
        cdf = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet3", ttl="1m")
        with st.form("comm_form", clear_on_submit=True):
            name = st.text_input("닉네임"); msg = st.text_area("플리님들에게 한마디!")
            if st.form_submit_button("메시지 남기기"):
                new_msg = pd.DataFrame([{"date": datetime.now().strftime('%m/%d %H:%M'), "name": name, "message": msg}])
                conn.update(spreadsheet=SHEET_URL, worksheet="Sheet3", data=pd.concat([cdf, new_msg], ignore_index=True))
                st.rerun()
        for _, row in cdf.sort_index(ascending=False).iterrows():
            st.markdown(f"""<div class="tweet-card">
                <strong>{row['name']}</strong> <small style='color:#8B949E'>{row['date']}</small><br>
                <div style='margin-top:10px;'>{row['message']}</div>
            </div>""", unsafe_allow_html=True)
    except: st.info("첫 메시지를 기다리고 있어요! 💙")
