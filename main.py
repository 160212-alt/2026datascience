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
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL)

    # 날짜 형식 변환
    df["날짜"] = pd.to_datetime(df["날짜"])

    # 평균기온을 숫자형으로 변환
    df["평균기온"] = pd.to_numeric(df["평균기온"], errors="coerce")

    # 결측값 제거
    df = df.dropna(subset=["평균기온"])

    return df


try:
    data = load_data()

    st.subheader("일별 평균기온 히스토그램")

    fig = px.histogram(
        data,
        x="평균기온",
        nbins=30,
        labels={
            "평균기온": "평균기온 (℃)",
            "count": "일수"
        },
        title="서울의 일별 평균기온 분포"
    )

    fig.update_layout(
        xaxis_title="평균기온 (℃)",
        yaxis_title="일수",
        bargap=0.05
    )

    st.plotly_chart(fig, use_container_width=True)

    # 기본 통계
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "전체 관측 일수",
            f"{len(data):,}일"
        )

    with col2:
        st.metric(
            "평균기온 평균",
            f"{data['평균기온'].mean():.2f} ℃"
        )

    with col3:
        st.metric(
            "가장 높은 일평균기온",
            f"{data['평균기온'].max():.1f} ℃"
        )

except Exception as e:
    st.error("데이터를 불러오는 중 문제가 발생했습니다.")
    st.write(f"오류 내용: {e}")
# 페이지 설정
st.set_page_config(
    page_title="서울 최저·최고기온 관계",
    page_icon="🌡️",
    layout="wide"
)

st.title("🌡️ 서울의 최저기온과 최고기온의 관계")
st.write("날마다의 최저기온과 최고기온 사이의 관계를 산점도로 나타냈습니다.")

# 데이터 주소
DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL)

    # 날짜 변환
    df["날짜"] = pd.to_datetime(df["날짜"])

    # 숫자형 변환
    df["최저기온"] = pd.to_numeric(df["최저기온"], errors="coerce")
    df["최고기온"] = pd.to_numeric(df["최고기온"], errors="coerce")

    # 결측값 제거
    df = df.dropna(subset=["최저기온", "최고기온"])

    return df

try:
    data = load_data()

    st.subheader("최저기온 vs 최고기온 산점도")

    fig = px.scatter(
        data,
        x="최저기온",
        y="최고기온",
        opacity=0.3,
        labels={
            "최저기온": "최저기온 (℃)",
            "최고기온": "최고기온 (℃)"
        },
        title="서울의 일별 최저기온과 최고기온 관계"
    )

    fig.update_layout(
        xaxis_title="최저기온 (℃)",
        yaxis_title="최고기온 (℃)"
    )

    st.plotly_chart(fig, use_container_width=True)

    # 상관계수 계산
    corr = data["최저기온"].corr(data["최고기온"])

    st.metric(
        "최저기온-최고기온 상관계수",
        f"{corr:.3f}"
    )

    st.write(
        f"상관계수는 **{corr:.3f}**로, 최저기온이 높을수록 최고기온도 높아지는 강한 양의 관계를 보입니다."
    )

except Exception as e:
    st.error("데이터를 불러오는 중 오류가 발생했습니다.")
    st.write(e)
