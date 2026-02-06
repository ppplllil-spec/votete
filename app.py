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

# 3. 디자인 CSS (색상 대비 개선 및 네온 효과)
st.markdown(f"""
    <style>
    /* 기본 배경 및 글자색 강제 설정 */
    .stApp {{ background-color: #0E1117; color: #FFFFFF !important; font-family: 'Pretendard', sans-serif; }}
    h1, h2, h3, h4, p, span, label, div {{ color: #FFFFFF !important; }}
    
    /* [네온 효과] 메인 로고 Glow */
    .glowing-logo {{
        border-radius: 50%;
        box-shadow: 0 0 15px #A2D2FF, 0 0 30px #FFB7D5;
        margin: 10px auto;
        display: block;
    }}

    /* [컬러 추출] 버튼 강조색 (핑크/블루 그라데이션) */
    div.stButton > button {{
        background: linear-gradient(45deg, #A2D2FF, #FFB7D5) !important;
        color: #000000 !important;
        font-weight: bold !important;
        border: none !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 15px rgba(162, 210, 255, 0.4) !important;
        transition: 0.3s !important;
        width: 100%;
    }}
    div.stButton > button:hover {{
        transform: scale(1.02) !important;
        box-shadow: 0 0 20px rgba(255, 183, 213, 0.6) !important;
    }}

    /* 입력창 디자인 */
    input, textarea, select {{
        background-color: #21262D !important;
        color: #FFFFFF !important;
        border: 1px solid #30363D !important;
    }}

    /* 투표 정보 카드 디자인 */
    .tweet-card {{ 
        background-color: #1E2330; 
        border-radius: 16px; 
        padding: 24px; 
        margin-bottom: 35px !important; 
        border-left: 6px solid #A2D2FF;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }}
    
    .category-tag {{ 
        padding: 4px 12px; border-radius: 6px; font-size: 0.85rem; font-weight: 800; color: #000000 !important; 
    }}
    
    .d-day-tag {{ 
        float: right; background-color: #FF5E57; color: white !important; padding: 4px 14px; border-radius: 50px; font-size: 0.9rem; font-weight: 800; 
    }}

    .main-title {{
        text-align: center; font-size: 2.8rem; font-weight: 800;
        background: linear-gradient(to right, #A2D2FF, #FFB7D5);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-shadow: 0 0 20px rgba(162, 210, 255, 0.4);
        margin-bottom: 40px;
    }}

    .radio-spacer {{ margin-bottom: 55px; border-bottom: 1px solid #30363D; padding-bottom: 30px; }}
    </style>
    """, unsafe_allow_html=True)

# --- [4. 유틸리티 함수] ---

# 1) 링크 자동 분류 함수 (음방/일반 분리)
def auto_categorize(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=3)
        soup = BeautifulSoup(res.text, 'html.parser')
        title = soup.title.string if soup.title else ""
        url_l = url.lower()
        
        if any(k in title or k in url_l for k in ["M카", "Mcountdown", "뮤직뱅크", "음악중심", "인기가요", "더쇼", "쇼챔"]): return "🎙️ 음악방송"
        if any(k in title or k in url_l for k in ["시상식", "Awards", "ASEA", "SMA", "MAMA", "포도알"]): return "🏆 시상식"
        if any(k in title or k in url_l for k in ["생일", "Birthday", "AD", "광고"]): return "🎂 생일/광고"
        if any(k in url_l for k in ["sbs.co.kr", "kbs.co.kr", "imbc.com", "forms"]): return "📻 라디오 신청"
        return "🗳️ 일반 투표"
    except: return "🗳️ 일반 투표"

# 2) 앱 아이콘 추출 함수 (플리 로고 기본 적용)
def get_app_icon_html(url):
    if not url: return f'<img src="{PLLI_LOGO}" style="width:24px; border-radius:50%; margin-right:8px;">'
    icons = {"podoal": "🍇", "fanplus": "🏆", "idolchamp": "🎙️", "duckad": "🦆", "mnet": "🌟", "mubeat": "💓"}
    for key, icon in icons.items():
        if key in url.lower(): return f"<span style='font-size:1.2rem; margin-right:8px;'>{icon}</span>"
    return f'<img src="{PLLI_LOGO}" style="width:24px; border-radius:50%; vertical-align:middle; margin-right:8px; box-shadow: 0 0 8px #A2D2FF;">'

# 이미지 클릭 다이얼로그
@st.dialog("이미지 크게 보기", width="large")
def show_image(img_url):
    st.image(img_url, use_container_width=True)

# --- [5. 메인 로직] ---

