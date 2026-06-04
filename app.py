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
    df_base['FF간편식_26']       = safe_sum(sales.iloc[:, [40,45,50]])

    # cost: 열 69개 기준
    # cost 탭 헤더 확인 결과: 202503 도시락 매입원가부터 시작 (컬럼 9~)
    # 매입/매출 짝 구조: 매입(홀수), 매출(짝수) 형태로 추정
    buy_cols_25  = list(range(9, 39, 2))   # 9,11,13,...,37 (15개)
    sell_cols_25 = list(range(10, 40, 2))  # 10,12,14,...,38 (15개)
    buy_cols_26  = list(range(39, 69, 2))  # 39,41,43,...,67 (15개)
    sell_cols_26 = list(range(40, 70, 2))  # 40,42,44,...,68 (15개)

    df_base['매입원가_25'] = safe_sum(cost.iloc[:, buy_cols_25])
    df_base['매출원가_25'] = safe_sum(cost.iloc[:, sell_cols_25])
    df_base['매입원가_26'] = safe_sum(cost.iloc[:, buy_cols_26])
    df_base['매출원가_26'] = safe_sum(cost.iloc[:, sell_cols_26])

    return df_base

try:
    df = load_data()
except Exception as e:
    st.error(f"데이터 로딩 오류: {e}")
    st.stop()

# 요약 인사이트
st.title("🚀 FF 봄 시즌 요약 및 6월 전략")
st.info("""
**💡 전체 현황 요약 (경영주 안내용)**
1. **매출과 이익 동시 상승:** 봄 시즌 FF 일매출은 전년 대비 **16.4% 올랐고**, 판매율(마진)은 **2.1%p 개선**되어 버리는 폐기가 줄었습니다.
2. **타겟팅 포인트:** '아파트 상권'은 **FF간편식(+33.7%)**, '소가구 상권'은 **도시락(+22.3%)**이 압도적으로 잘 팔립니다.
3. **🚨 주의할 점:** 매출은 오르는데 FF만 떨어지는 점포는 발주 자체가 줄어든 경우입니다. 발주부터 늘리라고 지도하세요.
""")
st.divider()

# 파트 및 점포 선택
st.subheader("🎯 점포별 진단 및 액션 플랜")
col1, col2 = st.columns(2)
with col1:
    part_list = sorted(df['파트'].dropna().unique().tolist())
    selected_part = st.selectbox("👤 파트 선택", part_list)
with col2:
    store_list = df[df['파트'] == selected_part]['점포명'].dropna().unique().tolist()
    selected_store = st.selectbox("🏬 점포 선택", store_list)

store_data = df[(df['파트'] == selected_part) & (df['점포명'] == selected_store)].iloc[0]

def calc_pct(v25, v26): return ((v26 / v25) - 1) * 100 if v25 > 0 else 0

yoy_total     = calc_pct(store_data['총매출_25'], store_data['총매출_26'])
yoy_ff        = calc_pct(store_data['FF총매출_25'], store_data['FF총매출_26'])
yoy_buy       = calc_pct(store_data['매입원가_25'], store_data['매입원가_26'])
sales_rate_25 = (store_data['매출원가_25'] / store_data['매입원가_25']) * 100 if store_data['매입원가_25'] > 0 else 0
sales_rate_26 = (store_data['매출원가_26'] / store_data['매입원가_26']) * 100 if store_data['매입원가_26'] > 0 else 0
rate_diff     = sales_rate_26 - sales_rate_25

st.markdown(f"#### 📊 {selected_store} 점포 실적 (상권: {store_data['점포유형']})")
m1, m2, m3 = st.columns(3)
m1.metric("점포 일매출 YOY", f"{store_data['총매출_26']:,.0f}원", f"{yoy_total:.1f}%")
m2.metric("FF 일매출 YOY",   f"{store_data['FF총매출_26']:,.0f}원", f"{yoy_ff:.1f}%")
m3.metric("FF 판매율 변동",  f"{sales_rate_26:.1f}%", f"{rate_diff:.1f}%p")

st.markdown("##### 💡 매니저 진단 및 6월 가이드")
if yoy_total > 2.0 and yoy_ff < -1.0:
    if yoy_buy < 0:
        st.error(f"🚨 **[진단]** 점포 매출은 잘 나오는데 FF만 역성장입니다. 작년보다 발주를 **{abs(yoy_buy):.1f}%** 덜 넣고 있기 때문입니다.\n\n👉 **[액션]** 도시락/주먹밥 발주부터 정상화하세요.")
    else:
        st.warning(f"⚠️ **[진단]** 발주는 넣는데 팔리질 않아 판매율이 {rate_diff:.1f}%p 떨어졌습니다.\n\n👉 **[액션]** 안 팔리는 구색은 줄이고 FF간편식(냉장면 등)으로 매대를 바꾸세요.")
elif yoy_ff > 10.0 and rate_diff > 0.5:
    st.success(f"🌟 **[진단]** 매출도 {yoy_ff:.1f}% 올랐고 판매율도 좋아진 훌륭한 점포입니다.\n\n👉 **[액션]** 프리미엄 도시락·신상 FF간편식을 전면에 내세워 이익을 극대화하세요.")
elif yoy_ff > 0 and rate_diff < -3.0:
    st.warning(f"⚠️ **[진단]** 매출은 올랐지만 판매율이 {abs(rate_diff):.1f}%p 나빠져 폐기가 많습니다.\n\n👉 **[액션]** 잘 나가는 김밥·FF간편식 위주로 발주하세요.")
else:
    st.info(f"📊 **[진단]** 작년과 비슷하게 유지 중입니다.\n\n👉 **[액션]** 초여름 비수기 대비해 면류·샐러드 등 하절기 FF간편식을 늘리세요.")

st.markdown("##### 📈 품목별 매출 상세비교")
categories = ['도시락','김밥','주먹밥','햄버거/샌드위치','FF간편식']
sales_25 = [store_data['도시락_25'], store_data['김밥_25'], store_data['주먹밥_25'], store_data['햄버거샌드위치_25'], store_data['FF간편식_25']]
sales_26 = [store_data['도시락_26'], store_data['김밥_26'], store_data['주먹밥_26'], store_data['햄버거샌드위치_26'], store_data['FF간편식_26']]

df_chart = pd.DataFrame({
    '품목': categories * 2,
    '매출': sales_25 + sales_26,
    '년도': ['2025년']*5 + ['2026년']*5
})
fig = px.bar(df_chart, x='품목', y='매출', color='년도', barmode='group',
             color_discrete_sequence=['#CCCCCC','#005EA6'])
fig.update_layout(xaxis_title=None, yaxis_title=None,
                  legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
st.plotly_chart(fig, use_container_width=True)
