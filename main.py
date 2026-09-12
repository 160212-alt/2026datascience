import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta, timezone

# --------------------------------------------------
# 기본 설정
# --------------------------------------------------
st.set_page_config(
    page_title="영화 데이터 그래프 도감",
    layout="wide"
)

st.title("🎬 영화 데이터 그래프 도감")

# --------------------------------------------------
# KOBIS API 설정
# --------------------------------------------------
API_KEY = st.secrets["KOBIS_KEY"]

KST = timezone(timedelta(hours=9))
yesterday = (datetime.now(KST) - timedelta(days=1)).strftime("%Y%m%d")

url = (
    "https://kobis.or.kr/kobisopenapi/webservice/rest/"
    "boxoffice/searchDailyBoxOfficeList.json"
)

params = {
    "key": API_KEY,
    "targetDt": yesterday
}

# --------------------------------------------------
# API 호출
# --------------------------------------------------
try:
    response = requests.get(url, params=params)
    response.raise_for_status()

    data = response.json()

    movie_list = data["boxOfficeResult"]["dailyBoxOfficeList"]

    if not movie_list:
        st.warning("어제의 영화 데이터가 없습니다.")
        st.stop()

    df = pd.DataFrame(movie_list)

except Exception as e:
    st.error(f"API 데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# --------------------------------------------------
# 숫자 데이터 변환
# --------------------------------------------------
numeric_columns = [
    "rank",
    "rankInten",
    "salesAmt",
    "salesShare",
    "salesInten",
    "salesChange",
    "salesAcc",
    "audiCnt",
    "audiInten",
    "audiChange",
    "audiAcc",
    "scrnCnt",
    "showCnt"
]

for col in numeric_columns:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# 총 관객수
df["total_audi"] = df["audiAcc"]

# 결측값 제거
df = df.dropna(subset=["total_audi"])

# --------------------------------------------------
# 1. 일별 관객수 TOP 5
# --------------------------------------------------
st.subheader("1. 관객수 TOP 5 영화")

top5 = df.sort_values(
    by="audiCnt",
    ascending=False
).head(5)

fig1, ax1 = plt.subplots(figsize=(10, 5))

ax1.bar(
    top5["movieNm"],
    top5["audiCnt"]
)

ax1.set_xlabel("영화")
ax1.set_ylabel("일 관객수")
ax1.set_title("어제 관객수 TOP 5")

plt.xticks(rotation=20)

st.pyplot(fig1)

# --------------------------------------------------
# 2. 영화별 총 관객수
# --------------------------------------------------
st.subheader("2. 영화별 총 관객수")

fig2, ax2 = plt.subplots(figsize=(10, 5))

sorted_df = df.sort_values(
    by="total_audi",
    ascending=False
)

ax2.bar(
    sorted_df["movieNm"],
    sorted_df["total_audi"]
)

ax2.set_xlabel("영화")
ax2.set_ylabel("총 관객수")
ax2.set_title("영화별 총 관객수")

plt.xticks(rotation=45, ha="right")

st.pyplot(fig2)

# --------------------------------------------------
# 3. 총 관객수 히스토그램
# --------------------------------------------------
st.subheader("3. 영화별 총 관객수 분포")

fig3, ax3 = plt.subplots(figsize=(10, 5))

ax3.hist(
    df["total_audi"],
    bins=20,
    edgecolor="black"
)

ax3.set_xlabel("총 관객수")
ax3.set_ylabel("영화 수")
ax3.set_title("영화별 총 관객수 히스토그램")

st.pyplot(fig3)

# --------------------------------------------------
# 히스토그램 분석
# --------------------------------------------------
counts, bins = np.histogram(
    df["total_audi"],
    bins=20
)

max_bin_index = np.argmax(counts)

low = bins[max_bin_index]
high = bins[max_bin_index + 1]

# 가장 관객이 많은 영화
max_index = df["total_audi"].idxmax()

max_movie = df.loc[max_index, "movieNm"]
max_audience = df.loc[max_index, "total_audi"]

st.write(
    f"📊 **대부분의 영화는 약 "
    f"{low:,.0f}명 ~ {high:,.0f}명 구간에 몰려 있습니다.**"
)

st.write(
    f"🏆 **가장 관객이 많은 영화는 "
    f"'{max_movie}'로, 총 관객은 "
    f"{max_audience:,.0f}명입니다.**"
)

# --------------------------------------------------
# 데이터 표
# --------------------------------------------------
st.subheader("📋 영화 데이터")

show_columns = [
    "rank",
    "movieNm",
    "audiCnt",
    "total_audi",
    "scrnCnt",
    "showCnt"
]

show_columns = [
    col for col in show_columns
    if col in df.columns
]

st.dataframe(
    df[show_columns],
    use_container_width=True
)