with st.sidebar:
    st.markdown(f'<img src="{PLLI_LOGO}" class="glowing-logo" width="120">', unsafe_allow_html=True)
    st.markdown("<div style='text-align:center; font-weight:800; margin-top:10px;'>PLLI CONNECT</div>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    menu = st.radio("MENU", ["📊 투표 보드", "📻 라디오 신청", "💡 가이드", "💬 커뮤니티"], label_visibility="collapsed")

st.markdown("<h1 class='main-title'>PLLI CONNECT</h1>", unsafe_allow_html=True)

if menu == "📊 투표 보드":
    try:
        raw_df = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1")
        if not raw_df.empty:
            today_str = datetime.now().strftime('%Y-%m-%d')
            
            # 관리자 도구
            with st.expander("🛠️ 관리자 도구 (데이터 관리)"):
                admin_pw = st.text_input("관리자 비밀번호", type="password")
                if admin_pw == ADMIN_PASSWORD:
                    edited_df = st.data_editor(raw_df, num_rows="dynamic")
                    if st.button("변경사항 저장하기 💾"):
                        conn.update(spreadsheet=SHEET_URL, worksheet="Sheet1", data=edited_df)
                        st.success("반영되었습니다!")
                        st.rerun()

            # 새로운 투표 정보 등록 (자동 분류 적용)
            with st.expander("➕ 새로운 정보 등록 (링크 자동 분류)"):
                with st.form("vote_form", clear_on_submit=True):
                    f_url = st.text_input("참여 링크")
                    f_text = st.text_area("내용 (문구)")
                    f_end = st.date_input("종료 날짜")
                    f_img = st.text_input("이미지 주소 (선택)")
                    if st.form_submit_button("등록하기 🚀"):
                        suggested = auto_categorize(f_url)
                        new_row = pd.DataFrame([{"category": suggested, "text": f_text, "end_date": f_end.strftime('%Y-%m-%d'), "link": f_url, "images": f_img}])
                        conn.update(spreadsheet=SHEET_URL, worksheet="Sheet1", data=pd.concat([raw_df, new_row], ignore_index=True))
                        st.success(f"'{suggested}' 카테고리로 등록되었습니다!")
                        st.rerun()

            # 고정 우선순위 정렬: 시상식(1) > 음악방송(2) > 생일(3) > 일반(4)
            priority_map = {"🏆 시상식": 1, "🎙️ 음악방송": 2, "🎂 생일/광고": 3, "🗳️ 일반 투표": 4, "📻 라디오 신청": 5}
            raw_df['priority'] = raw_df['category'].map(priority_map).fillna(10)
            df_sorted = raw_df.sort_values(by=['priority', 'end_date'])

            # 카드 출력
            cols = st.columns(2)
            for idx, row in df_sorted.reset_index().iterrows():
                with cols[idx % 2]:
                    icon = get_app_icon_html(row['link'])
                    # 카테고리별 포인트 컬러 (생일은 핑크, 나머지는 블루)
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
                    # 이미지 표시
                    if pd.notna(row.get('images')) and str(row['images']).strip() != "":
                        st.image(row['images'], use_container_width=True)
                        if st.button("🖼️ 이미지 크게 보기", key=f"img_{idx}"): show_image(row['images'])
    except Exception as e: st.error(f"데이터 로드 실패: {e}")

elif menu == "📻 라디오 신청":
    st.markdown("### 🕒 글로벌 신청 시간 체크")
    t1, t2 = st.columns(2)
    t1.metric("🇰🇷 서울", datetime.now(pytz.timezone('Asia/Seoul')).strftime('%m/%d %H:%M'))
    t2.metric("🇺🇸 뉴욕", datetime.now(pytz.timezone('America/New_York')).strftime('%m/%d %H:%M'), delta="-14h (시차)")
    st.divider()
    
    st.markdown('<div class="radio-spacer">', unsafe_allow_html=True)
    with st.expander("💙 KBS 쿨FM 신청 게시판"):
        st.link_button("키라더 (일요일)", "https://program.kbs.co.kr/2fm/radio/hanhaekiss/mobile/board.html")
    st.markdown('</div>', unsafe_allow_html=True)

    with st.expander("🌐 해외 라디오 실시간 요청"):
        st.link_button("🍎 NYC 주말 실시간 요청", "https://docs.google.com/forms/d/e/1FAIpQLSfyVYf-rss5jZ0uA6RHIkb-Im180whM7I_U98HLnpu3w1C4cw/viewform")
    
    st.success("### 📱 문자 신청 번호: KBS #8910 / SBS #1077 / MBC #8000")

elif menu == "💡 가이드":
    st.info("플레이브 투표 앱 가이드 정보가 업데이트될 예정입니다. 💙🩷")

elif menu == "💬 플리 커뮤니티":
    st.write("플리님들의 소중한 한마디를 남겨주세요. 💙💜🩷❤️🖤")
