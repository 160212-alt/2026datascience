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
```

