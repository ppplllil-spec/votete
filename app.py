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

# 1. 페이지 설정
st.set_page_config(page_title="PLAVE PLLI CONNECT", page_icon="💙🩷", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. 디자인 CSS (가독성 최적화 & 네온 효과)
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E1117; color: #FFFFFF !important; font-family: 'Pretendard', sans-serif; }}
    
    /* 사이드바 다크 모드 및 가독성 고정 */
    section[data-testid="stSidebar"] {{ background-color: #161B22 !important; border-right: 1px solid #30363D; }}
    section[data-testid="stSidebar"] .stRadio label {{
        background-color: #21262D !important; color: #FFFFFF !important;
        padding: 15px 20px !important; border-radius: 12px !important;
        margin-bottom: 12px !important; border: 1px solid #30363D; font-weight: 600;
    }}
    section[data-testid="stSidebar"] div[aria-checked="true"] label {{ background-color: #A2D2FF !important; color: #000000 !important; }}
    
    /* 로고 네온 효과 */
    .glowing-logo {{ border-radius: 50%; box-shadow: 0 0 20px #A2D2FF, 0 0 40px #FFB7D5; margin: 20px auto; display: block; border: 2px solid rgba(162, 210, 255, 0.3); }}
    
    /* 버튼 가독성 (핑크/블루 그라데이션) */
    div.stButton > button, .stLinkButton > a {{
        background: linear-gradient(45deg, #A2D2FF, #FFB7D5) !important;
        color: #161B22 !important; font-weight: 800 !important; border: none !important; 
        border-radius: 10px !important; box-shadow: 0 4px 15px rgba(162, 210, 255, 0.3) !important;
        text-decoration: none !important; width: 100%;
    }}
    
    .tweet-card {{ background-color: #1E2330; border-radius: 16px; padding: 24px; margin-bottom: 25px !important; border-left: 6px solid #A2D2FF; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }}
    .category-tag {{ padding: 4px 12px; border-radius: 6px; font-size: 0.85rem; font-weight: 800; color: #000000 !important; }}
    .d-day-tag {{ float: right; background-color: #FF5E57; color: white !important; padding: 4px 14px; border-radius: 50px; font-size: 0.9rem; font-weight: 800; }}
    .main-title {{ text-align: center; font-size: 2.8rem; font-weight: 800; background: linear-gradient(to right, #A2D2FF, #FFB7D5); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-shadow: 0 0 20px rgba(162, 210, 255, 0.4); margin-bottom: 30px; }}
    </style>
    """, unsafe_allow_html=True)

# --- [3. 유틸리티 함수] ---
def auto_categorize(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=3)
        soup = BeautifulSoup(res.text, 'html.parser')
        title = soup.title.string if soup.title else ""
        url_l = str(url).lower()
        if any(k in title or k in url_l for k in ["M카", "음방", "인가", "Mcountdown"]): return "🎙️ 음악방송"
        if any(k in title or k in url_l for k in ["시상식", "Awards", "ASEA", "SMA", "MAMA"]): return "🏆 시상식"
        if any(k in title or k in url_l for k in ["생일", "Birthday", "AD", "광고"]): return "🎂 생일/광고"
        return "🗳️ 일반 투표"
    except: return "🗳️ 일반 투표"

def get_app_icon_html(url):
    safe_url = str(url).lower() if pd.notna(url) else ""
    if not safe_url or safe_url == "nan": return f'<img src="{PLLI_LOGO}" style="width:24px; border-radius:50%; margin-right:8px;">'
    if "x.com" in safe_url or "twitter.com" in safe_url: return "🐦 "
    icons = {"podoal": "🍇", "fanplus": "🏆", "idolchamp": "🎙️", "duckad": "🦆", "mnet": "🌟", "mubeat": "💓"}
    for key, icon in icons.items():
        if key in safe_url: return f"<span style='font-size:1.2rem; margin-right:8px;'>{icon}</span>"
    return f'<img src="{PLLI_LOGO}" style="width:24px; border-radius:50%; vertical-align:middle; margin-right:8px; box-shadow: 0 0 8px #A2D2FF;">'
    # --- [파트 2 시작] ---

with st.sidebar:
    st.markdown(f'<img src="{PLLI_LOGO}" class="glowing-logo" width="120">', unsafe_allow_html=True)
    st.markdown("<div style='text-align:center; font-weight:800; font-size:1.2rem; margin-top:10px;'>PLLI CONNECT</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    menu = st.radio("MENU", ["📊 전체 보드", "🎨 광고/시안", "📍 광고 맵", "📻 라디오 신청", "💬 커뮤니티"], label_visibility="collapsed")

st.markdown("<h1 class='main-title'>PLLI CONNECT</h1>", unsafe_allow_html=True)

# --- 1. 투표 및 광고 보드 로직 ---
if menu in ["📊 전체 보드", "🎨 광고/시안"]:
    try:
        raw_df = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1")
        today = datetime.now().date()
        raw_df['end_dt'] = pd.to_datetime(raw_df['end_date'], errors='coerce').dt.date
        
        # [자동 필터링] 종료된 일정 숨기기
        active_df = raw_df[raw_df['end_dt'] >= today].copy()

        # [오늘 마감 알림]
        deadline_today = active_df[active_df['end_dt'] == today]
        if not deadline_today.empty:
            st.warning(f"⚠️ **오늘 마감 일정 {len(deadline_today)}건!** 화력을 집중해 주세요! 💙")

        # [정보 등록 폼]
        with st.expander("➕ 정보 등록 (X 링크 및 내용 자동 분석)"):
            with st.form("vote_form", clear_on_submit=True):
                f_cat = st.selectbox("분류", ["🗳️ 일반 투표", "🎙️ 음악방송", "🏆 시상식", "🎨 광고/시안", "🗓️ 스케줄"])
                f_text = st.text_area("내용 (X 링크를 포함해서 적어도 인식됩니다)")
                f_end = st.date_input("종료 날짜")
                f_img = st.text_input("이미지 주소 (선택사항)")
                if st.form_submit_button("등록하기 🚀"):
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
                    st.balloons(); st.rerun()

        # [메뉴별 필터링 및 정렬]
        display_df = active_df[active_df['category'].str.contains("광고|시안")].copy() if menu == "🎨 광고/시안" else active_df.copy()
        priority_map = {"🏆 시상식": 1, "🎙️ 음악방송": 2, "🎨 광고/시안": 3, "🗳️ 일반 투표": 4}
        display_df['priority'] = display_df['category'].map(priority_map).fillna(10)
        df_sorted = display_df.sort_values(by=['priority', 'end_dt'], ascending=[True, True])

        # [카드 출력]
        cols = st.columns(2)
        for idx, row in df_sorted.reset_index().iterrows():
            with cols[idx % 2]:
                icon = get_app_icon_html(row['link'])
                b_color = "#FFEAA7" if "광고" in str(row['category']) else "#A2D2FF"
                d_day = f"D-{(row['end_dt'] - today).days}" if (row['end_dt'] - today).days > 0 else "🔥 오늘마감"
                
                st.markdown(f"""<div class="tweet-card" style="border-left-color:{b_color};">
                    <div style="margin-bottom: 12px;">{icon} <span class="category-tag" style="background-color:{b_color};">{row['category']}</span><span class="d-day-tag">{d_day}</span></div>
                    <div style="font-size:1.1rem; font-weight:700; color:white;">{row['text']}</div>
                </div>""", unsafe_allow_html=True)
                
                if pd.notna(row['images']) and str(row['images']).strip(): st.image(row['images'], use_container_width=True)
                if row['link']: st.link_button("🔗 상세 내용/X(트위터) 보기", row['link'], use_container_width=True)
                
                # [스마트 맵 버튼]
                if any(k in str(row['text']) for k in ["역", "카페", "빌딩", "광고판"]):
                    st.link_button("📍 광고 위치 지도보기", f"https://www.google.com/maps/search/{row['text']}", use_container_width=True)
    except: st.error("데이터 로드 실패")

# --- 2. 광고 맵 성지 메뉴 ---
elif menu == "📍 광고 맵":
    st.subheader("📍 플레이브 광고 성지 (클릭 시 구글 지도)")
    m_cols = st.columns(2)
    hot_spots = {"홍대입구역": "홍대입구역", "삼성역 코엑스": "삼성역 코엑스", "강남역": "강남역", "건대입구역": "건대입구역"}
    for i, (name, query) in enumerate(hot_spots.items()):
        with m_cols[i % 2]: st.link_button(f"🗺️ {name} 주변 광고 확인", f"https://www.google.com/maps/search/{query}+광고", use_container_width=True)

# --- 3. 라디오 신청 (Sheet2 연동) ---
elif menu == "📻 라디오 신청":
    try:
        rdf = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet2")
        t1, t2 = st.columns(2)
        t1.metric("🇰🇷 서울", datetime.now(pytz.timezone('Asia/Seoul')).strftime('%m/%d %H:%M'))
        t2.metric("🇺🇸 뉴욕", datetime.now(pytz.timezone('America/New_York')).strftime('%m/%d %H:%M'), delta="-14h")
        st.divider()
        for _, row in rdf.iterrows():
            st.markdown(f"""<div class="tweet-card" style="border-left-color: #A2D2FF; padding: 15px 20px;">
                <span style="font-size:0.75rem; background:#3E4556; padding:2px 8px; border-radius:4px;">{row['type']}</span>
                <div style="font-size:1.1rem; font-weight:700; margin-top:5px;">{row['name']}</div>
            </div>""", unsafe_allow_html=True)
            st.link_button(f"👉 {row['name']} 신청하기", row['link'], use_container_width=True)
    except: st.info("라디오 정보(Sheet2)를 입력해주세요!")

# --- 4. 커뮤니티 (Sheet3 연동) ---
elif menu == "💬 플리 커뮤니티":
    try:
        cdf = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet3")
        with st.form("comm_form", clear_on_submit=True):
            name = st.text_input("닉네임"); msg = st.text_area("플리님들에게 한마디! 💙")
            if st.form_submit_button("메시지 남기기"):
                new_msg = pd.DataFrame([{"date": datetime.now().strftime('%m/%d %H:%M'), "name": name, "message": msg}])
                conn.update(spreadsheet=SHEET_URL, worksheet="Sheet3", data=pd.concat([cdf, new_msg], ignore_index=True))
                st.rerun()
        for _, row in cdf.sort_index(ascending=False).iterrows():
            st.markdown(f"**{row['name']}** <small>({row['date']})</small>\n\n{row['message']}\n\n---")
    except: st.info("커뮤니티(Sheet3)의 첫 메시지를 기다립니다! 💙💜🩷❤️🖤")

