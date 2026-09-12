import streamlit as st
import pandas as pd
import plotly.express as px

# 페이지 설정
st.set_page_config(
    page_title="영화 데이터 그래프 도감 2 - 분포와 관계",
    page_icon="🎬",
    layout="wide"
)

# 제목
st.title("영화 데이터 그래프 도감 2 - 분포와 관계")

st.write(
    "1년간 박스오피스 10위권에 든 영화 가운데 해당 기간에 개봉한 "
    "216편의 데이터를 이용해 영화의 분포와 관계를 살펴봅니다."
)

# 데이터 불러오기
DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_movies.csv"

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL)

    # 개봉일을 문자열로 변환
    df["openDt"] = df["openDt"].astype(str).str.zfill(8)

    # 여러 장르가 세로막대(|)로 구분되어 있다면 첫 번째 장르만 사용
    df["genre"] = df["genre"].astype(str).str.split("|").str[0]

    return df


try:
    df = load_data()

    # 데이터 확인
    st.success(f"총 {len(df)}편의 영화 데이터를 불러왔습니다.")

    # --------------------------------------------------
    # 1. 장르별 영화 편수 - 도넛 그래프
    # --------------------------------------------------

    st.subheader("① 장르별 영화 편수")

    genre_count = (
        df["genre"]
        .value_counts()
        .reset_index()
    )

    genre_count.columns = ["장르", "영화 편수"]

    fig = px.pie(
        genre_count,
        names="장르",
        values="영화 편수",
        hole=0.45,
        title="장르별 영화 편수"
    )

    fig.update_traces(
        textposition="inside",
        textinfo="percent",
        hovertemplate=(
            "<b>%{label}</b><br>"
            "영화 편수: %{value}편<br>"
            "비율: %{percent}<extra></extra>"
        )
    )

    fig.update_layout(
        height=500,
        legend_title="장르"
    )

    st.plotly_chart(fig, use_container_width=True)

    # 그래프 분석 구역
    st.markdown("---")
    st.markdown("### 💡 이 그래프로 알 수 있는 것")
    st.info(
        "장르별 영화 편수를 비교하면 1년간 박스오피스 10위권에 진입한 영화에서 "
        "어떤 장르가 상대적으로 많이 나타났는지 알 수 있다."
    )

except Exception as e:
    st.error("데이터를 불러오는 중 오류가 발생했습니다.")
    st.exception(e)
import streamlit as st
import pandas as pd
import plotly.express as px

# 페이지 설정
st.set_page_config(
    page_title="영화 데이터 그래프 도감 2 - 분포와 관계",
    page_icon="🎬",
    layout="wide"
)

# 제목
st.title("영화 데이터 그래프 도감 2 - 분포와 관계")

st.write(
    "1년간 박스오피스 10위권에 든 영화 가운데 해당 기간에 개봉한 "
    "216편의 데이터를 이용해 영화의 분포와 관계를 살펴봅니다."
)

# 데이터 주소
DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_movies.csv"


# 데이터 불러오기
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL)

    # 개봉일을 문자열로 변환
    df["openDt"] = df["openDt"].astype(str).str.zfill(8)

    # 여러 장르가 |로 구분되어 있다면 첫 번째 장르만 사용
    df["genre"] = df["genre"].astype(str).str.split("|").str[0]

    # 총 관객을 숫자로 변환
    df["total_audi"] = pd.to_numeric(
        df["total_audi"],
        errors="coerce"
    )

    return df


try:
    df = load_data()

    st.success(f"총 {len(df)}편의 영화 데이터를 불러왔습니다.")

    # ==================================================
    # ① 장르별 영화 편수 - 도넛 그래프
    # ==================================================

    st.subheader("① 장르별 영화 편수")

    genre_count = (
        df["genre"]
        .value_counts()
        .reset_index()
    )

    genre_count.columns = ["장르", "영화 편수"]

    fig1 = px.pie(
        genre_count,
        names="장르",
        values="영화 편수",
        hole=0.45,
        title="장르별 영화 편수"
    )

    fig1.update_traces(
        textposition="inside",
        textinfo="percent",
        hovertemplate=(
            "<b>%{label}</b><br>"
            "영화 편수: %{value}편<br>"
            "비율: %{percent}<extra></extra>"
        )
    )

    fig1.update_layout(
        height=500,
        legend_title="장르"
    )

    st.plotly_chart(fig1, use_container_width=True)

    # 분석 구역
    st.markdown("---")
    st.markdown("### 💡 이 그래프로 알 수 있는 것")

    st.info(
        "장르별 영화 편수를 비교하면 1년간 박스오피스 10위권에 진입한 영화에서 "
        "어떤 장르가 상대적으로 많이 나타났는지 알 수 있다."
    )

    # ==================================================
    # ② 장르별 영화 트리맵 - 총 관객 기준
    # ==================================================

    st.markdown("---")
    st.subheader("② 장르별 영화 트리맵")

    fig2 = px.treemap(
        df,
        path=["genre", "movieNm"],
        values="total_audi",
        title="장르 안의 영화별 총 관객",
        custom_data=["genre", "movieNm", "total_audi"]
    )

    fig2.update_traces(
        hovertemplate=(
            "<b>%{customdata[1]}</b><br>"
            "장르: %{customdata[0]}<br>"
            "총 관객: %{customdata[2]:,}명"
            "<extra></extra>"
        )
    )

    fig2.update_layout(
        height=700
    )

    st.plotly_chart(fig2, use_container_width=True)

    # 분석 구역
    st.markdown("---")
    st.markdown("### 💡 이 그래프로 알 수 있는 것")

    st.info(
        "각 장르 안에서 영화별 총 관객 규모를 비교하면 어떤 장르의 어떤 영화가 "
        "많은 관객을 확보했는지 한눈에 확인할 수 있다."
    )

except Exception as e:
    st.error("데이터를 불러오는 중 오류가 발생했습니다.")
    st.exception(e)
