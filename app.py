import streamlit as st
import os
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFDirectoryLoader
import time

from dotenv import load_dotenv
load_dotenv()

# Set environment variables
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ['OPENAI_API_KEY'] = os.getenv("OPENAI_API_KEY")
os.environ['GROQ_API_KEY'] = os.getenv("GROQ_API_KEY")
groq_api_key = os.getenv("GROQ_API_KEY")
os.environ['HF_TOKEN'] = os.getenv("HF_TOKEN")

# Initialize ChatGroq LLM
llm = ChatGroq(groq_api_key=groq_api_key, model_name="Llama3-8b-8192")

# Prompt template
prompt = ChatPromptTemplate.from_template(
    """
    Answer the questions based on the provided context only.
    Please provide the most accurate response based on the question.
    <context>
    {context}
    <context>
    Question:{input}
    """
)

def create_vector_embedding():
    if "vectors" not in st.session_state:
        st.session_state.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        st.session_state.loader = PyPDFDirectoryLoader("research_papers")
        st.session_state.docs = st.session_state.loader.load()
        print(f"Number of loaded documents: {len(st.session_state.docs)}")
        st.session_state.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        st.session_state.final_documents = st.session_state.text_splitter.split_documents(st.session_state.docs[:50])
        print(f"Number of split documents: {len(st.session_state.final_documents)}")
        print(f"Embedding Model: {st.session_state.embeddings}")
        texts = [doc.page_content for doc in st.session_state.final_documents]
        embeddings = st.session_state.embeddings.embed_documents(texts)
        print(f"Number of embeddings: {len(embeddings)}")
        st.session_state.vectors = FAISS.from_documents(st.session_state.final_documents, st.session_state.embeddings)
        st.write("Vector Database is ready. You can now enter your query.")

st.title("RAG Document Q&A With Groq And Lama3")
st.write("## Instructions:")
st.write("1. **Click the 'Create Document Embeddings' button.**")
st.write("2. **Once the vector database is ready, enter your query related to 'A Comprehensive Overview of Large Language Models' and 'Attention Is All You Need' research papers.**")

if st.button("Create Document Embeddings"):
    create_vector_embedding()

user_prompt = st.text_input("Enter your query from the research paper:")

if user_prompt:
    if "vectors" in st.session_state:
        document_chain = create_stuff_documents_chain(llm, prompt)
        retriever = st.session_state.vectors.as_retriever()
        retrieval_chain = create_retrieval_chain(retriever, document_chain)

        start = time.process_time()
        response = retrieval_chain.invoke({'input': user_prompt})
        print(f"Response time: {time.process_time() - start}")

        st.write(response['answer'])

        with st.expander("Document similarity Search"):
            for i, doc in enumerate(response['context']):
                st.write(doc.page_content)
                st.write('------------------------')
    else:
        st.write("Please create the vector embeddings first.")