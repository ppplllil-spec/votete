import streamlit as st
import pandas as pd
from datetime import datetime
import re
from urllib.parse import urlparse
from streamlit_gsheets import GSheetsConnection
import streamlit.components.v1 as components

# 1. 페이지 설정
st.set_page_config(page_title="PLAVE PLLI 투표정보", page_icon="💙💜🩷❤️🖤", layout="wide")

# 2. 구글 시트 연결 설정
SHEET_ID = "1nf0XEDSj5kc0k29pWKaCa345aUG0-3RmofWqd4bRZ9M"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

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
    }
    .main-title { color: #FFFFFF; text-shadow: 0px 0px 15px rgba(162, 155, 254, 0.6); text-align: center; font-size: 2.5rem; font-weight: 800; margin-bottom: 30px; }
    .tweet-card { background-color: #1E2330; border-radius: 16px; padding: 24px; margin-bottom: 24px; transition: transform 0.2s; }
    .tweet-card:hover { transform: translateY(-5px); }
    .tweet-card.expired { opacity: 0.4; filter: grayscale(50%); }
    .category-tag { padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 700; }
    .importance-tag { background-color: #FFEAA7; color: #000000; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 700; margin-left: 5px; }
    .d-day-tag { float: right; background-color: #FF5E57; color: white; padding: 4px 14px; border-radius: 50px; font-size: 0.9rem; font-weight: 800; }
    .link-container { display: flex; align-items: center; background-color: #2D3436; padding: 12px; border-radius: 10px; margin-top: 15px; text-decoration: none !important; }
    </style>
    """, unsafe_allow_html=True)

# 4. 사이드바 메뉴
with st.sidebar:
    st.markdown("<h2 style='text-align:center; color:#A29BFE;'>PLLI CONNECT</h2>", unsafe_allow_html=True)
    menu = st.radio("메뉴 이동", ["📊 투표/광고 보드", "💡 투표 팁 & 가이드", "💬 플리 커뮤니티"], label_visibility="collapsed")
    st.divider()

st.markdown(f"<h1 class='main-title'>💙💜🩷❤️🖤 PLAVE PLLI 투표정보</h1>", unsafe_allow_html=True)

# --- [데이터 처리 로직] ---
def process_data(df):
    processed_rows = []
    for _, row in df.iterrows():
        raw_text = str(row['text']) if pd.notna(row['text']) else ""
        
        # 멤버 상징색 판별
        m_color = "#3E4556"
        if any(k in raw_text for k in ["노아", "NOAH", "💜"]): m_color = "#C294FB"
        elif any(k in raw_text for k in ["하민", "HAMIN", "🖤", "💚"]): m_color = "#B2EBC1"
        elif any(k in raw_text for k in ["예준", "YEJUN", "💙"]): m_color = "#A2D2FF"
        elif any(k in raw_text for k in ["밤비", "BAMBY", "🩷"]): m_color = "#FFB7D5"
        elif any(k in raw_text for k in ["은호", "EUNHO", "❤️"]): m_color = "#FF8E8E"

        # 링크 및 카테고리 자동 추출
        found_links = re.findall(r'(https?://\S+)', raw_text)
        final_link = row['link'] if pd.notna(row['link']) and str(row['link']).strip() != "" else (found_links[0] if found_links else None)
        
        cat = row['category']
        if pd.isna(cat) or str(cat).strip() == "":
            if "시상식" in raw_text: cat = "🏆 시상식"
            elif "생일" in raw_text: cat = "🎂 생일"
            elif any(k in raw_text for k in ["광고", "시안"]): cat = "🎨 광고시안"
            else: cat = "🗳️ 일반/음방"

        # D-Day 계산
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
            'd_day_label': d_label, 'd_day_val': d_val, 'is_expired': is_exp,
            'color': m_color
        })
    return pd.DataFrame(processed_rows)

# --- [섹션 1: 보드 출력 및 등록] ---
if menu == "📊 투표/광고 보드":
    with st.expander("➕ 새로운 투표 정보 등록하기"):
        with st.form("vote_form", clear_on_submit=True):
            f_cat = st.selectbox("분류", ["자동 분류", "🏆 시상식", "🗳️ 일반/음방", "🎂 생일", "🎨 광고시안"])
            f_imp = st.slider("중요도", 1, 3, 1)
            f_text = st.text_area("내용 (문구나 링크를 붙여넣으세요)")
            f_end = st.date_input("종료 날짜", value=datetime.now())
            f_img = st.text_input("이미지 주소 (없으면 비워둠)")
            if st.form_submit_button("보드에 등록하기 💙"):
                if f_text:
                    # [해결] spreadsheet 경로 명시
                    existing = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1", usecols=list(range(7)))
                    new_row = pd.DataFrame([{"category": f_cat if f_cat != "자동 분류" else "", "importance": f_imp, "text": f_text, "start_date": datetime.now().strftime('%Y-%m-%d'), "end_date": f_end.strftime('%Y-%m-%d'), "link": "", "images": f_img}])
                    conn.update(spreadsheet=SHEET_URL, worksheet="Sheet1", data=pd.concat([existing, new_row], ignore_index=True))
                    st.success("등록되었습니다! 화면을 새로고침 해주세요.")

    try:
        # [해결] spreadsheet 경로 명시
        raw_df = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1", usecols=list(range(7)))
        if not raw_df.empty:
            df = process_data(raw_df)
            sort_opt = st.segmented_control("정렬", ["🔥 마감순", "⭐ 중요도순"], default="🔥 마감순")
            if sort_opt == "🔥 마감순": df = df.sort_values(by=['is_expired', 'd_day_val'], ascending=[True, True])
            else: df = df.sort_values(by=['is_expired', 'importance'], ascending=[True, False])
            
            tabs = st.tabs(["전체", "🏆 시상식", "🎂 생일", "🗳️ 일반/음방", "🎨 광고시안"])

            def display_fn(data):
                if data.empty: st.info("소식이 없습니다. 💫")
                else:
                    cols = st.columns(2)
                    for idx, row in data.reset_index().iterrows():
                        with cols[idx % 2]:
                            card_style = f"border: 1.5px solid {row['color']}; box-shadow: 0px 4px 15px {row['color']}33;"
                            tweet_html = ""
                            if row['link'] and ("x.com" in row['link'] or "twitter.com" in row['link']):
                                tweet_html = f'<blockquote class="twitter-tweet" data-theme="dark"><a href="{row["link"]}"></a></blockquote><script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>'

                            st.markdown(f"""
                                <div class="tweet-card {'expired' if row['is_expired'] else ''}" style="{card_style}">
                                    <span class="category-tag" style="background-color:{row['color']}; color:{'#000' if row['color'] != '#333333' else '#fff'};">{row['category']}</span>
                                    <span class="importance-tag">⭐ {row['importance']}</span>
                                    <span class="d-day-tag">{row['d_day_label']}</span>
                                    <div style="font-size:0.85rem; color:#B2BEC3; margin:15px 0 5px 0;">🗓️ {row['start_date']} ~ {row['end_date']}</div>
                                    <div style="color:#FDFDFD; line-height:1.7; font-size:1.05rem; white-space:pre-wrap; margin-bottom:10px;">{row['text']}</div>
                                </div>
                            """, unsafe_allow_html=True)
                            
                            if tweet_html: components.html(tweet_html, height=450, scrolling=True)
                            if row['link'] and not tweet_html:
                                st.markdown(f"<a href='{row['link']}' target='_blank' class='link-container' style='border-left: 4px solid {row['color']}; text-decoration:none;'><span style='color:#A29BFE; font-weight:bold;'>🔗 참여 링크 이동</span></a>", unsafe_allow_html=True)
                            if pd.notna(row['images']) and str(row['images']).strip() != "":
                                st.image(row['images'], use_container_width=True)

            for i, cat in enumerate(["", "시상식", "생일", "🗳️|투표|음방", "광고|시안"]):
                with tabs[i]: display_fn(df if i==0 else df[df['category'].str.contains(cat, na=False)])
    except Exception as e: st.error(f"데이터 로드 실패: {e}")

# --- [섹션 2: 팁 등록] ---
elif menu == "💡 투표 팁 & 가이드":
    st.subheader("💡 앱별 재화 수급 및 투표 가이드")
    with st.expander("➕ 새로운 팁 직접 등록하기"):
        with st.form("tip_form", clear_on_submit=True):
            title = st.text_input("팁 제목")
            app = st.text_input("앱 이름")
            content = st.text_area("공략 내용")
            link = st.text_input("상세 링크")
            if st.form_submit_button("팁 등록하기"):
                if title and content:
                    existing = conn.read(spreadsheet=SHEET_URL, worksheet="tips", usecols=list(range(4)))
                    new_tip = pd.DataFrame([{"title": title, "app_name": app, "content": content, "link": link}])
                    conn.update(spreadsheet=SHEET_URL, worksheet="tips", data=pd.concat([existing, new_tip], ignore_index=True))
                    st.success("팁이 등록되었습니다!")

    try:
        tips = conn.read(spreadsheet=SHEET_URL, worksheet="tips")
        for _, row in tips.iterrows():
            with st.expander(f"[{row['app_name']}] {row['title']}"):
                st.write(row['content'])
                if pd.notna(row['link']) and str(row['link']).strip() != "":
                    st.link_button("상세 가이드", row['link'])
    except: st.info("등록된 팁이 없습니다.")

# --- [섹션 3: 커뮤니티 등록] ---
elif menu == "💬 플리 커뮤니티":
    st.subheader("💬 플리 자유 게시판")
    with st.form("comm_form", clear_on_submit=True):
        nick = st.text_input("닉네임")
        msg = st.text_area("내용")
        if st.form_submit_button("메시지 남기기"):
            if nick and msg:
                existing = conn.read(spreadsheet=SHEET_URL, worksheet="comments", usecols=list(range(3)))
                new_comm = pd.DataFrame([{"nickname": nick, "comment": msg, "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M')}])
                conn.update(spreadsheet=SHEET_URL, worksheet="comments", data=pd.concat([existing, new_comm], ignore_index=True))
                st.success("메시지가 등록되었습니다!")

    try:
        comms = conn.read(spreadsheet=SHEET_URL, worksheet="comments")
        for _, row in comms.iloc[::-1].iterrows():
            st.info(f"👤 {row['nickname']} ({row['timestamp']})\n\n{row['comment']}")
    except: st.info("첫 메시지를 기다리고 있습니다. 💙")
