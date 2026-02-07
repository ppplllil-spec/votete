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

# --- [1. 스타일링 (CSS)] ---
st.markdown(f"""
    <style>
    /* 배경: 파스텔 하늘색 + 격자무늬 */
    .stApp {{
        background-color: #F0F7FF;
        background-image: linear-gradient(rgba(187, 222, 251, 0.2) 1px, transparent 1px),
                          linear-gradient(90deg, rgba(187, 222, 251, 0.2) 1px, transparent 1px);
        background-size: 30px 30px;
        color: #455A64 !important;
        font-family: 'Pretendard', sans-serif;
    }}
    
    /* 사이드바 입체 디자인 */
    section[data-testid="stSidebar"] {{
        background-color: rgba(255, 255, 255, 0.95) !important;
        border-right: 2px solid #E3F2FD;
    }}
    section[data-testid="stSidebar"] .stRadio label {{
        background-color: #FFFFFF !important; color: #546E7A !important;
        padding: 15px 20px !important; border-radius: 15px !important;
        margin-bottom: 10px !important; border: 1px solid #F0F4F8;
        transition: all 0.3s; font-weight: 600; box-shadow: 0 2px 5px rgba(0,0,0,0.02);
    }}
    section[data-testid="stSidebar"] div[aria-checked="true"] label {{
        background: linear-gradient(135deg, #BBDEFB 0%, #E3F2FD 100%) !important;
        color: #1976D2 !important; border: 1px solid #90CAF9 !important; font-weight: 800;
    }}

    /* 카드 및 배너 */
    .main-title {{ text-align: center; font-size: 2.8rem; font-weight: 900; background: linear-gradient(90deg, #91C8FF, #FFB7D5); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 30px; }}
    .urgent-banner {{ background: #FFFFFF; border: 3px solid #FFB7D5; border-radius: 25px; padding: 30px; text-align: center; box-shadow: 0 10px 25px rgba(255, 183, 213, 0.3); margin-bottom: 20px; }}
    .tweet-card {{ background-color: rgba(255, 255, 255, 0.8); border: 1px solid #E3F2FD; border-radius: 20px; padding: 24px; margin-bottom: 20px !important; }}
    .category-tag {{ background: #E3F2FD; color: #1976D2; padding: 4px 12px; border-radius: 8px; font-weight: 700; }}
    .d-day-tag {{ float: right; background: #FFEBEE; color: #D32F2F; padding: 4px 12px; border-radius: 8px; font-weight: 800; }}

    /* 버튼 가독성 강화 */
    div.stButton > button, .stLinkButton > a {{
        background: #FFFFFF !important; color: #1976D2 !important; border: 2px solid #BBDEFB !important; border-radius: 15px !important; font-weight: 700 !important; text-decoration: none !important; display: flex; justify-content: center;
    }}
    </style>
    """, unsafe_allow_html=True)
# --- [2. 스마트 로직 함수] ---
def extract_date_from_text(text):
    today = datetime.now()
    patterns = [r'(\d{1,2})[/\.\-](\d{1,2})', r'(\d{1,2})월\s*(\d{1,2})일']
    for p in patterns:
        match = re.search(p, text)
        if match:
            month, day = int(match.group(1)), int(match.group(2))
            try:
                res_date = datetime(today.year, month, day).date()
                if res_date < today.date(): res_date = datetime(today.year + 1, month, day).date()
                return res_date
            except: continue
    return today.date()

