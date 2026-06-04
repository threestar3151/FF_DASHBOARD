import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
from io import StringIO

SPREADSHEET_ID = "1AnT3gDAfx2cGhTCklDerm-gQsbcZWuzH7-mJ-gTpDf4"

st.set_page_config(page_title="GS25 FF 실적 대시보드", page_icon="🏪", layout="wide")

st.markdown("""
<style>
  .block-container { padding-top: 1.5rem; }
  .kpi-label { font-size:0.78rem; color:#888; margin-bottom:2px; }
  .kpi-value { font-size:1.55rem; font-weight:700; color:#111; }
  .kpi-delta-pos { font-size:0.9rem; color:#2ECC71; font-weight:600; }
  .kpi-delta-neg { font-size:0.9rem; color:#E74C3C; font-weight:600; }
  .kpi-delta-neu { font-size:0.9rem; color:#888; font-weight:600; }
  .kpi-card {
    background:#fff;
    border:1px solid #E8EEF6;
    border-radius:12px;
    padding:1rem 1.2rem 0.8rem;
    box-shadow:0 2px 8px rgba(0,94,166,0.06);
  }
  .type-card {
    border-radius:12px;
    padding:1.2rem 1.5rem;
    margin:0.5rem 0;
  }
  .type-A { background:#FFF3F3; border-left:5px solid #E74C3C; }
  .type-B { background:#FFFBF0; border-left:5px solid #F39C12; }
  .type-C { background:#FFF8F0; border-left:5px solid #E67E22; }
  .type-D { background:#F0FFF4; border-left:5px solid #2ECC71; }
  .type-title { font-size:1.1rem; font-weight:700; margin-bottom:0.4rem; }
  .type-insight { font-size:0.88rem; color:#555; margin-bottom:0.6rem; }
  .coaching-box {
    background:#fff;
    border-radius:8px;
    padding:0.8rem 1rem;
    font-size:0.92rem;
    line-height:1.7;
    color:#222;
  }
  .pinset-highlight {
    background:linear-gradient(90deg,#FFF9E6,#FFFDF5);
    border:1px solid #F0C040;
    border-radius:8px;
    padding:0.7rem 1rem;
    margin:0.3rem 0;
    font-size:0.9rem;
  }
  .pinset-warn {
    background:linear-gradient(90deg,#FFF3F3,#FFF8F8);
    border:1px solid #F0A0A0;
    border-radius:8px;
    padding:0.7rem 1rem;
    margin:0.3rem 0;
    font-size:0.9rem;
  }
  .section-divider {
    border:none; border-top:2px solid #EEF2F8;
    margin:1.5rem 0;
  }
  .summary-card {
    background:linear-gradient(135deg,#f8faff,#eef3fb);
    border-left:4px solid #005EA6;
    border-radius:10px;
    padding:1rem 1.4rem;
    margin-bottom:0.5rem;
  }
</style>
""", unsafe_allow_html=True)

# ── 비밀번호 ────────────────────────────────────────────────────
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

