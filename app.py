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

@st.cache_data(ttl=300)
def load_sheet(sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    r = requests.get(url, timeout=10)
    df = pd.read_csv(StringIO(r.text), header=None)
    return df

@st.cache_data(ttl=300)
def load_data():
    df_sales_raw = load_sheet("sales")
    df_cost_raw  = load_sheet("cost")

    def safe_sum(df_slice):
        return (df_slice
                .replace({',': ''}, regex=True)
                .apply(pd.to_numeric, errors='coerce')
                .fillna(0)
                .sum(axis=1)
                .reset_index(drop=True))

    # ✅ 행 인덱스 1부터 (0행은 헤더)
    sales = df_sales_raw.iloc[1:].reset_index(drop=True)
    cost  = df_cost_raw.iloc[1:].reset_index(drop=True)

    # 기본 정보 컬럼 (0~8)
    df_base = sales.iloc[:, 0:9].copy()
    df_base.columns = ['부문','지역','팀','파트','점포유형','최초코드','현재코드','점포명','점포수']

    # sales: 전체 일매출
    # 컬럼 9~11  : 25년 3개월 전체
    # 컬럼 12~14 : 26년 3개월 전체
    # 컬럼 15~17 : 25년 FF 3개월
    # 컬럼 18~20 : 26년 FF 3개월
    df_base['총매출_25']   = safe_sum(sales.iloc[:, 9:12])
    df_base['총매출_26']   = safe_sum(sales.iloc[:, 12:15])
    df_base['FF총매출_25'] = safe_sum(sales.iloc[:, 15:18])
    df_base['FF총매출_26'] = safe_sum(sales.iloc[:, 18:21])

    # 품목별 (기존 코드 인덱스 유지)
    df_base['도시락_25']         = safe_sum(sales.iloc[:, [21,26,31]])
    df_base['도시락_26']         = safe_sum(sales.iloc[:, [36,41,46]])
    df_base['김밥_25']           = safe_sum(sales.iloc[:, [22,27,32]])
    df_base['김밥_26']           = safe_sum(sales.iloc[:, [37,42,47]])
    df_base['주먹밥_25']         = safe_sum(sales.iloc[:, [23,28,33]])
    df_base['주먹밥_26']         = safe_sum(sales.iloc[:, [38,43,48]])
    df_base['햄버거샌드위치_25'] = safe_sum(sales.iloc[:, [24,29,34]])
    df_base['햄버거샌드위치_26'] = safe_sum(sales.iloc[:, [39,44,49]])
    df_base['FF간편식_25']       = safe_sum(sales.iloc[:, [25,30,35]])
    df_base['FF간편식_26']       = safe_sum(
