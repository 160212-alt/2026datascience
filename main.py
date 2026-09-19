```python
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(
    page_title="기온 예측기",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 기온 예측기")
st.write("서울의 연도별 평균기온을 이용해 회귀 직선을 만들고 예상 기온을 확인합니다.")

DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/bb860932644270ad1199f10d3e7670e30231bce4/data/seoul.csv"


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL, encoding="utf-8")
    
    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")
    df["평균기온"] = pd.to_numeric(df["평균기온"], errors="coerce")
    df["연도"] = df["날짜"].dt.year
    
    df = df.dropna(subset=["연도", "평균기온"])
    
    return df


df = load_data()

# 연도별 평균기온과 관측일수 계산
yearly = (
    df.groupby("연도")
    .agg(
        연평균기온=("평균기온", "mean"),
        관측일수=("평균기온", "count")
    )
    .reset_index()
)

# 1908~2025년 중 관측일수가 300일 이상인 해만 사용
analysis_df = yearly[
    (yearly["연도"] >= 1908) &
    (yearly["연도"] <= 2025) &
    (yearly["관측일수"] >= 300)
].copy()

analysis_df = analysis_df.sort_values("연도").reset_index(drop=True)

# 1908년부터 지난 연수
analysis_df["지난연수"] = analysis_df["연도"] - 1908

x = analysis_df["지난연수"].to_numpy()
y = analysis_df["연평균기온"].to_numpy()

# 1차 회귀
slope, intercept = np.polyfit(x, y, 1)

# 상관계수
correlation = np.corrcoef(x, y)[0, 1]


# 연도 슬라이더
selected_year = st.slider(
    "예상 기온을 확인할 연도를 선택하세요.",
    min_value=1900,
    max_value=2100,
    value=2025,
    step=1
)

# 선택한 연도의 예상 기온
selected_x = selected_year - 1908
predicted_temp = slope * selected_x + intercept

st.subheader(f"📅 {selected_year}년 예상 연평균기온")

st.metric(
    label=f"{selected_year}년 예상 연평균기온",
    value=f"{predicted_temp:.2f} °C"
)


# 회귀 정보
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("회귀에 사용된 연도 수", f"{len(analysis_df)}개")

with col2:
    st.metric("시작 연도", f"{analysis_df['연도'].min()}년")

with col3:
    st.metric("끝 연도", f"{analysis_df['연도'].max()}년")

with col4:
    st.metric("상관계수", f"{correlation:.3f}")


st.info(
    f"회귀식: 연평균기온 = "
    f"{slope:.4f} × (연도 - 1908) + {intercept:.4f}"
)

st.caption(
    "2025년 이하이면서 관측일수가 300일 이상인 연도만 회귀분석에 사용했습니다."
)


# Plotly 그래프
fig = go.Figure()

# 실제 연평균기온 산점도
fig.add_trace(
    go.Scatter(
        x=analysis_df["연도"],
        y=analysis_df["연평균기온"],
        mode="markers",
        name="실제 연평균기온",
        text=analysis_df["관측일수"],
        hovertemplate=
            "<b>%{x}년</b><br>" +
            "연평균기온: %{y:.2f} °C<br>" +
            "관측일수: %{text}일" +
            "<extra></extra>"
    )
)

# 회귀 직선
regression_years = np.linspace(
    analysis_df["연도"].min(),
    analysis_df["연도"].max(),
    300
)

regression_x = regression_years - 1908
regression_y = slope * regression_x + intercept

fig.add_trace(
    go.Scatter(
        x=regression_years,
        y=regression_y,
        mode="lines",
        name="회귀 직선",
        hovertemplate=
            "연도: %{x:.0f}<br>" +
            "예상기온: %{y:.2f} °C" +
            "<extra></extra>"
    )
)

# 선택한 연도의 예상값
fig.add_trace(
    go.Scatter(
        x=[selected_year],
        y=[predicted_temp],
        mode="markers",
        name="선택 연도 예상값",
        marker=dict(size=12),
        hovertemplate=
            f"<b>{selected_year}년</b><br>" +
            "예상 연평균기온: %{y:.2f} °C" +
            "<extra></extra>"
    )
)

fig.update_layout(
    title="서울 연도별 평균기온과 회귀 직선",
    xaxis_title="연도",
    yaxis_title="연평균기온 (°C)",
    xaxis=dict(
        tickmode="linear",
        dtick=10
    ),
    hovermode="x unified",
    height=600
)

st.plotly_chart(fig, use_container_width=True)


# 사용된 데이터 확인
with st.expander("📊 회귀분석에 사용된 데이터 보기"):
    display_df = analysis_df[
        ["연도", "관측일수", "연평균기온", "지난연수"]
    ].copy()

    display_df["연평균기온"] = display_df["연평균기온"].round(2)

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )


st.caption(
    "※ 회귀선은 과거 자료의 선형 추세를 이용한 값이며 실제 미래 기온을 보장하지 않습니다."
)
```
