# ==================================================
# ② 장르별 영화 트리맵 - 총 관객 기준
# ==================================================

st.markdown("---")

st.subheader("② 장르별 영화 트리맵")

# 트리맵에 필요한 데이터만 사용
treemap_df = df[
    ["genre", "movieNm", "total_audi"]
].copy()

# 비어 있는 값 제거
treemap_df = treemap_df.dropna(
    subset=["genre", "movieNm", "total_audi"]
)

# 문자열이 비어 있는 경우도 제거
treemap_df["genre"] = treemap_df["genre"].astype(str).str.strip()
treemap_df["movieNm"] = treemap_df["movieNm"].astype(str).str.strip()

treemap_df = treemap_df[
    (treemap_df["genre"] != "") &
    (treemap_df["movieNm"] != "")
]

# 같은 장르·영화가 여러 번 있을 경우 관객 수 합치기
treemap_df = (
    treemap_df
    .groupby(
        ["genre", "movieNm"],
        as_index=False
    )["total_audi"]
    .sum()
)

fig2 = px.treemap(
    treemap_df,
    path=["genre", "movieNm"],
    values="total_audi",
    title="장르 안의 영화별 총 관객",
    custom_data=["genre", "movieNm", "total_audi"]
)

fig2.update_traces(
    hovertemplate=(
        "<b>%{customdata[1]}</b><br>"
        "장르: %{customdata[0]}<br>"
        "총 관객: %{customdata[2]:,}명"
        "<extra></extra>"
    )
)

fig2.update_layout(
    height=700
)

st.plotly_chart(
    fig2,
    use_container_width=True
)

# --------------------------------------------------
# ② 그래프 분석 구역
# --------------------------------------------------

st.markdown("---")

st.markdown(
    "### 💡 이 그래프로 알 수 있는 것"
)

st.info(
    "각 장르 안에서 영화별 총 관객 규모를 비교하면 "
    "어떤 장르의 어떤 영화가 많은 관객을 확보했는지 "
    "한눈에 확인할 수 있다."
)
