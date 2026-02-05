import streamlit as st
import pandas as pd
from datetime import datetime
from urllib.parse import urlparse

# 1. 페이지 설정
st.set_page_config(page_title="PLAVE PLLI TRACKER", page_icon="💙💜🩷❤️🖤", layout="wide")

# 2. 구글 시트 연결 (본인의 시트 ID 및 탭 이름 확인 필수)
SHEET_ID = "1fO9eZpzP8orgwRkH0FiwO1ZAQmvaKJqpMmophIP_8Ts"
# 데이터 탭 (Sheet1) 및 커뮤니티 탭 (comments)
DATA_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet1"
COMM_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=comments"

# 3. 통합 디자인 CSS
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; font-family: 'Pretendard', sans-serif; }
    .main-title { color: #FFFFFF; text-shadow: 0px 0px 15px rgba(162, 155, 254, 0.6); text-align: center; font-size: 2.5rem; font-weight: 800; margin-bottom: 20px; }
    
    /* 보드 카드 스타일 */
    .tweet-card { background-color: #1E2330; border: 1px solid #3E4556; border-radius: 16px; padding: 24px; margin-bottom: 24px; }
    .tweet-card.expired { opacity: 0.4; filter: grayscale(50%); }
    .category-tag { background-color: #A29BFE; color: #000000; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 700; }
    .importance-tag { background-color: #FFEAA7; color: #000000; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 700; margin-left: 5px; }
    .d-day-tag { float: right; background-color: #FF5E57; color: white; padding: 4px 14px; border-radius: 50px; font-size: 0.9rem; font-weight: 800; }
    
    /* 커뮤니티 스타일 */
    .comment-box { background-color: #1E2330; border-radius: 12px; padding: 18px; margin-bottom: 12px; border-left: 6px solid #A29BFE; box-shadow: 0 2px 10px rgba(0,0,0,0.2); }
    .nickname { color: #A29BFE; font-weight: bold; font-size: 1rem; }
    .comment-text { color: #FDFDFD; margin-top: 8px; font-size: 1.05rem; white-space: pre-wrap; }
    .timestamp { color: #636e72; font-size: 0.75rem; float: right; }
    
    /* 링크 컨테이너 */
    .link-container { display: flex; align-items: center; background-color: #2D3436; padding: 12px; border-radius: 10px; margin-top: 15px; text-decoration: none !important; }
    .app-icon { width: 22px; height: 22px; border-radius: 5px; margin-right: 12px; }
    </style>
    """, unsafe_allow_html=True)

# 4. 사이드바 메뉴 (섹션 분리)
with st.sidebar:
    st.markdown("## 연결망")
    menu = st.radio("메뉴 이동", ["📊 투표/광고 보드", "💬 플리 커뮤니티"], index=0)
    st.divider()
    st.info("플리들이 직접 만드는 실시간 대시보드입니다.")

st.markdown(f"<h1 class='main-title'>PLAVE PLLI TRACKER</h1>", unsafe_allow_html=True)

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
