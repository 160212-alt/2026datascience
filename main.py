import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error


# ---------------------------------------------------------
# 기본 설정
# ---------------------------------------------------------
st.set_page_config(
    page_title="영화 흥행 예측기",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 영화 흥행 예측기")
st.write("영화의 여러 정보를 이용해 총 관객 수를 다중 회귀로 예측합니다.")


# ---------------------------------------------------------
# 데이터 주소
# ---------------------------------------------------------
DAILY_URL = (
    "https://raw.githubusercontent.com/greatsong/modudata/"
    "main/data/kobis_daily.csv"
)

MOVIES_URL = (
    "https://raw.githubusercontent.com/greatsong/modudata/"
    "main/data/kobis_movies.csv"
)


# ---------------------------------------------------------
# 데이터 불러오기
# ---------------------------------------------------------
@st.cache_data
def load_data():
    daily = pd.read_csv(DAILY_URL, encoding="utf-8")
    movies = pd.read_csv(MOVIES_URL, encoding="utf-8")

    return daily, movies


try:
    daily, movies = load_data()
except Exception as e:
    st.error("데이터를 불러오는 중 오류가 발생했습니다.")
    st.code(str(e))
    st.stop()


# ---------------------------------------------------------
# 데이터 정리
# ---------------------------------------------------------

# 영화코드는 두 표에서 같은 영화를 연결하는 기준
daily["movieCd"] = daily["movieCd"].astype(str).str.strip()
movies["movieCd"] = movies["movieCd"].astype(str).str.strip()

# 날짜를 숫자로 변환
daily["날짜"] = pd.to_numeric(daily["날짜"], errors="coerce")

# 숫자형 열 변환
daily["일관객"] = pd.to_numeric(daily["일관객"], errors="coerce")
daily["누적관객"] = pd.to_numeric(daily["누적관객"], errors="coerce")

# 영화 정보 표의 숫자형 변수
numeric_columns = [
    "first_scrn",
    "first_show",
    "first_week_audi",
    "total_audi",
    "days_in_top10",
    "peak"
]

for col in numeric_columns:
    movies[col] = pd.to_numeric(movies[col], errors="coerce")


# ---------------------------------------------------------
# 기준 기간 표시
# ---------------------------------------------------------
valid_dates = daily["날짜"].dropna()

if len(valid_dates) > 0:
    start_date = str(int(valid_dates.min()))
    end_date = str(int(valid_dates.max()))

    start_date = (
        f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}"
    )
    end_date = (
        f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}"
    )

    period_text = f"{start_date} ~ {end_date}"
else:
    period_text = "기간을 확인할 수 없습니다."


# ---------------------------------------------------------
# 영화별 표 맨 위 열 줄 표시
# ---------------------------------------------------------
st.subheader("📋 영화 정보 표")

st.caption("영화별 표(kobis_movies.csv)의 첫 번째 데이터 행입니다.")

st.dataframe(
    movies.head(1),
    use_container_width=True,
    hide_index=True
)

st.info(f"📅 기준 기간: **{period_text}**")


# ---------------------------------------------------------
# 영화코드 순으로 정렬
# ---------------------------------------------------------
movies = movies.sort_values(
    by="movieCd",
    ascending=True
).reset_index(drop=True)


# ---------------------------------------------------------
# 10편마다 앞의 3편 테스트
#
# 예:
# 1~3번 → 테스트
# 4~10번 → 학습
# 11~13번 → 테스트
# 14~20번 → 학습
# ...
# ---------------------------------------------------------
movies["order"] = np.arange(len(movies))

test_mask = (movies["order"] % 10) < 3

test_df = movies[test_mask].copy()
train_df = movies[~test_mask].copy()


# ---------------------------------------------------------
# 사용할 수 있는 설명 변수
# ---------------------------------------------------------
possible_features = [
    "first_scrn",
    "first_show",
    "peak",
    "first_week_audi",
    "days_in_top10",
    "genre",
    "nation"
]

feature_labels = {
    "first_scrn": "첫 관측일 스크린수",
    "first_show": "첫 관측일 상영횟수",
    "peak": "성수기 개봉 여부",
    "first_week_audi": "첫 주 관객",
    "days_in_top10": "TOP10 진입일수",
    "genre": "장르",
    "nation": "제작 국가"
}


# ---------------------------------------------------------
# 변수 선택
# ---------------------------------------------------------
st.subheader("⚙️ 예측에 사용할 변수 선택")

