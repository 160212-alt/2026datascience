import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score


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

st.write(
    "영화의 흥행 특성을 바탕으로 비슷한 영화끼리 유형으로 나눕니다."
)


# =========================================================
# 데이터 주소
# =========================================================
DATA_URL = (
    "https://raw.githubusercontent.com/greatsong/modudata/"
    "main/data/kobis_movies.csv"
)


# =========================================================
# 데이터 불러오기
# =========================================================
@st.cache_data
def load_data():

    return pd.read_csv(
        DATA_URL,
        encoding="utf-8"
    )


try:

    df = load_data()

except Exception as e:

    st.error(
        "데이터를 불러오는 중 오류가 발생했습니다."
    )

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
    col
    for col in required_columns
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
# 롱런 지수
# 누적 관객 / 첫 주 관객
# 20 초과 → 20
# =========================================================
df["롱런 지수"] = (
    df["total_audi"]
    / df["first_week_audi"]
)

df["롱런 지수"] = df[
    "롱런 지수"
].clip(
    upper=20
)


# =========================================================
# 상용로그 변환
# =========================================================
df["로그 스크린 수"] = df[
    "first_scrn"
].apply(
    lambda x:
        __import__("math").log10(x)
        if pd.notna(x) and x > 0
        else None
)


df["로그 누적 관객"] = df[
    "total_audi"
].apply(
    lambda x:
        __import__("math").log10(x)
        if pd.notna(x) and x > 0
        else None
)


# =========================================================
# 네 가지 속성 이름
# =========================================================
feature_map = {

    "스크린 수":
        "로그 스크린 수",

    "누적 관객":
        "로그 누적 관객",

    "10위권 일수":
        "days_in_top10",

    "롱런 지수":
        "롱런 지수"
}


feature_labels = {

    "스크린 수":
        "스크린 수 (로그)",

    "누적 관객":
        "누적 관객 (로그)",

    "10위권 일수":
        "10위권 일수",

    "롱런 지수":
        "롱런 지수"
}


# =========================================================
# 분석에 사용할 영화만 남기기
#
# 네 속성 중 하나라도 없거나
# 첫 주 관객이 0이면 제외
# =========================================================
valid_columns = [

    "로그 스크린 수",

    "로그 누적 관객",

    "days_in_top10",

    "롱런 지수",

    "first_week_audi"
]


valid_mask = (

    df[valid_columns]
    .notna()
    .all(axis=1)

    &

    (df["first_week_audi"] > 0)
)


analysis_df = df.loc[
    valid_mask
].copy()


# =========================================================
# 전체 편수 / 묶은 편수
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

    "묶음 분석에 사용할 속성을 선택하세요. "
    "두 개 이상 선택해야 합니다.",

    options=list(
        feature_map.keys()
    ),

    default=list(
        feature_map.keys()
    ),

    format_func=lambda x:
        feature_labels[x]
)


if len(selected_labels) < 2:

    st.warning(
        "속성을 두 개 이상 선택해 주세요."
    )

    st.stop()


selected_columns = [

    feature_map[x]
    for x in selected_labels

]


# =========================================================
# 묶음 수 선택
# =========================================================
st.subheader("🔢 묶음 수 정하기")


cluster_count = st.slider(

    "묶음 수",

    min_value=2,

    max_value=7,

    value=3,

    step=1

)


st.write(
    f"현재 선택한 묶음 수: **{cluster_count}개**"
)


# =========================================================
# 선택한 속성만 사용해서 표준화
# =========================================================
X = analysis_df[
    selected_columns
].copy()


scaler = StandardScaler()


X_scaled = scaler.fit_transform(
    X
)


# =========================================================
# 현재 선택한 묶음 수로 K-means
# =========================================================
kmeans = KMeans(

    n_clusters=cluster_count,

    random_state=42,

    n_init=10

)


analysis_df["원래_군집"] = (
    kmeans.fit_predict(
        X_scaled
    )
)


# =========================================================
# 군집별 누적 관객 평균
# =========================================================
cluster_total_mean = (

    analysis_df
    .groupby("원래_군집")
    ["total_audi"]
    .mean()
    .sort_values(
        ascending=False
    )

)


