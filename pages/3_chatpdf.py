import streamlit as st
import os
import tempfile
from PyPDF2 import PdfReader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA

# 페이지 설정
st.set_page_config(page_title="ChatPDF", layout="wide")
st.title("📄 ChatPDF: PDF 문서 기반 챗봇")

# 세션 상태 초기화
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

# API 키 입력 받기
api_key = st.text_input("🔑 OpenAI API Key를 입력하세요", type="password", value=st.session_state.api_key)
if api_key:
    st.session_state.api_key = api_key
    os.environ["OPENAI_API_KEY"] = api_key

# PDF 업로드
uploaded_file = st.file_uploader("📎 PDF 파일 업로드", type="pdf")

# 벡터 스토어 초기화 버튼
if st.button("🧹 Clear Vector Store"):
    st.session_state.vectorstore = None
    st.success("벡터 저장소 초기화 완료!")

# PDF 파일 처리 및 벡터 저장소 생성
if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_path = tmp_file.name

    # 텍스트 추출
    reader = PdfReader(tmp_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()

    # 텍스트 분할
    splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    texts = splitter.split_text(text)

    # 벡터 저장소 생성
    embeddings = OpenAIEmbeddings(openai_api_key=st.session_state.api_key)
    st.session_state.vectorstore = FAISS.from_texts(texts, embeddings)
    st.success("✅ PDF에서 벡터 저장소 생성 완료!")

# 사용자 질문 입력
query = st.text_input("❓ 질문을 입력하세요:")

# 질의응답 수행
if query and st.session_state.vectorstore:
    llm = ChatOpenAI(temperature=0.3, openai_api_key=st.session_state.api_key)
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=st.session_state.vectorstore.as_retriever()
    )
    response = qa_chain.run(query)
    st.markdown(f"📘 **답변:** {response}")