st.write(
    "체크한 변수만 다중 회귀 모델의 입력값으로 사용합니다."
)

selected_features = []

cols = st.columns(4)

for i, feature in enumerate(possible_features):
    with cols[i % 4]:
        if st.checkbox(
            feature_labels[feature],
            value=True,
            key=f"feature_{feature}"
        ):
            selected_features.append(feature)


if len(selected_features) == 0:
    st.warning("최소 1개의 변수를 선택해 주세요.")
    st.stop()


# ---------------------------------------------------------
# 선택 변수 표시
# ---------------------------------------------------------
st.write("**선택된 변수:**")

st.write(
    ", ".join(feature_labels[x] for x in selected_features)
)


# ---------------------------------------------------------
# 학습 / 테스트 데이터
# ---------------------------------------------------------
X_train = train_df[selected_features].copy()
y_train = train_df["total_audi"].copy()

X_test = test_df[selected_features].copy()
y_test = test_df["total_audi"].copy()


# ---------------------------------------------------------
# 숫자형 / 범주형 변수 분리
# ---------------------------------------------------------
numeric_features = [
    x for x in selected_features
    if x in [
        "first_scrn",
        "first_show",
        "peak",
        "first_week_audi",
        "days_in_top10"
    ]
]

categorical_features = [
    x for x in selected_features
    if x in ["genre", "nation"]
]


# ---------------------------------------------------------
# 전처리
# ---------------------------------------------------------
numeric_transformer = Pipeline(
    steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler())
    ]
)

categorical_transformer = Pipeline(
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


transformers = []

if numeric_features:
    transformers.append(
        (
            "num",
            numeric_transformer,
            numeric_features
        )
    )

if categorical_features:
    transformers.append(
        (
            "cat",
            categorical_transformer,
            categorical_features
        )
    )


preprocessor = ColumnTransformer(
    transformers=transformers
)


# ---------------------------------------------------------
# 다중 회귀 모델
# ---------------------------------------------------------
model = Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        ("regressor", LinearRegression())
    ]
)


# ---------------------------------------------------------
# 학습
# ---------------------------------------------------------
model.fit(X_train, y_train)


# ---------------------------------------------------------
# 테스트 데이터 예측
# ---------------------------------------------------------
predictions = model.predict(X_test)

# 음수 관객 수 방지
predictions = np.maximum(predictions, 0)


# ---------------------------------------------------------
# 평가
# ---------------------------------------------------------
r2 = r2_score(y_test, predictions)
mae = mean_absolute_error(y_test, predictions)
rmse = np.sqrt(
    mean_squared_error(y_test, predictions)
)


# ---------------------------------------------------------
# 평가 결과
# ---------------------------------------------------------
st.subheader("📊 모델 평가")

metric1, metric2, metric3, metric4 = st.columns(4)

with metric1:
    st.metric(
        "학습에 사용한 영화",
        f"{len(train_df)}편"
    )

with metric2:
    st.metric(
        "평가한 영화",
        f"{len(test_df)}편"
    )

with metric3:
    st.metric(
        "R² 점수",
        f"{r2:.3f}"
    )

with metric4:
    st.metric(
        "평균 절대 오차",
        f"{mae:,.0f}명"
    )

st.caption(
    "R²는 테스트 영화에서 실제 관객 수의 변동을 모델이 얼마나 설명하는지 나타냅니다. "
    "평균 절대 오차(MAE)는 실제 관객 수와 예측 관객 수의 평균적인 차이입니다."
)

st.write(
    f"**RMSE:** {rmse:,.0f}명"
)


# ---------------------------------------------------------
# 실제값 / 예측값 표
# ---------------------------------------------------------
result_df = test_df[
    ["movieCd", "movieNm", "total_audi"]
].copy()

result_df["예측 총 관객"] = predictions

result_df["오차"] = (
    result_df["예측 총 관객"]
    - result_df["total_audi"]
)

result_df["절대 오차"] = (
    result_df["오차"].abs()
)

result_df = result_df.sort_values(
    by="movieCd"
).reset_index(drop=True)

result_df = result_df.rename(
    columns={
        "movieCd": "영화코드",
        "movieNm": "영화명",
        "total_audi": "실제 총 관객"
    }
)

st.subheader("🎥 테스트 영화의 실제값과 예측값")

