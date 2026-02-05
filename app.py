import streamlit as st
import pandas as pd
from datetime import datetime
import re
from urllib.parse import urlparse

# 1. 페이지 설정
st.set_page_config(page_title="PLAVE PLLI 투표정보", page_icon="💙💜🩷❤️🖤", layout="wide")

# 2. 구글 시트 연결
SHEET_ID = "1nf0XEDSj5kc0k29pWKaCa345aUG0-3RmofWqd4bRZ9M"
# range=A:G를 설정하여 시트 우측의 한글 가이드 설명(I열 이후)이 앱에 불러와지지 않도록 원천 차단합니다.
DATA_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet1&range=A:G"
COMM_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=comments&range=A:C"
TIPS_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=tips&range=A:D"

# 3. 디자인 CSS
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; font-family: 'Pretendard', sans-serif; }
    section[data-testid="stSidebar"] { background-color: #161B22 !important; border-right: 1px solid #30363D; }
    div[data-testid="stSidebarUserContent"] .stRadio > div { gap: 10px; }
    div[data-testid="stSidebarUserContent"] label {
        background-color: #21262D; border: 1px solid #30363D; padding: 15px 20px !important;
        border-radius: 12px !important; color: #C9D1D9 !important; transition: all 0.3s ease; width: 100%;
    }
    div[data-testid="stSidebarUserContent"] div[aria-checked="true"] label {
        background-color: #A29BFE !important; color: #000000 !important; font-weight: bold !important;
        box-shadow: 0 0 15px rgba(162, 155, 254, 0.4);
    }
    .main-title { color: #FFFFFF; text-shadow: 0px 0px 15px rgba(162, 155, 254, 0.6); text-align: center; font-size: 2.5rem; font-weight: 800; margin-bottom: 30px; }
    .tweet-card { background-color: #1E2330; border: 1px solid #3E4556; border-radius: 16px; padding: 24px; margin-bottom: 24px; }
    .tweet-card.expired { opacity: 0.4; filter: grayscale(50%); }
    .category-tag { background-color: #A29BFE; color: #000000; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 700; }
    .importance-tag { background-color: #FFEAA7; color: #000000; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 700; margin-left: 5px; }
    .d-day-tag { float: right; background-color: #FF5E57; color: white; padding: 4px 14px; border-radius: 50px; font-size: 0.9rem; font-weight: 800; }
    .link-container { display: flex; align-items: center; background-color: #2D3436; padding: 12px; border-radius: 10px; margin-top: 15px; text-decoration: none !important; }
    .app-icon { width: 22px; height: 22px; border-radius: 5px; margin-right: 12px; }
    .tip-content { background-color: #2D3436; padding: 20px; border-radius: 12px; line-height: 1.8; color: #FDFDFD; font-size: 1.05rem; }
    </style>
    """, unsafe_allow_html=True)

# 4. 사이드바 메뉴
with st.sidebar:
    st.markdown("<h2 style='text-align:center; color:#A29BFE;'>PLLI CONNECT</h2>", unsafe_allow_html=True)
    menu = st.radio("메뉴 이동", ["📊 투표/광고 보드", "💡 투표 팁 & 가이드", "💬 플리 커뮤니티"], label_visibility="collapsed")
    st.write("") # 에러가 났던 v_spacer 대신 안전한 공백 처리
    st.divider()

st.markdown(f"<h1 class='main-title'>💙💜🩷❤️🖤 PLAVE PLLI 투표정보</h1>", unsafe_allow_html=True)

# --- [자동 분류 및 데이터 처리 로직] ---
def process_data(df):
    processed_rows = []
    for _, row in df.iterrows():
        raw_text = str(row['text']) if pd.notna(row['text']) else ""
        
        # 1. 링크 추출
        found_links = re.findall(r'(https?://\S+)', raw_text)
        final_link = row['link'] if pd.notna(row['link']) and str(row['link']).strip() != "" else (found_links[0] if found_links else None)
        
        # 2. 카테고리 자동 분류 (비어있을 경우 '일반'을 기본값으로)
        cat = row['category']
        if pd.isna(cat) or str(cat).strip() == "":
            # 특정 키워드가 본문에 있을 때만 변경, 그 외엔 모두 '일반'
            if "시상식" in raw_text: cat = "🏆 시상식"
            elif "생일" in raw_text: cat = "🎂 생일"
            elif any(k in raw_text for k in ["광고", "시안"]): cat = "🎨 광고시안"
            else: cat = "🗳️ 일반/음방"  # 기본값 설정

        # 3. D-Day 및 숫자 에러 방지 로직 (기존과 동일)
        def get_dday(date_str):
            try:
                if pd.isna(date_str) or str(date_str).strip() == "": return "상시", 999, False
                end_date = datetime.strptime(str(date_str).strip(), '%Y-%m-%d').date()
                delta = (end_date - datetime.now().date()).days
                if delta > 0: return f"D-{delta}", delta, False
                elif delta == 0: return "D-Day", 0, False
                else: return "종료", delta, True
            except: return "정보없음", 999, False

        d_label, d_val, is_exp = get_dday(row['end_date'])
        
        imp = 1
        try:
            if pd.notna(row['importance']): imp = int(float(row['importance']))
        except: imp = 1

        processed_rows.append({
            'category': cat, 'importance': imp,
            'text': raw_text.split('http')[0].strip(),
            'start_date': row['start_date'], 'end_date': row['end_date'],
            'link': final_link, 'images': row['images'],
            'd_day_label': d_label, 'd_day_val': d_val, 'is_expired': is_exp
        })
    return pd.DataFrame(processed_rows)

# --- [섹션 1: 보드 출력] ---
if menu == "📊 투표/광고 보드":
    try:
        raw_df = pd.read_csv(DATA_URL)
        if raw_df.empty:
            st.info("시트에 데이터를 입력해주세요! 💙")
        else:
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
                                    <span class="importance-tag">⭐ {row['importance']}</span>
                                    <span class="d-day-tag">{row['d_day_label']}</span>
                                    <div style="font-size:0.85rem; color:#B2BEC3; margin:15px 0 5px 0;">🗓️ {row['start_date'] if pd.notna(row['start_date']) else '-'} ~ {row['end_date'] if pd.notna(row['end_date']) else '-'}</div>
                                    <div style="color:#FDFDFD; line-height:1.7; font-size:1.05rem; white-space:pre-wrap;">{row['text']}</div>
                                    {"<a href='"+str(row['link'])+"' target='_blank' class='link-container'>" + icon_html + "<span style='color:#A29BFE; font-weight:bold;'>참여 링크로 이동</span></a>" if row['link'] else ""}
                                </div>
                            """, unsafe_allow_html=True)
                            if pd.notna(row['images']): st.image(row['images'], use_container_width=True)
            with tabs[0]: display_cards(df)
            with tabs[1]: display_cards(df[df['category'].str.contains('시상식', na=False)])
            with tabs[2]: display_cards(df[df['category'].str.contains('생일', na=False)])
            with tabs[3]: display_cards(df[df['category'].str.contains('🗳️|투표|음방', na=False)])
            with tabs[4]: display_cards(df[df['category'].str.contains('광고|시안', na=False)])
    except Exception as e: st.error(f"데이터 로드 실패: {e}")

# (섹션 2, 3은 이전과 동일하게 유지 - 버튼 링크 gid는 알려주신 번호로 유지)
elif menu == "💡 투표 팁 & 가이드":
    st.subheader("💡 앱별 재화 수급 및 투표 가이드")
    st.link_button("✍️ 팁 추가/수정하러 가기", f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit?gid=1194006631#gid=1194006631")
    try:
        tips_df = pd.read_csv(TIPS_URL)
        if not tips_df.empty:
            for _, row in tips_df.iterrows():
                with st.expander(f"[{row['app_name']}] {row['title']}"):
                    st.markdown(f"<div class='tip-content'>{row['content']}</div>", unsafe_allow_html=True)
    except: st.info("팁을 등록해주세요!")

elif menu == "💬 플리 커뮤니티":
    st.subheader("💬 플리 자유 게시판")
    st.link_button("✍️ 의견 남기러 가기 (구글 시트)", f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit?gid=881882748#gid=881882748")
    try:
        comm_df = pd.read_csv(COMM_URL)
        for _, row in comm_df.iloc[::-1].iterrows():
            st.markdown(f"""<div class="comment-box"><span class="timestamp">{row['timestamp']}</span><div class="nickname">👤 {row['nickname']}</div><div class="comment-text">{row['comment']}</div></div>""", unsafe_allow_html=True)
    except: st.info("첫 의견을 남겨보세요!")
