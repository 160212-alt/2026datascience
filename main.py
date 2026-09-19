import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error


# =========================================================
# 페이지 설정
# =========================================================
st.set_page_config(
    page_title="영화 흥행 예측기",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 영화 흥행 예측기")
st.write(
    "영화 정보를 이용해 총 관객 수를 다중 회귀 모델로 예측합니다."
)


# =========================================================
# 데이터 주소
# =========================================================
DAILY_URL = (
    "https://raw.githubusercontent.com/greatsong/modudata/"
    "main/data/kobis_daily.csv"
)

MOVIES_URL = (
    "https://raw.githubusercontent.com/greatsong/modudata/"
    "main/data/kobis_movies.csv"
)


# =========================================================
# 데이터 불러오기
# =========================================================
@st.cache_data
def load_data():

    daily = pd.read_csv(
        DAILY_URL,
        encoding="utf-8-sig"
    )

    movies = pd.read_csv(
        MOVIES_URL,
        encoding="utf-8-sig"
    )

    return daily, movies


try:
    daily, movies = load_data()

except Exception as e:
    st.error("데이터를 불러오지 못했습니다.")
    st.write("오류 내용:")
    st.code(str(e))
    st.stop()


# =========================================================
# 열 이름 확인 및 정리
# =========================================================
daily.columns = daily.columns.str.strip()
movies.columns = movies.columns.str.strip()

# 실제 daily 파일의 영화코드를 movieCd로 통일
daily = daily.rename(
    columns={
        "영화코드": "movieCd"
    }
)

# BOM이나 공백 제거
daily["movieCd"] = (
    daily["movieCd"]
    .astype(str)
    .str.strip()
)

movies["movieCd"] = (
    movies["movieCd"]
    .astype(str)
    .str.strip()
)


# =========================================================
# 필요한 열 존재 여부 확인
# =========================================================
required_daily = [
    "날짜",
    "movieCd"
]

required_movies = [
    "movieCd",
    "movieNm",
    "first_scrn",
    "first_show",
    "genre",
    "nation",
    "peak",
    "first_week_audi",
    "total_audi",
    "days_in_top10"
]

missing_daily = [
    col for col in required_daily
    if col not in daily.columns
]

missing_movies = [
    col for col in required_movies
    if col not in movies.columns
]

if missing_daily:
    st.error(
        "kobis_daily.csv에 다음 열이 없습니다: "
        + ", ".join(missing_daily)
    )
    st.stop()

if missing_movies:
    st.error(
        "kobis_movies.csv에 다음 열이 없습니다: "
        + ", ".join(missing_movies)
    )
    st.stop()


# =========================================================
# 숫자형 변환
# =========================================================
daily["날짜"] = pd.to_numeric(
    daily["날짜"],
    errors="coerce"
)

for col in [
    "first_scrn",
    "first_show",
    "peak",
    "first_week_audi",
    "total_audi",
    "days_in_top10"
]:
    movies[col] = pd.to_numeric(
        movies[col],
        errors="coerce"
    )


# =========================================================
# 기준 기간
# =========================================================
valid_dates = daily["날짜"].dropna()

if len(valid_dates) > 0:

    min_date = str(int(valid_dates.min()))
    max_date = str(int(valid_dates.max()))

    start_date = (
        f"{min_date[:4]}-"
        f"{min_date[4:6]}-"
        f"{min_date[6:8]}"
    )

    end_date = (
        f"{max_date[:4]}-"
        f"{max_date[4:6]}-"
        f"{max_date[6:8]}"
    )

    period = f"{start_date} ~ {end_date}"

else:
    period = "확인할 수 없음"


# =========================================================
# 기준 기간 표시
# =========================================================
st.info(
    f"📅 일별 박스오피스 기준 기간: **{period}**"
)


# =========================================================
# 영화 정보 표의 맨 위 행
# =========================================================
st.subheader("📋 영화 정보 표")

st.write("영화 정보 표의 맨 위 데이터 행입니다.")

st.dataframe(
    movies.head(1),
    use_container_width=True,
    hide_index=True
)


# =========================================================
# 영화코드 순으로 정렬
# =========================================================
movies = movies.sort_values(
    by="movieCd",
    key=lambda x: x.astype(str)
).reset_index(drop=True)


# =========================================================
# 전체 영화 수
# =========================================================
total_movies = len(movies)

if total_movies < 4:
    st.error("테스트와 학습에 사용할 영화가 너무 적습니다.")
    st.stop()


# =========================================================
# 10편마다 앞의 3편을 테스트
#
# 1~3    테스트
# 4~10   학습
# 11~13  테스트
# 14~20  학습
# ...
# =========================================================
movies["순서"] = np.arange(total_movies)

test_mask = (
    movies["순서"] % 10 < 3
)

test_df = movies.loc[
    test_mask
].copy()

train_df = movies.loc[
    ~test_mask
].copy()


# =========================================================
# 사용할 수 있는 변수
# =========================================================
feature_options = {
    "first_scrn": "첫 관측일 스크린수",
    "first_show": "첫 관측일 상영횟수",
    "peak": "성수기 개봉 여부",
    "first_week_audi": "첫 주 관객",
    "days_in_top10": "TOP10 진입일수",
    "genre": "장르",
    "nation": "제작 국가"
}


# =========================================================
# 체크박스
# =========================================================
st.subheader("⚙️ 예측 변수 선택")

st.write(
    "예측에 사용할 변수를 선택하세요."
)

selected_features = []

feature_cols = st.columns(4)

for i, (column, label) in enumerate(
    feature_options.items()
):

    with feature_cols[i % 4]:

        checked = st.checkbox(
            label,
            value=True,
            key=f"check_{column}"
        )

        if checked:
            selected_features.append(column)


if len(selected_features) == 0:

    st.warning(
        "최소 하나의 변수를 선택해야 합니다."
    )

    st.stop()


# =========================================================
# 선택 변수 출력
# =========================================================
st.write("**선택된 변수**")

for feature in selected_features:

    st.write(
        f"- {feature_options[feature]}"
    )


# =========================================================
# 학습 / 테스트 데이터
# =========================================================
X_train = train_df[
    selected_features
].copy()

y_train = train_df[
    "total_audi"
].copy()

X_test = test_df[
    selected_features
].copy()

y_test = test_df[
    "total_audi"
].copy()


# =========================================================
# target 결측값 제거
# =========================================================
train_valid = y_train.notna()
test_valid = y_test.notna()

X_train = X_train.loc[train_valid]
y_train = y_train.loc[train_valid]

X_test = X_test.loc[test_valid]
y_test = y_test.loc[test_valid]

test_df = test_df.loc[
    test_valid
].copy()


# =========================================================
# 숫자형 / 문자형 변수
# =========================================================
numeric_features = [
    col for col in selected_features
    if col in [
        "first_scrn",
        "first_show",
        "peak",
        "first_week_audi",
        "days_in_top10"
    ]
]

categorical_features = [
    col for col in selected_features
    if col in [
        "genre",
        "nation"
    ]
]


# =========================================================
# 전처리
# =========================================================
transformers = []


if numeric_features:

    numeric_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="median"
                )
            ),
            (
                "scaler",
                StandardScaler()
            )
        ]
    )

    transformers.append(
        (
            "numeric",
            numeric_pipeline,
            numeric_features
        )
    )