st.dataframe(
    result_df.style.format(
        {
            "실제 총 관객": "{:,.0f}",
            "예측 총 관객": "{:,.0f}",
            "오차": "{:,.0f}",
            "절대 오차": "{:,.0f}"
        }
    ),
    use_container_width=True,
    hide_index=True
)


# ---------------------------------------------------------
# 1,000명 미만 예측 영화
# ---------------------------------------------------------
low_prediction_mask = predictions < 1000
low_prediction_count = int(
    low_prediction_mask.sum()
)

st.subheader("⚠️ 1,000명 미만으로 예측된 영화")

st.write(
    f"예측 총 관객 수가 1,000명보다 작은 영화는 "
    f"**{low_prediction_count}편**입니다."
)


# ---------------------------------------------------------
# 로그 스케일 산점도
# ---------------------------------------------------------
st.subheader("📈 실제 총 관객 수와 예측 총 관객 수")

# 로그 그래프에서는 0을 사용할 수 없기 때문에
# 1 미만 값은 1로 올림
actual_plot = np.maximum(
    y_test.to_numpy(),
    1
)

pred_plot = np.maximum(
    predictions,
    1
)


# 전체 축 범위 계산
all_values = np.concatenate(
    [actual_plot, pred_plot]
)

axis_min = max(
    1,
    float(np.min(all_values)) * 0.7
)

axis_max = (
    float(np.max(all_values)) * 1.5
)


fig = go.Figure()


# ---------------------------------------------------------
# 1,000명 미만 예측값을 바닥에 붙여 표시
# ---------------------------------------------------------
# 실제 예측값은 hover에서 보여주고,
# 표시 위치만 그래프의 바닥으로 내려준다.
display_pred = pred_plot.copy()

if low_prediction_count > 0:
    display_pred[low_prediction_mask] = axis_min


# 테스트 영화 산점도
fig.add_trace(
    go.Scatter(
        x=actual_plot,
        y=display_pred,
        mode="markers",
        text=test_df["movieNm"],
        customdata=np.column_stack(
            [
                y_test.to_numpy(),
                predictions
            ]
        ),
        hovertemplate=(
            "<b>%{text}</b><br>"
            "실제 총 관객: %{customdata[0]:,.0f}명<br>"
            "예측 총 관객: %{customdata[1]:,.0f}명"
            "<extra></extra>"
        ),
        name="테스트 영화",
        marker=dict(
            size=9
        )
    )
)


# ---------------------------------------------------------
# 실제값 = 예측값 대각선
# ---------------------------------------------------------
line_min = axis_min
line_max = axis_max

fig.add_trace(
    go.Scatter(
        x=[line_min, line_max],
        y=[line_min, line_max],
        mode="lines",
        name="실제값 = 예측값",
        line=dict(
            dash="dash",
            width=2
        )
    )
)


# ---------------------------------------------------------
# 그래프 설정
# ---------------------------------------------------------
fig.update_layout(
    xaxis=dict(
        title="실제 총 관객 수",
        type="log",
        range=[
            np.log10(axis_min),
            np.log10(axis_max)
        ]
    ),
    yaxis=dict(
        title="예측 총 관객 수",
        type="log",
        range=[
            np.log10(axis_min),
            np.log10(axis_max)
        ]
    ),
    hovermode="closest",
    height=650,
    legend=dict(
        orientation="h"
    )
)

fig.add_annotation(
    x=0.02,
    y=0.02,
    xref="paper",
    yref="paper",
    text=(
        f"예측 1,000명 미만: {low_prediction_count}편"
    ),
    showarrow=False,
    xanchor="left",
    yanchor="bottom"
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# ---------------------------------------------------------
# 데이터 사용 정보
# ---------------------------------------------------------
st.subheader("ℹ️ 데이터 사용 정보")

info1, info2, info3 = st.columns(3)

with info1:
    st.write(
        f"**전체 영화:** {len(movies)}편"
    )

with info2:
    st.write(
        f"**학습 영화:** {len(train_df)}편"
    )

with info3:
    st.write(
        f"**평가 영화:** {len(test_df)}편"
    )

st.write(
    f"**기준 기간:** {period_text}"
)

st.caption(
    "영화 정보 표를 영화코드(movieCd) 순으로 정렬한 뒤, "
    "10편마다 앞의 3편을 테스트용으로 분리하고 나머지를 학습에 사용했습니다. "
    "영화 정보 표의 모든 영화가 학습 또는 평가에 포함됩니다."
)
