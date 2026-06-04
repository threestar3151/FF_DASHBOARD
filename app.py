import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# 1. 페이지 설정 (모바일 친화적 화면 구성)
st.set_page_config(page_title="GS25 FF 실적 대시보드", page_icon="🏪", layout="wide")

# 2. 보안: 비밀번호 입력 기능
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 GS25 FF 분석 대시보드")
    st.markdown("보안을 위해 비밀번호를 입력해주세요.")
    pwd = st.text_input("비밀번호", type="password")
    
    if st.button("로그인"):
        if pwd == "gs25":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("비밀번호가 일치하지 않습니다.")
    st.stop() # 인증 전에는 아래 코드가 실행되지 않음

# 3. 데이터 로딩 (구글 스프레드시트 연동)
@st.cache_data
def load_data_from_gsheets():
    # Streamlit 클라우드의 Secrets에 등록된 인증 정보를 자동으로 사용하여 연결합니다.
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # 구글 스프레드시트 파일의 URL 주소를 입력합니다.
    # (주의: 서비스 계정 이메일에 '편집자' 또는 '뷰어' 권한이 공유되어 있어야 합니다)
    spreadsheet_url = "https://docs.google.com/spreadsheets/d/시트_고유_ID_입력/edit#gid=0"
    
    # 첫 번째 시트(일매출)와 두 번째 시트(매입매출)를 각각 읽어옵니다.
    df_sales = conn.read(spreadsheet=spreadsheet_url, worksheet="Sheet1") # 일매출 시트명
    df_cost = conn.read(spreadsheet=spreadsheet_url, worksheet="Sheet2")  # 매입매출 시트명
    
    # 원본 데이터 로드 (첫 3행은 헤더/메타데이터)
    df_sales = pd.read_excel(sales_file, header=None)
    df_cost = pd.read_excel(cost_file, header=None)
    
    # 기본 정보 (점포명, 파트 등) 추출
    df_base = df_sales.iloc[3:, 0:9].copy()
    df_base.columns = ['부문', '지역', '팀', '파트', '점포유형', '최초코드', '현재코드', '점포명', '점포수']
    
    # 매출 데이터 추출 ('25년 3~5월 vs '26년 3~5월)
    df_base['총매출_25'] = df_sales.iloc[3:, 9:12].astype(float).sum(axis=1)
    df_base['총매출_26'] = df_sales.iloc[3:, 12:15].astype(float).sum(axis=1)
    df_base['FF총매출_25'] = df_sales.iloc[3:, 15:18].astype(float).sum(axis=1)
    df_base['FF총매출_26'] = df_sales.iloc[3:, 18:21].astype(float).sum(axis=1)
    
    # 카테고리별 매출 ('25 vs '26)
    df_base['도시락_25'] = df_sales.iloc[3:, [21, 26, 31]].astype(float).sum(axis=1)
    df_base['도시락_26'] = df_sales.iloc[3:, [36, 41, 46]].astype(float).sum(axis=1)
    df_base['김밥_25'] = df_sales.iloc[3:, [22, 27, 32]].astype(float).sum(axis=1)
    df_base['김밥_26'] = df_sales.iloc[3:, [37, 42, 47]].astype(float).sum(axis=1)
    df_base['주먹밥_25'] = df_sales.iloc[3:, [23, 28, 33]].astype(float).sum(axis=1)
    df_base['주먹밥_26'] = df_sales.iloc[3:, [38, 43, 48]].astype(float).sum(axis=1)
    df_base['햄버거샌드위치_25'] = df_sales.iloc[3:, [24, 29, 34]].astype(float).sum(axis=1)
    df_base['햄버거샌드위치_26'] = df_sales.iloc[3:, [39, 44, 49]].astype(float).sum(axis=1)
    df_base['FF간편식_25'] = df_sales.iloc[3:, [25, 30, 35]].astype(float).sum(axis=1)
    df_base['FF간편식_26'] = df_sales.iloc[3:, [40, 45, 50]].astype(float).sum(axis=1)
    
    # 원가 데이터 추출 (매입원가 / 매출원가)
    buy_cols_25 = [9,11,13,15,17, 19,21,23,25,27, 29,31,33,35,37]
    sell_cols_25 = [10,12,14,16,18, 20,22,24,26,28, 30,32,34,36,38]
    buy_cols_26 = [39,41,43,45,47, 49,51,53,55,57, 59,61,63,65,67]
    sell_cols_26 = [40,42,44,46,48, 50,52,54,56,58, 60,62,64,66,68]
    
    df_base['매입원가_25'] = df_cost.iloc[3:, buy_cols_25].astype(float).sum(axis=1)
    df_base['매출원가_25'] = df_cost.iloc[3:, sell_cols_25].astype(float).sum(axis=1)
    df_base['매입원가_26'] = df_cost.iloc[3:, buy_cols_26].astype(float).sum(axis=1)
    df_base['매출원가_26'] = df_cost.iloc[3:, sell_cols_26].astype(float).sum(axis=1)
    
    return df_base

