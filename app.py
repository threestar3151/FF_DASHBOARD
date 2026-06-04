# 임시 디버깅 - 문제 확인 후 삭제
import streamlit as st
import requests
from io import StringIO
import pandas as pd

st.set_page_config(page_title="디버그", layout="wide")

SPREADSHEET_ID = "1AnT3gDAfx2cGhTCklDerm-gQsbcZWuzH7-mJ-gTpDf4"

st.write("### 🔍 연결 테스트")

for sheet in ["sales", "cost"]:
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet}"
    try:
        r = requests.get(url, timeout=10)
        st.write(f"**{sheet}** 상태코드: {r.status_code}")
        if r.status_code == 200:
            df = pd.read_csv(StringIO(r.text), header=None)
            st.write(f"→ 행 {len(df)}개, 열 {len(df.columns)}개 로딩 성공 ✅")
            st.write(df.iloc[:3, :10])  # 상위 3행, 10열만 미리보기
        else:
            st.error(f"→ 실패: {r.text[:200]}")
    except Exception as e:
        st.error(f"→ 예외 발생: {e}")

st.stop()
import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from io import StringIO

SPREADSHEET_ID = "1AnT3gDAfx2cGhTCklDerm-gQsbcZWuzH7-mJ-gTpDf4"

st.set_page_config(page_title="GS25 FF 실적 대시보드", page_icon="🏪", layout="wide")

# 비밀번호 잠금
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 GS25 FF 분석 시스템")
    st.markdown("보안을 위해 비밀번호를 입력해주세요.")
    pwd = st.text_input("비밀번호", type="password")
    if st.button("접속하기"):
        if pwd == "gs25":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("비밀번호가 틀렸습니다.")
    st.stop()

# 데이터 로딩 (requests 방식 - secrets 불필요)
@st.cache_data(ttl=300)
def load_sheet(sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    r = requests.get(url)
    if r.status_code != 200:
        st.error(f"🚨 '{sheet_name}' 탭을 불러오지 못했습니다. 시트 공유 설정을 확인해주세요.")
        st.stop()
    df = pd.read_csv(StringIO(r.text), header=None)
    return df

@st.cache_data(ttl=300)
def load_data():
    df_sales_raw = load_sheet("sales")
    df_cost_raw  = load_sheet("cost")

    def safe_sum(df_slice):
        return df_slice.replace({',': ''}, regex=True).apply(pd.to_numeric, errors='coerce').fillna(0).sum(axis=1)

    # 기본 정보 (행 인덱스 2부터, 컬럼 0~8)
    df_base = df_sales_raw.iloc[2:, 0:9].copy()
    df_base.columns = ['부문','지역','팀','파트','점포유형','최초코드','현재코드','점포명','점포수']
    df_base = df_base.reset_index(drop=True)

    # sales 탭: 스크린샷 기준 컬럼 매핑
    # J~L (idx 9~11
