import streamlit as st
import pandas as pd
import pytz
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
from streamlit_gsheets import GSheetsConnection

# --- 설정 정보 ---
SHEET_ID = "1nf0XEDSj5kc0k29pWKaCa345aUG0-3RmofWqd4bRZ9M"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit"
ADMIN_PASSWORD = "plave123"
PLLI_LOGO = "https://pbs.twimg.com/profile_images/1982462665361330176/xHkk84gA.jpg"

st.set_page_config(page_title="PLAVE PLLI CONNECT", page_icon="💙🩷", layout="wide")
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 스타일링 (CSS) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0B0E14; color: #FFFFFF !important; font-family: 'Pretendard', sans-serif; }}
    section[data-testid="stSidebar"] {{ background-color: #12161D !important; border-right: 1px solid #30363D; }}
    section[data-testid="stSidebar"] div[aria-checked="true"] label {{
        background-color: rgba(162, 210, 255, 0.1) !important; color: #A2D2FF !important; border: 1px solid #A2D2FF; font-weight: 700;
    }}
    .main-title {{ text-align: center; font-size: 2.5rem; font-weight: 900; background: linear-gradient(90deg, #A2D2FF, #FFB7D5); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 20px; }}
    .urgent-banner {{ background: linear-gradient(135deg, rgba(255, 94, 87, 0.2) 0%, rgba(18, 22, 29, 0) 100%); border: 2px solid #FF5E57; border-radius: 20px; padding: 25px; margin-bottom: 30px; text-align: center; box-shadow: 0 0 20px rgba(255, 94, 87, 0.1); }}
    .tweet-card {{ background-color: #1C2128; border: 1px solid #30363D; border-radius: 16px; padding: 24px; margin-bottom: 20px !important; }}
    .card-text {{ font-size: 1.15rem; font-weight: 600; color: #FFFFFF; margin-top: 10px; line-height: 1.6; }}
    .category-tag {{ background: rgba(162, 210, 255, 0.15); color: #A2D2FF; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 600; border: 1px solid rgba(162, 210, 255, 0.3); }}
    .d-day-tag {{ float: right; color: #FF7B72; font-weight: 800; }}
    div.stButton > button, .stLinkButton > a {{ background: transparent !important; color: #A2D2FF !important; border: 1px solid #A2D2FF !important; border-radius: 10px !important; font-weight: 700 !important; transition: 0.3s; text-decoration: none !important; display: flex; justify-content: center; }}
    div.stButton > button:hover, .stLinkButton > a:hover {{ background: rgba(162, 210, 255, 0.15) !important; transform: translateY(-2px); }}
    </style>
    """, unsafe_allow_html=True)
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
        
        category = "🗳️ 일반 투표"
        if any(k in full_text for k in ["M카", "음방", "인가", "뮤뱅"]): category = "🎙️ 음악방송"
        elif any(k in full_text for k in ["Awards", "시상식"]): category = "🏆 시상식"
        elif any(k in full_text for k in ["광고", "생일"]): category = "🎨 광고/시안"
        
        detected_date = extract_date_from_text(full_text)
        clean_text = full_text.split('|')[0][:37] + "..." if len(full_text) > 40 else full_text
        return {"cat": category, "text": clean_text, "date": detected_date}
    except:
        return {"cat": "🗳️ 일반 투표", "text": "", "date": datetime.now().date()}
# 사이드바 메뉴 및 메인 타이틀
with st.sidebar:
    st.markdown(f'<img src="{PLLI_LOGO}" style="border-radius:50%; width:100px; margin: 0 auto; display:block; border: 2px solid #A2D2FF;">', unsafe_allow_html=True)
    menu = st.radio("MENU", ["📊 전체 보드", "🎨 광고/시안", "📻 라디오 신청", "💬 커뮤니티"], label_visibility="collapsed")

st.markdown("<h1 class='main-title'>PLLI CONNECT</h1>", unsafe_allow_html=True)

# 데이터 로드
raw_df = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet1", ttl="5m")
today = datetime.now().date()
raw_df['end_dt'] = pd.to_datetime(raw_df['end_date'], errors='coerce').dt.date
active_df = raw_df[raw_df['end_dt'] >= today].copy()

if menu in ["📊 전체 보드", "🎨 광고/시안"]:
    # 1. 긴급 전광판
    urgent_items = active_df.sort_values(by='end_dt', ascending=True).head(1)
    if not urgent_items.empty:
        t = urgent_items.iloc[0]
        d_val = (t['end_dt'] - today).days
        st.markdown(f'<div class="urgent-banner"><div style="color: #FF5E57; font-weight:800;">🚨 EMERGENCY</div><div style="font-size:1.5rem; font-weight:700; color:white;">{t["text"]}</div><span style="background:#FF5E57; padding:3px 12px; border-radius:50px; font-size:0.9rem;">{"오늘 마감!" if d_val==0 else f"마감 {d_val}일 전"}</span></div>', unsafe_allow_html=True)
        st.link_button("🔥 지금 바로 화력 집중", t['link'], use_container_width=True)
        st.divider()

    # 2. 스마트 제보/등록
    with st.expander("🚀 초간단 정보 제보/등록"):
        input_url = st.text_input("X(트위터) 링크를 붙여넣으세요")
        if input_url:
            info = smart_parser(input_url)
            with st.form("smart_add"):
                f_cat = st.selectbox("분류", ["🗳️ 일반 투표", "🎙️ 음악방송", "🏆 시상식", "🎨 광고/시안"], index=["🗳️ 일반 투표", "🎙️ 음악방송", "🏆 시상식", "🎨 광고/시안"].index(info['cat']))
                f_text = st.text_input("제목", value=info['text'])
                f_date = st.date_input("마감일", value=info['date'])
                f_pwd = st.text_input("관리자 암호", type="password")
                if st.form_submit_button("등록/제보하기"):
                    new_row = pd.DataFrame([{"category": f_cat, "text": f_text, "end_date": f_date.strftime('%Y-%m-%d'), "link": input_url}])
                    target_ws = "Sheet1" if f_pwd == ADMIN_PASSWORD else "Sheet4"
                    conn.update(spreadsheet=SHEET_URL, worksheet=target_ws, data=new_row)
                    st.success("제보 완료! 💙"); st.rerun()
    # 3. 카드 리스트 출력
    display_df = active_df[active_df['category'].str.contains("광고|시안")].copy() if menu == "🎨 광고/시안" else active_df.copy()
    df_sorted = display_df.sort_values(by='end_dt', ascending=True)
    
    cols = st.columns(2)
    for idx, row in df_sorted.reset_index().iterrows():
        with cols[idx % 2]:
            d_day = (row['end_dt'] - today).days
            st.markdown(f'<div class="tweet-card"><div><span class="category-tag">{row["category"]}</span><span class="d-day-tag">D-{d_day if d_day > 0 else "Day"}</span></div><div class="card-text">{row["text"]}</div></div>', unsafe_allow_html=True)
            if row['link']: st.link_button("🔗 자세히 보기", row['link'], use_container_width=True)

elif menu == "📻 라디오 신청":
    rdf = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet2", ttl="5m")
    for _, row in rdf.iterrows():
        st.markdown(f'<div class="tweet-card"><span class="category-tag">{row["type"]}</span><div class="card-text">{row["name"]}</div></div>', unsafe_allow_html=True)
        st.link_button("신청하러 가기", row['link'], use_container_width=True)

elif menu == "💬 커뮤니티":
    cdf = conn.read(spreadsheet=SHEET_URL, worksheet="Sheet3", ttl="1m")
    with st.form("comm"):
        name = st.text_input("닉네임"); msg = st.text_area("메시지")
        if st.form_submit_button("남기기"):
            new_msg = pd.DataFrame([{"date": datetime.now().strftime('%m/%d %H:%M'), "name": name, "message": msg}])
            conn.update(spreadsheet=SHEET_URL, worksheet="Sheet3", data=pd.concat([cdf, new_msg]))
            st.rerun()
    for _, row in cdf.sort_index(ascending=False).iterrows():
        st.markdown(f'<div class="tweet-card"><strong>{row["name"]}</strong> <small style="color:#BABBBD">({row["date"]})</small><br><div style="margin-top:10px;">{row["message"]}</div></div>', unsafe_allow_html=True)
# --- [5. 투표 앱별 공략 데이터] ---
VOTE_TIPS = {
    "🍇 포도알": [
        "출석 체크와 광고 시청으로 '알'을 모으세요.",
        "팬딩(Fanding) 투표는 마감 직전 화력이 중요합니다.",
        "무료 충전소의 '오늘의 미션'을 적극 활용하세요!"
    ],
    "🏆 팬플러스": [
        "친구와 '투표권 주고받기'를 매일 잊지 마세요 (최대 50명).",
        "캐시 게시판에서 '완료' 인증을 하면 추가 포인트를 줍니다.",
        "생일 투표는 최소 3개월 전부터 모으는 것을 추천해요."
    ],
    "🎙️ 아이돌챔프": [
        "매일 출석 시 'CHAMPIM'이 지급됩니다.",
        "퀴즈를 풀면 대량의 하트를 얻을 수 있으니 공략을 참고하세요.",
        "음악방송(쇼챔) 투표는 매주 정해진 기간에만 열립니다."
    ],
    "🦆 덕애드": [
        "광고 시청 횟수가 많아 노가다가 필요하지만 효율이 좋습니다.",
        "투표권 전송 기능을 통해 총공 계정에 화력을 모을 수 있어요."
    ]
}

# --- [메뉴 추가 시 로직] ---
if menu == "💡 앱별 팁":
    st.subheader("💡 투표 앱별 효율 극대화 꿀팁")
    st.info("플리들의 화력을 1%라도 더 끌어올리기 위한 가이드입니다! 💙")
    
    for app, tips in VOTE_TIPS.items():
        with st.expander(f"{app} 공략 보기"):
            for tip in tips:
                st.write(f"• {tip}")
            
    st.divider()
    st.warning("⚠️ **주의사항**: 투표 앱의 정책은 수시로 변경될 수 있으니 공식 공지를 항상 확인해 주세요!")
