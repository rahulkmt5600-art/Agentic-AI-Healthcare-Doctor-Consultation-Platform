from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

llm = ChatGoogleGenerativeAI(model="gemini-flash-latest")

response = llm.invoke("Say hello and confirm you're working, in one sentence.")

# Handle both simple string responses and structured list responses
if isinstance(response.content, str):
    print(response.content)
else:
    # Extract just the text parts from the structured response
    for part in response.content:
        if isinstance(part, dict) and part.get("type") == "text":
            print(part["text"])