# =========================================================
# 군집 표시 기호
# =========================================================
symbols = [
    "㉮",
    "㉯",
    "㉰",
    "㉱",
    "㉲",
    "㉳",
    "㉴"
]


cluster_symbols = {

    cluster: symbols[i]

    for i, cluster
    in enumerate(
        cluster_total_mean.index
    )

}


analysis_df["군집"] = (

    analysis_df[
        "원래_군집"
    ]
    .map(cluster_symbols)

)


# =========================================================
# 현재 선택된 군집 수의 실루엣 점수
# =========================================================
if cluster_count >= 2:

    current_silhouette = silhouette_score(

        X_scaled,

        analysis_df[
            "원래_군집"
        ]

    )

else:

    current_silhouette = None


# =========================================================
# 현재 실루엣 점수
# =========================================================
st.subheader("📐 현재 묶음의 실루엣 점수")


st.write(

    f"현재 묶음 수 **{cluster_count}개**의 "
    f"실루엣 점수: **{current_silhouette:.3f}**  "
    f"(−1 ~ 1, 1에 가까울수록 묶음이 뚜렷함)"

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

        format_func=lambda x:
            feature_labels[x],

        index=0,

        key="x_axis"

    )


with col2:

    y_index = 1

    if len(selected_labels) <= 1:
        y_index = 0

    y_axis = st.selectbox(

        "세로축 속성",

        options=selected_labels,

        format_func=lambda x:
            feature_labels[x],

        index=y_index,

        key="y_axis"

    )


