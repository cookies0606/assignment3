import streamlit as st
import openai
import tempfile

st.set_page_config(page_title="ChatPDF", page_icon="📄")
st.title("📄 Chat with PDF")

# 세션 상태 초기화
if "vector_store_id" not in st.session_state:
    st.session_state.vector_store_id = None
if "pdf_file_id" not in st.session_state:
    st.session_state.pdf_file_id = None
if "assistant_id" not in st.session_state:
    st.session_state.assistant_id = None
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

# API 키 입력
api_key = st.text_input("🔑 OpenAI API Key", type="password", value=st.session_state.get("api_key", ""))
if api_key:
    st.session_state.api_key = api_key
    client = openai.OpenAI(api_key=api_key)
else:
    st.warning("API Key를 입력하세요.")
    st.stop()

# PDF 업로드
uploaded_file = st.file_uploader("📁 PDF 파일 업로드", type=["pdf"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    with st.spinner("📤 PDF를 업로드하고 벡터 스토어를 생성 중입니다..."):
        try:
            file = client.files.create(file=open(tmp_path, "rb"), purpose="assistants")

            vector_store = client.vector_stores.create(name="My PDF Store")
            client.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vector_store.id,
                files=[file.id]
            )

            assistant = client.assistants.create(
                name="PDF Assistant",
                instructions="답변할 때 업로드된 PDF를 참조하세요.",
                tools=[{"type": "file_search"}],
                model="gpt-4-1106-preview",
                tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}}
            )

            thread = client.threads.create()

            st.session_state.vector_store_id = vector_store.id
            st.session_state.pdf_file_id = file.id
            st.session_state.assistant_id = assistant.id
            st.session_state.thread_id = thread.id

            st.success("✅ 벡터 스토어가 준비되었습니다. 질문을 입력해보세요!")

        except Exception as e:
            st.error(f"❌ 오류 발생: {e}")

# Clear 버튼
if st.session_state.vector_store_id and st.button("🧹 Clear Vector Store"):
    try:
        client.vector_stores.delete(st.session_state.vector_store_id)
        st.success("🗑️ Vector Store 삭제 완료")
        for key in ["vector_store_id", "pdf_file_id", "assistant_id", "thread_id"]:
            st.session_state[key] = None
    except Exception as e:
        st.error(f"❌ 삭제 중 오류 발생: {e}")

# 질문 및 응답
if st.session_state.vector_store_id:
    question = st.text_input("❓ PDF에 대해 질문해보세요")
    if question:
        with st.spinner("🤖 GPT가 응답 중입니다..."):
            try:
                client.threads.messages.create(
                    thread_id=st.session_state.thread_id,
                    role="user",
                    content=question,
                    file_ids=[st.session_state.pdf_file_id]
                )

                run = client.threads.runs.create_and_poll(
                    thread_id=st.session_state.thread_id,
                    assistant_id=st.session_state.assistant_id
                )

                messages = client.threads.messages.list(thread_id=st.session_state.thread_id)
                for msg in reversed(messages.data):
                    if msg.role == "assistant":
                        st.markdown("### 🤖 GPT의 답변")
                        st.write(msg.content[0].text.value)
                        break
            except Exception as e:
                st.error(f"❌ 응답 중 오류 발생: {e}")
