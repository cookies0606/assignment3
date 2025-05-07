import streamlit as st
import openai
import tempfile

st.set_page_config(page_title="ChatPDF", page_icon="📄")
st.title("📄 ChatPDF - PDF 파일로 대화하기")

# 세션 상태 초기화
if "vector_store_id" not in st.session_state:
    st.session_state.vector_store_id = None
if "pdf_file_id" not in st.session_state:
    st.session_state.pdf_file_id = None
if "assistant_id" not in st.session_state:
    st.session_state.assistant_id = None
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

# API Key 입력
api_key = st.text_input("🔑 OpenAI API Key", type="password", value=st.session_state.get("api_key", ""))
if api_key:
    st.session_state.api_key = api_key
    client = openai.OpenAI(api_key=api_key)
else:
    st.warning("API Key를 입력하세요.")
    st.stop()

# PDF 파일 업로드
uploaded_file = st.file_uploader("📁 PDF 파일을 업로드하세요", type=["pdf"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    with st.spinner("📤 파일 업로드 및 벡터 스토어 생성 중..."):
        try:
            file = client.files.create(file=open(tmp_path, "rb"), purpose="assistants")
            vector_store = client.beta.vector_stores.create(name="ChatPDF Store")
            client.beta.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vector_store.id,
                files=[file.id]
            )
            assistant = client.beta.assistants.create(
                name="PDF Assistant",
                instructions="사용자가 업로드한 PDF를 참고해 질문에 답하세요.",
                tools=[{"type": "file_search"}],
                model="gpt-4-1106-preview",
                tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}}
            )
            thread = client.beta.threads.create()

            # 세션 상태에 저장
            st.session_state.vector_store_id = vector_store.id
            st.session_state.pdf_file_id = file.id
            st.session_state.assistant_id = assistant.id
            st.session_state.thread_id = thread.id

            st.success("✅ 벡터 스토어 생성 완료! 질문을 입력해보세요.")
        except Exception as e:
            st.error(f"❌ 오류 발생: {e}")

# Clear 버튼
if st.session_state.vector_store_id and st.button("🧹 Clear Vector Store"):
    try:
        client.beta.vector_stores.delete(st.session_state.vector_store_id)
        st.success("🗑️ Vector Store 삭제 완료")
        st.session_state.vector_store_id = None
        st.session_state.pdf_file_id = None
        st.session_state.assistant_id = None
        st.session_state.thread_id = None
    except Exception as e:
        st.error(f"❌ 삭제 중 오류 발생: {e}")

# 질문 입력 및 응답 처리
if st.session_state.vector_store_id:
    question = st.text_input("❓ 질문을 입력하세요")
    if question:
        with st.spinner("🤖 GPT가 응답 중입니다..."):
            try:
                client.beta.threads.messages.create(
                    thread_id=st.session_state.thread_id,
                    role="user",
                    content=question,
                    file_ids=[st.session_state.pdf_file_id]
                )
                run = client.beta.threads.runs.create_and_poll(
                    thread_id=st.session_state.thread_id,
                    assistant_id=st.session_state.assistant_id
                )
                messages = client.beta.threads.messages.list(
                    thread_id=st.session_state.thread_id
                )
                for msg in reversed(messages.data):
                    if msg.role == "assistant":
                        st.markdown("### 💬 GPT의 응답")
                        st.write(msg.content[0].text.value)
                        break
            except Exception as e:
                st.error(f"❌ 응답 오류: {e}")
