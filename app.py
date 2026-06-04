import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# =========================================================
# 1. 구글시트 URL
# =========================================================
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1AnT3gDAfx2cGhTCklDerm-gQsbcZWuzH7-mJ-gTpDf4/edit?usp=sharing"

# =========================================================
# 2. 기본 설정
# =========================================================
st.set_page_config(
    page_title="GS25 FF 실적 대시보드",
    page_icon="🏪",
    layout="wide"
)

# =========================================================
# 3. 로그인
# =========================================================
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

# =========================================================
# 4. 숫자 변환 함수
# =========================================================
def to_num(data):
    return (
        data.astype(str)
        .replace(",", "", regex=True)
        .replace("-", "0")
        .replace("", "0")
        .apply(pd.to_numeric, errors="coerce")
        .fillna(0)
    )

# =========================================================
# 5. 구글시트 데이터 로딩
# =========================================================
@st.cache_data(ttl=10)
def load_gsheets_data(url):
    conn = st.connection("gsheets", type=GSheetsConnection)

    try:
        df_sales_raw = conn.read(spreadsheet=url, worksheet="일매출")
        df_cost_raw = conn.read(spreadsheet=url, worksheet="매입매출")
    except Exception as e:
        st.error(f"구글시트 연결 실패: {e}")
        st.stop()

    # 기본 점포 정보
    df_base = df_sales_raw.iloc[2:, 0:9].copy()
    df_base.columns = [
        "부문", "지역", "팀", "파트", "점포유형",
        "최초코드", "현재코드", "점포명", "점포수"
    ]

    # 매출 데이터
    df_base["총매출_25"] = to_num(df_sales_raw.iloc[2:, 9:12]).sum(axis=1)
    df_base["총매출_26"] = to_num(df_sales_raw.iloc[2:, 12:15]).sum(axis=1)
    df_base["FF총매출_25"] = to_num(df_sales_raw.iloc[2:, 15:18]).sum(axis=1)
    df_base["FF총매출_26"] = to_num(df_sales_raw.iloc[2:, 18:21]).sum(axis=1)

    # 카테고리별 매출
    df_base["도시락_25"] = to_num(df_sales_raw.iloc[2:, [21, 26, 31]]).sum(axis=1)
    df_base["도시락_26"] = to_num(df_sales_raw.iloc[2:, [36, 41, 46]]).sum(axis=1)

    df_base["김밥_25"] = to_num(df_sales_raw.iloc[2:, [22, 27, 32]]).sum(axis=1)
    df_base["김밥_26"] = to_num(df_sales_raw.iloc[2:, [37, 42, 47]]).sum(axis=1)

    df_base["주먹밥_25"] = to_num(df_sales_raw.iloc[2:, [23, 28, 33]]).sum(axis=1)
    df_base["주먹밥_26"] = to_num(df_sales_raw.iloc[2:, [38, 43, 48]]).sum(axis=1)

    df_base["햄버거샌드위치_25"] = to_num(df_sales_raw.iloc[2:, [24, 29, 34]]).sum(axis=1)
    df_base["햄버거샌드위치_26"] = to_num(df_sales_raw.iloc[2:, [39, 44, 49]]).sum(axis=1)

    df_base["FF간편식_25"] = to_num(df_sales_raw.iloc[2:, [25, 30, 35]]).sum(axis=1)
    df_base["FF간편식_26"] = to_num(df_sales_raw.iloc[2:, [40, 45, 50]]).sum(axis=1)

    # 매입/매출원가
    buy_cols_25 = [9,11,13,15,17,19,21,23,25,27,29,31,33,35,37]
    sell_cols_25 = [10,12,14,16,18,20,22,24,26,28,30,32,34,36,38]

    buy_cols_26 = [39,41,43,45,47,49,51,53,55,57,59,61,63,65,67]
    sell_cols_26 = [40,42,44,46,48,50,52,54,56,58,60,62,64,66,68]

    df_base["매입원가_25"] = to_num(df_cost_raw.iloc[2:, buy_cols_25]).sum(axis=1)
    df_base["매출원가_25"] = to_num(df_cost_raw.iloc[2:, sell_cols_25]).sum(axis=1)
    df_base["매입원가_26"] = to_num(df_cost_raw.iloc[2:, buy_cols_26]).sum(axis=1)
    df_base["매출원가_26"] = to_num(df_cost_raw.iloc[2:, sell_cols_26]).sum(axis=1)

    df_base = df_base.dropna(subset=["파트", "점포명"])

    return df_base

# =========================================================
# 6. 데이터 불러오기
# =========================================================
df = load_gsheets_data(SPREADSHEET_URL)

# =========================================================
# 7. 화면 구성
# =========================================================
st.title("🚀 FF 봄 시즌 요약 및 6월 전략")

st.info("""
**💡 전체 현황 요약**

1. **매출과 이익 동시 상승:** 봄 시즌 FF 일매출은 전년 대비 상승했고, 판매율도 개선되었습니다.  
2. **타겟팅 포인트:** 상권별로 잘 팔리는 FF 카테고리를 확인해 발주 방향을 조정해야 합니다.  
3. **주의 점포:** 총매출은 오르는데 FF만 떨어지는 점포는 발주량 부족 가능성이 높습니다.
""")

st.divider()

# =========================================================
# 8. 점포 선택
# =========================================================
st.subheader("🎯 점포별 진단 및 액션 플랜")

