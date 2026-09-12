import streamlit as st
import requests
import pandas as pd
import plotly.express as px
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
# 한국 시간 기준 어제
# =========================================
kst = ZoneInfo("Asia/Seoul")

today = datetime.now(kst).date()
yesterday = today - timedelta(days=1)

target_date = yesterday.strftime("%Y%m%d")

st.write(
    f"📅 조회 날짜: {yesterday.strftime('%Y-%m-%d')}"
)

# =========================================
# 1. 일별 박스오피스 API
# =========================================
boxoffice_url = (
    "https://kobis.or.kr/kobisopenapi/webservice/rest/"
    "boxoffice/searchDailyBoxOfficeList.json"
)

params = {
    "key": KOBIS_KEY,
    "targetDt": target_date
}

response = requests.get(
    boxoffice_url,
    params=params,
    timeout=10
)

if response.status_code != 200:
    st.error("KOBIS API 요청에 실패했습니다.")
    st.stop()

try:
    result = response.json()
    movies = result["boxOfficeResult"]["dailyBoxOfficeList"]
except Exception:
    st.error("영화 데이터를 불러오지 못했습니다.")
    st.stop()

if not movies:
    st.warning("해당 날짜의 영화 데이터가 없습니다.")
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

# total_audi = 누적 관객 수
df["total_audi"] = pd.to_numeric(
    df["audiAcc"],
    errors="coerce"
)

# =========================================
# 2. 영화 상세정보에서 장르 가져오기
# =========================================
movie_info_url = (
    "https://kobis.or.kr/kobisopenapi/webservice/rest/"
    "movie/searchMovieInfo.json"
)

genres = []
open_dates = []

for movie_code in df["movieCd"]:

    params_movie = {
        "key": KOBIS_KEY,
        "movieCd": movie_code
    }

    try:
        movie_response = requests.get(
            movie_info_url,
            params=params_movie,
            timeout=10
        )

        movie_result = movie_response.json()

        movie_info = (
            movie_result
            ["movieInfoResult"]
            ["movieInfo"]
        )

        # -------------------------------
        # 장르
        # -------------------------------
        genre_data = movie_info.get(
            "genres",
            []
        )

        if genre_data:
            genre_name = genre_data[0]["genreNm"]
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

    genres.append(genre_name)
    open_dates.append(open_date)

df["genre"] = genres
df["openDt"] = open_dates

# =========================================
# 3. 개봉일 스크린 수(first_scrn) 구하기
# =========================================
#
# KOBIS 일별 박스오피스의 scrnCnt는
# '해당 날짜의 스크린 수'이므로,
# 영화의 개봉일과 같은 날짜의 박스오피스
# 데이터를 다시 조회해서 그때의 scrnCnt를 사용한다.
#
# =========================================

first_scrn_list = []

for index, row in df.iterrows():

    open_dt = row["openDt"]

    # 개봉일 정보가 없는 경우
    if not open_dt:
        first_scrn_list.append(np.nan)
        continue

    # YYYYMMDD 형태인지 확인
    if len(open_dt) != 8:
        first_scrn_list.append(np.nan)
        continue

    first_boxoffice_url = (
        "https://kobis.or.kr/kobisopenapi/webservice/rest/"
        "boxoffice/searchDailyBoxOfficeList.json"
    )

    first_params = {
        "key": KOBIS_KEY,
        "targetDt": open_dt
    }

    try:
        first_response = requests.get(
            first_boxoffice_url,
            params=first_params,
            timeout=10
        )

        first_result = first_response.json()

        first_movies = (
            first_result
            ["boxOfficeResult"]
            ["dailyBoxOfficeList"]
        )

        movie_code = row["movieCd"]

        first_scrn = np.nan

        for first_movie in first_movies:

            if first_movie["movieCd"] == movie_code:
                first_scrn = pd.to_numeric(
                    first_movie.get("scrnCnt"),
                    errors="coerce"
                )
                break

        first_scrn_list.append(first_scrn)

    except Exception:
        first_scrn_list.append(np.nan)

df["first_scrn"] = first_scrn_list

# =========================================
# ① 영화별 총 관객 수 TOP 10
# =========================================
st.subheader("① 영화별 총 관객 수 TOP 10")

top10 = (
    df
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

# =========================================
# ② 장르별 영화 트리맵
# =========================================
st.subheader("② 장르별 영화 총 관객 수")

treemap_data = df.dropna(
    subset=["total_audi"]
).copy()

fig2 = px.treemap(
    treemap_data,
    path=["genre", "movieNm"],
    values="total_audi",
    title="장르별 영화 총 관객 수",
    hover_data={
        "total_audi": ":,"
    }
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

# =========================================
# ③ 총 관객 수 히스토그램
# =========================================
st.subheader("③ 총 관객 수 분포")

hist_data = df.dropna(
    subset=["total_audi"]
).copy()

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

    # -------------------------------------
    # 가장 관객이 많은 영화
    # -------------------------------------
    max_movie = hist_data.loc[
        hist_data["total_audi"].idxmax()
    ]

    st.write(
        f"🎬 총 관객이 가장 많은 영화는 "
        f"**{max_movie['movieNm']}**이며, "
        f"총 관객 수는 "
        f"**{max_movie['total_audi']:,.0f}명**입니다."
    )

# =========================================
# ④ 개봉일 스크린 수와 총 관객 수
# =========================================
st.subheader(
    "④ 개봉일 스크린 수와 총 관객 수의 관계"
)

scatter_data = df.dropna(
    subset=[
        "first_scrn",
        "total_audi",
        "movieNm",
        "genre"
    ]
).copy()

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

st.plotly_chart(
    fig4,
    use_container_width=True
)

# =========================================
# ④ 그래프 설명
# =========================================
st.write(
    "💡 그래프의 각 점은 하나의 영화를 나타냅니다. "
    "점에 마우스를 올리면 영화명이 표시되며, "
    "장르에 따라 점의 색이 다르게 표시됩니다."
)