# ── 데이터 로딩 ─────────────────────────────────────────────────
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

    def safe_avg(df_slice):
        return (
            df_slice
            .replace({',': ''}, regex=True)
            .apply(pd.to_numeric, errors='coerce')
            .fillna(0)
            .mean(axis=1)
            .reset_index(drop=True)
        )

    sales = df_sales_raw.iloc[1:].reset_index(drop=True)
    cost  = df_cost_raw.iloc[1:].reset_index(drop=True)

    df_base = sales.iloc[:, 0:9].copy()
    df_base.columns = ['부문','지역','팀','파트','점포유형','최초코드','현재코드','점포명','점포수']

    df_base['총매출_25']   = safe_avg(sales.iloc[:, 9:12])
    df_base['총매출_26']   = safe_avg(sales.iloc[:, 12:15])
    df_base['FF총매출_25'] = safe_avg(sales.iloc[:, 15:18])
    df_base['FF총매출_26'] = safe_avg(sales.iloc[:, 18:21])

    item_keys = ['도시락','김밥','주먹밥','햄버거샌드위치','FF간편식']
    offsets25 = [21,22,23,24,25]
    for i, k in enumerate(item_keys):
        cols25 = [offsets25[i], offsets25[i]+5, offsets25[i]+10]
        cols26 = [offsets25[i]+15, offsets25[i]+20, offsets25[i]+25]
        df_base[f'{k}_25'] = safe_avg(sales.iloc[:, cols25])
        df_base[f'{k}_26'] = safe_avg(sales.iloc[:, cols26])

    buy_cols_25  = list(range(9,  39, 2))
    sell_cols_25 = list(range(10, 40, 2))
    buy_cols_26  = list(range(39, 69, 2))
    sell_cols_26 = list(range(40, 70, 2))

    df_base['매입원가_25'] = safe_avg(cost.iloc[:, buy_cols_25])
    df_base['매출원가_25'] = safe_avg(cost.iloc[:, sell_cols_25])
    df_base['매입원가_26'] = safe_avg(cost.iloc[:, buy_cols_26])
    df_base['매출원가_26'] = safe_avg(cost.iloc[:, sell_cols_26])

    items_buy_25 = {
        '도시락':         [9,  19, 29],
        '김밥':           [11, 21, 31],
        '주먹밥':         [13, 23, 33],
        '햄버거샌드위치': [15, 25, 35],
        'FF간편식':       [17, 27, 37],
    }
    items_sell_25 = {k: [v+1  for v in vs] for k, vs in items_buy_25.items()}
    items_buy_26  = {k: [v+30 for v in vs] for k, vs in items_buy_25.items()}
    items_sell_26 = {k: [v+1  for v in vs] for k, vs in items_buy_26.items()}

    for item in items_buy_25:
        df_base[f'{item}_매입_25'] = safe_avg(cost.iloc[:, items_buy_25[item]])
        df_base[f'{item}_매출_25'] = safe_avg(cost.iloc[:, items_sell_25[item]])
        df_base[f'{item}_매입_26'] = safe_avg(cost.iloc[:, items_buy_26[item]])
        df_base[f'{item}_매출_26'] = safe_avg(cost.iloc[:, items_sell_26[item]])

    return df_base

try:
    df = load_data()
except Exception as e:
    st.error(f"데이터 로딩 오류: {e}")
    st.stop()

# ── 유틸 ────────────────────────────────────────────────────────
def calc_pct(v25, v26):
    return ((v26 / v25) - 1) * 100 if v25 > 0 else 0

def delta_html(val, suffix="%", threshold=1.0):
    if val > threshold:
        return f'<span class="kpi-delta-pos">▲ {val:+.1f}{suffix}</span>'
    elif val < -threshold:
        return f'<span class="kpi-delta-neg">▼ {val:+.1f}{suffix}</span>'
    else:
        return f'<span class="kpi-delta-neu">➖ {val:+.1f}{suffix}</span>'

# ── 상단 요약 ────────────────────────────────────────────────────
st.title("🚀 FF 봄 시즌 요약 및 6월 전략")
st.markdown("""
<div class="summary-card">
  <b>💡 전체 현황 요약</b> — 기준: <b>'25년 3~5월 vs '26년 3~5월 일평균 매출</b> (참고용, 점포별 편차 있음)
  <ul style="margin:0.4rem 0 0 0; padding-left:1.2rem; font-size:0.92rem;">
    <li>봄 시즌 FF 일평균 매출 전년 대비 약 <b>+16.4%</b> 증가, 판매율 <b>+2.1%p</b> 개선 흐름 감지</li>
    <li>'아파트 상권' → FF간편식(+33.7%), '소가구 상권' → 도시락(+22.3%) 두드러짐. 점포별 확인 필요</li>
    <li>FF 역성장 점포는 발주 감소가 원인일 가능성 높음 — 발주 이력 먼저 확인 후 지도 권장</li>
  </ul>
</div>
""", unsafe_allow_html=True)
st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

# ── 점포 선택 ────────────────────────────────────────────────────
st.subheader("🎯 점포별 진단 및 액션 플랜")
col1, col2 = st.columns(2)
with col1:
    part_list = sorted(df['파트'].dropna().unique().tolist())
    selected_part = st.selectbox("👤 파트 선택", part_list)
