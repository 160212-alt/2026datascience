import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime, timedelta


# ============================================================
# 기본 설정
# ============================================================

st.set_page_config(
    page_title="영화 데이터 그래프 도감",
    layout="wide"
)

st.title("🎬 영화 데이터 그래프 도감")


# ============================================================
# KOBIS API KEY
# ============================================================

try:
    KOBIS_KEY = st.secrets["KOBIS_KEY"]

except Exception:
    st.error(
        "Streamlit Secrets에 KOBIS_KEY를 등록해주세요."
    )
    st.stop()


# ============================================================
# 어제 날짜
# ============================================================

yesterday = datetime.now() - timedelta(days=1)

target_date = yesterday.strftime("%Y%m%d")

display_date = yesterday.strftime("%Y-%m-%d")

st.caption(
    f"📅 기준 날짜: {display_date}"
)


# ============================================================
# KOBIS 일일 박스오피스 API
# ============================================================

@st.cache_data(ttl=3600)
def get_boxoffice_data(target_date):

    url = (
        "https://www.kobis.or.kr/"
        "kobisopenapi/webservice/rest/boxoffice/"
        "searchDailyBoxOfficeList.json"
    )

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

    return (
        data
        .get("boxOfficeResult", {})
        .get("dailyBoxOfficeList", [])
    )


# ============================================================
# 데이터 불러오기
# ============================================================

try:

    movies = get_boxoffice_data(
        target_date
    )

except Exception as e:

    st.error(
        f"영화 데이터를 불러오는 중 오류가 발생했습니다.\n\n{e}"
    )

    st.stop()


if not movies:

    st.warning(
        "해당 날짜의 영화 데이터가 없습니다."
    )

    st.stop()


# ============================================================
# 데이터프레임
# ============================================================

df = pd.DataFrame(
    movies
)


# ============================================================
# 숫자형 컬럼 변환
# ============================================================

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
# total_audi 생성
# ============================================================

df["total_audi"] = pd.to_numeric(
    df["audiAcc"],
    errors="coerce"
)


# ============================================================
# 영화명 정리
# ============================================================

df["movieNm"] = df[
    "movieNm"
].fillna(
    "영화명 없음"
)


# ============================================================
# 영화별 장르 가져오기
# ============================================================

@st.cache_data(ttl=3600)
def get_movie_genres(movie_codes):

    genre_dict = {}

    detail_url = (
        "https://www.kobis.or.kr/"
        "kobisopenapi/webservice/rest/movie/"
        "searchMovieInfo.json"
    )

    for movie_code in movie_codes:

        try:

            response = requests.get(
                detail_url,
                params={
                    "key": KOBIS_KEY,
                    "movieCd": movie_code
                },
                timeout=10
            )

            response.raise_for_status()

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
                    genre["genreNm"]
                    for genre in genres
                )

            else:

                genre_dict[movie_code] = "기타"

        except Exception:

            genre_dict[movie_code] = "기타"

    return genre_dict


# ============================================================
# 장르 데이터 추가
# ============================================================

movie_codes = tuple(
    df["movieCd"]
    .dropna()
    .tolist()
)

genre_dict = get_movie_genres(
    movie_codes
)

df["genre"] = df[
    "movieCd"
].map(
    genre_dict
)

df["genre"] = df[
    "genre"
].fillna(
    "기타"
)


# ============================================================
# first_week_audi가 있으면 숫자로 변환
# ============================================================

if "first_week_audi" in df.columns:

    df["first_week_audi"] = pd.to_numeric(
        df["first_week_audi"],
        errors="coerce"
    )


# ============================================================
# 원본 데이터 보기
# ============================================================

with st.expander(
    "📋 원본 데이터 보기"
):

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

top10 = (
    df
    .sort_values(
        "audiCnt",
        ascending=False
    )
    .head(10)
    .copy()
)


