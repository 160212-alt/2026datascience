import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta, timezone


# =========================================================
# 기본 설정
# =========================================================

st.set_page_config(
    page_title="영화 데이터 그래프 도감",
    layout="wide"
)

st.title("🎬 영화 데이터 그래프 도감")


# =========================================================
# KOBIS API
# =========================================================

API_KEY = st.secrets["KOBIS_KEY"]

KST = timezone(timedelta(hours=9))

yesterday = (
    datetime.now(KST) - timedelta(days=1)
).strftime("%Y%m%d")

url = (
    "https://kobis.or.kr/kobisopenapi/webservice/rest/"
    "boxoffice/searchDailyBoxOfficeList.json"
)

params = {
    "key": API_KEY,
    "targetDt": yesterday
}


# =========================================================
# API 데이터 가져오기
# =========================================================

try:
    response = requests.get(
        url,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    result = response.json()

    movie_list = result[
        "boxOfficeResult"
    ][
        "dailyBoxOfficeList"
    ]

    if not movie_list:
        st.warning("어제의 박스오피스 데이터가 없습니다.")
        st.stop()

    df = pd.DataFrame(movie_list)

except Exception as e:
    st.error(f"API 데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()


# =========================================================
# 데이터 정리
# =========================================================

# 숫자로 변환할 열
number_columns = [
    "rank",
    "salesAmt",
    "salesShare",
    "salesInten",
    "salesChange",
    "salesAcc",
    "audiCnt",
    "audiInten",
    "audiChange",
    "audiAcc",
    "scrnCnt",
    "showCnt"
]

for column in number_columns:
    if column in df.columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )


# 총 관객수
df["total_audi"] = df["audiAcc"]

df["total_audi"] = pd.to_numeric(
    df["total_audi"],
    errors="coerce"
)

df = df.dropna(
    subset=["total_audi"]
)


# =========================================================
# 1. 일일 관객수 TOP 5
# =========================================================

st.subheader("1. 일일 관객수 TOP 5")

top5 = (
    df.sort_values(
        "audiCnt",
        ascending=False
    )
    .head(5)
    .copy()
)

fig1, ax1 = plt.subplots(
    figsize=(10, 5)
)

ax1.bar(
    top5["movieNm"],
    top5["audiCnt"]
)

ax1.set_title(
    "어제 일일 관객수 TOP 5"
)

ax1.set_xlabel("영화")
ax1.set_ylabel("일 관객수")

plt.xticks(
    rotation=20,
    ha="right"
)

plt.tight_layout()

st.pyplot(fig1)


# =========================================================
# 2. 장르 → 영화 트리맵
# =========================================================

st.subheader("2. 장르별 영화 총 관객수 트리맵")

# KOBIS 일일 박스오피스 API에는 장르 정보가 없으므로
# 영화 상세정보 API를 이용해서 장르를 가져온다.

genre_data = []

detail_url = (
    "https://kobis.or.kr/kobisopenapi/webservice/rest/"
    "movie/searchMovieInfo.json"
)

for _, row in df.iterrows():

    movie_code = row.get("movieCd")

    if not movie_code:
        continue

    detail_params = {
        "key": API_KEY,
        "movieCd": movie_code
    }

    try:
        detail_response = requests.get(
            detail_url,
            params=detail_params,
            timeout=10
        )

        detail_response.raise_for_status()

        detail_result = detail_response.json()

        movie_info = (
            detail_result
            .get("movieInfoResult", {})
            .get("movieInfo", {})
        )

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

    except Exception:
        genre_name = "기타"

    genre_data.append({
        "movieNm": row["movieNm"],
        "genre": genre_name,
        "total_audi": row["total_audi"]
    })


genre_df = pd.DataFrame(
    genre_data
)


if not genre_df.empty:

    fig2 = px.treemap(
        genre_df,
        path=["genre", "movieNm"],
        values="total_audi",
        title="장르별 영화 총 관객수",
        hover_data={
            "total_audi": ":,"
        }
    )

    fig2.update_traces(
        hovertemplate=(
            "<b>%{label}</b>"
            "<br>총 관객: %{value:,.0f}명"
            "<extra></extra>"
        )
    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )

else:

    st.warning(
        "장르 데이터를 가져오지 못했습니다."
    )


# =========================================================
# 3. 총 관객수 히스토그램
# =========================================================

st.subheader("3. 총 관객수 분포")

fig3, ax3 = plt.subplots(
    figsize=(10, 5)
)

ax3.hist(
    df["total_audi"],
    bins=20,
    edgecolor="black"
)

ax3.set_title(
    "영화별 총 관객수 분포"
)

ax3.set_xlabel(
    "총 관객수"
)

ax3.set_ylabel(
    "영화 수"
)

plt.tight_layout()

st.pyplot(fig3)


# =========================================================
# 히스토그램 분석 문구
# =========================================================

counts, bins = np.histogram(
    df["total_audi"],
    bins=20
)

most_common_bin = np.argmax(
    counts
)

low = bins[most_common_bin]
high = bins[most_common_bin + 1]


# 가장 관객이 많은 영화
max_index = df["total_audi"].idxmax()

max_movie = df.loc[
    max_index,
    "movieNm"
]

max_audience = df.loc[
    max_index,
    "total_audi"
]


st.markdown(
    f"""
📊 **대부분의 영화는 약 {low:,.0f}명 ~ {high:,.0f}명 구간에 몰려 있습니다.**

🏆 **가장 관객이 많은 영화는 '{max_movie}'이며,
총 관객은 {max_audience:,.0f}명입니다.**
"""
)


# =========================================================
# 데이터 확인
# =========================================================

st.subheader("📋 박스오피스 데이터")

display_columns = [
    "rank",
    "movieNm",
    "audiCnt",
    "total_audi",
    "scrnCnt",
    "showCnt"
]

display_columns = [
    column
    for column in display_columns
    if column in df.columns
]

st.dataframe(
    df[display_columns],
    use_container_width=True
)
