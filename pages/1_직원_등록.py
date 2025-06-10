import streamlit as st
import pandas as pd

st.title("직원 등록")

with st.form("employee_form"):
    name = st.text_input("이름")
    department = st.selectbox("부서", ["인사", "개발", "영업", "기획"])
    hire_date = st.date_input("입사일")
    phone = st.text_input("연락처")
    submitted = st.form_submit_button("등록하기")

    if submitted:
        st.success(f"{name} 님의 정보를 등록했습니다.")
        # DB 저장 또는 session_state에 저장
