import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# ==============================================================================
# 🎯 [수정 완료] 주소가 중복으로 들어간 부분을 올바르게 수정했습니다.
# ==============================================================================
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1AnT3gDAfx2cGhTCklDerm-gQsbcZWuzH7-mJ-gTpDf4/edit"

# 1. 모바일 화면에 맞게 화면 넓히기
st.set_page_config(page_title="GS25 FF 실적 대시보드", page_icon="🏪", layout="wide")

# 2. 비밀번호 잠금 기능 (비밀번호: gs25)
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

# 3. 데이터 로딩 (구글 스프레드시트 연동 및 캐싱)
@st.cache_data(ttl=5) # 수정 사항이 바로 반영되도록 캐시 시간을 5초로 단축했습니다.
def load_gsheets_data(url):
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # 구글 시트에서 각각의 워크시트 로드 (시트명이 정확히 일치해야 합니다)
    try:
        df_sales_raw = conn.read(spreadsheet=url, worksheet="sales")
        df_cost_raw = conn.read(spreadsheet=url, worksheet="cost")
    except Exception as e:
        st.error("🚨 구글 시트에서 '일매출' 또는 '매입매출' 탭을 찾지 못했습니다. 탭 이름에 띄어쓰기(공백)가 없는지 확인해주세요!")
        st.stop()
    
    # --- [데이터 전처리 및 정제] ---
    df_base = df_sales_raw.iloc[2:, 0:9].copy()
    df_base.columns = ['부문', '지역', '팀', '파트', '점포유형', '최초코드', '현재코드', '점포명', '점포수']

    # 💡 [핵심 수정] 숫자가 아닌 값(글자, 콤마 등)이 섞여 있을 때 에러를 방지하는 안전 계산 함수
    def safe_sum(df_slice):
        # 문자가 섞여있어도 무시하고, 강제로 숫자로 변환하여 합산합니다.
        return df_slice.replace({',': ''}, regex=True).apply(pd.to_numeric, errors='coerce').fillna(0).sum(axis=1)

    df_base['총매출_25'] = safe_sum(df_sales_raw.iloc[2:, 9:12])
    df_base['총매출_26'] = safe_sum(df_sales_raw.iloc[2:, 12:15])
    df_base['FF총매출_25'] = safe_sum(df_sales_raw.iloc[2:, 15:18])
    df_base['FF총매출_26'] = safe_sum(df_sales_raw.iloc[2:, 18:21])
    
    df_base['도시락_25'] = safe_sum(df_sales_raw.iloc[2:, [21, 26, 31]])
    df_base['도시락_26'] = safe_sum(df_sales_raw.iloc[2:, [36, 41, 46]])
    df_base['김밥_25'] = safe_sum(df_sales_raw.iloc[2:, [22, 27, 32]])
    df_base['김밥_26'] = safe_sum(df_sales_raw.iloc[2:, [37, 42, 47]])
    df_base['주먹밥_25'] = safe_sum(df_sales_raw.iloc[2:, [23, 28, 33]])
    df_base['주먹밥_26'] = safe_sum(df_sales_raw.iloc[2:, [38, 43, 48]])
    df_base['햄버거샌드위치_25'] = safe_sum(df_sales_raw.iloc[2:, [24, 29, 34]])
    df_base['햄버거샌드위치_26'] = safe_sum(df_sales_raw.iloc[2:, [39, 44, 49]])
    df_base['FF간편식_25'] = safe_sum(df_sales_raw.iloc[2:, [25, 30, 35]])
    df_base['FF간편식_26'] = safe_sum(df_sales_raw.iloc[2:, [40, 45, 50]])
    
    buy_cols_25, sell_cols_25 = [9,11,13,15,17, 19,21,23,25,27, 29,31,33,35,37], [10,12,14,16,18, 20,22,24,26,28, 30,32,34,36,38]
    buy_cols_26, sell_cols_26 = [39,41,43,45,47, 49,51,53,55,57, 59,61,63,65,67], [40,42,44,46,48, 50,52,54,56,58, 60,62,64,66,68]
    
    df_base['매입원가_25'] = safe_sum(df_cost_raw.iloc[2:, buy_cols_25])
    df_base['매출원가_25'] = safe_sum(df_cost_raw.iloc[2:, sell_cols_25])
    df_base['매입원가_26'] = safe_sum(df_cost_raw.iloc[2:, buy_cols_26])
    df_base['매출원가_26'] = safe_sum(df_cost_raw.iloc[2:, sell_cols_26])
    
    return df_base

# 구글 시트 정보 가져오기
try:
    df = load_gsheets_data(SPREADSHEET_URL)
except Exception as e:
    st.error("구글 시트 주소가 틀렸거나 접근 권한이 없습니다. 1단계를 다시 확인해주세요!")
    st.stop()

# 4. 맨 위에 고정되는 요약 인사이트
st.title("🚀 FF 봄 시즌 요약 및 6월 전략")
st.info("""
**💡 전체 현황 요약 (경영주 안내용)**
1. **매출과 이익 동시 상승:** 봄 시즌 FF 일매출은 전년 대비 **16.4% 올랐고**, 판매율(마진)은 **2.1%p 개선**되어 버리는 폐기가 줄었습니다.
2. **타겟팅 포인트:** '아파트 상권'은 **FF간편식(+33.7%)**, '소가구 상권'은 **도시락(+22.3%)**이 압도적으로 잘 팔립니다.
3. **🚨 주의할 점 (데이터 진단):**
   * **매출은 오르는데 FF만 떨어지는 점포:** 조회를 해보면 십중팔구 발주(매입원가) 자체를 작년보다 적게 넣고 있는 점포입니다. 물건이 없어서 못 파는 상황이니 발주부터 늘리라고 지도해야 합니다.
""")
st.divider()

