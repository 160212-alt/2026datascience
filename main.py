```python
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# 페이지 설정
st.set_page_config(
    page_title="기온 예측기",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 기온 예측기")
st.write("서울의 연도별 평균기온을 분석하여 회귀 직선과 예상 기온을 보여줍니다.")

# 데이터 주소
URL = "https://raw.githubusercontent.com/greatsong/modudata/bb860932644270ad1199f10d3e7670e30231bce4/data/seoul.csv"


# 데이터 불러오기
@st.cache_data
def get_data():
    df = pd.read_csv(URL, encoding="utf-8")

    # 날짜 변환
    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")

    # 평균기온 숫자로 변환
    df["평균기온"] = pd.to_numeric(df["평균기온"], errors="coerce")

    # 날짜나 평균기온이 없는 행 제거
    df = df.dropna(subset=["날짜", "평균기온"])

    # 연도 만들기
    df["연도"] = df["날짜"].dt.year

    return df


try:
    df = get_data()

    # 연도별 평균기온과 관측일수
    yearly = df.groupby("연도").agg(
        연평균기온=("평균기온", "mean"),
        관측일수=("평균기온", "count")
    ).reset_index()

    # 1908~2025년, 관측일수 300일 이상인 연도만 사용
    data = yearly[
        (yearly["연도"] >= 1908) &
        (yearly["연도"] <= 2025) &
        (yearly["관측일수"] >= 300)
    ].copy()

    data = data.sort_values("연도").reset_index(drop=True)

    if len(data) < 2:
        st.error("회귀분석에 사용할 데이터가 부족합니다.")
        st.stop()

    # 1908년부터 지난 연수
    data["지난연수"] = data["연도"] - 1908

    x = data["지난연수"].values
    y = data["연평균기온"].values

    # 회귀직선
    slope, intercept = np.polyfit(x, y, 1)

    # 상관계수
    correlation = np.corrcoef(x, y)[0, 1]

    # -------------------------------
    # 슬라이더
    # -------------------------------
    selected_year = st.slider(
        "예상 연도를 선택하세요.",
        min_value=1900,
        max_value=2100,
        value=2025,
        step=1
    )

    # 선택한 연도의 예상기온
    selected_x = selected_year - 1908
    predicted = slope * selected_x + intercept

    st.subheader(f"📅 {selected_year}년 예상 연평균기온")

    st.metric(
        "예상 연평균기온",
        f"{predicted:.2f} °C"
    )

    # -------------------------------
    # 회귀분석 정보
    # -------------------------------
    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "회귀에 사용된 연도 수",
        f"{len(data)}개"
    )

    c2.metric(
        "시작 연도",
        f"{int(data['연도'].min())}년"
    )

    c3.metric(
        "끝 연도",
        f"{int(data['연도'].max())}년"
    )

    c4.metric(
        "상관계수",
        f"{correlation:.3f}"
    )

    st.info(
        f"회귀식: 연평균기온 = "
        f"{slope:.4f} × (연도 - 1908) + {intercept:.4f}"
    )

    # -------------------------------
    # Plotly 그래프
    # -------------------------------
    fig = go.Figure()

    # 실제 데이터
    fig.add_trace(
        go.Scatter(
            x=data["연도"],
            y=data["연평균기온"],
            mode="markers",
            name="실제 연평균기온",
            text=data["관측일수"],
            hovertemplate=
                "%{x}년<br>" +
                "연평균기온: %{y:.2f} °C<br>" +
                "관측일수: %{text}일" +
                "<extra></extra>"
        )
    )

    # 회귀선
    line_years = np.arange(
        int(data["연도"].min()),
        int(data["연도"].max()) + 1
    )

    line_x = line_years - 1908
    line_y = slope * line_x + intercept

    fig.add_trace(
        go.Scatter(
            x=line_years,
            y=line_y,
            mode="lines",
            name="회귀 직선",
            hovertemplate=
                "%{x}년<br>" +
                "예상기온: %{y:.2f} °C" +
                "<extra></extra>"
        )
    )

    # 선택한 연도
    fig.add_trace(
        go.Scatter(
            x=[selected_year],
            y=[predicted],
            mode="markers",
            name="선택한 연도",
            marker=dict(size=14),
            hovertemplate=
                f"{selected_year}년<br>" +
                "예상기온: %{y:.2f} °C" +
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
        height=600
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # -------------------------------
    # 데이터 표
    # -------------------------------
    with st.expander("📊 분석에 사용된 데이터 보기"):
        table = data[
            ["연도", "관측일수", "연평균기온", "지난연수"]
        ].copy()

        table["연평균기온"] = table["연평균기온"].round(2)

        st.dataframe(
            table,
            use_container_width=True,
            hide_index=True
        )

    st.caption(
        "※ 2025년 이후 자료와 관측일수가 300일 미만인 연도는 분석에서 제외했습니다."
    )
    st.caption(
        "※ 미래 연도의 기온은 과거 자료를 이용한 선형 회귀에 따른 예상값입니다."
    )

except Exception as e:
    st.error("데이터를 불러오거나 분석하는 과정에서 오류가 발생했습니다.")
    st.code(str(e))
```
