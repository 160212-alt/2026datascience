import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------------
# 기본 설정
# -----------------------------------
st.set_page_config(
    page_title="영화 데이터 그래프 도감 1 - 시간",
    layout="wide"
)

st.title("영화 데이터 그래프 도감 1 - 시간")
st.write("365일 동안의 일별 박스오피스 데이터를 시간의 흐름에 따라 살펴봅니다.")


# -----------------------------------
# 데이터 불러오기
# -----------------------------------
DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/kobis_daily.csv"

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL)

    # 날짜를 실제 날짜 형식으로 변환
    df["날짜"] = pd.to_datetime(
        df["날짜"].astype(str),
        format="%Y%m%d"
    )

    # 숫자형 데이터로 변환
    df["일관객"] = pd.to_numeric(
        df["일관객"],
        errors="coerce"
    )

    return df


try:
    df = load_data()

except Exception as e:
    st.error("데이터를 불러오는 중 오류가 발생했습니다.")
    st.exception(e)
    st.stop()


# ===================================
# 그래프 1. 영화별 일관객 변화
# ===================================
st.header("그래프 1. 영화별 일관객 변화")

movie_list = sorted(df["영화명"].dropna().unique())

selected_movie = st.selectbox(
    "영화를 선택하세요.",
    movie_list
)

movie_df = df[df["영화명"] == selected_movie].copy()
movie_df = movie_df.sort_values("날짜")

fig1 = px.line(
    movie_df,
    x="날짜",
    y="일관객",
    markers=True,
    title=f"{selected_movie}의 날짜별 일관객 변화",
    labels={
        "날짜": "날짜",
        "일관객": "일관객 수"
    }
)

fig1.update_traces(
    hovertemplate="날짜: %{x|%Y-%m-%d}<br>일관객: %{y:,}명<extra></extra>"
)

fig1.update_layout(
    hovermode="x unified"
)

st.plotly_chart(fig1, use_container_width=True)

st.markdown("**이 그래프로 알 수 있는 것:**")
st.info(
    "선택한 영화의 날짜별 일관객 수가 시간의 흐름에 따라 "
    "어떻게 변화했는지 알 수 있습니다."
)


# ===================================
# 그래프 2. 일관객 합계 TOP 5 영화 비교
# ===================================
st.divider()
st.header("그래프 2. 일관객 합계 TOP 5 영화의 날짜별 변화")

# 영화별 일관객 합계 계산
movie_total = (
    df.groupby("영화명", as_index=False)["일관객"]
    .sum()
    .sort_values("일관객", ascending=False)
)

# 일관객 합계 상위 5편
top5_movies = movie_total.head(5)["영화명"].tolist()

# 상위 5편 데이터만 추출
top5_df = df[df["영화명"].isin(top5_movies)].copy()
top5_df = top5_df.sort_values(["날짜", "영화명"])

fig2 = px.line(
    top5_df,
    x="날짜",
    y="일관객",
    color="영화명",
    markers=True,
    title="일관객 합계가 가장 큰 5편의 날짜별 일관객 변화",
    labels={
        "날짜": "날짜",
        "일관객": "일관객 수",
        "영화명": "영화"
    }
)

fig2.update_traces(
    hovertemplate="날짜: %{x|%Y-%m-%d}<br>일관객: %{y:,}명<extra>%{fullData.name}</extra>"
)

fig2.update_layout(
    hovermode="x unified",
    legend_title_text="영화"
)

st.plotly_chart(fig2, use_container_width=True)

st.markdown("**이 그래프로 알 수 있는 것:**")
st.info(
    "전체 기간의 일관객 합계가 가장 큰 5편의 흥행 추이를 비교하고, "
    "영화별로 관객 수가 언제 증가하거나 감소했는지 알 수 있습니다."
)


# ===================================
# 그래프 3. 추가 예정
# ===================================
st.divider()
st.header("그래프 3. 추가 예정")

st.write("앞으로 새로운 시간 관련 그래프를 이 구역에 추가할 수 있습니다.")


# ===================================
# 그래프 4. 추가 예정
# ===================================
st.divider()
st.header("그래프 4. 추가 예정")

st.write("앞으로 새로운 그래프를 이 구역에 추가할 수 있습니다.")
# ===================================
# 그래프 3. 날짜별 10위권 일관객 합계
# ===================================
st.divider()
st.header("그래프 3. 날짜별 10위권 일관객 합계")

# 날짜별 10위권 일관객 합계 계산
daily_total = (
    df.groupby("날짜", as_index=False)["일관객"]
    .sum()
    .sort_values("날짜")
)

# 일관객 합계가 가장 큰 3일 찾기
top3_days = (
    daily_total
    .nlargest(3, "일관객")
    .sort_values("날짜")
)

