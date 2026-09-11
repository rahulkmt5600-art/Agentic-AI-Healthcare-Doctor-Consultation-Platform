from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.document_loaders import TextLoader

load_dotenv()

# Load and split the knowledge base ONCE when this module is first imported
loader = TextLoader("medical_knowledge.txt")
documents = loader.load()

splitter = CharacterTextSplitter(separator="\n\n", chunk_size=50, chunk_overlap=0)
chunks = splitter.split_documents(documents)

embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
vector_store = FAISS.from_documents(chunks, embeddings)


def retrieve_relevant_knowledge(query: str, k: int = 3) -> str:
    """Searches the medical knowledge base and returns the top matching entries as one text block."""
    results = vector_store.similarity_search(query, k=k)
    combined = "\n\n".join([doc.page_content for doc in results])
    return combined