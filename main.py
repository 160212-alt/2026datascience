import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime, timedelta
from collections import defaultdict

# ============================================================
# 기본 설정
# ============================================================

st.set_page_config(
    page_title="영화 데이터 그래프 도감",
    layout="wide"
)

st.title("🎬 영화 데이터 그래프 도감")

# ============================================================
# KOBIS API 설정
# ============================================================

try:
    KOBIS_KEY = st.secrets["KOBIS_KEY"]
except Exception:
    st.error("Streamlit Secrets에 KOBIS_KEY를 등록해주세요.")
    st.stop()


# ============================================================
# 어제 날짜 계산
# ============================================================

yesterday = datetime.now() - timedelta(days=1)
target_date = yesterday.strftime("%Y%m%d")


# ============================================================
# KOBIS 일일 박스오피스 API
# ============================================================

url = "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"

params = {
    "key": KOBIS_KEY,
    "targetDt": target_date
}


@st.cache_data(ttl=3600)
def get_boxoffice_data(target_date):

    params = {
        "key": KOBIS_KEY,
        "targetDt": target_date
    }

    response = requests.get(
        url,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    return data["boxOfficeResult"]["dailyBoxOfficeList"]


# ============================================================
# 데이터 가져오기
# ============================================================

try:

    movies = get_boxoffice_data(target_date)

except Exception as e:

    st.error(
        "영화 데이터를 불러오는 중 오류가 발생했습니다."
    )

    st.stop()


# ============================================================
# 기본 데이터프레임
# ============================================================

df = pd.DataFrame(movies)


# ============================================================
# 필요한 컬럼 정리
# ============================================================

# 숫자형 컬럼
numeric_columns = [
    "rank",
    "rankInten",
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

for col in numeric_columns:

    if col in df.columns:

        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )


# ============================================================
# 장르 데이터 가져오기
# ============================================================

@st.cache_data(ttl=3600)
def get_movie_genres(movie_list):

    genre_dict = {}

    detail_url = (
        "https://www.kobis.or.kr/"
        "kobisopenapi/webservice/rest/movie/"
        "searchMovieInfo.json"
    )

    for movie in movie_list:

        movie_code = movie.get("movieCd")

        try:

            response = requests.get(
                detail_url,
                params={
                    "key": KOBIS_KEY,
                    "movieCd": movie_code
                },
                timeout=10
            )

            data = response.json()

            movie_info = (
                data
                .get("movieInfoResult", {})
                .get("movieInfo", {})
            )

            genres = movie_info.get(
                "genres",
                []
            )

            if genres:

                genre_dict[movie_code] = ", ".join(
                    [g["genreNm"] for g in genres]
                )

            else:

                genre_dict[movie_code] = "기타"

        except Exception:

            genre_dict[movie_code] = "기타"

    return genre_dict


# ============================================================
# 장르 추가
# ============================================================

genre_dict = get_movie_genres(movies)

df["genre"] = df["movieCd"].map(
    genre_dict
)

df["genre"] = df["genre"].fillna("기타")


# ============================================================
# total_audi 생성
# ============================================================

df["total_audi"] = pd.to_numeric(
    df["audiAcc"],
    errors="coerce"
)


# ============================================================
# movieNm 정리
# ============================================================

df["movieNm"] = df["movieNm"].fillna(
    "영화명 없음"
)


# ============================================================
# 날짜
# ============================================================

display_date = (
    datetime.strptime(
        target_date,
        "%Y%m%d"
    ).strftime("%Y-%m-%d")
)

st.caption(
    f"📅 기준 날짜: {display_date}"
)


# ============================================================
# 원본 데이터 확인
# ============================================================

with st.expander("📋 원본 데이터 보기"):

    st.dataframe(
        df,
        use_container_width=True
    )


# ============================================================
# ① 일일 관객 수 TOP 10
# ============================================================

st.subheader(
    "① 일일 관객 수 TOP 10"
)

fig1 = px.bar(
    df.head(10),
    x="movieNm",
    y="audiCnt",
    text="audiCnt",
    title="일일 관객 수 TOP 10",
    labels={
        "movieNm": "영화",
        "audiCnt": "일일 관객 수"
    }
)

fig1.update_traces(
    texttemplate="%{text:,}",
    textposition="outside",
    hovertemplate=(
        "<b>%{x}</b><br>"
        "일일 관객: %{y:,}명"
        "<extra></extra>"
    )
)

fig1.update_layout(
    xaxis_tickangle=-45
)

st.plotly_chart(
    fig1,
    use_container_width=True
)


# ============================================================
# ② 장르별 영화 트리맵
# ============================================================

st.subheader(
    "② 장르별 영화 총 관객 트리맵"
)

tree_data = df.dropna(
    subset=[
        "genre",
        "movieNm",
        "total_audi"
    ]
).copy()


if len(tree_data) > 0:

    fig2 = px.treemap(
        tree_data,
        path=[
            "genre",
            "movieNm"
        ],
        values="total_audi",
        title="장르별 영화 총 관객 수",
        custom_data=[
            "movieNm",
            "total_audi"
        ]
    )

    fig2.update_traces(

        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "총 관객: %{customdata[1]:,}명"
            "<extra></extra>"
        )
    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )


else:

    st.warning(
        "트리맵을 만들 데이터가 없습니다."
    )


# ============================================================
# ③ 총 관객 수 히스토그램
# ============================================================

st.subheader(
    "③ 총 관객 수 히스토그램"
)

hist_data = df.dropna(
    subset=[
        "total_audi",
        "movieNm"
    ]
).copy()


