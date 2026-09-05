import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


# ---------------------------------------------------------
# 1. 기본 화면 설정
# ---------------------------------------------------------
st.set_page_config(
    page_title="어제의 박스오피스",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 어제의 박스오피스")
st.caption("KOBIS 영화관입장권통합전산망 기준")


# ---------------------------------------------------------
# 2. 한국 시간 기준으로 '어제' 날짜 계산
# ---------------------------------------------------------
# Streamlit Cloud 서버가 한국 시간이 아닐 수도 있기 때문에
# 반드시 Asia/Seoul 시간대를 지정해서 날짜를 계산한다.
KST = ZoneInfo("Asia/Seoul")

now_kst = datetime.now(KST)
yesterday = now_kst.date() - timedelta(days=1)

# KOBIS API가 요구하는 YYYYMMDD 형식으로 변환
target_date = yesterday.strftime("%Y%m%d")

# 화면에 보여줄 날짜
display_date = yesterday.strftime("%Y년 %m월 %d일")


# ---------------------------------------------------------
# 3. KOBIS API에서 박스오피스 데이터 가져오기
# ---------------------------------------------------------
# st.cache_data를 사용하면 같은 날짜를 다시 조회할 때
# API를 계속 호출하지 않고 약 1시간 동안 저장된 결과를 사용한다.
@st.cache_data(ttl=3600)
def get_boxoffice(target_dt):
    # Streamlit Cloud의 Secrets에서 인증키를 가져온다.
    # 실제 인증키는 코드에 절대로 작성하지 않는다.
    try:
        api_key = st.secrets["KOBIS_KEY"]
    except Exception:
        return {
            "success": False,
            "message": (
                "KOBIS 인증키를 찾을 수 없습니다.\n\n"
                "Streamlit Cloud의 Settings → Secrets에서 "
                "`KOBIS_KEY`가 등록되어 있는지 확인해 주세요."
            ),
            "data": None
        }

    url = (
        "https://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    )

    params = {
        "key": api_key,
        "targetDt": target_dt
    }

    try:
        # KOBIS API 요청
        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        # HTTP 오류 확인
        response.raise_for_status()

        # JSON으로 변환
        result = response.json()

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "message": (
                "KOBIS API 요청 시간이 초과되었습니다.\n\n"
                "잠시 후 다시 실행해 보세요. "
                "인터넷 연결이나 KOBIS 서버 상태도 확인해 주세요."
            ),
            "data": None
        }

    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "message": (
                "KOBIS API에 접속하지 못했습니다.\n\n"
                f"오류 내용: {e}\n\n"
                "인터넷 연결과 KOBIS API 서버 상태를 확인해 주세요."
            ),
            "data": None
        }

    except ValueError:
        return {
            "success": False,
            "message": (
                "KOBIS API에서 정상적인 JSON 데이터를 받지 못했습니다.\n\n"
                "잠시 후 다시 실행해 보세요."
            ),
            "data": None
        }

    # -----------------------------------------------------
    # 4. faultInfo 확인
    # -----------------------------------------------------
    # KOBIS는 인증키가 틀려도 HTTP 상태코드가 200일 수 있다.
    # 따라서 반드시 faultInfo가 있는지 확인해야 한다.
    if "faultInfo" in result:
        fault_info = result["faultInfo"]

        error_message = fault_info.get(
            "message",
            "KOBIS API에서 오류가 발생했습니다."
        )

        return {
            "success": False,
            "message": (
                "KOBIS API에서 오류가 발생했습니다.\n\n"
                f"오류 내용: {error_message}\n\n"
                "다음을 확인해 주세요.\n"
                "• Streamlit Secrets의 KOBIS_KEY가 정확한지\n"
                "• KOBIS API 인증키가 활성화되어 있는지\n"
                "• API 요청 날짜가 올바른지"
            ),
            "data": None
        }

    # -----------------------------------------------------
    # 5. boxOfficeResult 확인
    # -----------------------------------------------------
    boxoffice = result.get("boxOfficeResult")

    if not boxoffice:
        return {
            "success": False,
            "message": (
                "KOBIS에서 박스오피스 결과를 받지 못했습니다.\n\n"
                "KOBIS API 응답 구조와 인증키 설정을 확인해 주세요."
            ),
            "data": None
        }

    movie_list = boxoffice.get("dailyBoxOfficeList", [])

    # 영화 목록이 비어 있는 경우
    if not movie_list:
        return {
            "success": False,
            "message": (
                f"{display_date}의 영화 목록이 비어 있습니다.\n\n"
                "다음을 확인해 주세요.\n"
                "• 조회 날짜에 실제 박스오피스 데이터가 있는지\n"
                "• KOBIS API가 정상적으로 응답했는지\n"
                "• KOBIS 인증키가 정상적으로 설정되어 있는지"
            ),
            "data": None
        }

    return {
        "success": True,
        "message": "",
        "data": movie_list
    }


