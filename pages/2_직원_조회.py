st.title("직원 조회")

# 예시용 데이터
data = pd.DataFrame({
    "이름": ["홍길동", "김영희"],
    "부서": ["개발", "인사"],
    "입사일": ["2021-01-01", "2022-05-10"]
})

search_name = st.text_input("이름으로 검색")
if search_name:
    result = data[data["이름"].str.contains(search_name)]
    st.dataframe(result)
else:
    st.dataframe(data)