fig1 = px.bar(
    top10,
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
# ② 장르별 영화 총 관객 트리맵
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
    # 가장 많이 몰린 구간
    # --------------------------------------------------------

    counts, bins = pd.cut(
        hist_data["total_audi"],
        bins=10,
        retbins=True
    )


    bin_counts = (
        hist_data
        .groupby(
            counts,
            observed=False
        )
        .size()
    )


    if len(bin_counts) > 0:

        most_common_bin = (
            bin_counts.idxmax()
        )

        st.write(
            f"💡 대부분의 영화는 "
            f"**{most_common_bin.left:,.0f}명 ~ "
            f"{most_common_bin.right:,.0f}명** 구간에 "
            f"몰려 있습니다."
        )


    # --------------------------------------------------------
    # 가장 관객이 많은 영화
    # --------------------------------------------------------

    max_movie = hist_data.loc[
        hist_data["total_audi"].idxmax()
    ]


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
# ④ 일일 관객 수와 총 관객 수의 관계 산점도
# ============================================================

st.subheader(
    "④ 일일 관객 수와 총 관객 수의 관계"
)


scatter_data = df.dropna(
    subset=[
        "audiCnt",
        "total_audi",
        "movieNm"
    ]
).copy()


if len(scatter_data) > 0:

    fig4 = px.scatter(
        scatter_data,
        x="audiCnt",
        y="total_audi",
        hover_name="movieNm",
        title="일일 관객 수와 총 관객 수의 관계",
        labels={
            "audiCnt": "일일 관객 수",
            "total_audi": "총 관객 수"
        }
    )


    fig4.update_traces(
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "일일 관객: %{x:,}명<br>"
            "총 관객: %{y:,}명"
            "<extra></extra>"
        )
    )


    st.plotly_chart(
        fig4,
        use_container_width=True
    )


else:

    st.warning(
        "산점도를 만들 데이터가 없습니다."
    )


# ============================================================
# ⑤ 장르별 총 관객 수 상자 그림
#    ★ 영화가 10편 이하인 장르만
# ============================================================

st.subheader(
    "⑤ 장르별 총 관객 수 상자 그림"
)


genre_counts = (
    df["genre"]
    .value_counts()
)


# ★ 10편 이하인 장르만 선택
valid_genres = genre_counts[
    genre_counts <= 10
].index.tolist()


box_data = df[
    df["genre"].isin(
        valid_genres
    )
].copy()


box_data = box_data.dropna(
    subset=[
        "genre",
        "total_audi",
        "movieNm"
    ]
)


if len(box_data) > 0:

    fig5 = px.box(
        box_data,
        x="genre",
        y="total_audi",
        points="outliers",
        custom_data=[
            "movieNm"
        ],
        title="영화가 10편 이하인 장르별 총 관객 수",
        labels={
            "genre": "장르",
            "total_audi": "총 관객 수"
        }
    )


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
        "💡 영화가 10편 이하인 장르만 표시했습니다. "
        "상자 밖의 점은 이상치이며, "
        "점에 마우스를 올리면 영화명이 표시됩니다."
    )


else:

    st.info(
        "현재 데이터에는 영화가 10편 이하인 장르가 없습니다."
    )


# ============================================================
# ⑥ 첫 주 관객 수를 점 크기로 넣은 버블 그래프
# ============================================================

st.subheader(
    "⑥ 첫 주 관객 수를 반영한 버블 그래프"
)


# ------------------------------------------------------------
# first_week_audi 컬럼 존재 여부 확인
# ------------------------------------------------------------

if "first_week_audi" in df.columns:

    bubble_data = df.dropna(
        subset=[
            "audiCnt",
            "total_audi",
            "first_week_audi",
            "movieNm"
        ]
    ).copy()


    # 첫 주 관객 수가 0보다 큰 데이터만 사용
    bubble_data = bubble_data[
        bubble_data["first_week_audi"] > 0
    ]


    if len(bubble_data) > 0:

        fig6 = px.scatter(
            bubble_data,
            x="audiCnt",
            y="total_audi",
            size="first_week_audi",
            hover_name="movieNm",
            size_max=60,
            title=(
                "일일 관객 수 × 총 관객 수 "
                "(버블 크기 = 첫 주 관객)"
            ),
            labels={
                "audiCnt": "일일 관객 수",
                "total_audi": "총 관객 수",
                "first_week_audi": "첫 주 관객 수"
            }
        )


        fig6.update_traces(
            hovertemplate=(
                "<b>%{hovertext}</b><br>"
                "일일 관객: %{x:,}명<br>"
                "총 관객: %{y:,}명<br>"
                "첫 주 관객: %{marker.size:,}명"
                "<extra></extra>"
            )
        )


        fig6.update_layout(
            xaxis_title="일일 관객 수",
            yaxis_title="총 관객 수"
        )


        st.plotly_chart(
            fig6,
            use_container_width=True
        )


        st.write(
            "💡 버블이 클수록 첫 주 관객 수가 많은 영화입니다."
        )


    else:

        st.info(
            "first_week_audi 값이 있는 데이터가 없어 "
            "버블 그래프를 표시할 수 없습니다."
        )


else:

    st.info(
        "현재 KOBIS 일일 박스오피스 데이터에는 "
        "first_week_audi(첫 주 관객) 항목이 없습니다. "
        "첫 주 관객 데이터가 포함된 누적 데이터를 사용하면 "
        "⑥ 버블 그래프를 만들 수 있습니다."
    )
