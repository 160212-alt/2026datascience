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
)
