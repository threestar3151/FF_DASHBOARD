import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# ==============================================================================
# [설정] 여기에 구글 스프레드시트의 '웹에 공유된 링크' 또는 '스프레드시트 URL'을 입력하세요.
# 서비스 계정이 뷰어 권한으로 접근할 수 있어야 합니다.
# ==============================================================================
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1AnT3gDAfx2cGhTCklDerm-gQsbcZWuzH7-mJ-gTpDf4/edit?usp=sharing"

# 1. 페이지 설정 (모바일 화면 최적화)
st.set_page_config(page_title="GS25 FF 실적 대시보드", page_icon="🏪", layout="wide")

# 2. 보안 기능: 암호 입력 ('gs25')
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 GS25 FF 분석 시스템 로그인")
    st.markdown("모바일/PC 보안 인증이 필요합니다.")
    pwd = st.text_input("비밀번호를 입력하세요", type="password")
    
    if st.button("인증하기"):
        if pwd == "gs25":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("비밀번호가 틀렸습니다. 다시 입력해주세요.")
    st.stop()

# 3. 데이터 로딩 (구글 스프레드시트 연동 및 캐싱)
@st.cache_data(ttl=600) # 10분 데이터 캐싱 유지
def load_gsheets_data(url):
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # 구글 시트에서 각각의 워크시트 로드 (시트명이 일치해야 합니다)
    df_sales_raw = conn.read(spreadsheet=url, worksheet="일매출")
    df_cost_raw = conn.read(spreadsheet=url, worksheet="매입매출")
    
    # --- [데이터 전처리 및 정제] ---
    # 구글 시트 read 시 첫 행이 컬럼명으로 잡히므로 일관된 인덱싱 적용
    # df_sales_raw.iloc[0] = 전체/FF분류행, iloc[1] = 부문/지역/파트 헤더행
    
    # 기본 점포 정보 추출
    df_base = df_sales_raw.iloc[2:, 0:9].copy()
    df_base.columns = ['부문', '지역', '팀', '파트', '점포유형', '최초코드', '현재코드', '점포명', '점포수']
    
    # 매출 데이터 정형화 및 합산
    df_base['총매출_25'] = df_sales_raw.iloc[2:, 9:12].astype(float).sum(axis=1)
    df_base['총매출_26'] = df_sales_raw.iloc[2:, 12:15].astype(float).sum(axis=1)
    df_base['FF총매출_25'] = df_sales_raw.iloc[2:, 15:18].astype(float).sum(axis=1)
    df_base['FF총매출_26'] = df_sales_raw.iloc[2:, 18:21].astype(float).sum(axis=1)
    
    # 카테고리별 매출 정형화 ('FF간편식' 반영)
    df_base['도시락_25'] = df_sales_raw.iloc[2:, [21, 26, 31]].astype(float).sum(axis=1)
    df_base['도시락_26'] = df_sales_raw.iloc[2:, [36, 41, 46]].astype(float).sum(axis=1)
    df_base['김밥_25'] = df_sales_raw.iloc[2:, [22, 27, 32]].astype(float).sum(axis=1)
    df_base['김밥_26'] = df_sales_raw.iloc[2:, [37, 42, 47]].astype(float).sum(axis=1)
    df_base['주먹밥_25'] = df_sales_raw.iloc[2:, [23, 28, 33]].astype(float).sum(axis=1)
    df_base['주먹밥_26'] = df_sales_raw.iloc[2:, [38, 43, 48]].astype(float).sum(axis=1)
    df_base['햄버거샌드위치_25'] = df_sales_raw.iloc[2:, [24, 29, 34]].astype(float).sum(axis=1)
    df_base['햄버거샌드위치_26'] = df_sales_raw.iloc[2:, [39, 44, 49]].astype(float).sum(axis=1)
    df_base['FF간편식_25'] = df_sales_raw.iloc[2:, [25, 30, 35]].astype(float).sum(axis=1)
    df_base['FF간편식_26'] = df_sales_raw.iloc[2:, [40, 45, 50]].astype(float).sum(axis=1)
    
    # 원가 데이터 인덱싱 매핑
    buy_cols_25, sell_cols_25 = [9,11,13,15,17, 19,21,23,25,27, 29,31,33,35,37], [10,12,14,16,18, 20,22,24,26,28, 30,32,34,36,38]
    buy_cols_26, sell_cols_26 = [39,41,43,45,47, 49,51,53,55,57, 59,61,63,65,67], [40,42,44,46,48, 50,52,54,56,58, 60,62,64,66,68]
    
    df_base['매입원가_25'] = df_cost_raw.iloc[2:, buy_cols_25].astype(float).sum(axis=1)
    df_base['매출원가_25'] = df_cost_raw.iloc[2:, sell_cols_25].astype(float).sum(axis=1)
    df_base['매입원가_26'] = df_cost_raw.iloc[2:, buy_cols_26].astype(float).sum(axis=1)
    df_base['매출원가_26'] = df_cost_raw.iloc[2:, sell_cols_26].astype(float).sum(axis=1)
    
    return df_base

