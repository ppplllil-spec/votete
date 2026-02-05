import streamlit as st
import pandas as pd
from datetime import datetime
import re
from urllib.parse import urlparse
from streamlit_gsheets import GSheetsConnection
import streamlit.components.v1 as components

# --- [0. 설정 정보] ---
SHEET_ID = "1nf0XEDSj5kc0k29pWKaCa345aUG0-3RmofWqd4bRZ9M"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"

# 1. 페이지 설정
st.set_page_config(page_title="PLAVE PLLI 투표정보", page_icon="💙💜🩷❤️🖤", layout="wide")

# 2. 구글 시트 연결
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. 디자인 CSS
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; font-family: 'Pretendard', sans-serif; }
    section[data-testid="stSidebar"] { background-color: #161B22 !important; border-right: 1px solid #30363D; }
    div[data-testid="stSidebarUserContent"] label { background-color: #21262D; border-radius: 12px !important; color: #C9D1D9 !important; padding: 15px 20px !important; }
    div[data-testid="stSidebarUserContent"] div[aria-checked="true"] label { background-color: #A29BFE !important; color: #000000 !important; font-weight: bold !important; }
    .main-title { color: #FFFFFF; text-shadow: 0px 0px 15px rgba(162, 155, 254, 0.6); text-align: center; font-size: 2.5rem; font-weight: 800; margin-bottom: 30px; }
    .tweet-card { background-color: #1E2330; border-radius: 16px; padding: 24px; margin-bottom: 24px; border-left: 5px solid #3E4556; transition: transform 0.2s; }
    .category-tag { padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 700; }
    .importance-tag { background-color: #FFEAA7; color: #000000; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 700; margin-left: 5px; }
    .d-day-tag { float: right; background-color: #FF5E57; color: white; padding: 4px 14px; border-radius: 50px; font-size: 0.9rem; font-weight: 800; }
    .radio-box { background-color: #2D3436; padding: 20px; border-radius: 16px; border-left: 5px solid #FFEAA7; margin-bottom: 25px; }
    </style>
    """, unsafe_allow_html=True)

# 이미지 클릭 시 크게 보기 (다이얼로그)
@st.dialog("이미지 크게 보기", width="large")
def show_image(img_url):
    st.image(img_url, use_container_width=True)

# 4. 데이터 처리 함수
def process_data(df):
    processed_rows = []
    for _, row in df.iterrows():
        raw_text = str(row['text']) if pd.notna(row['text']) else ""
        m_color = "#3E4556"
        if any(k in raw_text for k in ["노아", "NOAH", "💜"]): m_color = "#C294FB"
        elif any(k in raw_text for k in ["하민", "HAMIN", "🖤", "💚"]): m_color = "#B2EBC1"
        elif any(k in raw_text for k in ["예준", "YEJUN", "💙"]): m_color = "#A2D2FF"
        elif any(k in raw_text for k in ["밤비", "BAMBY", "🩷"]): m_color = "#FFB7D5"
        elif any(k in raw_text for k in ["은호", "EUNHO", "❤️"]): m_color = "#FF8E8E"

        found_links = re.findall(r'(https?://\S+)', raw_text)
        final_link = row['link'] if pd.notna(row['link']) and str(row['link']).strip() != "" else (found_links[0] if found_links else None)
        
        def get_dday(date_str):
            try:
                if pd.isna(date_str) or str(date_str).strip() == "": return "상시", 999, False
                end_date = datetime.strptime(str(date_str).strip(), '%Y-%m-%d').date()
                delta = (end_date - datetime.now().date()).days
                return (f"D-{delta}", delta, False) if delta >= 0 else ("종료", delta, True)
            except: return "정보없음", 999, False

        d_label, d_val, is_exp = get_dday(row['end_date'])
        processed_rows.append({
            'category': row['category'] if pd.notna(row['category']) else "🗳️ 일반",
            'importance': row['importance'] if pd.notna(row['importance']) else 1,
            'text': raw_text.split('http')[0].strip(),
            'start_date': row['start_date'], 'end_date': row['end_date'],
            'link': final_link, 'images': row['images'],
            'd_day_label': d_label, 'd_day_val': d_val, 'is_expired': is_exp, 'color': m_color
        })
    return pd.DataFrame(processed_rows)

# 5. 사이드바 메뉴
with st.sidebar:
    st.markdown("<h2 style='text-align:center; color:#A29BFE;'>PLLI CONNECT</h2>", unsafe_allow_html=True)
    menu = st.radio("메뉴 이동", ["📊 투표/광고 보드", "📻 라디오 상시 신청", "💡 투표 팁 & 가이드", "💬 플리 커뮤니티"], label_visibility="collapsed")

st.markdown(f"<h1 class='main-title'>💙💜🩷❤️🖤 PLAVE PLLI 투표정보</h1>", unsafe_allow_html=True)

# --- [메뉴 1: 투표/광고 보드] ---
if menu == "📊 투표/광고 보드":
    try:
        raw_df = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1")
        if not raw_df.empty:
            df = process_data(raw_df)
            
            # 🔥 오늘 마감 요약 알림창
            today_str = datetime.now().strftime('%Y-%m-%d')
            today_deadlines = df[df['end_date'] == today_str]
            if not today_deadlines.empty:
                st.error(f"⚠️ **오늘 마감!** ({len(today_deadlines)}건): {', '.join(today_deadlines['text'].str[:10] + '...')}")

            # 투표 등록 폼
            with st.expander("➕ 새로운 투표 정보 등록하기"):
                with st.form("vote_form", clear_on_submit=True):
                    f_cat = st.selectbox("분류", ["🗳️ 일반/음방", "🏆 시상식", "🎂 생일", "🎨 광고시안"])
                    f_text = st.text_area("내용 (문구나 링크)")
                    f_end = st.date_input("종료 날짜")
                    f_img = st.text_input("이미지 주소")
                    if st.form_submit_button("등록하기 💙"):
                        new_data = pd.DataFrame([{"category": f_cat, "importance": 1, "text": f_text, "start_date": today_str, "end_date": f_end.strftime('%Y-%m-%d'), "images": f_img}])
                        conn.update(spreadsheet=SHEET_URL, worksheet="Sheet1", data=pd.concat([raw_df, new_data], ignore_index=True))
                        st.success("등록되었습니다! 새로고침 해주세요.")

            # 보드 출력
            cols = st.columns(2)
            for idx, row in df.sort_values(by=['is_expired', 'd_day_val']).reset_index().iterrows():
                with cols[idx % 2]:
                    st.markdown(f"""<div class="tweet-card" style="border-left-color:{row['color']};">
                        <span class="category-tag" style="background-color:{row['color']}; color:#000;">{row['category']}</span>
                        <span class="d-day-tag">{row['d_day_label']}</span>
                        <div style="margin-top:10px; font-weight:bold; font-size:1.1rem;">{row['text']}</div>
                    </div>""", unsafe_allow_html=True)
                    if pd.notna(row['images']) and str(row['images']).strip() != "":
                        st.image(row['images'], use_container_width=True)
                        if st.button("🖼️ 이미지 크게 보기", key=f"img_{idx}"): show_image(row['images'])
                    if row['link']: st.link_button("🔗 참여 링크 이동", row['link'], use_container_width=True)
    except Exception as e: st.error(f"데이터 로드 실패: {e}")

# --- [메뉴 2: 라디오 상시 신청] ---
elif menu == "📻 라디오 상시 신청":
    st.markdown('<div class="radio-box"><h2>📻 라디오 신청 가이드</h2><p>국내외 라디오에 플레이브의 음악을 들려주세요! 💙</p></div>', unsafe_allow_html=True)
    
    day_tabs = st.tabs(["🇰🇷 KBS 쿨FM", "🇸🇰 SBS 파워FM", "🌐 해외 라디오", "📱 문자 번호"])
    
    with day_tabs[0]:
        st.markdown("### 💙 KBS 쿨FM (2FM) 상세 신청")
        k_cols = st.columns(2)
        with k_cols[0]:
            st.link_button("💋 키라더 (일요일)", "https://program.kbs.co.kr/2fm/radio/hanhaekiss/mobile/board.html?smenu=ba2c4f&bbs_loc=R2025-0082-03-761603,list,none,1,0", use_container_width=True)
            st.link_button("🎮 놀초대 [화/목]", "https://program.kbs.co.kr/2fm/radio/hanhaekiss/mobile/board.html?smenu=66d014&bbs_loc=R2025-0082-03-789244,list,none,1,0", use_container_width=True)
        with k_cols[1]:
            st.link_button("🎧 볼륨을 높여요 (금/토/일)", "https://program.kbs.co.kr/2fm/radio/hyojung_volume/mobile/board.html", use_container_width=True)
            st.link_button("☀️ 이은지의 가요광장", "https://program.kbs.co.kr/2fm/radio/ejgayo/mobile/board.html", use_container_width=True)

    with day_tabs[1]:
        st.markdown("### 🧡 SBS 파워FM 주요 게시판")
        s_cols = st.columns(2)
        with s_cols[0]:
            st.link_button("🎙️ 두시탈출 컬투쇼", "https://m.programs.sbs.co.kr/radio/cultwoshow/boards/58047", use_container_width=True)
            st.link_button("🌟 웬디의 영스트리트", "https://m.programs.sbs.co.kr/radio/wendy0s/boards/69691", use_container_width=True)
        with s_cols[1]:
            st.link_button("🎸 박소현의 러브게임", "https://m.programs.sbs.co.kr/radio/lovegame/boards/57679", use_container_width=True)
            st.link_button("⚽ 배성재의 텐", "https://m.programs.sbs.co.kr/radio/ten/boards/57950", use_container_width=True)

    with day_tabs[2]:
        st.markdown("### 🌐 글로벌 라디오 신청")
        st.link_button("🍎 [NYC] 뉴욕 주말 요청", "https://docs.google.com/forms/d/e/1FAIpQLSfyVYf-rss5jZ0uA6RHIkb-Im180whM7I_U98HLnpu3w1C4cw/viewform", use_container_width=True)
        st.info("영문 문구: `I would like to request 제목 by PLAVE`")

    with day_tabs[3]:
        st.success("### 📱 문자 신청 번호\n- **KBS**: #8910 / **SBS**: #1077 / **MBC**: #8000")

# --- [메뉴 3 & 4] ---
elif menu == "💡 투표 팁 & 가이드": st.write("투표 앱 가이드를 준비 중입니다.")
elif menu == "💬 플리 커뮤니티": st.write("자유 게시판 공간입니다.")