# ---------------------------------------------------------
# 6. API 데이터 가져오기
# ---------------------------------------------------------
result = get_boxoffice(target_date)


# ---------------------------------------------------------
# 7. API 요청에 실패한 경우 안내
# ---------------------------------------------------------
if not result["success"]:
    st.error(result["message"])
    st.info(
        "💡 문제가 계속되면 Streamlit Cloud의 "
        "Settings → Secrets에서 KOBIS_KEY 설정을 먼저 확인해 주세요."
    )
    st.stop()


# ---------------------------------------------------------
# 8. 영화 데이터를 데이터프레임으로 변환
# ---------------------------------------------------------
df = pd.DataFrame(result["data"])


# ---------------------------------------------------------
# 9. 숫자로 들어와야 하는 항목을 실제 숫자형으로 변환
# ---------------------------------------------------------
# KOBIS API에서는 이 값들이 문자열로 제공되므로
# 정렬과 그래프를 위해 숫자형으로 변환한다.
numeric_columns = [
    "rank",
    "audiCnt",
    "audiAcc",
    "scrnCnt",
    "showCnt",
    "rankInten"
]

for column in numeric_columns:
    if column in df.columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        ).fillna(0)


# 순위를 숫자 기준으로 정렬
df = df.sort_values("rank").reset_index(drop=True)


# ---------------------------------------------------------
# 10. 1위 영화 확인
# ---------------------------------------------------------
if len(df) == 0:
    st.error(
        "영화 데이터가 없습니다. "
        "KOBIS API 응답을 확인해 주세요."
    )
    st.stop()

first_movie = df.iloc[0]


# ---------------------------------------------------------
# 11. 조회 날짜 표시
# ---------------------------------------------------------
st.subheader(f"📅 {display_date}")

st.write(
    "한국 시간 기준으로 어제의 일일 박스오피스를 조회했습니다."
)


# ---------------------------------------------------------
# 12. 1위 영화 정보
# ---------------------------------------------------------
st.header(f"🥇 1위: {first_movie['movieNm']}")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "어제 관객수",
        f"{int(first_movie['audiCnt']):,}명"
    )

with col2:
    st.metric(
        "누적 관객수",
        f"{int(first_movie['audiAcc']):,}명"
    )

with col3:
    st.metric(
        "스크린 수",
        f"{int(first_movie['scrnCnt']):,}개"
    )


# ---------------------------------------------------------
# 13. 전체 박스오피스 표
# ---------------------------------------------------------
st.header("📊 전체 박스오피스")

# 화면에 표시할 열과 한글 이름을 지정한다.
table_df = df[
    [
        "rank",
        "movieNm",
        "openDt",
        "audiCnt",
        "audiAcc",
        "scrnCnt"
    ]
].copy()

table_df.columns = [
    "순위",
    "영화명",
    "개봉일",
    "관객수",
    "누적관객",
    "스크린수"
]


# 숫자를 보기 좋게 쉼표가 들어간 문자열로 표시
# (정렬과 그래프에 사용하는 원본 df는 숫자형 그대로 유지한다.)
display_df = table_df.copy()