# 데이터 불러오기
try:
    df = load_data()
except Exception as e:
    st.error("데이터 파일을 읽는 중 오류가 발생했습니다. 'FF 분석(일매출)_0604.xlsx' 및 'FF 분석(매입매출)_0604.xlsx' 파일이 폴더에 있는지 확인해주세요.")
    st.stop()

# 4. 상단 고정: 전체 핵심 인사이트 요약
st.title("🏪 FF 봄 시즌(3~5월) 실적 리뷰 및 6월 전략")

st.info("""
**💡 FF 카테고리 종합 분석 및 다각도 원인 파악 (경영주 안내용 핵심 요약)**

1. **외형 성장 및 마진율 동시 개선:** 전체 점포 기준, FF 매출은 전년 대비 **16.4% 성장**했으며 판매율(매입 대비 매출원가 비중)은 **2.1%p 상승**했습니다. 이는 단순 밀어넣기식 발주가 아닌, 실질적인 고객 수요가 늘어 폐기 손실이 줄고 마진이 개선되었음을 의미합니다.
2. **상권별 맞춤형 진단:** '아파트 주거' 상권은 **FF간편식(33.7% 증가)**의 성장이 압도적이며, '소가구 주거' 상권은 **도시락(22.3% 증가)** 수요가 폭발하고 있습니다. 상권별 핀셋 구색 강화가 6월 매출의 핵심입니다.
3. **⚠️ 이상 징후 다각도 파악 (주의 구간):**
   * **[점포 전체 매출 증가 / FF 매출 감소] 발생 시:** 대부분 **'매입원가(발주량)' 자체가 전년 대비 축소**된 것이 주원인입니다. 타 카테고리(주류/스낵 등)에 집중하느라 FF 진열장(쇼케이스)의 골든타임 재고가 비어있을 확률이 높으므로, 발주량 복구가 최우선입니다.
   * **[FF 매출 증가 / 매입원가 폭증(판매율 하락)] 발생 시:** 무리한 발주로 폐기가 급증한 경우입니다. 요일별, 시간대별 타임세일 적극 유도 및 FF간편식 등 보존기한이 상대적으로 긴 상품으로 포트폴리오를 조정해야 합니다.
""")

st.divider()

# 5. 파트 및 점포 선택 UI (모바일 친화적 Selectbox)
st.subheader("🎯 담당 점포별 상세 진단")

col1, col2 = st.columns(2)
with col1:
    # 파트명 드롭다운 (결측치 제외 및 오름차순 정렬)
    part_list = sorted(df['파트'].dropna().unique().tolist())
    selected_part = st.selectbox("👤 파트를 선택하세요 (입력하여 검색 가능)", part_list)

with col2:
    # 선택된 파트의 점포 리스트
    store_list = df[df['파트'] == selected_part]['점포명'].dropna().unique().tolist()
    selected_store = st.selectbox("🏬 점포를 선택하세요", store_list)

# 6. 선택된 점포 데이터 필터링
store_data = df[(df['파트'] == selected_part) & (df['점포명'] == selected_store)].iloc[0]

# 증감률 계산 함수
def calc_yoy(val25, val26):
    if val25 == 0: return 0
    return ((val26 / val25) - 1) * 100

# 점포 지표 계산
yoy_total = calc_yoy(store_data['총매출_25'], store_data['총매출_26'])
yoy_ff = calc_yoy(store_data['FF총매출_25'], store_data['FF총매출_26'])
yoy_buy = calc_yoy(store_data['매입원가_25'], store_data['매입원가_26'])

sales_rate_25 = (store_data['매출원가_25'] / store_data['매입원가_25']) * 100 if store_data['매입원가_25'] > 0 else 0
sales_rate_26 = (store_data['매출원가_26'] / store_data['매입원가_26']) * 100 if store_data['매입원가_26'] > 0 else 0
rate_diff = sales_rate_26 - sales_rate_25

# 7. 모바일 UI 대시보드 - KPI 메트릭 표시
st.markdown(f"### {selected_store} 점포 실적 요약 (상권: {store_data['점포유형']})")
metric_col1, metric_col2, metric_col3 = st.columns(3)

metric_col1.metric("총 일매출 YOY", f"{store_data['총매출_26']:,.0f}원", f"{yoy_total:.1f}%")
metric_col2.metric("FF 일매출 YOY", f"{store_data['FF총매출_26']:,.0f}원", f"{yoy_ff:.1f}%")
metric_col3.metric("FF 판매율 (매출/매입)", f"{sales_rate_26:.1f}%", f"{rate_diff:.1f}%p")

