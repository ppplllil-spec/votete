import streamlit as st
import pandas as pd
from datetime import datetime
import re
from urllib.parse import urlparse

# 1. 페이지 설정
st.set_page_config(page_title="PLAVE PLLI TRACKER", page_icon="💙💜🩷❤️🖤", layout="wide")

# 2. 구글 시트 연결
SHEET_ID = "1nf0XEDSj5kc0k29pWKaCa345aUG0-3RmofWqd4bRZ9M"
DATA_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet1"
COMM_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=comments"
TIPS_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=tips"

# 3. 통합 디자인 CSS
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; font-family: 'Pretendard', sans-serif; }
    section[data-testid="stSidebar"] { background-color: #161B22 !important; border-right: 1px solid #30363D; }
    
    /* 사이드바 메뉴 스타일 */
    div[data-testid="stSidebarUserContent"] .stRadio > div { gap: 10px; }
    div[data-testid="stSidebarUserContent"] label {
        background-color: #21262D; border: 1px solid #30363D; padding: 15px 20px !important;
        border-radius: 12px !important; color: #C9D1D9 !important; transition: all 0.3s ease; width: 100%;
    }
    div[data-testid="stSidebarUserContent"] div[aria-checked="true"] label {
        background-color: #A29BFE !important; color: #000000 !important; font-weight: bold !important;
        box-shadow: 0 0 15px rgba(162, 155, 254, 0.4);
    }

    /* 메인 타이틀 */
    .main-title { color: #FFFFFF; text-shadow: 0px 0px 15px rgba(162, 155, 254, 0.6); text-align: center; font-size: 2.5rem; font-weight: 800; margin-bottom: 30px; }
    
    /* 카드 디자인 */
    .tweet-card { background-color: #1E2330; border: 1px solid #3E4556; border-radius: 16px; padding: 24px; margin-bottom: 24px; }
    .tweet-card.expired { opacity: 0.4; filter: grayscale(50%); }
    .category-tag { background-color: #A29BFE; color: #000000; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 700; }
    .importance-tag { background-color: #FFEAA7; color: #000000; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 700; margin-left: 5px; }
    .d-day-tag { float: right; background-color: #FF5E57; color: white; padding: 4px 14px; border-radius: 50px; font-size: 0.9rem; font-weight: 800; }
    
    /* 팁 섹션 스타일 */
    .tip-content { background-color: #2D3436; padding: 20px; border-radius: 12px; line-height: 1.8; color: #FDFDFD; font-size: 1.05rem; }
    
    .link-container { display: flex; align-items: center; background-color: #2D3436; padding: 12px; border-radius: 10px; margin-top: 15px; text-decoration: none !important; }
    .app-icon { width: 22px; height: 22px; border-radius: 5px; margin-right: 12px; }
    </style>
    """, unsafe_allow_html=True)

# 4. 사이드바 메뉴
with st.sidebar:
    st.markdown("<h2 style='text-align:center; color:#A29BFE;'>PLLI CONNECT</h2>", unsafe_allow_html=True)
    menu = st.radio("메뉴 이동", ["📊 투표/광고 보드", "💡 투표 팁 & 가이드", "💬 플리 커뮤니티"], label_visibility="collapsed")
    st.write("")
    st.divider()
    st.caption("플리들이 직접 만드는 실시간 대시보드입니다.")

# 메인 타이틀 (요청하신 하트와 제목 적용)
st.markdown(f"<h1 class='main-title'>💙💜🩷❤️🖤 PLAVE PLLI 투표정보</h1>", unsafe_allow_html=True)

# --- [자동 분류 및 데이터 처리 로직] ---
def process_data(df):
    processed_rows = []
    for _, row in df.iterrows():
        raw_text = str(row['text'])
        found_links = re.findall(r'(https?://\S+)', raw_text)
        final_link = row['link'] if pd.notna(row['link']) else (found_links[0] if found_links else None)
        
        cat = row['category']
        if pd.isna(cat) or cat == "":
            if "투표" in raw_text or "순위" in raw_text: cat = "🗳️ 일반/음방"
            elif "시상식" in raw_text: cat = "🏆 시상식"
            elif "생일" in raw_text: cat = "🎂 생일"
            elif "광고" in raw_text or "시안" in raw_text: cat = "🎨 광고시안"
            else: cat = "📢 일반소식"

        def get_dday(date_str):
            try:
                if pd.isna(date_str) or str(date_str).strip() == "": return "상시", 999, False
                end_date = datetime.strptime(str(date_str).strip(), '%Y-%m-%d').date()
                delta = (end_date - datetime.now().date()).days
                if delta > 0: return f"D-{delta}", delta, False
                elif delta == 0: return "D-Day", 0, False
                else: return "종료", delta, True
            except: return "상시", 999, False

        d_label, d_val, is_exp = get_dday(row['end_date'])
        processed_rows.append({
            'category': cat, 'importance': pd.to_numeric(row['importance'], errors='coerce') or 1,
            'text': raw_text.split('http')[0].strip(), 'start_date': row['start_date'],
            'end_date': row['end_date'], 'link': final_link, 'images': row['images'],
            'd_day_label': d_label, 'd_day_val': d_val, 'is_expired': is_exp
        })
    return pd.DataFrame(processed_rows)

# --- [섹션 1: 투표/광고 보드] ---
if menu == "📊 투표/광고 보드":
    try:
        raw_df = pd.read_csv(DATA_URL)
        df = process_data(raw_df)
        sort_opt = st.segmented_control("정렬 방식", ["🔥 마감 임박순", "⭐ 중요도 순"], default="🔥 마감 임박순")
        if sort_opt == "🔥 마감 임박순": df = df.sort_values(by=['is_expired', 'd_day_val'], ascending=[True, True])
        else: df = df.sort_values(by=['is_expired', 'importance'], ascending=[True, False])

        tabs = st.tabs(["전체", "🏆 시상식", "🎂 생일", "🗳️ 일반/음방", "🎨 광고시안"])
        def display_cards(data):
            if data.empty: st.info("소식을 기다리고 있습니다. 💫")
            else:
                cols = st.columns(2)
                for idx, row in data.reset_index().iterrows():
                    icon_html = ""
                    if row['link']:
                        domain = urlparse(row['link']).netloc
                        icon_url = f"https://www.google.com/s2/favicons?domain={domain}&sz=64"
                        icon_html = f"<img src='{icon_url}' class='app-icon'>"
                    with cols[idx % 2]:
                        st.markdown(f"""
                            <div class="tweet-card {'expired' if row['is_expired'] else ''}">
                                <span class="category-tag">{row['category']}</span>
                                <span class="importance-tag">⭐ {int(row['importance'])}</span>
                                <span class="d-day-tag">{row['d_day_label']}</span>
                                <div style="font-size:0.85rem; color:#B2BEC3; margin:15px 0 5px 0;">🗓️ {row['start_date']} ~ {row['end_date']}</div>
                                <div style="color:#FDFDFD; line-height:1.7; font-size:1.05rem; white-space:pre-wrap;">{row['text']}</div>
                                {"<a href='"+str(row['link'])+"' target='_blank' class='link-container'>" + icon_html + "<span style='color:#A29BFE; font-weight:bold;'>참여 링크로 이동</span></a>" if row['link'] else ""}
                            </div>
                        """, unsafe_allow_html=True)
                        if pd.notna(row['images']): st.image(row['images'], use_container_width=True)
        with tabs[0]: display_cards(df)
        with tabs[1]: display_cards(df[df['category'].str.contains('시상식')])
        with tabs[2]: display_cards(df[df['category'].str.contains('생일')])
        with tabs[3]: display_cards(df[df['category'].str.contains('🗳️|투표|음방')])
        with tabs[4]: display_cards(df[df['category'].str.contains('광고|시안')])
    except Exception as e: st.error(f"데이터 로드 실패: {e}")

# --- [섹션 2: 💡 투표 팁 & 가이드] ---
elif menu == "💡 투표 팁 & 가이드":
    st.subheader("💡 앱별 재화 수급 및 투표 가이드")
    # 팁 전용 링크 버튼 (알려주신 gid=1194006631 적용)
    st.link_button("✍️ 팁 추가/수정하러 가기", f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit?gid=1194006631#gid=1194006631")
    st.divider()
    
    try:
        tips_df = pd.read_csv(TIPS_URL)
        if tips_df.empty: st.info("아직 등록된 팁이 없습니다.")
        else:
            app_list = ["전체"] + list(tips_df['app_name'].unique())
            selected_app = st.selectbox("앱 선택", app_list)
            display_tips = tips_df if selected_app == "전체" else tips_df[tips_df['app_name'] == selected_app]
            for _, row in display_tips.iterrows():
                with st.expander(f"[{row['app_name']}] {row['title']}"):
                    st.markdown(f"<div class='tip-content'>{row['content']}</div>", unsafe_allow_html=True)
                    if pd.notna(row['link']): st.link_button("🔗 상세 가이드 보기", row['link'])
    except: st.warning("팁 데이터를 불러올 수 없습니다. 'tips' 탭 설정을 확인해 주세요.")

# --- [섹션 3: 💬 플리 커뮤니티] ---
elif menu == "💬 플리 커뮤니티":
    st.subheader("💬 플리 자유 게시판")
    # 커뮤니티 전용 링크 버튼 (알려주신 gid=881882748 적용)
    st.link_button("✍️ 의견 남기러 가기 (구글 시트)", f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit?gid=881882748#gid=881882748")
    st.divider()
    
    try:
        comm_df = pd.read_csv(COMM_URL)
        if comm_df.empty:
            st.write("아직 남겨진 메시지가 없네요. 첫 마디를 떼어보세요! 💙")
        else:
            for _, row in comm_df.iloc[::-1].iterrows():
                st.markdown(f"""
                    <div class="comment-box">
                        <span class="timestamp">{row['timestamp'] if pd.notna(row['timestamp']) else ''}</span>
                        <div class="nickname">👤 {row['nickname']}</div>
                        <div class="comment-text">{row['comment']}</div>
                    </div>
                """, unsafe_allow_html=True)
    except: st.warning("커뮤니티 시트를 읽어올 수 없습니다.")
