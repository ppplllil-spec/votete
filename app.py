import streamlit as st
import pandas as pd
from datetime import datetime
from urllib.parse import urlparse

# 1. 페이지 설정
st.set_page_config(page_title="PLAVE PLLI 투표정보", page_icon="💙💜🩷❤️🖤", layout="wide")

# 2. 구글 시트 연결 (수정된 ID 적용)
SHEET_ID = "1nf0XEDSj5kc0k29pWKaCa345aUG0-3RmofWqd4bRZ9M"
DATA_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet1"
COMM_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=comments"

# 3. 통합 디자인 CSS (사이드바 및 레이아웃 강화)
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; font-family: 'Pretendard', sans-serif; }
    
    /* 사이드바 커스텀 */
    section[data-testid="stSidebar"] {
        background-color: #161B22 !important;
        border-right: 1px solid #30363D;
    }
    
    /* 메뉴 라디오 버튼 이쁘게 만들기 */
    div[data-testid="stSidebarUserContent"] .stRadio > div {
        gap: 10px;
    }
    div[data-testid="stSidebarUserContent"] label {
        background-color: #21262D;
        border: 1px solid #30363D;
        padding: 15px 20px !important;
        border-radius: 12px !important;
        color: #C9D1D9 !important;
        transition: all 0.3s ease;
        width: 100%;
    }
    div[data-testid="stSidebarUserContent"] label:hover {
        background-color: #30363D;
        border-color: #A29BFE;
    }
    div[data-testid="stSidebarUserContent"] div[aria-checked="true"] label {
        background-color: #A29BFE !important;
        color: #000000 !important;
        font-weight: bold !important;
        border-color: #A29BFE !important;
        box-shadow: 0 0 15px rgba(162, 155, 254, 0.4);
    }
    
    /* 메인 타이틀 */
    .main-title { 
        color: #FFFFFF; 
        text-shadow: 0px 0px 15px rgba(162, 155, 254, 0.6); 
        text-align: center; 
        font-size: 2.5rem; 
        font-weight: 800; 
        margin-bottom: 30px;
        letter-spacing: -0.05em;
    }

    /* 카드 및 기타 스타일 유지 */
    .tweet-card { background-color: #1E2330; border: 1px solid #3E4556; border-radius: 16px; padding: 24px; margin-bottom: 24px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); }
    .category-tag { background-color: #A29BFE; color: #000000; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 700; }
    .d-day-tag { float: right; background-color: #FF5E57; color: white; padding: 4px 14px; border-radius: 50px; font-size: 0.9rem; font-weight: 800; }
    </style>
    """, unsafe_allow_html=True)

# 4. 사이드바 메뉴 (개선된 배치)
with st.sidebar:
    st.markdown("<h2 style='text-align:center; color:#A29BFE;'>PLLI CONNECT</h2>", unsafe_allow_html=True)
    st.write("")
    # 라디오 버튼을 버튼 형태로 활용
    menu = st.radio(
        "이동할 메뉴를 선택하세요",
        ["📊 투표/광고 보드", "💬 플리 커뮤니티"],
        label_visibility="collapsed"
    )
    st.divider()
    st.markdown("### 📢 공지사항")
    st.caption("플리들이 직접 관리하는 실시간 대시보드입니다. 허위 정보 기재 시 삭제될 수 있습니다.")

st.markdown(f"<h1 class='main-title'>PLAVE PLLI 투표정보</h1>", unsafe_allow_html=True)

# --- [섹션 1: 투표/광고 보드] ---
if menu == "📊 투표/광고 보드":
    try:
        df = pd.read_csv(DATA_URL)
        
        # 데이터 처리
        def get_status(date_str):
            try:
                if pd.isna(date_str): return "상시", 999, False
                end_date = datetime.strptime(str(date_str).strip(), '%Y-%m-%d').date()
                delta = (end_date - datetime.now().date()).days
                if delta > 0: return f"D-{delta}", delta, False
                elif delta == 0: return "D-Day", 0, False
                else: return "종료", delta, True
            except: return "상시", 999, False

        status_info = df['end_date'].apply(get_status)
        df['d_day_label'], df['d_day_val'], df['is_expired'] = zip(*status_info)
        df['importance'] = pd.to_numeric(df['importance'], errors='coerce').fillna(0)

        # 상단 필터
        c1, c2 = st.columns([3, 1])
        with c1:
            sort_opt = st.segmented_control("정렬 방식", ["🔥 마감 임박순", "⭐ 중요도 순"], default="🔥 마감 임박순")
        with c2:
            st.link_button("✍️ 소식 제보하기", f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit")

        if sort_opt == "🔥 마감 임박순":
            df = df.sort_values(by=['is_expired', 'd_day_val'], ascending=[True, True])
        else:
            df = df.sort_values(by=['is_expired', 'importance'], ascending=[True, False])

        tabs = st.tabs(["전체", "🏆 시상식", "🎂 생일", "🗳️ 일반/음방", "🎨 광고시안"])
        
        def display_cards(data):
            if data.empty: st.info("소식을 기다리고 있습니다. 💫")
            else:
                cols = st.columns(2)
                for idx, row in data.reset_index().iterrows():
                    is_exp = row['is_expired']
                    link_url = row.get('link')
                    icon_html = ""
                    if pd.notna(link_url):
                        domain = urlparse(link_url).netloc
                        icon_url = f"https://www.google.com/s2/favicons?domain={domain}&sz=64"
                        icon_html = f"<img src='{icon_url}' class='app-icon'>"
                    
                    with cols[idx % 2]:
                        st.markdown(f"""
                            <div class="tweet-card {'expired' if is_exp else ''}">
                                <span class="category-tag">{row['category']}</span>
                                <span class="importance-tag">⭐ {int(row['importance'])}</span>
                                <span class="d-day-tag">{row['d_day_label']}</span>
                                <div style="font-size:0.9rem; color:#B2BEC3; margin:15px 0 5px 0;">🗓️ {row.get('start_date','-')} ~ {row.get('end_date','-')}</div>
                                <div class="tweet-text">{row['text']}</div>
                                {"<a href='"+str(link_url)+"' target='_blank' class='link-container'>" + icon_html + "<span style='color:#A29BFE; font-weight:bold;'>참여 링크로 이동</span></a>" if pd.notna(link_url) else ""}
                            </div>
                        """, unsafe_allow_html=True)
                        if pd.notna(row.get('images')): st.image(row['images'], use_container_width=True)

        with tabs[0]: display_cards(df)
        with tabs[1]: display_cards(df[df['category'] == '시상식'])
        with tabs[2]: display_cards(df[df['category'] == '생일'])
        with tabs[3]: display_cards(df[df['category'].isin(['일반', '음방'])])
        with tabs[4]: display_cards(df[df['category'] == '광고시안'])

    except Exception as e: st.error(f"데이터 로드 실패: {e}")

# --- [섹션 2: 플리 커뮤니티] ---
elif menu == "💬 플리 커뮤니티":
    st.subheader("💬 플리 자유 게시판")
    st.markdown("의견 공유, 투표 인증, 응원 메시지 등 무엇이든 환영합니다!")
    
    c1, c2 = st.columns([1, 1])
    with c1:
        st.info("📢 작성하신 내용은 구글 시트 'comments' 탭에 실시간으로 기록됩니다.")
    with c2:
        st.link_button("✍️ 의견 남기러 가기 (구글 시트)", f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit#gid=커뮤니티탭ID")

    st.divider()

    try:
        comm_df = pd.read_csv(COMM_URL)
        if comm_df.empty:
            st.write("아직 남겨진 메시지가 없네요. 첫 마디를 떼어보세요!")
        else:
            # 최신순 정렬 (마지막 행이 위로)
            for _, row in comm_df.iloc[::-1].iterrows():
                st.markdown(f"""
                    <div class="comment-box">
                        <span class="timestamp">{row['timestamp']}</span>
                        <div class="nickname">👤 {row['nickname']}</div>
                        <div class="comment-text">{row['comment']}</div>
                    </div>
                """, unsafe_allow_html=True)
    except:
        st.warning("커뮤니티 시트를 읽어올 수 없습니다. 'comments' 탭 이름을 확인해 주세요.")