# 영역 그래프 생성
fig3 = px.area(
    daily_total,
    x="날짜",
    y="일관객",
    title="날짜별 박스오피스 10위권 일관객 합계",
    labels={
        "날짜": "날짜",
        "일관객": "10위권 일관객 합계"
    }
)

# 마우스를 올렸을 때 표시되는 정보
fig3.update_traces(
    hovertemplate="날짜: %{x|%Y-%m-%d}<br>10위권 일관객 합계: %{y:,}명<extra></extra>"
)

# 합계가 가장 큰 3일을 그래프에 표시
for _, row in top3_days.iterrows():
    fig3.add_annotation(
        x=row["날짜"],
        y=row["일관객"],
        text=f"{row['날짜'].strftime('%Y-%m-%d')}<br>{row['일관객']:,}명",
        showarrow=True,
        arrowhead=2,
        ax=0,
        ay=-50
    )

fig3.update_layout(
    hovermode="x unified"
)

st.plotly_chart(fig3, use_container_width=True)

st.markdown("**이 그래프로 알 수 있는 것:**")
st.info(
    "날짜별 박스오피스 10위권 전체의 관객 규모 변화를 확인하고, "
    "관객이 가장 많이 몰린 상위 3일을 알 수 있습니다."
)


# ===================================
# 그래프 4. 추가 예정
# ===================================
st.divider()
st.header("그래프 4. 추가 예정")

st.write("앞으로 새로운 그래프를 이 구역에 추가할 수 있습니다.")
# ===================================
# 그래프 4. 영화별 누적 일관객 TOP 10
# ===================================
st.divider()
st.header("그래프 4. 영화별 일관객 합계 TOP 10")

# 영화별 일관객 합계와 10위권에 든 날수 계산
movie_summary = (
    df.groupby("영화명")
    .agg(
        일관객합계=("일관객", "sum"),
        10위권_일수=("날짜", "nunique")
    )
    .reset_index()
    .sort_values("일관객합계", ascending=False)
    .head(10)
)

# 관객이 많은 영화가 위에 오도록 순서 설정
movie_summary = movie_summary.sort_values("일관객합계", ascending=True)

fig4 = px.bar(
    movie_summary,
    x="일관객합계",
    y="영화명",
    orientation="h",
    title="기간 내 일관객 합계 TOP 10",
    labels={
        "일관객합계": "일관객 합계",
        "영화명": "영화"
    },
    custom_data=["10위권_일수"]
)

fig4.update_traces(
    hovertemplate=(
        "영화: %{y}<br>"
        "일관객 합계: %{x:,}명<br>"
        "10위권에 든 날수: %{customdata[0]}일"
        "<extra></extra>"
    )
)

fig4.update_layout(
    yaxis=dict(categoryorder="total ascending")
)

st.plotly_chart(fig4, use_container_width=True)

st.markdown("**이 그래프로 알 수 있는 것:**")
st.info(
    "이 기간 동안 일관객을 모두 합산했을 때 가장 많은 관객을 기록한 "
    "영화 TOP 10을 비교할 수 있으며, 각 영화가 박스오피스 10위권에 "
    "얼마나 오래 머물렀는지도 확인할 수 있습니다."
)# ===================================
# 그래프 4. 영화별 누적 일관객 TOP 10
# ===================================
st.divider()
st.header("그래프 4. 영화별 일관객 합계 TOP 10")

# 영화별 일관객 합계와 10위권에 든 날수 계산
movie_summary = (
    df.groupby("영화명")
    .agg(
        일관객합계=("일관객", "sum"),
        10위권_일수=("날짜", "nunique")
    )
    .reset_index()
    .sort_values("일관객합계", ascending=False)
    .head(10)
)

# 관객이 많은 영화가 위에 오도록 순서 설정
movie_summary = movie_summary.sort_values("일관객합계", ascending=True)

fig4 = px.bar(
    movie_summary,
    x="일관객합계",
    y="영화명",
    orientation="h",
    title="기간 내 일관객 합계 TOP 10",
    labels={
        "일관객합계": "일관객 합계",
        "영화명": "영화"
    },
    custom_data=["10위권_일수"]
)

fig4.update_traces(
    hovertemplate=(
        "영화: %{y}<br>"
        "일관객 합계: %{x:,}명<br>"
        "10위권에 든 날수: %{customdata[0]}일"
        "<extra></extra>"
    )
)

fig4.update_layout(
    yaxis=dict(categoryorder="total ascending")
)

st.plotly_chart(fig4, use_container_width=True)

st.markdown("**이 그래프로 알 수 있는 것:**")
st.info(
    "이 기간 동안 일관객을 모두 합산했을 때 가장 많은 관객을 기록한 "
    "영화 TOP 10을 비교할 수 있으며, 각 영화가 박스오피스 10위권에 "
    "얼마나 오래 머물렀는지도 확인할 수 있습니다."
)