display_df["순위"] = display_df["순위"].astype(int)

display_df["관객수"] = display_df["관객수"].apply(
    lambda x: f"{int(x):,}"
)

display_df["누적관객"] = display_df["누적관객"].apply(
    lambda x: f"{int(x):,}"
)

display_df["스크린수"] = display_df["스크린수"].apply(
    lambda x: f"{int(x):,}"
)

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)


# ---------------------------------------------------------
# 14. 관객수 상위 5편 막대그래프
# ---------------------------------------------------------
st.header("📈 관객수 상위 5편")

# 관객수가 많은 순서로 정렬한 뒤 5편만 가져온다.
top5 = (
    df.sort_values(
        "audiCnt",
        ascending=False
    )
    .head(5)
    .copy()
)

# 그래프에 사용할 데이터만 선택한다.
chart_df = top5[
    ["movieNm", "audiCnt"]
].copy()

# 영화명을 인덱스로 설정하면 Streamlit의 bar_chart에서
# 영화별 관객수를 쉽게 막대그래프로 표현할 수 있다.
chart_df = chart_df.set_index("movieNm")

# 막대그래프 표시
st.bar_chart(
    chart_df,
    y="audiCnt"
)

st.caption(
    "※ 관객수는 해당 날짜의 일일 관객수이며, "
    "KOBIS API의 audiCnt 값을 숫자로 변환하여 사용했습니다."
)
```python
# ---------------------------------------------------------
# 장르별 영화순위
# ---------------------------------------------------------

st.header("🎞️ 장르별 영화순위")

st.write(
    "원하는 장르를 선택하면 해당 장르 영화만 모아서 "
    "어제의 관객수 기준으로 순위를 보여줍니다."
)


# ---------------------------------------------------------
# 영화 상세정보 API에서 장르 가져오기
# ---------------------------------------------------------
@st.cache_data(ttl=3600)
def get_movie_genre(movie_cd, api_key):
    """
    영화 코드(movieCd)를 이용해서
    KOBIS 영화 상세정보 API에서 장르를 가져온다.
    """

    url = (
        "https://www.kobis.or.kr/kobisopenapi/webservice/rest/"
        "movie/searchMovieInfo.json"
    )

    params = {
        "key": api_key,
        "movieCd": movie_cd
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        response.raise_for_status()
        result = response.json()

        # API 오류 확인
        if "faultInfo" in result:
            return "장르 미상"

        movie_info = result.get("movieInfoResult", {})
        movie_info = movie_info.get("movieInfo", {})

        genres = movie_info.get("genres", [])

        # 장르 정보가 없는 경우
        if not genres:
            return "장르 미상"

        # 여러 장르가 있다면 쉼표로 연결
        genre_names = [
            genre.get("genreNm", "")
            for genre in genres
            if genre.get("genreNm")
        ]

        if not genre_names:
            return "장르 미상"

        return ", ".join(genre_names)

    except Exception:
        # 장르 하나를 가져오지 못하더라도
        # 전체 앱이 멈추지 않도록 한다.
        return "장르 미상"


# ---------------------------------------------------------
# 인증키 확인
# ---------------------------------------------------------
try:
    api_key = st.secrets["KOBIS_KEY"]
except Exception:
    st.error(
        "KOBIS_KEY를 찾을 수 없습니다. "
        "Streamlit Cloud의 Settings → Secrets에서 "
        "KOBIS_KEY를 등록했는지 확인해 주세요."
    )
    st.stop()


# ---------------------------------------------------------
# 일일 박스오피스 데이터에 영화 코드가 있는지 확인
# ---------------------------------------------------------
if "movieCd" not in df.columns:
    st.error(
        "박스오피스 데이터에 영화 코드(movieCd)가 없습니다."
    )
    st.stop()


# ---------------------------------------------------------
# 각 영화의 장르 가져오기
# ---------------------------------------------------------
with st.spinner("영화 장르 정보를 가져오는 중입니다..."):

    # 영화별 장르를 하나씩 가져온다.
    df["genre"] = df["movieCd"].apply(
        lambda movie_cd: get_movie_genre(
            movie_cd,
            api_key
        )
    )


# ---------------------------------------------------------
# 전체 장르 목록 만들기
# ---------------------------------------------------------
all_genres = set()

for genres in df["genre"]:
    # 영화 하나가 여러 장르를 가지고 있을 수 있으므로
    # 쉼표를 기준으로 장르를 나눈다.
    for genre in genres.split(","):
        genre = genre.strip()

        if genre:
            all_genres.add(genre)


# 장르 이름을 가나다순으로 정렬
genre_list = sorted(all_genres)


# ---------------------------------------------------------
# 장르 선택창
# ---------------------------------------------------------
selected_genre = st.selectbox(
    "🔎 조회할 장르를 선택하세요",
    genre_list
)


# ---------------------------------------------------------
# 선택한 장르에 해당하는 영화만 찾기
# ---------------------------------------------------------
genre_df = df[
    df["genre"].apply(
        lambda genres: selected_genre in [
            g.strip()
            for g in genres.split(",")
        ]
    )
].copy()


# ---------------------------------------------------------
# 선택한 장르의 영화가 없는 경우
# ---------------------------------------------------------
if genre_df.empty:

    st.warning(
        f"어제 박스오피스에는 '{selected_genre}' 장르의 "
        "영화가 없습니다."
    )

else:

    # -----------------------------------------------------
    # 관객수 기준으로 다시 순위 매기기
    # -----------------------------------------------------
    genre_df = genre_df.sort_values(
        "audiCnt",
        ascending=False
    ).reset_index(drop=True)

    # 장르 안에서의 새로운 순위 부여
    genre_df["genreRank"] = range(
        1,
        len(genre_df) + 1
    )


    # -----------------------------------------------------
    # 결과 제목
    # -----------------------------------------------------
    st.subheader(
        f"🏆 {selected_genre} 영화순위"
    )

    st.caption(
        f"{display_date} 관객수 기준"
    )


    # -----------------------------------------------------
    # 1위 영화 강조
    # -----------------------------------------------------
    genre_first = genre_df.iloc[0]

    st.success(
        f"🥇 {selected_genre} 1위: "
        f"{genre_first['movieNm']}"
    )


    # -----------------------------------------------------
    # 장르별 순위 표 만들기
    # -----------------------------------------------------
    genre_table = genre_df[
        [
            "genreRank",
            "movieNm",
            "genre",
            "openDt",
            "audiCnt",
            "audiAcc",
            "scrnCnt"
        ]
    ].copy()

    genre_table.columns = [
        "장르순위",
        "영화명",
        "장르",
        "개봉일",
        "관객수",
        "누적관객",
        "스크린수"
    ]


    # 숫자를 보기 좋게 표시
    genre_table["장르순위"] = (
        genre_table["장르순위"].astype(int)
    )

    genre_table["관객수"] = (
        genre_table["관객수"]
        .astype(int)
        .apply(lambda x: f"{x:,}")
    )

    genre_table["누적관객"] = (
        genre_table["누적관객"]
        .astype(int)
        .apply(lambda x: f"{x:,}")
    )

    genre_table["스크린수"] = (
        genre_table["스크린수"]
        .astype(int)
        .apply(lambda x: f"{x:,}")
    )


    # -----------------------------------------------------
    # 표 출력
    # -----------------------------------------------------
    st.dataframe(
        genre_table,
        use_container_width=True,
        hide_index=True
    )


    # -----------------------------------------------------
    # 장르별 관객수 그래프
    # -----------------------------------------------------
    st.subheader(
        f"📊 {selected_genre} 관객수 TOP 5"
    )

    # 최대 5편까지만 그래프로 표시
    genre_top5 = genre_df.head(5).copy()

    chart_data = genre_top5[
        ["movieNm", "audiCnt"]
    ].copy()

    chart_data = chart_data.set_index(
        "movieNm"
    )

    st.bar_chart(
        chart_data,
        y="audiCnt"
    )
```
