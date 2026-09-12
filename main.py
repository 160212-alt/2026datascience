import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# -----------------------------------
# 기본 설정
# -----------------------------------
st.set_page_config(
    page_title="영화 데이터 그래프 도감",
    layout="wide"
)

st.title("🎬 영화 데이터 그래프 도감")

# -----------------------------------
# KOBIS API 키
# -----------------------------------
try:
    KOBIS_KEY = st.secrets["KOBIS_KEY"]
except Exception:
    st.error("KOBIS_KEY가 Streamlit Secrets에 설정되어 있지 않습니다.")
    st.stop()

# -----------------------------------
# 한국 시간 기준 어제 날짜
# -----------------------------------
kst = ZoneInfo("Asia/Seoul")
today = datetime.now(kst).date()
yesterday = today - timedelta(days=1)

target_date = yesterday.strftime("%Y%m%d")

st.write(f"📅 조회 날짜: {yesterday.strftime('%Y-%m-%d')}")

# -----------------------------------
# KOBIS 일별 박스오피스 API
# -----------------------------------
url = "https://kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"

params = {
    "key": KOBIS_KEY,
    "targetDt": target_date
}

response = requests.get(url, params=params)

if response.status_code != 200:
    st.error("API 요청에 실패했습니다.")
    st.stop()

data = response.json()

# -----------------------------------
# API 데이터 가져오기
# -----------------------------------
try:
    movies = data["boxOfficeResult"]["dailyBoxOfficeList"]
except Exception:
    st.error("영화 데이터를 불러오지 못했습니다.")
    st.stop()

if not movies:
    st.warning("해당 날짜의 영화 데이터가 없습니다.")
    st.stop()

df = pd.DataFrame(movies)

# -----------------------------------
# 숫자 데이터 변환
# -----------------------------------
numeric_columns = [
    "rank",
    "rankInten",
    "salesAmt",
    "audiCnt",
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

# total_audi 컬럼 만들기
df["total_audi"] = pd.to_numeric(
    df["audiAcc"],
    errors="coerce"
)

# ===================================
# 1. 영화별 총 관객 수 TOP 10
# ===================================
st.subheader("① 영화별 총 관객 수 TOP 10")

top10 = df.sort_values(
    "total_audi",
    ascending=False
).head(10)

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

# ===================================
# 2. 장르별 영화 트리맵
# ===================================
st.subheader("② 장르별 영화 총 관객 수")

# 영화 상세정보 API에서 장르 가져오기
genre_list = []

detail_url = (
    "https://kobis.or.kr/kobisopenapi/webservice/rest/"
    "movie/searchMovieInfo.json"
)

for movie in df["movieCd"]:
    params_movie = {
        "key": KOBIS_KEY,
        "movieCd": movie
    }

    try:
        detail_response = requests.get(
            detail_url,
            params=params_movie
        )

        detail_data = detail_response.json()

        movie_info = detail_data["movieInfoResult"]["movieInfo"]

        genres = movie_info.get("genres", [])

        if genres:
            genre_name = genres[0]["genreNm"]
        else:
            genre_name = "기타"

    except Exception:
        genre_name = "기타"

    genre_list.append(genre_name)

df["genre"] = genre_list

# 트리맵
fig2 = px.treemap(
    df,
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

# ===================================
# 3. 총 관객 수 히스토그램
# ===================================
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

# -----------------------------------
# 가장 많이 몰려 있는 구간 계산
# -----------------------------------
if len(hist_data) > 0:

    counts, bins = np.histogram(
        hist_data["total_audi"],
        bins=10
    )

    max_bin = counts.argmax()

    low = bins[max_bin]
    high = bins[max_bin + 1]

    st.write(
        f"📊 **대부분의 영화는 "
        f"{low:,.0f}명 ~ {high:,.0f}명 "
        f"구간에 몰려 있습니다.**"
    )

    # -----------------------------------
    # 가장 관객이 많은 영화
    # -----------------------------------
    max_movie = hist_data.loc[
        hist_data["total_audi"].idxmax()
    ]

    st.write(
        f"🎬 **총 관객이 가장 많은 영화는 "
        f"{max_movie['movieNm']}**이며, "
        f"총 관객 수는 "
        f"**{max_movie['total_audi']:,.0f}명**입니다."
    )
