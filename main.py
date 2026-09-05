import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


# --------------------------------------------------
# 1. 기본 설정
# --------------------------------------------------

st.set_page_config(
    page_title="어제의 박스오피스",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 어제의 박스오피스")
st.write("KOBIS 영화관입장권통합전산망 데이터를 이용한 영화 순위")


# --------------------------------------------------
# 2. 한국 시간 기준으로 '어제' 날짜 구하기
# --------------------------------------------------

kst = ZoneInfo("Asia/Seoul")

today_kst = datetime.now(kst)
yesterday_kst = today_kst - timedelta(days=1)

target_date = yesterday_kst.strftime("%Y%m%d")
target_date_text = yesterday_kst.strftime("%Y년 %m월 %d일")


# --------------------------------------------------
# 3. KOBIS API 주소
# --------------------------------------------------

BOXOFFICE_URL = (
    "https://www.kobis.or.kr/kobisopenapi/webservice/rest/"
    "boxoffice/searchDailyBoxOfficeList.json"
)

MOVIE_INFO_URL = (
    "https://www.kobis.or.kr/kobisopenapi/webservice/rest/"
    "movie/searchMovieInfo.json"
)


# --------------------------------------------------
# 4. API 키 가져오기
# --------------------------------------------------

try:
    KOBIS_KEY = st.secrets["KOBIS_KEY"]
except Exception:
    st.error(
        "KOBIS_KEY를 찾을 수 없습니다.\n\n"
        "Streamlit Cloud의 Settings → Secrets에 "
        "KOBIS_KEY를 등록했는지 확인해주세요."
    )
    st.stop()


# --------------------------------------------------
# 5. 어제의 박스오피스 데이터 가져오기
#    같은 날짜의 데이터는 1시간 동안 캐시
# --------------------------------------------------

@st.cache_data(ttl=3600)
def get_boxoffice_data(target_date, api_key):

    params = {
        "key": api_key,
        "targetDt": target_date
    }

    try:
        response = requests.get(
            BOXOFFICE_URL,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

    except Exception:
        return None, "KOBIS API에 연결할 수 없습니다."

    # API에서 오류 정보를 보내는 경우
    if "faultInfo" in data:
        fault = data["faultInfo"]

        message = fault.get(
            "message",
            "KOBIS API에서 오류가 발생했습니다."
        )

        return None, message

    try:
        movie_list = data["boxOfficeResult"]["dailyBoxOfficeList"]
    except Exception:
        return None, "박스오피스 데이터를 가져오지 못했습니다."

    if not movie_list:
        return None, "해당 날짜의 박스오피스 데이터가 없습니다."

    df = pd.DataFrame(movie_list)

    return df, None


# --------------------------------------------------
# 6. 영화별 장르 가져오기
# --------------------------------------------------

@st.cache_data(ttl=3600)
def get_movie_genre(movie_code, api_key):

    params = {
        "key": api_key,
        "movieCd": movie_code
    }

    try:
        response = requests.get(
            MOVIE_INFO_URL,
            params=params,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

    except Exception:
        return "장르 미상"

    # API 오류 확인
    if "faultInfo" in data:
        return "장르 미상"

    try:
        genres = data["movieInfoResult"]["movieInfo"]["genres"]

        if not genres:
            return "장르 미상"

        # 여러 장르가 있으면 "/"로 연결
        genre_names = []

        for genre in genres:
            genre_name = genre.get("genreNm")

            if genre_name:
                genre_names.append(genre_name)

        if genre_names:
            return " / ".join(genre_names)

    except Exception:
        pass

    return "장르 미상"


# --------------------------------------------------
# 7. 박스오피스 데이터 가져오기
# --------------------------------------------------

df, error_message = get_boxoffice_data(
    target_date,
    KOBIS_KEY
)

if error_message:
    st.error(error_message)
    st.info(
        "잠시 후 다시 시도하거나 KOBIS API 키와 "
        "Streamlit Secrets 설정을 확인해주세요."
    )
    st.stop()


# --------------------------------------------------
# 8. 숫자 데이터를 숫자로 변환
# --------------------------------------------------

numeric_columns = [
    "rank",
    "audiCnt",
    "audiAcc",
    "scrnCnt"
]

for column in numeric_columns:
    if column in df.columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        ).fillna(0)


# --------------------------------------------------
# 9. 영화 장르 가져오기
# --------------------------------------------------

genres = []

for movie_code in df["movieCd"]:
    genre = get_movie_genre(
        movie_code,
        KOBIS_KEY
    )

    genres.append(genre)

df["genre"] = genres


# --------------------------------------------------
# 10. 날짜 표시
# --------------------------------------------------

st.subheader(f"📅 {target_date_text} 박스오피스")


# --------------------------------------------------
# 11. 1위 영화 정보
# --------------------------------------------------

first_movie = df.iloc[0]

st.markdown("## 🏆 박스오피스 1위")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "1위 영화",
        first_movie["movieNm"]
    )

with col2:
    st.metric(
        "일일 관객 수",
        f"{int(first_movie['audiCnt']):,}명"
    )

with col3:
    st.metric(
        "누적 관객 수",
        f"{int(first_movie['audiAcc']):,}명"
    )


# --------------------------------------------------
# 12. 전체 박스오피스 표
# --------------------------------------------------

st.markdown("## 🎞️ 전체 영화 순위")

display_df = df[
    [
        "rank",
        "movieNm",
        "genre",
        "openDt",
        "audiCnt",
        "audiAcc",
        "scrnCnt"
    ]
].copy()

display_df.columns = [
    "순위",
    "영화명",
    "장르",
    "개봉일",
    "일일 관객 수",
    "누적 관객 수",
    "상영 스크린 수"
]

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)


