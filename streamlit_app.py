import streamlit as st
import openai

# --- 세션 상태를 활용한 API 키 저장 ---
if 'api_key' not in st.session_state:
    st.session_state['api_key'] = ""

st.title("GPT-4.1-mini ChatBot")

# --- API Key 입력 받기 ---
api_key_input = st.text_input("Enter your OpenAI API Key:", type="password")
if api_key_input:
    st.session_state['api_key'] = api_key_input

# --- 질문 입력 ---
user_input = st.text_input("Ask me anything:")

# --- 응답 생성 함수 (캐시 사용) ---
@st.cache_data(show_spinner=True)
def get_gpt_response(prompt, api_key):
    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",  # 또는 "gpt-4.0"에 해당하는 이름
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

# --- 결과 출력 ---
if user_input and st.session_state['api_key']:
    try:
        response = get_gpt_response(user_input, st.session_state['api_key'])
        st.write("**GPT Response:**")
        st.write(response)
    except Exception as e:
        st.error(f"Error: {e}")
