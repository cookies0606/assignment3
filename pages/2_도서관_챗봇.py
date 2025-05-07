import streamlit as st
from openai import OpenAI

st.title("📚 국립부경대학교 도서관 챗봇")

# 도서관 규정 문자열 (예시 일부)
library_rules = """
1. 도서관 운영시간은 평일 오전 9시부터 오후 9시까지입니다. 주말과 공휴일은 휴관입니다.
2. 학부생은 최대 5권까지 14일 동안 도서를 대출할 수 있습니다.
3. 연체 시 하루 1권당 100원의 연체료가 부과됩니다.
4. 대출한 도서는 1회에 한해 연장할 수 있으며, 연장은 추가 7일입니다.
"""

# 세션 상태 초기화
if "library_chat_history" not in st.session_state:
    st.session_state.library_chat_history = []

# API 키 입력
api_key = st.text_input("OpenAI API Key", type="password")
if api_key:
    st.session_state.api_key = api_key

# 사용자 질문 입력
user_input = st.text_input("도서관에 대해 궁금한 점을 물어보세요:")

# 대화 내용 초기화 버튼
if st.button("🧹 Clear Chat"):
    st.session_state.library_chat_history = []

# 이전 대화 출력
for role, msg in st.session_state.library_chat_history:
    if role == "user":
        st.markdown(f"🧑‍🎓 **You**: {msg}")
    else:
        st.markdown(f"🤖 **도서관 챗봇**: {msg}")

# GPT 호출 함수
def ask_library_bot(history, api_key):
    client = OpenAI(api_key=api_key)
    prompt = [
        {"role": "system", "content": "다음은 국립부경대학교 도서관 규정입니다:\n" + library_rules},
    ] + history
    response = client.responses.create(
        model="gpt-4.1-mini-2025-04-14",
        input=prompt
    )
    return response.output[0].content[0].text

# 응답 처리
if user_input and st.session_state.api_key:
    st.session_state.library_chat_history.append(("user", user_input))
    messages = [{"role": role, "content": msg} for role, msg in st.session_state.library_chat_history]
    try:
        answer = ask_library_bot(messages, st.session_state.api_key)
        st.session_state.library_chat_history.append(("assistant", answer))
        st.rerun()
    except Exception as e:
        st.error(f"오류 발생: {e}")