if len(hist_data) > 0:

    fig3 = px.histogram(
        hist_data,
        x="total_audi",
        nbins=10,
        title="영화별 총 관객 수 분포",
        labels={
            "total_audi": "총 관객 수"
        }
    )

    fig3.update_traces(
        hovertemplate=(
            "총 관객 수: %{x:,}명<br>"
            "영화 수: %{y}편"
            "<extra></extra>"
        )
    )

    st.plotly_chart(
        fig3,
        use_container_width=True
    )


    # --------------------------------------------------------
    # 대부분의 영화가 어느 구간에 몰려 있는지
    # --------------------------------------------------------

    counts, bins = pd.cut(
        hist_data["total_audi"],
        bins=10,
        retbins=True
    )

    bin_counts = (
        hist_data
        .groupby(counts, observed=False)
        .size()
    )

    most_common_bin = bin_counts.idxmax()

    # --------------------------------------------------------
    # 가장 관객이 많은 영화
    # --------------------------------------------------------

    max_movie = hist_data.loc[
        hist_data["total_audi"].idxmax()
    ]

    st.write(
        f"💡 대부분의 영화는 "
        f"**{most_common_bin.left:,.0f}명 ~ "
        f"{most_common_bin.right:,.0f}명** 구간에 "
        f"몰려 있습니다."
    )

    st.write(
        f"🏆 총 관객이 가장 많은 영화는 "
        f"**{max_movie['movieNm']}**이며, "
        f"총 관객 수는 "
        f"**{max_movie['total_audi']:,.0f}명**입니다."
    )


else:

    st.warning(
        "히스토그램을 만들 데이터가 없습니다."
    )


# ============================================================
# ④ 월 × 요일별 일관객 합계 히트맵
# ============================================================

st.subheader(
    "④ 월 × 요일별 일관객 합계 히트맵"
)

# ------------------------------------------------------------
# 현재 API는 하루치 데이터이므로
# 날짜를 기준으로 월/요일을 생성
# ------------------------------------------------------------

heat_data = df.copy()

heat_data["date"] = pd.to_datetime(
    target_date,
    format="%Y%m%d"
)

heat_data["month"] = (
    heat_data["date"].dt.month
)

weekday_order = [
    "월요일",
    "화요일",
    "수요일",
    "목요일",
    "금요일",
    "토요일",
    "일요일"
]

heat_data["weekday"] = (
    heat_data["date"]
    .dt.dayofweek
    .map(
        dict(
            enumerate(weekday_order)
        )
    )
)

# ------------------------------------------------------------
# 월 × 요일별 일관객 합계
# ------------------------------------------------------------

heatmap_data = (
    heat_data
    .groupby(
        [
            "month",
            "weekday"
        ],
        as_index=False
    )["audiCnt"]
    .sum()
)

heatmap_pivot = (
    heatmap_data
    .pivot(
        index="month",
        columns="weekday",
        values="audiCnt"
    )
)

heatmap_pivot = heatmap_pivot.reindex(
    columns=weekday_order
)

fig4 = px.imshow(
    heatmap_pivot,
    text_auto=True,
    aspect="auto",
    title="월 × 요일별 일관객 합계",
    labels={
        "x": "요일",
        "y": "월",
        "color": "일관객 수"
    }
)

fig4.update_traces(
    hovertemplate=(
        "월: %{y}월<br>"
        "요일: %{x}<br>"
        "일관객 합계: %{z:,}명"
        "<extra></extra>"
    )
)

st.plotly_chart(
    fig4,
    use_container_width=True
)

st.write(
    "💡 색이 진할수록 해당 월·요일의 "
    "일관객 합계가 많습니다."
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
# 영화가 10편 이상인 장르 찾기
# -----------------------------------------

valid_genres = genre_counts[
    genre_counts >= 10
].index.tolist()


# -----------------------------------------
# 10편 이상인 장르가 있으면 해당 장르만 사용
# 없으면 전체 장르 사용
# -----------------------------------------

if len(valid_genres) > 0:

    box_data = df[
        df["genre"].isin(valid_genres)
    ].copy()

    box_title = (
        "영화가 10편 이상인 장르별 총 관객 수"
    )

else:

    # 어제 데이터는 영화 수가 적기 때문에
    # 10편 이상인 장르가 없을 경우 전체 장르 사용

    box_data = df.copy()

    box_title = (
        "장르별 총 관객 수 "
        "(현재 데이터 기준)"
    )


# -----------------------------------------
# 필요한 데이터만 남기기
# -----------------------------------------

box_data = box_data.dropna(
    subset=[
        "genre",
        "total_audi",
        "movieNm"
    ]
).copy()


# -----------------------------------------
# 박스플롯 그리기
# -----------------------------------------

if len(box_data) > 0:

    fig5 = px.box(
        box_data,
        x="genre",
        y="total_audi",
        points="outliers",
        custom_data=[
            "movieNm"
        ],
        title=box_title,
        labels={
            "genre": "장르",
            "total_audi": "총 관객 수"
        }
    )


    # -----------------------------------------
    # 마우스를 이상치에 올렸을 때
    # 영화명과 총 관객 수 표시
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


    # -----------------------------------------
    # 안내 문구
    # -----------------------------------------

    if len(valid_genres) == 0:

        st.write(
            "💡 현재 조회된 데이터에서는 "
            "영화가 10편 이상인 장르가 없어 "
            "전체 장르를 대상으로 상자 그림을 표시했습니다."
        )

    else:

        st.write(
            "💡 영화가 10편 이상인 장르만 표시했습니다. "
            "상자 밖의 점은 이상치를 나타내며, "
            "점에 마우스를 올리면 영화명이 표시됩니다."
        )

else:

    st.warning(
        "상자 그림을 만들 데이터가 없습니다."
    )