with col2:
    store_list = df[df['파트'] == selected_part]['점포명'].dropna().unique().tolist()
    selected_store = st.selectbox("🏬 점포 선택", store_list)

s = df[(df['파트'] == selected_part) & (df['점포명'] == selected_store)].iloc[0]

yoy_total    = calc_pct(s['총매출_25'],   s['총매출_26'])
yoy_ff       = calc_pct(s['FF총매출_25'], s['FF총매출_26'])
yoy_buy      = calc_pct(s['매입원가_25'], s['매입원가_26'])
rate_25      = (s['매출원가_25'] / s['매입원가_25'] * 100) if s['매입원가_25'] > 0 else 0
rate_26      = (s['매출원가_26'] / s['매입원가_26'] * 100) if s['매입원가_26'] > 0 else 0
rate_diff    = rate_26 - rate_25
sang_kwon    = s['점포유형']

# ══════════════════════════════════════════════════════════════════
# [섹션 1] 4대 핵심 KPI 카드
# ══════════════════════════════════════════════════════════════════
st.markdown(
    f"#### 📊 {selected_store} "
    f"<span style='font-size:0.82rem;color:#999;font-weight:400;'>"
    f"상권: {sang_kwon} | 기준: 일평균 '25년3~5월 vs '26년3~5월</span>",
    unsafe_allow_html=True
)

c1, c2, c3, c4 = st.columns(4)
kpi_data = [
    (c1, "① 점포 총매출 증감률", f"{s['총매출_26']:,.0f}원", yoy_total, "%",
     "객수 흐름 파악"),
    (c2, "② FF 매출 증감률",     f"{s['FF총매출_26']:,.0f}원", yoy_ff,  "%",
     "FF 실제 판매 결과"),
    (c3, "③ FF 매입원가 증감률", f"{s['매입원가_26']:,.0f}원", yoy_buy, "%",
     "발주량 변화 (원인①)"),
    (c4, "④ FF 판매율 변동",     f"{rate_26:.1f}%",           rate_diff,"%p",
     "폐기율·마진 방어 (원인②)"),
]
for col, label, val, delta, unit, sub in kpi_data:
    with col:
        st.markdown(
            f"""<div class="kpi-card">
              <div class="kpi-label">{label}</div>
              <div class="kpi-value">{val}</div>
              {delta_html(delta, unit)}
              <div class="kpi-label" style="margin-top:4px;">{sub}</div>
            </div>""",
            unsafe_allow_html=True
        )

st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# [섹션 2] 자동 유형 진단 + 코칭 멘트
# ══════════════════════════════════════════════════════════════════
st.markdown("#### 🤖 자동 진단 및 코칭 가이드")

# 유형 판별 로직
if yoy_total > 2.0 and yoy_ff < -1.0 and yoy_buy < -1.0:
    diag_type = "A"
elif yoy_total > 2.0 and yoy_ff < -1.0 and yoy_buy >= -1.0:
    diag_type = "B"
elif yoy_ff > 2.0 and rate_diff < -3.0:
    diag_type = "C"
elif yoy_ff > 5.0 and rate_diff > 0.5:
    diag_type = "D"
else:
    diag_type = "N"  # 해당 없음

