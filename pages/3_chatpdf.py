import streamlit as st
import openai
import tempfile
import os

st.title("📄 Chat with PDF")

# 세션 상태 초기화
if "pdf_file_id" not in st.session_state:
    st.session_state.pdf_file_id = None
if "vector_store_id" not in st.session_state:
    st.session_state.vector_store_id = None

# API 키 입력
api_key = st.text_input("🔑 OpenAI API Key 입력", type="password", value=st.session_state.get("api_key", ""))
if api_key:
    st.session_state.api_key = api_key
    openai_client = openai.OpenAI(api_key=api_key)
else:
    st.warning("먼저 API 키를 입력하세요.")
    st.stop()

# PDF 업로드
uploaded_file = st.file_uploader("📄 PDF 파일 업로드", type=["pdf"])

# Vector Store 생성
if uploaded_file and st.session_state.api_key:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_file_path = tmp_file.name

    with st.spinner("📚 PDF 파일을 업로드하고 임베딩 중입니다..."):
        try:
            # 1. PDF를 OpenAI에 업로드
            uploaded_pdf = openai_client.files.create(file=open(tmp_file_path, "rb"), purpose="assistants")

            # 2. Vector store 생성 및 파일 연결
            vector_store = openai_client.beta.vector_stores.create(name="PDF Vector Store")
            openai_client.beta.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vector_store.id,
                files=[uploaded_pdf.id]
            )

            st.session_state.pdf_file_id = uploaded_pdf.id
            st.session_state.vector_store_id = vector_store.id
            st.success("✅ Vector Store 생성 완료!")

        except Exception as e:
            st.error(f"❌ 오류 발생: {e}")

# Vector Store 삭제
if st.session_state.vector_store_id and st.button("🧹 Clear Vector Store"):
    try:
        openai_client.beta.vector_stores.delete(st.session_state.vector_store_id)
        st.success("🗑️ Vector Store가 삭제되었습니다.")
        st.session_state.vector_store_id = None
        st.session_state.pdf_file_id = None
    except Exception as e:
        st.error(f"❌ 삭제 중 오류 발생: {e}")

# 질문 입력
if st.session_state.vector_store_id:
    question = st.text_input("❓ PDF와 관련된 질문을 입력하세요:")
    if question:
        with st.spinner("🤖 GPT가 응답 중입니다..."):
            try:
                assistant = openai_client.beta.assistants.create(
                    name="ChatPDF Assistant",
                    instructions="업로드된 PDF 파일을 참고해서 질문에 정확하게 답변하세요.",
                    tools=[{"type": "file_search"}],
                    model="gpt-4-1106-preview"
                )

                thread = openai_client.beta.threads.create()
                openai_client.beta.threads.messages.create(
                    thread_id=thread.id,
                    role="user",
                    content=question,
                    file_ids=[st.session_state.pdf_file_id]
                )

                run = openai_client.beta.threads.runs.create_and_poll(
                    thread_id=thread.id,
                    assistant_id=assistant.id,
                    tool_choice="file_search"
                )

                messages = openai_client.beta.threads.messages.list(thread_id=thread.id)
                for msg in reversed(messages.data):
                    if msg.role == "assistant":
                        st.markdown("### 🤖 GPT의 답변")
                        st.write(msg.content[0].text.value)
                        break

            except Exception as e:
                st.error(f"❌ 응답 처리 중 오류 발생: {e}")