# 데이터 로딩 실행
try:
    df = load_gsheets_data(SPREADSHEET_URL)
except Exception as e:
    st.error(f"구글 시트 연동 실패: URL 주소나 시트 권한 설정을 확인하세요. (오류 내용: {e})")
    st.stop()

# 4. 상단 고정: 전체 봄 시즌 최종 인사이트 요약
st.title("🚀 FF 봄 시즌 성과 최종 요약 및 6월 가이드")
st.info("""
**💡 전체 상권 종합 진단 보고**
1. **외형 & 효율 동시 달성:** 봄 시즌 FF 매출은 전년 동기 대비 **16.4% 대폭 성장**했으며, 단순 발주 밀어내기가 아닌 순수 판매 증가로 인해 **판매율이 2.1%p 개선(폐기율 감소)**되었습니다.
2. **상권 타겟팅 핵심 지표:** '아파트 주거' 상권은 **FF간편식(+33.7%)**이 성장을 완전히 독주 중이며, '소가구 주거' 상권은 **도시락(+22.3%)**이 성장을 리드하고 있습니다. 
3. **⚠️ 다각도 원인 파악 가이드:** * **[총매출 증가 / FF매출 감소]** 점포는 객수가 늘어남에도 FF 진열 가판대가 비어 기회로스가 난 경우입니다. 원인을 뜯어보면 **매입원가(발주량) 자체가 줄어든 것**이 주 원인입니다. 6월 즉시 발주량 복구가 정답입니다.
   * **[FF매출 증가 / 판매율 급락]** 점포는 무리한 과발주로 폐기 폭탄을 맞고 있는 상태입니다. 회전율이 낮은 비주력 구색을 축소하고 회전 속도가 빠른 핵심 상품 위주로 압축 발주해야 합니다.
""")

st.divider()

# 5. 파트 / 점포 선택 UI (입력 및 드롭다운 검색 기능)
st.subheader("🎯 점포별 다각도 원인 분석 및 맞춤 처방")

col1, col2 = st.columns(2)
with col1:
    part_list = sorted(df['파트'].dropna().unique().tolist())
    selected_part = st.selectbox("👤 담당 파트 선택 (입력하여 검색 가능)", part_list)

with col2:
    store_list = df[df['파트'] == selected_part]['점포명'].dropna().unique().tolist()
    selected_store = st.selectbox("🏬 진단할 점포 선택", store_list)

# 선택 점포 데이터 바인딩
store_data = df[(df['파트'] == selected_part) & (df['점포명'] == selected_store)].iloc[0]

# 증감 지표 연산 함수
def calc_pct(v25, v26):
    return ((v26 / v25) - 1) * 100 if v25 > 0 else 0

yoy_total = calc_pct(store_data['총매출_25'], store_data['총매출_26'])
yoy_ff = calc_pct(store_data['FF총매출_25'], store_data['FF총매출_26'])
yoy_buy = calc_pct(store_data['매입원가_25'], store_data['매입원가_26'])

sales_rate_25 = (store_data['매출원가_25'] / store_data['매입원가_25']) * 100 if store_data['매입원가_25'] > 0 else 0
sales_rate_26 = (store_data['매출원가_26'] / store_data['매입원가_26']) * 100 if store_data['매입원가_26'] > 0 else 0
rate_diff = sales_rate_26 - sales_rate_25

# 6. 모바일 UI 최적화 메트릭 대시보드
st.markdown(f"#### 📊 {selected_store} 실적 진단 현황 (상권형태: {store_data['점포유형']})")
m_col1, m_col2, m_col3 = st.columns(3)
m_col1.metric("점포 총매출 YOY", f"{store_data['총매출_26']:,.0f}원", f"{yoy_total:.1f}%")
m_col2.metric("FF 일매출 YOY", f"{store_data['FF총매출_26']:,.0f}원", f"{yoy_ff:.1f}%")
m_col3.metric("FF 판매율 변동", f"{sales_rate_26:.1f}%", f"{rate_diff:.1f}%p", delta_color="normal")

# 7. 다각도 매칭 엔진을 활용한 6월 실적 향상 맞춤형 진단 및 처방
st.markdown("##### 💡 6월 실적 개선을 위한 매니저 액션 가이드")