# --------------------------------------------------
# 13. 장르별 영화 순위
# --------------------------------------------------

st.markdown("---")
st.header("🎭 장르별 영화 순위")

st.write(
    "원하는 장르를 선택하면 해당 장르의 영화만 "
    "관객 수를 기준으로 순위를 매깁니다."
)


# 장르 목록 만들기
all_genres = []

for genre_text in df["genre"]:

    # 여러 장르가 "/"로 연결되어 있을 수 있음
    for genre in genre_text.split(" / "):

        if genre not in all_genres:
            all_genres.append(genre)


# 가나다순으로 정렬
all_genres = sorted(all_genres)


if not all_genres:

    st.warning("장르 데이터를 찾을 수 없습니다.")

else:

    # --------------------------------------------------
    # 14. 장르 선택 창
    # --------------------------------------------------

    selected_genre = st.selectbox(
        "🎬 장르를 선택하세요",
        all_genres
    )


    # --------------------------------------------------
    # 15. 선택한 장르의 영화만 가져오기
    # --------------------------------------------------

    genre_df = df[
        df["genre"].str.contains(
            selected_genre,
            na=False
        )
    ].copy()


    # --------------------------------------------------
    # 16. 관객 수 기준으로 순위 정렬
    # --------------------------------------------------

    genre_df = genre_df.sort_values(
        by="audiCnt",
        ascending=False
    ).reset_index(drop=True)


    # 새로운 장르 순위 만들기
    genre_df["genreRank"] = range(
        1,
        len(genre_df) + 1
    )


    # --------------------------------------------------
    # 17. 선택한 장르의 영화 개수
    # --------------------------------------------------

    st.success(
        f"🎭 {selected_genre} 영화는 "
        f"총 {len(genre_df)}편입니다."
    )


    if genre_df.empty:

        st.warning(
            f"{selected_genre} 장르의 영화가 없습니다."
        )

    else:

        # --------------------------------------------------
        # 18. 장르별 순위 표
        # --------------------------------------------------

        genre_display_df = genre_df[
            [
                "genreRank",
                "movieNm",
                "openDt",
                "audiCnt",
                "audiAcc",
                "scrnCnt"
            ]
        ].copy()

        genre_display_df.columns = [
            "장르 순위",
            "영화명",
            "개봉일",
            "일일 관객 수",
            "누적 관객 수",
            "상영 스크린 수"
        ]

        st.dataframe(
            genre_display_df,
            use_container_width=True,
            hide_index=True
        )


        # --------------------------------------------------
        # 19. 장르별 TOP 5 그래프
        # --------------------------------------------------

        st.subheader(
            f"📊 {selected_genre} 장르 TOP 5"
        )

        top5 = genre_df.head(5).copy()

        chart_df = top5[
            [
                "movieNm",
                "audiCnt"
            ]
        ].copy()

        chart_df.columns = [
            "영화명",
            "관객 수"
        ]

        # 영화명을 인덱스로 설정
        chart_df = chart_df.set_index("영화명")

        st.bar_chart(chart_df)


# --------------------------------------------------
# 20. 데이터 출처
# --------------------------------------------------

st.markdown("---")

st.caption(
    "※ 데이터 출처: 영화관입장권통합전산망(KOBIS) Open API"
)
