import streamlit as st
import pandas as pd

# 페이지 설정
st.set_page_config(
    page_title="서울 100년 기온 변화",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 서울의 100년간 연평균 기온 변화")
st.write("서울의 기온 데이터를 이용하여 연도별 평균기온의 변화를 살펴봅니다.")

# 데이터 주소
DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"

# 데이터 불러오기
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL)

    # 날짜를 날짜 형식으로 변환
    df["날짜"] = pd.to_datetime(df["날짜"])

    # 연도 추출
    df["연도"] = df["날짜"].dt.year

    # 연도별 평균기온 계산
    yearly = (
        df.groupby("연도")["평균기온"]
        .mean()
        .reset_index()
    )

    return yearly


try:
    data = load_data()

    # 100년 범위에 해당하는 데이터 선택
    data = data.sort_values("연도")

    st.subheader("연도별 평균기온")

    # Streamlit 기본 라인 차트
    chart_data = data.set_index("연도")
    st.line_chart(
        chart_data,
        y="평균기온",
        x_label="연도",
        y_label="평균기온 (℃)"
    )

    # 간단한 통계 정보
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "분석 시작 연도",
            f"{int(data['연도'].min())}년"
        )

    with col2:
        st.metric(
            "분석 종료 연도",
            f"{int(data['연도'].max())}년"
        )

    with col3:
        change = data["평균기온"].iloc[-1] - data["평균기온"].iloc[0]
        st.metric(
            "시작-마지막 연도 기온 차이",
            f"{change:+.2f} ℃"
        )

    st.subheader("연도별 데이터")
    st.dataframe(
        data,
        use_container_width=True,
        hide_index=True
    )

except Exception as e:
    st.error("데이터를 불러오는 중 문제가 발생했습니다.")
    st.write(f"오류 내용: {e}")