# =========================================================
# 2차원 그래프
# =========================================================
fig_2d = px.scatter(

    analysis_df,

    x=feature_map[x_axis],

    y=feature_map[y_axis],

    color="군집",

    hover_name="movieNm",

    hover_data={

        feature_map[x_axis]: ":.2f",

        feature_map[y_axis]: ":.2f",

        "군집": True

    },

    labels={

        feature_map[x_axis]:
            feature_labels[x_axis],

        feature_map[y_axis]:
            feature_labels[y_axis],

        "군집":
            "영화 유형"

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

        "3차원 산점도를 그리려면 "
        "묶는 데 사용할 속성을 3개 이상 선택해 주세요."

    )

else:

    col1, col2, col3 = st.columns(3)


    with col1:

        x3 = st.selectbox(

            "X축",

            options=selected_labels,

            format_func=lambda x:
                feature_labels[x],

            key="x3"

        )


    with col2:

        y3 = st.selectbox(

            "Y축",

            options=selected_labels,

            format_func=lambda x:
                feature_labels[x],

            key="y3"

        )


    with col3:

        z3 = st.selectbox(

            "Z축",

            options=selected_labels,

            format_func=lambda x:
                feature_labels[x],

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

            feature_map[x3]:
                feature_labels[x3],

            feature_map[y3]:
                feature_labels[y3],

            feature_map[z3]:
                feature_labels[z3],

            "군집":
                "영화 유형"

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
# 군집별 특징 표
# =========================================================
st.subheader("📋 영화 유형별 특징")


summary = (

    analysis_df

    .groupby("군집")

    .agg(

        편수=("movieNm", "count"),

        스크린수_평균=(
            "first_scrn",
            "mean"
        ),

        누적관객_평균=(
            "total_audi",
            "mean"
        ),

        십위권일수_평균=(
            "days_in_top10",
            "mean"
        ),

        롱런지수_평균=(
            "롱런 지수",
            "mean"
        )

    )

    .reset_index()

)


# =========================================================
# 군집 표시 순서
# =========================================================
symbol_order = {

    symbol: i

    for i, symbol
    in enumerate(symbols)

}


summary["순서"] = (
    summary["군집"]
    .map(symbol_order)
)


summary = (

    summary

    .sort_values(
        "순서"
    )

    .drop(
        columns="순서"
    )

)


summary = summary.rename(

    columns={

        "군집":
            "영화 유형",

        "스크린수_평균":
            "스크린 수 평균",

        "누적관객_평균":
            "누적 관객 평균",

        "십위권일수_평균":
            "10위권 일수 평균",

        "롱런지수_평균":
            "롱런 지수 평균"

    }

)


st.dataframe(

    summary.style.format({

        "편수":
            "{:,.0f}",

        "스크린 수 평균":
            "{:,.1f}",

        "누적 관객 평균":
            "{:,.0f}",

        "10위권 일수 평균":
            "{:,.1f}",

        "롱런 지수 평균":
            "{:,.2f}"

    }),

    use_container_width=True,

    hide_index=True

)


# =========================================================
# 유형별 누적 관객 TOP 5
# =========================================================
st.subheader(
    "🏆 영화 유형별 누적 관객 TOP 5"
)


for symbol in symbols[:cluster_count]:

    group = (

        analysis_df[
            analysis_df["군집"]
            == symbol
        ]

        .sort_values(

            by="total_audi",

            ascending=False

        )

        .head(5)

    )


    st.markdown(
        f"### {symbol}"
    )


    if len(group) == 0:

        st.write(
            "해당 유형의 영화가 없습니다."
        )

    else:

        top5 = group[
            [
                "movieNm",
                "total_audi"
            ]
        ].copy()


        top5.columns = [
            "영화 제목",
            "누적 관객"
        ]


        st.dataframe(

            top5.style.format({

                "누적 관객":
                    "{:,.0f}"

            }),

            use_container_width=True,

            hide_index=True

        )


# =========================================================
# 엘보우 분석
# =========================================================
st.subheader(
    "📉 묶음 수에 따른 중심에서의 거리 제곱합"
)


st.write(

    "묶음 수를 1개부터 7개까지 바꿔 가며, "
    "각 영화가 자기 묶음의 중심에서 떨어진 거리의 제곱을 "
    "모두 더한 값입니다."

)


inertia_values = []


for k in range(1, 8):

    elbow_model = KMeans(

        n_clusters=k,

        random_state=42,

        n_init=10

    )


    elbow_model.fit(
        X_scaled
    )


    inertia_values.append(
        elbow_model.inertia_
    )


# =========================================================
# 엘보우 그래프
# =========================================================
fig_elbow = go.Figure()


fig_elbow.add_trace(

    go.Scatter(

        x=list(
            range(1, 8)
        ),

        y=inertia_values,

        mode="lines+markers",

        name="거리 제곱합"

    )

)


# 현재 선택한 묶음 수에 세로선
fig_elbow.add_vline(

    x=cluster_count,

    line_dash="dash",

    line_width=2,

    annotation_text=(
        f"현재 선택: {cluster_count}개"
    ),

    annotation_position="top"

)


fig_elbow.update_layout(

    xaxis_title="묶음 수",

    yaxis_title="중심에서의 거리 제곱합",

    xaxis=dict(
        dtick=1
    ),

    height=500

)


st.plotly_chart(

    fig_elbow,

    use_container_width=True

)


# =========================================================
# 묶음 수별 값과 감소량 표
# =========================================================
elbow_table = pd.DataFrame({

    "묶음 수":
        list(range(1, 8)),

    "거리 제곱합":
        inertia_values

})


elbow_table["바로 앞 값에서 감소"] = (
    elbow_table[
        "거리 제곱합"
    ].shift(1)
    - elbow_table[
        "거리 제곱합"
    ]
)


# 첫 줄은 비교할 앞 값이 없으므로 빈칸
elbow_table.loc[
    0,
    "바로 앞 값에서 감소"
] = None


st.dataframe(

    elbow_table.style.format({

        "거리 제곱합":
            "{:,.2f",

        "바로 앞 값에서 감소":
            "{:,.2f"

    }),

    use_container_width=True,

    hide_index=True

)


# =========================================================
# 분석 정보
# =========================================================
st.subheader("ℹ️ 분석 정보")


st.write(
    f"- 전체 영화: **{total_count}편**"
)

st.write(
    f"- 분석에 사용한 영화: **{len(analysis_df)}편**"
)

st.write(
    f"- 현재 묶음 수: **{cluster_count}개**"
)

st.write(
    "- 스크린 수와 누적 관객은 상용로그로 변환했습니다."
)

st.write(
    "- 10위권 일수는 원래 값을 그대로 사용했습니다."
)

st.write(
    "- 롱런 지수는 누적 관객 ÷ 첫 주 관객으로 계산하고 "
    "20을 초과하면 20으로 제한했습니다."
)

st.write(
    "- 선택한 속성만 표준화하여 K-means에 사용했습니다."
)

st.write(
    "- K-means의 난수는 random_state=42로 고정했습니다."
)
