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

# 2. 구글 시트 연결
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. 디자인 CSS
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E1117; color: #FFFFFF !important; font-family: 'Pretendard', sans-serif; }}
    h1, h2, h3, h4, p, span, label, div {{ color: #FFFFFF !important; }}
    
    /* 네온 로고 */
    .glowing-logo {{
        border-radius: 50%;
        box-shadow: 0 0 20px #A2D2FF, 0 0 40px #FFB7D5;
        margin: 10px auto; display: block;
        border: 2px solid rgba(162, 210, 255, 0.3);
    }}

    /* 버튼 가독성 */
    div.stButton > button {{
        background: linear-gradient(45deg, #A2D2FF, #FFB7D5) !important;
        color: #161B22 !important; font-weight: bold !important;
        border: none !important; border-radius: 10px !important;
        box-shadow: 0 4px 15px rgba(162, 210, 255, 0.4) !important;
        transition: 0.3s !important; width: 100%;
    }}

    /* 카드 디자인 */
    .tweet-card {{ 
        background-color: #1E2330; border-radius: 16px; padding: 24px; 
        margin-bottom: 25px !important; border-left: 6px solid #A2D2FF;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }}
    
    .category-tag {{ padding: 4px 12px; border-radius: 6px; font-size: 0.85rem; font-weight: 800; color: #000000 !important; }}
    .d-day-tag {{ float: right; background-color: #FF5E57; color: white !important; padding: 4px 14px; border-radius: 50px; font-size: 0.9rem; font-weight: 800; }}
    .main-title {{
        text-align: center; font-size: 2.8rem; font-weight: 800;
        background: linear-gradient(to right, #A2D2FF, #FFB7D5);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-shadow: 0 0 20px rgba(162, 210, 255, 0.4); margin-bottom: 30px;
    }}
    /* 라디오 그리드용 */
    .radio-card {{
        background-color: #252A34; border-radius: 12px; padding: 15px;
        border: 1px solid #3E4556; margin-bottom: 15px;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- [4. 유틸리티 함수] ---

def auto_categorize(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=3)
        soup = BeautifulSoup(res.text, 'html.parser')
        title = soup.title.string if soup.title else ""
        url_l = url.lower()
        if any(k in title or k in url_l for k in ["M카", "Mcountdown", "뮤직뱅크", "음방", "인가", "인기가요"]): return "🎙️ 음악방송"
        if any(k in title or k in url_l for k in ["시상식", "Awards", "ASEA", "SMA", "MAMA"]): return "🏆 시상식"
        if any(k in title or k in url_l for k in ["생일", "Birthday", "AD", "광고"]): return "🎂 생일/광고"
        return "🗳️ 일반 투표"
    except: return "🗳️ 일반 투표"

def get_app_icon_html(url):
    safe_url = str(url).lower() if pd.notna(url) else ""
    if not safe_url or safe_url == "nan":
        return f'<img src="{PLLI_LOGO}" style="width:24px; border-radius:50%; margin-right:8px;">'
    icons = {"podoal": "🍇", "fanplus": "🏆", "idolchamp": "🎙️", "duckad": "🦆", "mnet": "🌟"}
    for key, icon in icons.items():
        if key in safe_url: return f"<span style='font-size:1.2rem; margin-right:8px;'>{icon}</span>"
    return f'<img src="{PLLI_LOGO}" style="width:24px; border-radius:50%; vertical-align:middle; margin-right:8px; box-shadow: 0 0 8px #A2D2FF;">'

# --- [5. 메인 로직] ---

with st.sidebar:
    st.markdown(f'<img src="{PLLI_LOGO}" class="glowing-logo" width="120">', unsafe_allow_html=True)
    st.markdown("<div style='text-align:center; font-weight:800; margin-top:10px;'>PLLI CONNECT</div>", unsafe_allow_html=True)
    menu = st.radio("MENU", ["📊 투표 보드", "📻 라디오 신청"], label_visibility="collapsed")

st.markdown("<h1 class='main-title'>PLLI CONNECT</h1>", unsafe_allow_html=True)

if menu == "📊 투표 보드":
    try:
        raw_df = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1")
        
        # [기능 2] 오늘 마감 투표 알림
        today_str = datetime.now().strftime('%Y-%m-%d')
        deadline_today = raw_df[raw_df['end_date'] == today_str]
        if not deadline_today.empty:
            st.warning(f"⚠️ **오늘 마감되는 투표가 {len(deadline_today)}건 있습니다!** 서둘러 참여해 주세요! 💙")

        with st.expander("➕ 새로운 정보 등록"):
            with st.form("vote_form", clear_on_submit=True):
                f_url_input = st.text_input("참여 링크 (생략 가능)")
                f_text = st.text_area("내용 (링크 포함 가능)")
                f_end = st.date_input("종료 날짜")
                if st.form_submit_button("등록하기 🚀"):
                    final_url = f_url_input if f_url_input else ""
                    if not final_url:
                        urls = re.findall(r'(https?://\S+)', f_text)
                        final_url = urls[0] if urls else ""
                    suggested = auto_categorize(final_url)
                    clean_text = f_text.split('http')[0].strip()
                    new_row = pd.DataFrame([{"category": suggested, "text": clean_text if clean_text else f_text, "end_date": f_end.strftime('%Y-%m-%d'), "link": final_url}])
                    conn.update(spreadsheet=SHEET_URL, worksheet="Sheet1", data=pd.concat([raw_df, new_row], ignore_index=True))
                    st.balloons()
                    st.rerun()

        priority_map = {"🏆 시상식": 1, "🎙️ 음악방송": 2, "🎂 생일/광고": 3, "🗳️ 일반 투표": 4}
        raw_df['priority'] = raw_df['category'].map(priority_map).fillna(10)
        df_sorted = raw_df.sort_values(by=['priority', 'end_date'])

        cols = st.columns(2)
        for idx, row in df_sorted.reset_index().iterrows():
            with cols[idx % 2]:
                icon = get_app_icon_html(row['link'])
                b_color = "#FFB7D5" if row['category'] == "🎂 생일/광고" else "#A2D2FF"
                
                # D-Day 계산
                try:
                    target = datetime.strptime(str(row['end_date']), '%Y-%m-%d').date()
                    days_left = (target - datetime.now().date()).days
                    d_day_str = f"D-{days_left}" if days_left >= 0 else "종료"
                except: d_day_str = "상시"

                st.markdown(f"""
                    <div class="tweet-card" style="border-left-color:{b_color};">
                        <div style="margin-bottom: 15px;">
                            {icon} <span class="category-tag" style="background-color:{b_color};">{row['category']}</span>
                            <span class="d-day-tag">{d_day_str}</span>
                        </div>
                        <div style="font-size:1.1rem; font-weight:700;">{row['text']}</div>
                        <a href="{row['link']}" target="_blank" style="text-decoration:none;">
                            <div style="margin-top:15px; color:#A2D2FF; font-size:0.9rem; font-weight:bold;">🔗 참여 링크 바로가기</div>
                        </a>
                    </div>
                """, unsafe_allow_html=True)
    except Exception as e: st.error(f"데이터 로드 실패: {e}")

elif menu == "📻 라디오 신청":
    st.markdown("### 🕒 실시간 신청 시간")
    t1, t2 = st.columns(2)
    t1.metric("🇰🇷 서울", datetime.now(pytz.timezone('Asia/Seoul')).strftime('%m/%d %H:%M'))
    t2.metric("🇺🇸 뉴욕", datetime.now(pytz.timezone('America/New_York')).strftime('%m/%d %H:%M'), delta="-14h")
    
    st.divider()
    
    # [한눈에 확인하는 라디오 카드 섹션]
    r_cols = st.columns(2)
    with r_cols[0]:
        st.markdown('<div class="radio-card"><h4>KBS 쿨FM</h4><p>#8910 (유료 50원)</p></div>', unsafe_allow_html=True)
        st.link_button("💋 키라더 (일요일 신청)", "https://program.kbs.co.kr/2fm/radio/hanhaekiss/mobile/board.html")
        st.link_button("☀️ 이은지의 가요광장", "https://program.kbs.co.kr/2fm/radio/ejgayo/mobile/board.html")
        
        st.markdown('<br><div class="radio-card"><h4>SBS 파워FM</h4><p>#1077 (유료 50원)</p></div>', unsafe_allow_html=True)
        st.link_button("🎙️ 두시탈출 컬투쇼", "https://m.programs.sbs.co.kr/radio/cultwoshow/boards/58047")
    
    with r_cols[1]:
        st.markdown('<div class="radio-card"><h4>해외 라디오</h4><p>NYC & Global Request</p></div>', unsafe_allow_html=True)
        st.link_button("🍎 NYC 주말 실시간 요청", "https://docs.google.com/forms/d/e/1FAIpQLSfyVYf-rss5jZ0uA6RHIkb-Im180whM7I_U98HLnpu3w1C4cw/viewform")
        st.link_button("📻 WYYT 106.3 Request", "http://wyyt1063.com/request")
        
        st.info("💡 **영문 문구:** `I would like to request [Song Title] by PLAVE`")

    st.success("📱 **문자 신청 번호 모음**: KBS #8910 / SBS #1077 / MBC #8000")
