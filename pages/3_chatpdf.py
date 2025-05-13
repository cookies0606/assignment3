import streamlit as st
import os
import openai
import tempfile
import faiss
import numpy as np
from PyPDF2 import PdfReader
from sklearn.metrics.pairwise import cosine_similarity

# 세션 초기화
if "index" not in st.session_state:
    st.session_state.index = None
if "docs" not in st.session_state:
    st.session_state.docs = []
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

# 페이지 기본 설정
st.set_page_config(page_title="ChatPDF (No LangChain)", layout="wide")
st.title("📄 ChatPDF (langchain 없이 구현)")

# API 키 입력
api_key = st.text_input("🔑 OpenAI API Key 입력", type="password", value=st.session_state.api_key)
if api_key:
    st.session_state.api_key = api_key
    openai.api_key = api_key

# Clear 버튼
if st.button("🧹 Clear Vector Store"):
    st.session_state.index = None
    st.session_state.docs = []
    st.success("벡터 저장소 초기화 완료!")

# PDF 업로드
uploaded_file = st.file_uploader("📎 PDF 파일을 업로드하세요", type="pdf")

# PDF → 텍스트 → 청크 분리 → 임베딩 + FAISS
def embed_texts(text_chunks):
    embeddings = []
    for chunk in text_chunks:
        response = openai.Embedding.create(
            model="text-embedding-ada-002",
            input=chunk
        )
        embedding = response['data'][0]['embedding']
        embeddings.append(np.array(embedding, dtype=np.float32))
    return embeddings

def split_text(text, max_tokens=500):
    sentences = text.split(". ")
    chunks, chunk = [], ""
    for sentence in sentences:
        if len(chunk) + len(sentence) < max_tokens:
            chunk += sentence + ". "
        else:
            chunks.append(chunk.strip())
            chunk = sentence + ". "
    if chunk:
        chunks.append(chunk.strip())
    return chunks

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    # 텍스트 추출
    reader = PdfReader(tmp_path)
    raw_text = ""
    for page in reader.pages:
        raw_text += page.extract_text()

    # 청크로 나누기
    text_chunks = split_text(raw_text)
    st.session_state.docs = text_chunks

    # 임베딩 및 FAISS 색인 구축
    embeddings = embed_texts(text_chunks)
    dimension = len(embeddings[0])
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings))
    st.session_state.index = index

    st.success("✅ PDF 처리 및 임베딩 완료!")

# 질문 입력
query = st.text_input("❓ 질문을 입력하세요:")

# 질의응답 수행
if query and st.session_state.index:
    # 쿼리 임베딩
    query_embedding = openai.Embedding.create(
        model="text-embedding-ada-002",
        input=query
    )["data"][0]["embedding"]
    query_vector = np.array(query_embedding, dtype=np.float32).reshape(1, -1)

    # 유사한 문서 검색
    D, I = st.session_state.index.search(query_vector, k=3)
    retrieved_docs = [st.session_state.docs[i] for i in I[0]]

    context = "\n".join(retrieved_docs)
    prompt = f"다음 문서를 참고하여 질문에 답변하세요:\n\n{context}\n\n질문: {query}\n답변:"
    
    # ChatGPT로 질문
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "당신은 문서 기반 질문에 친절하게 답변하는 전문가입니다."},
            {"role": "user", "content": prompt}
        ]
    )
    answer = response["choices"][0]["message"]["content"]
    st.markdown(f"📘 **답변:** {answer}")
