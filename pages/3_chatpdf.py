import streamlit as st
import openai
from openai import OpenAI
import os

# 파일 저장용
def save_file(uploaded_file):
    with open(uploaded_file.name, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return uploaded_file.name

# 세션 상태 초기화
if "assistant" not in st.session_state:
    st.session_state.assistant = None
if "thread" not in st.session_state:
    st.session_state.thread = None
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "client" not in st.session_state:
    st.session_state.client = None
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

# Streamlit UI
st.title("📄 File Assistant ChatBot")
api_key = st.text_input("🔑 OpenAI API Key", type="password", value=st.session_state.api_key)
if api_key:
    st.session_state.api_key = api_key
    st.session_state.client = OpenAI(api_key=api_key)

uploaded_file = st.file_uploader(" 텍스트 또는 PDF 파일 업로드", type=["txt", "pdf"])

if st.button("🧹 Clear Vector Store"):
    st.session_state.vectorstore = None
    st.success("벡터 저장소가 초기화되었습니다.")

# 벡터 스토어 + 어시스턴트 생성
if uploaded_file and st.button(" 파일 업로드 및 챗봇 생성"):
    filename = save_file(uploaded_file)
    client = st.session_state.client

    # 벡터 스토어 생성
    vector_store = client.vector_stores.create(name="chatfilestore")
    st.session_state.vector_store = vector_store
    st.session_state.vector_store_id = vector_store.id

    # 파일 업로드 및 인덱싱
    with open(filename, "rb") as f:
        client.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store.id,
            files=[f]
        )

    # 어시스턴트 생성
    assistant = client.beta.assistants.create(
        instructions="업로드된 파일을 기반으로 친절하게 응답하세요.",
        model="gpt-4o",  # 또는 "gpt-4o-mini"
        tools=[{"type": "file_search"}],
        tool_resources={
            "file_search": {
                "vector_store_ids": [vector_store.id]
            }
        }
    )
    st.session_state.assistant = assistant

    # 쓰레드 생성
    st.session_state.thread = client.beta.threads.create()
    st.success("어시스턴트 준비 완료! 질문을 입력해보세요.")

# 챗 인터페이스
if st.session_state.assistant and st.session_state.thread:
    user_input = st.text_input("질문을 입력하세요:")
    if user_input:
        with st.spinner("답변 생성 중..."):
            msg = st.session_state.client.beta.threads.messages.create(
                thread_id=st.session_state.thread.id,
                role="user",
                content=user_input
            )
            run = st.session_state.client.beta.threads.runs.create_and_poll(
                thread_id=st.session_state.thread.id,
                assistant_id=st.session_state.assistant.id
            )

            if run.status == "completed":
                messages = st.session_state.client.beta.threads.messages.list(
                    thread_id=st.session_state.thread.id
                )
                for m in reversed(messages.data):
                    if m.role == "assistant":
                        st.markdown(f" **Assistant:** {m.content[0].text.value}")
                        break
            else:
                st.error(f" Error: {run.status}")
