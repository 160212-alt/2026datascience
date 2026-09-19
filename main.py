import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans


# =========================================================
# 페이지 설정
# =========================================================
st.set_page_config(
    page_title="영화 유형 나누기",
    page_icon="🎬",
    layout="wide"
)


# =========================================================
# 제목
# =========================================================
st.title("🎬 영화 유형 나누기")
st.write("영화의 흥행 특성을 바탕으로 비슷한 영화끼리 세 유형으로 나눕니다.")


# =========================================================
# 데이터 불러오기
# =========================================================
DATA_URL = (
    "https://raw.githubusercontent.com/greatsong/modudata/"
    "main/data/kobis_movies.csv"
)


@st.cache_data
def load_data():
    return pd.read_csv(
        DATA_URL,
        encoding="utf-8"
    )


try:
    df = load_data()

except Exception as e:
    st.error("데이터를 불러오는 중 오류가 발생했습니다.")
    st.code(str(e))
    st.stop()


# =========================================================
# 필요한 열 확인
# =========================================================
required_columns = [
    "movieCd",
    "movieNm",
    "openDt",
    "genre",
    "nation",
    "first_scrn",
    "first_show",
    "first_date",
    "peak",
    "first_week_audi",
    "total_audi",
    "days_in_top10"
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    st.error(
        "다음 열이 데이터에 없습니다: "
        + ", ".join(missing_columns)
    )
    st.stop()


# =========================================================
# 숫자형 변환
# =========================================================
numeric_columns = [
    "first_scrn",
    "first_show",
    "first_date",
    "peak",
    "first_week_audi",
    "total_audi",
    "days_in_top10"
]

for col in numeric_columns:
    df[col] = pd.to_numeric(
        df[col],
        errors="coerce"
    )


# =========================================================
# 전체 영화 수
# =========================================================
total_count = len(df)


# =========================================================
# 롱런 지수 만들기
# 누적 관객 / 첫 주 관객
# 20 초과는 20으로 제한
# =========================================================
df["롱런 지수"] = (
    df["total_audi"] / df["first_week_audi"]
)

df["롱런 지수"] = df["롱런 지수"].clip(
    upper=20
)


# =========================================================
# 로그 변환
# 스크린 수와 누적 관객에 상용로그 적용
# =========================================================
df["로그 스크린 수"] = df["first_scrn"].apply(
    lambda x: __import__("math").log10(x)
    if pd.notna(x) and x > 0
    else None
)

df["로그 누적 관객"] = df["total_audi"].apply(
    lambda x: __import__("math").log10(x)
    if pd.notna(x) and x > 0
    else None
)


# =========================================================
# 군집 분석용 속성
# =========================================================
feature_map = {
    "스크린 수": "로그 스크린 수",
    "누적 관객": "로그 누적 관객",
    "10위권 일수": "days_in_top10",
    "롱런 지수": "롱런 지수"
}


feature_labels = {
    "스크린 수": "스크린 수 (로그)",
    "누적 관객": "누적 관객 (로그)",
    "10위권 일수": "10위권 일수",
    "롱런 지수": "롱런 지수"
}


# =========================================================
# 결측값 및 첫 주 관객 0인 영화 제거
# =========================================================
analysis_columns = [
    "로그 스크린 수",
    "로그 누적 관객",
    "days_in_top10",
    "롱런 지수",
    "first_week_audi"
]

valid_mask = (
    df[analysis_columns].notna().all(axis=1)
    & (df["first_week_audi"] > 0)
)

analysis_df = df.loc[
    valid_mask
].copy()


# =========================================================
# 화면 위에 전체 편수 / 분석 편수 표시
# =========================================================
st.info(
    f"전체 영화: **{total_count}편**  |  "
    f"묶은 영화: **{len(analysis_df)}편**"
)


# =========================================================
# 사용할 속성 선택
# =========================================================
st.subheader("⚙️ 묶는 데 사용할 속성")

selected_labels = st.multiselect(
    "속성을 두 개 이상 선택하세요.",
    options=list(feature_map.keys()),
    default=list(feature_map.keys()),
    format_func=lambda x: feature_labels[x]
)


if len(selected_labels) < 2:
    st.warning(
        "K-평균 군집 분석을 위해 속성을 2개 이상 선택해 주세요."
    )
    st.stop()


selected_columns = [
    feature_map[x]
    for x in selected_labels
]


# =========================================================
# 군집 분석 데이터
# =========================================================
X = analysis_df[
    selected_columns
].copy()


# =========================================================
# 표준화
# =========================================================
scaler = StandardScaler()

X_scaled = scaler.fit_transform(X)


# =========================================================
# K-means
# 난수 고정
# =========================================================
kmeans = KMeans(
    n_clusters=3,
    random_state=42,
    n_init=10
)

analysis_df["원래_군집"] = kmeans.fit_predict(
    X_scaled
)


# =========================================================
# 군집별 누적 관객 평균 계산
# =========================================================
cluster_total_mean = (
    analysis_df
    .groupby("원래_군집")["total_audi"]
    .mean()
    .sort_values(
        ascending=False
    )
)


# =========================================================
# 누적 관객 평균이 큰 군집부터
# ㉮ → ㉯ → ㉰
# =========================================================
cluster_symbols = {
    cluster: symbol
    for cluster, symbol in zip(
        cluster_total_mean.index,
        ["㉮", "㉯", "㉰"]
    )
}


analysis_df["군집"] = (
    analysis_df["원래_군집"]
    .map(cluster_symbols)
)


# =========================================================
# 2차원 산점도
# =========================================================
st.subheader("📊 2차원 산점도")

col1, col2 = st.columns(2)

with col1:
    x_axis = st.selectbox(
        "가로축 속성",
        options=selected_labels,
        format_func=lambda x: feature_labels[x],
        index=0
    )

with col2:

    # y축은 가능한 경우 x축과 다른 값을 기본으로 선택
    if len(selected_labels) > 1:
        default_y = 1
    else:
        default_y = 0

    y_axis = st.selectbox(
        "세로축 속성",
        options=selected_labels,
        format_func=lambda x: feature_labels[x],
        index=default_y
    )


scatter_df = analysis_df.copy()

scatter_df["군집 표시"] = (
    "㉮" + ""
)

scatter_df["군집 표시"] = (
    scatter_df["군집"]
)


fig_2d = px.scatter(
    scatter_df,
    x=feature_map[x_axis],
    y=feature_map[y_axis],
    color="군집 표시",
    hover_name="movieNm",
    hover_data={
        feature_map[x_axis]: ":.2f",
        feature_map[y_axis]: ":.2f",
        "군집 표시": True
    },
    labels={
        feature_map[x_axis]: feature_labels[x_axis],
        feature_map[y_axis]: feature_labels[y_axis],
        "군집 표시": "영화 유형"
    }
)

fig_2d.update_traces(
    marker={
        "size": 7
    }
)

fig_2d.update_layout(
    height=600
)

st.plotly_chart(
    fig_2d,
    use_container_width=True
)


# =========================================================
# 3차원 산점도
# =========================================================
st.subheader("🌐 3차원 산점도")

if len(selected_labels) < 3:

    st.info(
        "3차원 산점도를 그리려면 묶는 데 사용할 속성을 "
        "3개 이상 선택해 주세요."
    )

else:

    col1, col2, col3 = st.columns(3)

    with col1:

        x3 = st.selectbox(
            "X축",
            options=selected_labels,
            format_func=lambda x: feature_labels[x],
            key="x3"
        )

    with col2:

        y3 = st.selectbox(
            "Y축",
            options=selected_labels,
            format_func=lambda x: feature_labels[x],
            key="y3"
        )

    with col3:

        z3 = st.selectbox(
            "Z축",
            options=selected_labels,
            format_func=lambda x: feature_labels[x],
            key="z3"
        )


    fig_3d = px.scatter_3d(
        analysis_df,
        x=feature_map[x3],
        y=feature_map[y3],
        z=feature_map[z3],
        color="군집",
        hover_name="movieNm",
        hover_data={
            feature_map[x3]: ":.2f",
            feature_map[y3]: ":.2f",
            feature_map[z3]: ":.2f",
            "군집": True
        },
        labels={
            feature_map[x3]: feature_labels[x3],
            feature_map[y3]: feature_labels[y3],
            feature_map[z3]: feature_labels[z3],
            "군집": "영화 유형"
        }
    )

    fig_3d.update_traces(
        marker={
            "size": 3
        }
    )

    fig_3d.update_layout(
        height=700
    )

    st.plotly_chart(
        fig_3d,
        use_container_width=True
    )


# =========================================================
# 군집별 편수와 평균
# =========================================================
st.subheader("📋 영화 유형별 특징")

summary = (
    analysis_df
    .groupby("군집")
    .agg(
        편수=("movieNm", "count"),
        스크린수_평균=("first_scrn", "mean"),
        누적관객_평균=("total_audi", "mean"),
        십위권일수_평균=("days_in_top10", "mean"),
        롱런지수_평균=("롱런 지수", "mean")
    )
    .reset_index()
)


# ㉮ → ㉯ → ㉰ 순서
symbol_order = ["㉮", "㉯", "㉰"]

summary["순서"] = summary["군집"].map(
    {
        "㉮": 0,
        "㉯": 1,
        "㉰": 2
    }
)

summary = summary.sort_values(
    "순서"
).drop(
    columns="순서"
)


summary = summary.rename(
    columns={
        "군집": "영화 유형",
        "스크린수_평균": "스크린 수 평균",
        "누적관객_평균": "누적 관객 평균",
        "십위권일수_평균": "10위권 일수 평균",
        "롱런지수_평균": "롱런 지수 평균"
    }
)


st.dataframe(
    summary.style.format(
        {
            "편수": "{:,.0f}",
            "스크린 수 평균": "{:,.1f}",
            "누적 관객 평균": "{:,.0f}",
            "10위권 일수 평균": "{:,.1f}",
            "롱런 지수 평균": "{:,.2f}"
        }
    ),
    use_container_width=True,
    hide_index=True
)


# =========================================================
# 유형별 누적 관객 TOP 5
# =========================================================
st.subheader("🏆 영화 유형별 누적 관객 TOP 5")

for symbol in ["㉮", "㉯", "㉰"]:

    group = analysis_df[
        analysis_df["군집"] == symbol
    ].sort_values(
        by="total_audi",
        ascending=False
    ).head(5)

    st.markdown(
        f"### {symbol}"
    )

    if len(group) == 0:

        st.write("해당 유형의 영화가 없습니다.")

    else:

        top5 = group[
            ["movieNm", "total_audi"]
        ].copy()

        top5.columns = [
            "영화 제목",
            "누적 관객"
        ]

        st.dataframe(
            top5.style.format(
                {
                    "누적 관객": "{:,.0f}"
                }
            ),
            use_container_width=True,
            hide_index=True
        )