if yoy_total > 2.0 and yoy_ff < -1.0:
    if yoy_buy < 0:
        st.error(f"🚨 **[원인 분석]** 점포 전체 매출은 {yoy_total:.1f}% 성장세이나, FF 매출만 {yoy_ff:.1f}%로 역성장 중입니다. 세부 지표를 파악한 결과, **FF 매입원가(발주량)가 전년비 {abs(yoy_buy):.1f}%나 감소한 것이 핵심 원인**입니다. 객수가 늘어날 때 정작 FF 상품이 없어 로스가 나고 있습니다.\n\n👉 **[6월 액션 플랜]** 경영주에게 매입 감소 지표를 제시하며 피크타임(11~13시, 18~20시) 도시락과 주먹밥 발주량을 작년 수준 이상으로 복구하도록 강력히 권고하세요.")
    else:
        st.warning(f"⚠️ **[원인 분석]** 전체 매출은 증가 중이나 FF 매출이 부진합니다. 발주(매입원가)는 유지되고 있으나 판매율이 {rate_diff:.1f}%p 하락했습니다. 이는 유통기한 경과로 인한 폐기 관리가 안 되거나, 비선호 상품 진열 비중이 높은 상태입니다.\n\n👉 **[6월 액션 플랜]** 6월 기온 상승에 대비해 폐기 리스크가 적고 트렌디한 **FF간편식** 위주로 진열 구색을 빠르게 전환하고 타임세일을 적극 활용해야 합니다.")
elif yoy_ff > 10.0 and rate_diff > 0.5:
    st.success(f"🌟 **[원인 분석]** FF 매출이 {yoy_ff:.1f}% 폭발적으로 증가함과 동시에, 판매율이 {rate_diff:.1f}%p 상승한 초우수 점포입니다. 발주를 공격적으로 늘려 진열 볼륨을 키운 것이 정석대로 판매 극대화와 폐기 감축의 선순환을 만들었습니다.\n\n👉 **[6월 액션 플랜]** 현재 상권({store_data['점포유형']})의 객수 파워가 증명되었습니다. 6월에는 단가가 높은 고부가가치 신상품 도시락과 조리면을 매대 전면에 적극 복수 진열하여 매출 기여도를 최고조로 끌어올리세요.")
elif yoy_ff > 0 and rate_diff < -3.0:
    st.warning(f"⚠️ **[원인 분석]** FF 매출은 전년 대비 늘었으나, 판매율이 {rate_diff:.1f}%p 크게 후퇴했습니다. 무리하게 발주 볼륨만 키워 점포의 폐기 손실 부담이 가중되고 있어 경영주 반발이 우려됩니다.\n\n👉 **[6월 액션 플랜]** 매출 비중이 낮은 조리빵이나 샌드위치류 구색은 최하단으로 압축하고, 안정적인 회전율을 보이는 **FF간편식**과 김밥류 위주로 발주 포트폴리오를 슬림화하여 마진을 방어하세요.")
else:
    st.info(f"📊 **[원인 분석]** 전년과 유사한 안정적인 흐름을 유지하고 있습니다. 현재 상태를 유지하되 여름철 비수기 카테고리 진입에 방어가 필요합니다.\n\n👉 **[6월 액션 플랜]** 6월 초여름 시즌에 맞춰 면류, 샐러드 등 하절기 전용 **FF간편식** 라인업의 진열 면적을 선제적으로 넓혀 매출을 점진적으로 부스팅하세요.")

# 8. 카테고리별 매출 시각화 (모바일 터치 및 확인에 유용한 바 차트)
st.markdown("##### 📈 카테고리별 매출 상세 비교 (원)")
categories = ['도시락', '김밥', '주먹밥', '햄버거/샌드위치', 'FF간편식']
sales_25 = [store_data['도시락_25'], store_data['김밥_25'], store_data['주먹밥_25'], store_data['햄버거샌드위치_25'], store_data['FF간편식_25']]
sales_26 = [store_data['도시락_26'], store_data['김밥_26'], store_data['주먹밥_26'], store_data['햄버거샌드위치_26'], store_data['FF간편식_26']]

df_chart = pd.DataFrame({
    '카테고리': categories * 2,
    '일매출합계': sales_25 + sales_26,
    '구분': ['2025년 봄']*5 + ['2026년 봄']*5
})

fig = px.bar(
    df_chart, x='카테고리', y='일매출합계', color='구분', barmode='group',
    color_discrete_sequence=['#CCCCCC', '#005EA6']
)
fig.update_layout(
    xaxis_title=None, yaxis_title=None,
    margin=dict(l=20, r=20, t=30, b=20),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
st.plotly_chart(fig, use_container_width=True)