type_configs = {
    "A": {
        "css": "type-A",
        "title": "🚨 [유형 A] 기회로스형 — 가장 시급한 코칭 대상",
        "badge": "총매출 🔼 | FF매출 🔽 | FF매입원가 🔽",
        "insight": "점포에 방문하는 고객은 늘고 있으나, 경영주가 선제적으로 발주(매입)를 줄여 진열대가 비어있기 때문에 팔지 못하는 '기회로스' 상태입니다.",
        "coaching": f"경영주님, 점포 전체 매출이 오르는데 FF만 떨어지는 이유는 안 팔려서가 아니라 '진열된 물건이 없어서'입니다. 손님들이 왔다가 빈 매대를 보고 돌아가고 있습니다. 당장 작년 수준으로 발주량을 복구하셔야 전체 이익이 깎이지 않습니다.",
    },
    "B": {
        "css": "type-B",
        "title": "⚠️ [유형 B] 구색/진열 부조화형",
        "badge": "총매출 🔼 | FF매출 🔽 | FF매입원가 ➖🔼",
        "insight": "발주는 꾸준히 넣고 있으나 고객의 선택을 받지 못해 폐기만 늘어나는 상태입니다.",
        "coaching": f"발주는 정상적인데 매출이 빠진다면 상권 타겟팅이 어긋난 것입니다. 상권에 맞지 않는 구색(예: 오피스 상권에 반찬용 HMR 위주 진열)이 없는지 확인하고, 피크타임 전에 FF 매대가 잘 보이도록 전진 진열을 정비해야 합니다.",
    },
    "C": {
        "css": "type-C",
        "title": "📉 [유형 C] 과발주 및 마진 악화형",
        "badge": "FF매출 🔼 | FF판매율 🔽🔽",
        "insight": "매출은 오르고 있으나, 무리한 구색 맞추기식 발주로 실질적인 마진이 무너지고 폐기 스트레스가 극심한 상태입니다.",
        "coaching": f"매출은 오르지만 남는 게 없는 상황입니다. 회전율이 떨어지는 햄버거/샌드위치 구색은 과감히 하단으로 빼거나 줄이고, 상권 주력 상품(FF간편식, 김밥 등)으로 포트폴리오를 압축해 마진을 방어하겠습니다.",
    },
    "D": {
        "css": "type-D",
        "title": "🌟 [유형 D] 선순환 우수형",
        "badge": "FF매출 🔼🔼 | FF판매율 🔼",
        "insight": "적극적인 발주가 판매 호조와 폐기 감소로 이어지는 완벽한 상태입니다.",
        "coaching": f"FF 수요가 완벽히 터진 타이밍입니다. 단가가 높은 신상품 프리미엄 도시락이나 조리면을 적극적으로 2~3개씩 복수 진열하여 객단가를 최고조로 끌어올리시죠.",
    },
}