# 5. 파트 및 점포 선택 화면
st.subheader("🎯 점포별 진단 및 액션 플랜")
col1, col2 = st.columns(2)
with col1:
    part_list = sorted(df['파트'].dropna().unique().tolist())
    selected_part = st.selectbox("👤 파트 선택", part_list)
with col2:
    store_list = df[df['파트'] == selected_part]['점포명'].dropna().unique().tolist()
    selected_store = st.selectbox("🏬 점포 선택", store_list)

store_data = df[(df['파트'] == selected_part) & (df['점포명'] == selected_store)].iloc[0]

# 계산식
def calc_pct(v25, v26): return ((v26 / v25) - 1) * 100 if v25 > 0 else 0
yoy_total = calc_pct(store_data['총매출_25'], store_data['총매출_26'])
yoy_ff = calc_pct(store_data['FF총매출_25'], store_data['FF총매출_26'])
yoy_buy = calc_pct(store_data['매입원가_25'], store_data['매입원가_26'])
sales_rate_25 = (store_data['매출원가_25'] / store_data['매입원가_25']) * 100 if store_data['매입원가_25'] > 0 else 0
sales_rate_26 = (store_data['매출원가_26'] / store_data['매입원가_26']) * 100 if store_data['매입원가_26'] > 0 else 0
rate_diff = sales_rate_26 - sales_rate_25

# 6. 점포별 요약 숫자
st.markdown(f"#### 📊 {selected_store} 점포 실적 (상권: {store_data['점포유형']})")
m_col1, m_col2, m_col3 = st.columns(3)
m_col1.metric("점포 일매출 YOY", f"{store_data['총매출_26']:,.0f}원", f"{yoy_total:.1f}%")
m_col2.metric("FF 일매출 YOY", f"{store_data['FF총매출_26']:,.0f}원", f"{yoy_ff:.1f}%")
m_col3.metric("FF 판매율 변동", f"{sales_rate_26:.1f}%", f"{rate_diff:.1f}%p", delta_color="normal")

# 7. 자동으로 분석해주는 6월 전략
st.markdown("##### 💡 매니저 진단 및 6월 가이드")
if yoy_total > 2.0 and yoy_ff < -1.0:
    if yoy_buy < 0:
        st.error(f"🚨 **[진단]** 점포 매출은 잘 나오는데 FF만 역성장입니다. 원인은 작년보다 **발주(매입원가)를 {abs(yoy_buy):.1f}%나 덜 넣고 있기 때문**입니다.\n\n👉 **[액션]** 손님은 오는데 물건이 없습니다. 6월엔 제일 잘 나가는 도시락/주먹밥 발주부터 정상화시키세요.")
    else:
        st.warning(f"⚠️ **[진단]** 발주는 작년만큼 넣는데 팔리질 않아 판매율이 {rate_diff:.1f}%p 떨어졌습니다.\n\n👉 **[액션]** 안 팔리는 구색은 과감히 줄이고, 6월 여름에 잘 팔리는 **FF간편식**(냉장면 등)으로 매대를 확 바꾸세요.")
elif yoy_ff > 10.0 and rate_diff > 0.5:
    st.success(f"🌟 **[진단]** 매출도 {yoy_ff:.1f}% 올랐고 판매율(마진)도 좋아진 아주 훌륭한 점포입니다.\n\n👉 **[액션]** 이 기세를 몰아 단가가 비싼 프리미엄 도시락이나 신상 **FF간편식**을 전면에 내세워 이익을 극대화하세요.")
elif yoy_ff > 0 and rate_diff < -3.0:
    st.warning(f"⚠️ **[진단]** 매출은 올랐지만 판매율이 {abs(rate_diff):.1f}%p 나빠져서 폐기가 많습니다.\n\n👉 **[액션]** 무리하게 햄버거/샌드위치까지 꽉 채우지 말고, 잘 나가는 김밥과 **FF간편식** 위주로 똘똘하게 발주하세요.")
else:
    st.info(f"📊 **[진단]** 작년과 비슷하게 잘 유지하고 있습니다.\n\n👉 **[액션]** 초여름 비수기에 대비해 6월엔 면류, 샐러드 등 하절기 **FF간편식**을 늘려서 선방해야 합니다.")

# 8. 모바일에서 보기 좋은 그래프
st.markdown("##### 📈 품목별 매출 상세비교")
categories = ['도시락', '김밥', '주먹밥', '햄버거/샌드위치', 'FF간편식']
sales_25 = [store_data['도시락_25'], store_data['김밥_25'], store_data['주먹밥_25'], store_data['햄버거샌드위치_25'], store_data['FF간편식_25']]
sales_26 = [store_data['도시락_26'], store_data['김밥_26'], store_data['주먹밥_26'], store_data['햄버거샌드위치_26'], store_data['FF간편식_26']]

df_chart = pd.DataFrame({
    '품목': categories * 2,
    '매출': sales_25 + sales_26,
    '년도': ['2025년']*5 + ['2026년']*5
})

fig = px.bar(df_chart, x='품목', y='매출', color='년도', barmode='group', color_discrete_sequence=['#CCCCCC', '#005EA6'])
fig.update_layout(xaxis_title=None, yaxis_title=None, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
st.plotly_chart(fig, use_container_width=True)