if categorical_features:

    categorical_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="most_frequent"
                )
            ),
            (
                "onehot",
                OneHotEncoder(
                    handle_unknown="ignore"
                )
            )
        ]
    )

    transformers.append(
        (
            "categorical",
            categorical_pipeline,
            categorical_features
        )
    )


preprocessor = ColumnTransformer(
    transformers=transformers
)


# =========================================================
# 다중 회귀 모델
# =========================================================
model = Pipeline(
    steps=[
        (
            "preprocessor",
            preprocessor
        ),
        (
            "regression",
            LinearRegression()
        )
    ]
)


# =========================================================
# 모델 학습
# =========================================================
try:

    model.fit(
        X_train,
        y_train
    )

except Exception as e:

    st.error(
        "회귀 모델 학습 중 오류가 발생했습니다."
    )

    st.code(str(e))

    st.stop()


# =========================================================
# 테스트 영화 예측
# =========================================================
predicted = model.predict(
    X_test
)

# 음수 관객 수 방지
predicted = np.maximum(
    predicted,
    0
)


# =========================================================
# 평가 점수
# =========================================================
r2 = r2_score(
    y_test,
    predicted
)

mae = mean_absolute_error(
    y_test,
    predicted
)


# =========================================================
# 평가 결과
# =========================================================
st.subheader("📊 모델 평가 결과")

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "전체 영화",
        f"{len(movies)}편"
    )

with col2:

    st.metric(
        "학습 영화",
        f"{len(train_df)}편"
    )

with col3:

    st.metric(
        "평가 영화",
        f"{len(test_df)}편"
    )

with col4:

    st.metric(
        "R² 점수",
        f"{r2:.3f}"
    )


st.write(
    f"**평균 절대 오차(MAE): "
    f"{mae:,.0f}명**"
)

st.write(
    f"**기준 기간: {period}**"
)