if diag_type != "N":
    cfg = type_configs[diag_type]
    st.markdown(f"""
    <div class="type-card {cfg['css']}">
      <div class="type-title">{cfg['title']}</div>
      <div style="font-size:0.82rem;color:#777;margin-bottom:0.5rem;">데이터 조건: {cfg['badge']}</div>
      <div class="type-insight">📌 진단: {cfg['insight']}</div>
      <div class="coaching-box">💬 코칭 멘트: {cfg['coaching']}</div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="type-card" style="background:#F8F8F8;border-left:5px solid #AAA;">
      <div class="type-title">📊 특이 유형 없음 — 안정 유지형</div>
      <div class="type-insight">전반적으로 전년과 유사한 수준을 유지하고 있습니다.</div>
      <div class="coaching-box">💬 코칭 멘트: 초여름 비수기에 대비해 면류·샐러드 등 하절기 FF간편식 비중을 미리 늘려두시길 권장합니다.</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# [섹션 3] 품목별 매출 차트
# ══════════════════════════════════════════════════════════════════
st.markdown("#### 📈 품목별 일평균 매출 비교")

item_labels  = ['도시락','김밥','주먹밥','햄버거샌드위치','FF간편식']
item_display = ['도시락','김밥','주먹밥','햄버거/샌드위치','FF간편식']
s25_vals = [s[f'{k}_25'] for k in item_labels]
s26_vals = [s[f'{k}_26'] for k in item_labels]
pcts     = [calc_pct(a, b) for a, b in zip(s25_vals, s26_vals)]

fig1 = go.Figure()
fig1.add_trace(go.Bar(
    name="'25년", x=item_display, y=s25_vals,
    marker=dict(color='#D0D8E8', line=dict(color='#B0BAD0', width=1)),
    text=[f"{v:,.0f}" for v in s25_vals],
    textposition='outside', textfont=dict(size=11, color='#888888'),
))
fig1.add_trace(go.Bar(
    name="'26년", x=item_display, y=s26_vals,
    marker=dict(color='#005EA6', line=dict(color='#004880', width=1)),
    text=[f"{v:,.0f} ({p:+.1f}%)" for v, p in zip(s26_vals, pcts)],
    textposition='outside', textfont=dict(size=11, color='#005EA6'),
))
fig1.update_layout(
    barmode='group', plot_bgcolor='white', paper_bgcolor='white',
    font=dict(family='Apple SD Gothic Neo, Noto Sans KR, sans-serif', size=12),
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, bgcolor='rgba(0,0,0,0)'),
    xaxis=dict(showgrid=False, tickfont=dict(size=13)),
    yaxis=dict(showgrid=True, gridcolor='#F0F0F0', tickformat=',', title='원 (일평균)'),
    margin=dict(t=60, b=20), height=360,
)
st.plotly_chart(fig1, use_container_width=True)

# ── 판매율 차트 ─────────────────────────────────────────────────
st.markdown("#### 📊 품목별 판매율 비교 (매출원가 ÷ 매입원가)")
st.caption("판매율이 높을수록 폐기 없이 완판에 가까움. 권장 기준: 85%")

rate25_list, rate26_list, rdiff_list = [], [], []
for item in item_labels:
    b25  = s.get(f'{item}_매입_25', 0)
    sv25 = s.get(f'{item}_매출_25', 0)
    b26  = s.get(f'{item}_매입_26', 0)
    sv26 = s.get(f'{item}_매출_26', 0)
    r25 = (sv25 / b25 * 100) if b25 > 0 else 0
    r26 = (sv26 / b26 * 100) if b26 > 0 else 0
    rate25_list.append(round(r25, 1))
    rate26_list.append(round(r26, 1))
    rdiff_list.append(round(r26 - r25, 1))

fig2 = go.Figure()
fig2.add_trace(go.Bar(
    name="'25년 판매율", x=item_display, y=rate25_list,
    marker=dict(color='#D0D8E8', line=dict(color='#B0BAD0', width=1)),
    text=[f"{v:.1f}%" for v in rate25_list],
    textposition='outside', textfont=dict(size=11, color='#888888'),
))
fig2.add_trace(go.Bar(
    name="'26년 판매율", x=item_display, y=rate26_list,
    marker=dict(color=['#2ECC71' if d >= 0 else '#E74C3C' for d in rdiff_list]),
    text=[f"{v:.1f}% ({d:+.1f}%p)" for v, d in zip(rate26_list, rdiff_list)],
    textposition='outside', textfont=dict(size=11),
))
fig2.add_hline(y=85, line_dash='dot', line_color='#FF6B35', line_width=1.5,
               annotation_text="권장 판매율 85%", annotation_position="top left",
               annotation_font=dict(color='#FF6B35', size=11))
fig2.update_layout(
    barmode='group', plot_bgcolor='white', paper_bgcolor='white',
    font=dict(family='Apple SD Gothic Neo, Noto Sans KR, sans-serif', size=12),
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1, bgcolor='rgba(0,0,0,0)'),
    xaxis=dict(showgrid=False, tickfont=dict(size=13)),
    yaxis=dict(showgrid=True, gridcolor='#F0F0F0', ticksuffix='%', range=[0, 115]),
    margin=dict(t=60, b=20), height=360,
)
st.plotly_chart(fig2, use_container_width=True)

st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# [섹션 4] 핀셋 코칭 뷰
# ══════════════════════════════════════════════════════════════════
st.markdown("#### 🔍 세부 품목별 핀셋 코칭")

item_display_map = {
    '도시락': '도시락',
    '김밥': '김밥',
    '주먹밥': '주먹밥',
    '햄버거샌드위치': '햄버거/샌드위치',
    'FF간편식': 'FF간편식',
}

# 상권별 1순위 모니터링 항목
priority_map = {
    '소가구': '도시락',
    '원룸': '도시락',
    '아파트': 'FF간편식',
    '주거': 'FF간편식',
    '오피스': '김밥',
    '역세권': '김밥',
}
priority_item = next((v for k, v in priority_map.items() if k in sang_kwon), None)

pinset_msgs = []
for item_key, item_name in item_display_map.items():
    ff_25 = s.get(f'{item_key}_25', 0)
    ff_26 = s.get(f'{item_key}_26', 0)
    buy_25 = s.get(f'{item_key}_매입_25', 0)
    buy_26 = s.get(f'{item_key}_매입_26', 0)

    yoy_item = calc_pct(ff_25, ff_26)
    yoy_item_buy = calc_pct(buy_25, buy_26)

    # 매출 역성장인데 발주가 원인인 경우
    if yoy_item < -3.0 and yoy_item_buy < -3.0:
        pinset_msgs.append({
            "level": "warn",
            "msg": (
                f"<b>{item_name}</b> 매출이 <b>{yoy_item:.1f}%</b> 하락했습니다. "
                f"데이터를 확인하니 <b>{item_name} 매입원가(발주)가 {yoy_item_buy:.1f}%</b> 줄어든 것이 직접 원인입니다. "
                f"발주를 즉시 전년 수준으로 복구하면 매출 회복 가능성이 높습니다."
            )
        })
    # 매출 역성장인데 발주는 유지 → 폐기/구색 문제
    elif yoy_item < -3.0 and yoy_item_buy >= -1.0:
        pinset_msgs.append({
            "level": "warn",
            "msg": (
                f"<b>{item_name}</b> 매출이 <b>{yoy_item:.1f}%</b> 빠졌지만 발주는 유지 중입니다. "
                f"폐기가 증가하고 있을 가능성이 있으니 진열 위치·시간대별 소진율을 점검해주세요."
            )
        })
    # 매출 상승 + 발주도 증가 → 긍정 신호
    elif yoy_item > 5.0 and yoy_item_buy > 3.0:
        pinset_msgs.append({
            "level": "ok",
            "msg": (
                f"<b>{item_name}</b>이 매출 <b>+{yoy_item:.1f}%</b>, "
                f"발주도 <b>+{yoy_item_buy:.1f}%</b> 동반 성장 중입니다. "
                f"이 기세를 유지하세요."
            )
        })

# 상권별 1순위 항목 하이라이트
if priority_item:
    p_key = next((k for k, v in item_display_map.items() if v == priority_item), None)
    if p_key:
        p_buy_yoy = calc_pct(s.get(f'{p_key}_매입_25', 0), s.get(f'{p_key}_매입_26', 0))
        p_ff_yoy  = calc_pct(s.get(f'{p_key}_25', 0), s.get(f'{p_key}_26', 0))
        highlight_color = "#FFF3CD" if p_buy_yoy < -2 else "#E8F8F0"
        border_color    = "#F0C040" if p_buy_yoy < -2 else "#2ECC71"
        st.markdown(
            f"""<div style="background:{highlight_color};border:2px solid {border_color};
            border-radius:10px;padding:0.8rem 1.1rem;margin-bottom:0.8rem;font-size:0.92rem;">
            ⭐ <b>[{sang_kwon} 상권 1순위 모니터링 품목]</b> → <b>{priority_item}</b><br>
            현재 매출 변동: <b>{p_ff_yoy:+.1f}%</b> | 발주 변동: <b>{p_buy_yoy:+.1f}%</b>
            {"&nbsp;&nbsp;🚨 발주 감소 감지 — 즉시 확인 필요" if p_buy_yoy < -2 else "&nbsp;&nbsp;✅ 발주 정상 유지 중"}
            </div>""",
            unsafe_allow_html=True
        )

# 핀셋 메시지 출력
if pinset_msgs:
    for msg in pinset_msgs:
        css_class = "pinset-warn" if msg["level"] == "warn" else "pinset-highlight"
        icon = "🔺" if msg["level"] == "warn" else "✅"
        st.markdown(f'<div class="{css_class}">{icon} {msg["msg"]}</div>', unsafe_allow_html=True)
else:
    st.markdown(
        '<div class="pinset-highlight">✅ 현재 특이 품목 없음 — 모든 품목이 전년 대비 안정적으로 유지되고 있습니다.</div>',
        unsafe_allow_html=True
    )

st.markdown("<br>", unsafe_allow_html=True)