# 8. 맞춤형 인사이트 및 6월 액션 플랜 자동 생성 (다각도 진단)
st.subheader("💡 6월 매출 증대를 위한 자동 진단 리포트")

insight_text = ""
if yoy_total > 0 and yoy_ff < 0:
    if yoy_buy < 0:
        insight_text = f"🚨 **[진단] 점포 전체 매출은 성장({yoy_total:.1f}%)하고 있으나, FF 카테고리(-{abs(yoy_ff):.1f}%)만 역성장 중입니다.**\n\n다각도로 원인을 분석한 결과, **FF 매입원가(발주량) 자체가 전년 대비 {abs(yoy_buy):.1f}% 감소**한 것이 주된 원인입니다. 객수가 늘어나고 있음에도 FF 쇼케이스 결품으로 기회로스를 내고 있습니다. 6월에는 주력 시간대(점심/저녁) **도시락과 주먹밥 발주량을 즉시 복구(증대)**하도록 경영주와 협의해야 합니다."
    else:
        insight_text = f"🚨 **[진단] 점포 전체 매출은 성장({yoy_total:.1f}%)하나, FF 카테고리(-{abs(yoy_ff):.1f}%)는 부진합니다.**\n\n발주량(매입원가)은 유지/증가했으나 고객의 선택을 받지 못하고 있습니다. 폐기 방어를 위해 타임세일(마감할인) 활용도를 점검하고, 고객 동선 내에 FF 매대가 가려져 있는지 진열 상태를 확인하세요."
elif yoy_ff > 10 and rate_diff > 0:
    insight_text = f"🌟 **[우수 진단] FF 매출이 전년비 {yoy_ff:.1f}% 크게 성장했으며, 판매율도 {rate_diff:.1f}%p 개선되었습니다.**\n\n발주량 증대가 실매출로 이어지는 완벽한 선순환 구조입니다. 다가오는 6월에는 이 점포의 주력 상권({store_data['점포유형']}) 특성에 맞춰, 객단가를 높일 수 있는 프리미엄 도시락이나 조리면, **FF간편식**의 신상품 최우선 도입을 제안해 객단가를 한 단계 더 높이세요."
elif yoy_ff > 0 and rate_diff < -3:
    insight_text = f"⚠️ **[진단] FF 매출은 늘었으나, 판매율이 전년 대비 {abs(rate_diff):.1f}%p 하락하여 폐기 부담이 커진 상태입니다.**\n\n발주는 공격적이나 마진율 방어가 안 되고 있습니다. 매출 비중이 낮은 구색 맞추기용 햄버거/샌드위치 발주는 줄이고, 회전율이 빠른 주력 카테고리로 발주를 압축하는 '선택과 집중' 전략이 6월에 필요합니다."
else:
    insight_text = f"📊 **[진단] 무난한 FF 실적을 유지 중입니다.**\n\n6월 기온 상승을 대비하여, 냉장면/샐러드 등 하절기 주력 **FF간편식**으로 라인업을 교체하고, 기존 김밥/주먹밥 매대를 꽉 채워 풍성한 시각적 효과를 주는 것이 중요합니다."

st.success(insight_text)

# 9. 카테고리별 매출 시각화 (Plotly)
st.subheader("📊 세부 카테고리 매출 비교")

categories = ['도시락', '김밥', '주먹밥', '햄버거/샌드위치', 'FF간편식']
sales_25 = [store_data['도시락_25'], store_data['김밥_25'], store_data['주먹밥_25'], store_data['햄버거샌드위치_25'], store_data['FF간편식_25']]
sales_26 = [store_data['도시락_26'], store_data['김밥_26'], store_data['주먹밥_26'], store_data['햄버거샌드위치_26'], store_data['FF간편식_26']]

# 그래프용 데이터프레임 구성
df_chart = pd.DataFrame({
    '카테고리': categories * 2,
    '매출액': sales_25 + sales_26,
    '연도': ['2025년 (3~5월)']*5 + ['2026년 (3~5월)']*5
})

# 모바일에서 잘 보이는 막대 그래프 (Plotly)
fig = px.bar(df_chart, x='카테고리', y='매출액', color='연도', barmode='group',
             title="전년 대비 카테고리별 일매출 증감",
             color_discrete_sequence=['#A6A6A6', '#004C99']) # 시인성 좋은 컬러매치

# 모바일 UI 깔끔하게 차트 설정
fig.update_layout(
    xaxis_title=None,
    yaxis_title="합계 금액 (원)",
    legend_title=None,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, use_container_width=True)
