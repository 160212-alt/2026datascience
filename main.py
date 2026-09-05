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
