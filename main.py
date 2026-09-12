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
