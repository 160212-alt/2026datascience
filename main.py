import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


# =========================================
# 기본 설정
# =========================================
st.set_page_config(
    page_title="영화 데이터 그래프 도감",
    layout="wide"
)

st.title("🎬 영화 데이터 그래프 도감")


# =========================================
# KOBIS API KEY
# =========================================
try:
    KOBIS_KEY = st.secrets["KOBIS_KEY"]
except Exception:
    st.error("Streamlit Secrets에 KOBIS_KEY를 등록해주세요.")
    st.stop()


# =========================================
# API 주소
# =========================================
BOXOFFICE_URL = (
    "https://kobis.or.kr/kobisopenapi/webservice/rest/"
    "boxoffice/searchDailyBoxOfficeList.json"
)

MOVIE_INFO_URL = (
    "https://kobis.or.kr/kobisopenapi/webservice/rest/"
    "movie/searchMovieInfo.json"
)


# =========================================
# 일별 박스오피스 데이터 함수
# =========================================
@st.cache_data(ttl=3600)
def get_daily_boxoffice(target_dt):

    params = {
        "key": KOBIS_KEY,
        "targetDt": target_dt
    }

    response = requests.get(
        BOXOFFICE_URL,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    return data[
        "boxOfficeResult"
    ][
        "dailyBoxOfficeList"
    ]


# =========================================
# 영화 상세정보 함수
# =========================================
@st.cache_data(ttl=3600)
def get_movie_info(movie_cd):

    params = {
        "key": KOBIS_KEY,
        "movieCd": movie_cd
    }

    response = requests.get(
        MOVIE_INFO_URL,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    return data[
        "movieInfoResult"
    ][
        "movieInfo"
    ]


# =========================================
# 한국 시간 기준 어제 날짜
# =========================================
kst = ZoneInfo("Asia/Seoul")

today = datetime.now(kst).date()
yesterday = today - timedelta(days=1)

target_date = yesterday.strftime("%Y%m%d")

st.write(
    f"📅 조회 날짜: {yesterday.strftime('%Y-%m-%d')}"
)


# =========================================
# 어제 박스오피스 데이터 가져오기
# =========================================
try:

    movies = get_daily_boxoffice(
        target_date
    )

except Exception:

    st.error(
        "KOBIS API에서 영화 데이터를 불러오지 못했습니다."
    )

    st.stop()


if not movies:

    st.warning(
        "해당 날짜의 영화 데이터가 없습니다."
    )

    st.stop()


df = pd.DataFrame(movies)


# =========================================
# 숫자형 데이터 변환
# =========================================
numeric_columns = [
    "rank",
    "rankInten",
    "salesAmt",
    "salesShare",
    "salesChange",
    "salesAcc",
    "audiCnt",
    "audiInten",
    "audiChange",
    "audiAcc",
    "scrnCnt",
    "showCnt"
]

for col in numeric_columns:

    if col in df.columns:

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )


# =========================================
# 총 관객 수
# =========================================
df["total_audi"] = pd.to_numeric(
    df["audiAcc"],
    errors="coerce"
)


# =========================================
# 영화별 장르와 개봉일 가져오기
# =========================================
genre_list = []
open_date_list = []

for movie_cd in df["movieCd"]:

    try:

        movie_info = get_movie_info(
            movie_cd
        )

        # -------------------------------
        # 장르
        # -------------------------------
        genres = movie_info.get(
            "genres",
            []
        )

        if genres:

            genre_name = genres[0].get(
                "genreNm",
                "기타"
            )

        else:

            genre_name = "기타"


        # -------------------------------
        # 개봉일
        # -------------------------------
        open_date = movie_info.get(
            "openDt",
            ""
        )

    except Exception:

        genre_name = "기타"
        open_date = ""


    genre_list.append(
        genre_name
    )

    open_date_list.append(
        open_date
    )


df["genre"] = genre_list
df["openDt"] = open_date_list


# =========================================
# 개봉일 스크린 수 구하기
# =========================================
@st.cache_data(ttl=3600)
def get_first_screen(
    movie_cd,
    open_dt
):

    if not open_dt:
        return np.nan

    open_dt = str(open_dt)

    if len(open_dt) != 8:
        return np.nan

    try:

        opening_movies = get_daily_boxoffice(
            open_dt
        )

        for movie in opening_movies:

            if movie.get(
                "movieCd"
            ) == movie_cd:

                return pd.to_numeric(
                    movie.get("scrnCnt"),
                    errors="coerce"
                )

    except Exception:

        return np.nan

    return np.nan


first_screen_list = []

for _, row in df.iterrows():

    first_screen = get_first_screen(
        row["movieCd"],
        row["openDt"]
    )

    first_screen_list.append(
        first_screen
    )


df["first_scrn"] = first_screen_list


# ============================================================
# ① 영화별 총 관객 수 TOP 10
# ============================================================
st.subheader(
    "① 영화별 총 관객 수 TOP 10"
)


top10 = (
    df
    .dropna(
        subset=["total_audi"]
    )
    .sort_values(
        "total_audi",
        ascending=False
    )
    .head(10)
)


fig1 = px.bar(
    top10,
    x="movieNm",
    y="total_audi",
    title="영화별 총 관객 수 TOP 10",
    labels={
        "movieNm": "영화명",
        "total_audi": "총 관객 수"
    },
    text="total_audi"
)


fig1.update_traces(
    texttemplate="%{text:,}",
    textposition="outside"
)


fig1.update_layout(
    xaxis_tickangle=-45
)


st.plotly_chart(
    fig1,
    use_container_width=True
)


# ============================================================
# ② 장르 × 영화 트리맵
# ============================================================
st.subheader(
    "② 장르별 영화 총 관객 수"
)


treemap_data = (
    df
    .dropna(
        subset=[
            "genre",
            "movieNm",
            "total_audi"
        ]
    )
    .copy()
)


fig2 = px.treemap(
    treemap_data,
    path=[
        "genre",
        "movieNm"
    ],
    values="total_audi",
    title="장르별 영화 총 관객 수"
)


fig2.update_traces(
    hovertemplate=(
        "<b>%{label}</b><br>"
        "총 관객: %{value:,}명"
        "<extra></extra>"
    )
)


st.plotly_chart(
    fig2,
    use_container_width=True
)


# ============================================================
# ③ 총 관객 수 히스토그램
# ============================================================
st.subheader(
    "③ 총 관객 수 분포"
)


hist_data = (
    df
    .dropna(
        subset=["total_audi"]
    )
    .copy()
)


fig3 = px.histogram(
    hist_data,
    x="total_audi",
    nbins=10,
    title="영화별 총 관객 수 분포",
    labels={
        "total_audi": "총 관객 수",
        "count": "영화 수"
    }
)


fig3.update_layout(
    bargap=0.05
)


st.plotly_chart(
    fig3,
    use_container_width=True
)


# -----------------------------------------
# 가장 많이 몰려 있는 구간
# -----------------------------------------
if len(hist_data) > 0:

    counts, bins = np.histogram(
        hist_data["total_audi"],
        bins=10
    )

    max_bin = counts.argmax()

    low = bins[max_bin]
    high = bins[max_bin + 1]

    st.write(
        f"📊 대부분의 영화는 "
        f"**{low:,.0f}명 ~ {high:,.0f}명** "
        f"구간에 몰려 있습니다."
    )


    # -----------------------------------------
    # 총 관객이 가장 많은 영화
    # -----------------------------------------
    max_movie = hist_data.loc[
        hist_data["total_audi"].idxmax()
    ]


    st.write(
        f"🎬 총 관객이 가장 많은 영화는 "
        f"**{max_movie['movieNm']}**이며, "
        f"총 관객 수는 "
        f"**{max_movie['total_audi']:,.0f}명**입니다."
    )


# ============================================================
# ④ 개봉일 스크린 수와 총 관객 수의 관계
# ============================================================
st.subheader(
    "④ 개봉일 스크린 수와 총 관객 수의 관계"
)


scatter_data = (
    df
    .dropna(
        subset=[
            "first_scrn",
            "total_audi",
            "movieNm",
            "genre"
        ]
    )
    .copy()
)


if len(scatter_data) > 0:

    fig4 = px.scatter(
        scatter_data,
        x="first_scrn",
        y="total_audi",
        color="genre",
        hover_name="movieNm",
        title="개봉일 스크린 수와 총 관객 수",
        labels={
            "first_scrn": "개봉일 스크린 수",
            "total_audi": "총 관객 수",
            "genre": "장르"
        }
    )


    fig4.update_traces(
        marker={
            "size": 10
        }
    )


    fig4.update_layout(
        xaxis_title="개봉일 스크린 수",
        yaxis_title="총 관객 수"
    )


    st.plotly_chart(
        fig4,
        use_container_width=True
    )


    st.write(
        "💡 각 점은 하나의 영화를 나타냅니다. "
        "점에 마우스를 올리면 영화명이 표시됩니다."
    )

else:

    st.info(
        "개봉일 스크린 수 데이터를 구할 수 있는 "
        "영화가 없습니다."
    )


# ============================================================
# ⑤ 장르별 총 관객 수 상자 그림
# ============================================================
st.subheader(
    "⑤ 장르별 총 관객 수 상자 그림"
)


# -----------------------------------------
# 장르별 영화 수 계산
# -----------------------------------------
genre_counts = (
    df["genre"]
    .value_counts()
)


# -----------------------------------------
# 영화가 10편 이상인 장르만 선택
# -----------------------------------------
valid_genres = genre_counts[
    genre_counts >= 10
].index.tolist()


box_data = (
    df[
        df["genre"].isin(
            valid_genres
        )
    ]
    .dropna(
        subset=[
            "genre",
            "total_audi",
            "movieNm"
        ]
    )
    .copy()
)


# -----------------------------------------
# 조건을 만족하는 장르가 없는 경우
# -----------------------------------------
if len(valid_genres) == 0:

    st.info(
        "현재 조회된 영화 데이터에는 "
        "영화가 10편 이상인 장르가 없습니다."
    )

else:

    # -----------------------------------------
    # 박스플롯
    # -----------------------------------------
    fig5 = px.box(
        box_data,
        x="genre",
        y="total_audi",
        points="outliers",
        custom_data=[
            "movieNm"
        ],
        title=(
            "영화가 10편 이상인 장르별 "
            "총 관객 수"
        ),
        labels={
            "genre": "장르",
            "total_audi": "총 관객 수"
        }
    )


    # -----------------------------------------
    # 이상치 마우스오버
    # -----------------------------------------
    fig5.update_traces(
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "총 관객: %{y:,}명"
            "<extra></extra>"
        )
    )


    fig5.update_layout(
        xaxis_title="장르",
        yaxis_title="총 관객 수",
        xaxis_tickangle=-45
    )


    st.plotly_chart(
        fig5,
        use_container_width=True
    )


    st.write(
        "📊 영화가 10편 이상인 장르만 "
        "표시했습니다."
    )

    st.write(
        "🔎 상자 밖으로 튀어나온 점은 "
        "해당 장르에서 관객 수가 "
        "특히 높거나 낮은 이상치입니다. "
        "점에 마우스를 올리면 영화명이 표시됩니다."
    )
