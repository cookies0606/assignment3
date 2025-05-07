import streamlit as st
from openai import OpenAI

# 세션 상태 초기화
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

st.title("💬 Chat with GPT-4.1-mini")

# API 키 입력
api_key_input = st.text_input("OpenAI API Key 입력", type="password")
if api_key_input:
    st.session_state.api_key = api_key_input

# 사용자 입력
user_message = st.text_input("메시지를 입력하세요:")

# Clear 버튼
if st.button("🧹 Clear"):
    st.session_state.chat_history = []

# 대화 기록 출력
for role, msg in st.session_state.chat_history:
    if role == "user":
        st.markdown(f"🧑‍💬 **You**: {msg}")
    else:
        st.markdown(f"🤖 **GPT**: {msg}")

# Responses API 호출 함수
def call_responses_api(history, api_key):
    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model="gpt-4.1-mini-2025-04-14",
        input=history
    )
    return response.output[0].content[0].text

# 응답 처리
if user_message and st.session_state.api_key:
    st.session_state.chat_history.append(("user", user_message))
    history = [{"role": role, "content": msg} for role, msg in st.session_state.chat_history]
    try:
        response_text = call_responses_api(history, st.session_state.api_key)
        st.session_state.chat_history.append(("assistant", response_text))
        st.rerun()
    except Exception as e:
        st.error(f"❌ 오류 발생: {e}")