def smart_parser(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        og_title = soup.find("meta", property="og:title")
        og_desc = soup.find("meta", property="og:description")
        full_text = (og_title['content'] if og_title else "") + " " + (og_desc['content'] if og_desc else "")
        
        url_l = str(url).lower()
        category = "🗳️ 일반 투표"
        if "podoal" in url_l: category = "🍇 포도알 투표"
        elif "idolchamp" in url_l: category = "🎙️ 아이돌챔프"
        elif any(k in full_text for k in ["M카", "음방", "인가"]): category = "🎙️ 음악방송"
        
        return {"cat": category, "text": full_text.split('|')[0][:37], "date": extract_date_from_text(full_text)}
    except:
        return {"cat": "🗳️ 일반 투표", "text": "", "date": datetime.now().date()}
# --- [3. 메인 레이아웃 및 제보 로직] ---
with st.sidebar:
    st.markdown(f'<div style="text-align:center;"><img src="{PLLI_LOGO}" style="border-radius:50%; border:3px solid #BBDEFB;" width="100"></div>', unsafe_allow_html=True)
    menu = st.radio("MENU", ["📊 투표 보드", "🎨 광고/시안", "💡 앱별 팁", "📻 라디오 신청", "💬 커뮤니티"], label_visibility="collapsed")

st.markdown("<h1 class='main-title'>PLLI CONNECT</h1>", unsafe_allow_html=True)

try:
    raw_df = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1", ttl="5m")
    today = datetime.now().date()
    raw_df['end_dt'] = pd.to_datetime(raw_df['end_date'], errors='coerce').dt.date
    active_df = raw_df[raw_df['end_dt'] >= today].copy()

    if "투표" in menu or "광고" in menu:
        # 3-1. 긴급 전광판 (에러 방지 적용)
        urgent = active_df.sort_values(by='end_dt', ascending=True).head(1)
        if not urgent.empty:
            t = urgent.iloc[0]
            target_url = str(t['link']) if pd.notna(t['link']) and str(t['link']).startswith("http") else "https://twitter.com/plave_official"
            st.markdown(f"""<div class="urgent-banner">
                <div style="color: #FF8AAB; font-weight:900;">💖 화력 집중 EMERGENCY 💖</div>
                <div style="font-size:1.8rem; font-weight:800; color:#37474F; margin: 15px 0;">{t['text']}</div>
            </div>""", unsafe_allow_html=True)
            st.link_button("✨ 지금 바로 참여하기", target_url, use_container_width=True)
            st.divider()

        # 3-2. 스마트 제보
        with st.expander("🚀 초간단 정보 제보/등록"):
            input_url = st.text_input("링크(X 또는 앱)를 붙여넣으세요")
            if input_url:
                info = smart_parser(input_url)
                with st.form("smart_add"):
                    f_cat = st.selectbox("분류", [info['cat'], "🗳️ 일반 투표", "🎙️ 음악방송", "🏆 시상식", "🎨 광고/시안"])
                    f_text = st.text_input("제목", value=info['text'])
                    f_date = st.date_input("마감일", value=info['date'])
                    f_pwd = st.text_input("관리자 암호 (제보 시 생략)", type="password")
                    if st.form_submit_button("등록/제보하기"):
                        new_row = pd.DataFrame([{"category": f_cat, "text": f_text, "end_date": f_date.strftime('%Y-%m-%d'), "link": input_url}])
                        target_ws = "Sheet1" if f_pwd == ADMIN_PASSWORD else "Sheet4"
                        conn.update(spreadsheet=SHEET_URL, worksheet=target_ws, data=new_row)
                        st.success("완료되었습니다! 💙"); st.rerun()
    # 4-1. 리스트 출력 (에러 방지 로직 포함)
    display_df = active_df[active_df['category'].str.contains("광고|시안")].copy() if "광고" in menu else active_df.copy()
    df_sorted = display_df.sort_values(by='end_dt', ascending=True)
    
    cols = st.columns(2)
    for idx, row in df_sorted.reset_index().iterrows():
        with cols[idx % 2]:
            d_day = (row['end_dt'] - today).days
            st.markdown(f"""<div class="tweet-card">
                <div><span class="category-tag">{row['category']}</span><span class="d-day-tag">D-{d_day if d_day > 0 else 'Day'}</span></div>
                <div class="card-text">{row['text']}</div>
            </div>""", unsafe_allow_html=True)
            
            # 링크 안전 변환 및 에러 방지
            safe_link = str(row['link']).strip() if pd.notna(row['link']) else ""
            if safe_link.startswith("http"):
                st.link_button("🔗 자세히 보기", safe_link, use_container_width=True)
            else:
                st.button("🔗 링크 준비 중", disabled=True, use_container_width=True, key=f"btn_{idx}")

except Exception as e:
    st.error(f"구글 시트에 'Sheet4'가 있는지 확인해주세요! 에러내용: {e}")
