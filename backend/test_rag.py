from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.document_loaders import TextLoader

load_dotenv()

# Step 1: Load the raw text file
loader = TextLoader("test_knowledge.txt")
documents = loader.load()

# Step 2: Split it into smaller chunks (one per paragraph, in our case)
splitter = CharacterTextSplitter(separator="\n\n", chunk_size=500, chunk_overlap=0)
chunks = splitter.split_documents(documents)

print(f"Split into {len(chunks)} chunks")

# Step 3: Convert each chunk into an embedding, and store them in FAISS
embeddings = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")
vector_store = FAISS.from_documents(chunks, embeddings)

# Step 4: Search for the most relevant chunk(s) given a query
query = "patient has chest tightness and trouble breathing"
results = vector_store.similarity_search(query, k=2)

print(f"\nQuery: {query}")
print("\nTop matching chunks:")
for i, doc in enumerate(results, 1):
    print(f"\n{i}. {doc.page_content}")