col1, col2 = st.columns(2)

with col1:
    part_list = sorted(df["파트"].dropna().unique().tolist())
    selected_part = st.selectbox("👤 파트 선택", part_list)

with col2:
    store_list = (
        df[df["파트"] == selected_part]["점포명"]
        .dropna()
        .unique()
        .tolist()
    )
    selected_store = st.selectbox("🏬 점포 선택", store_list)

store_data = df[
    (df["파트"] == selected_part) &
    (df["점포명"] == selected_store)
].iloc[0]

# =========================================================
# 9. 계산 함수
# =========================================================
def calc_pct(v25, v26):
    if v25 == 0:
        return 0
    return ((v26 / v25) - 1) * 100

yoy_total = calc_pct(store_data["총매출_25"], store_data["총매출_26"])
yoy_ff = calc_pct(store_data["FF총매출_25"], store_data["FF총매출_26"])
yoy_buy = calc_pct(store_data["매입원가_25"], store_data["매입원가_26"])

sales_rate_25 = (
    store_data["매출원가_25"] / store_data["매입원가_25"] * 100
    if store_data["매입원가_25"] > 0 else 0
)

sales_rate_26 = (
    store_data["매출원가_26"] / store_data["매입원가_26"] * 100
    if store_data["매입원가_26"] > 0 else 0
)

rate_diff = sales_rate_26 - sales_rate_25

# =========================================================
# 10. 점포 요약
# =========================================================
st.markdown(f"#### 📊 {selected_store} 실적 진단")
st.caption(f"상권: {store_data['점포유형']}")

m_col1, m_col2, m_col3 = st.columns(3)

m_col1.metric(
    "점포 일매출 YOY",
    f"{store_data['총매출_26']:,.0f}원",
    f"{yoy_total:.1f}%"
)

m_col2.metric(
    "FF 일매출 YOY",
    f"{store_data['FF총매출_26']:,.0f}원",
    f"{yoy_ff:.1f}%"
)

m_col3.metric(
    "FF 판매율 변동",
    f"{sales_rate_26:.1f}%",
    f"{rate_diff:.1f}%p"
)

# =========================================================
# 11. 자동 진단
# =========================================================
st.markdown("##### 💡 매니저 진단 및 6월 가이드")

if yoy_total > 2.0 and yoy_ff < -1.0:
    if yoy_buy < 0:
        st.error(
            f"🚨 **[진단]** 점포 매출은 성장 중이나 FF 매출은 역성장입니다. "
            f"주요 원인은 FF 발주량이 전년 대비 {abs(yoy_buy):.1f}% 감소했기 때문입니다.\n\n"
            f"👉 **[액션]** 피크타임 도시락, 김밥, 주먹밥 발주량을 우선 복구하세요."
        )
    else:
        st.warning(
            f"⚠️ **[진단]** 발주는 유지되고 있으나 FF 판매율이 {rate_diff:.1f}%p 하락했습니다.\n\n"
            f"👉 **[액션]** 비선호 상품 구색을 줄이고 회전율 높은 상품 중심으로 진열을 조정하세요."
        )

elif yoy_ff > 10.0 and rate_diff > 0.5:
    st.success(
        f"🌟 **[진단]** FF 매출이 {yoy_ff:.1f}% 성장했고 판매율도 개선된 우수 점포입니다.\n\n"
        f"👉 **[액션]** 고단가 신상품과 주력 FF 상품을 전면 진열해 추가 매출을 노리세요."
    )

elif yoy_ff > 0 and rate_diff < -3.0:
    st.warning(
        f"⚠️ **[진단]** FF 매출은 증가했지만 판매율이 {abs(rate_diff):.1f}%p 하락했습니다.\n\n"
        f"👉 **[액션]** 과발주 가능성이 있으므로 회전율 낮은 상품은 줄이고 핵심 상품 위주로 발주하세요."
    )

else:
    st.info(
        f"📊 **[진단]** 전년과 유사한 안정적 흐름입니다.\n\n"
        f"👉 **[액션]** 하절기 FF간편식, 면류, 샐러드류 진열을 선제적으로 확대하세요."
    )

# =========================================================
# 12. 카테고리별 그래프
# =========================================================
st.markdown("##### 📈 품목별 매출 상세 비교")

categories = ["도시락", "김밥", "주먹밥", "햄버거/샌드위치", "FF간편식"]

sales_25 = [
    store_data["도시락_25"],
    store_data["김밥_25"],
    store_data["주먹밥_25"],
    store_data["햄버거샌드위치_25"],
    store_data["FF간편식_25"]
]

sales_26 = [
    store_data["도시락_26"],
    store_data["김밥_26"],
    store_data["주먹밥_26"],
    store_data["햄버거샌드위치_26"],
    store_data["FF간편식_26"]
]

df_chart = pd.DataFrame({
    "품목": categories * 2,
    "매출": sales_25 + sales_26,
    "년도": ["2025년"] * 5 + ["2026년"] * 5
})

fig = px.bar(
    df_chart,
    x="품목",
    y="매출",
    color="년도",
    barmode="group",
    color_discrete_sequence=["#CCCCCC", "#005EA6"]
)

fig.update_layout(
    xaxis_title=None,
    yaxis_title=None,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    )
)

st.plotly_chart(fig, use_container_width=True)