# =========================================================
# 실제값 / 예측값 표
# =========================================================
result = pd.DataFrame({

    "영화코드":
        test_df["movieCd"].values,

    "영화명":
        test_df["movieNm"].values,

    "실제 총 관객":
        y_test.values,

    "예측 총 관객":
        predicted

})


result["오차"] = (
    result["예측 총 관객"]
    - result["실제 총 관객"]
)

result["절대 오차"] = (
    result["오차"].abs()
)


result = result.sort_values(
    by="영화코드"
).reset_index(drop=True)


st.subheader(
    "🎥 테스트 영화의 실제값과 예측값"
)

st.dataframe(
    result.style.format({
        "실제 총 관객": "{:,.0f}",
        "예측 총 관객": "{:,.0f}",
        "오차": "{:,.0f}",
        "절대 오차": "{:,.0f}"
    }),
    use_container_width=True,
    hide_index=True
)


# =========================================================
# 1,000명 미만 예측
# =========================================================
low_mask = (
    predicted < 1000
)

low_count = int(
    low_mask.sum()
)


st.subheader(
    "⚠️ 1,000명 미만 예측 영화"
)

st.write(
    f"예측 총 관객 수가 1,000명보다 작은 영화는 "
    f"**{low_count}편**입니다."
)


# =========================================================
# 로그 산점도
# =========================================================
st.subheader(
    "📈 실제 총 관객 수와 예측 총 관객 수"
)


# 로그축은 0을 사용할 수 없으므로 1로 변환
actual_values = np.maximum(
    y_test.to_numpy(dtype=float),
    1
)

predicted_values = np.maximum(
    predicted.astype(float),
    1
)


# 모든 값으로 축 범위 결정
all_values = np.concatenate([
    actual_values,
    predicted_values
])


positive_values = all_values[
    all_values > 0
]


axis_min = max(
    1,
    positive_values.min() * 0.7
)

axis_max = (
    positive_values.max() * 1.5
)


# ---------------------------------------------------------
# 1,000명 미만 예측값을 그래프 바닥으로 이동
# ---------------------------------------------------------
display_y = predicted_values.copy()

display_y[low_mask] = axis_min


fig = go.Figure()


# =========================================================
# 산점도
# =========================================================
fig.add_trace(
    go.Scatter(
        x=actual_values,
        y=display_y,

        mode="markers",

        text=test_df["movieNm"],

        customdata=np.column_stack([
            y_test.to_numpy(),
            predicted
        ]),

        hovertemplate=(
            "<b>%{text}</b><br>"
            "실제 총 관객: %{customdata[0]:,.0f}명<br>"
            "예측 총 관객: %{customdata[1]:,.0f}명"
            "<extra></extra>"
        ),

        name="테스트 영화",

        marker={
            "size": 9
        }
    )
)


# =========================================================
# 실제값 = 예측값 대각선
# =========================================================
fig.add_trace(
    go.Scatter(

        x=[
            axis_min,
            axis_max
        ],

        y=[
            axis_min,
            axis_max
        ],

        mode="lines",

        name="실제값 = 예측값",

        line={
            "dash": "dash",
            "width": 2
        }
    )
)


# =========================================================
# 그래프 설정
# =========================================================
fig.update_layout(

    height=650,

    xaxis={
        "title": "실제 총 관객 수",
        "type": "log"
    },

    yaxis={
        "title": "예측 총 관객 수",
        "type": "log"
    },

    hovermode="closest",

    legend={
        "orientation": "h"
    }
)


fig.add_annotation(

    x=0.02,
    y=0.02,

    xref="paper",
    yref="paper",

    text=(
        f"예측 1,000명 미만: "
        f"{low_count}편"
    ),

    showarrow=False,

    xanchor="left",
    yanchor="bottom"
)


st.plotly_chart(
    fig,
    use_container_width=True
)


# =========================================================
# 사용 정보
# =========================================================
st.subheader(
    "ℹ️ 데이터 사용 정보"
)

st.write(
    f"- 전체 영화: **{len(movies)}편**"
)

st.write(
    f"- 학습에 사용한 영화: **{len(train_df)}편**"
)

st.write(
    f"- 평가한 영화: **{len(test_df)}편**"
)

st.write(
    f"- 기준 기간: **{period}**"
)

st.write(
    "- 영화코드 순으로 정렬한 뒤 "
    "10편마다 앞의 3편을 테스트용으로 사용했습니다."
)

st.write(
    "- 나머지 영화는 학습에 사용했습니다."
)

st.write(
    "- 영화 정보 표의 모든 영화는 "
    "학습 또는 평가에 포함됩니다."
)
