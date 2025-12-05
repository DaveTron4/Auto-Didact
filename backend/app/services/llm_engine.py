import os
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

# Initialize Groq (Llama 3)
llm = ChatGroq(
    temperature=0.5, # 0.0 = Robot, 1.0 = Creative
    model_name="llama3-8b-8192",
    groq_api_key=os.getenv("GROQ_API_KEY")
)

def generate_answer(question: str, context: str):
    """
    Asks the AI to answer the question using ONLY the context provided.
    """
    prompt = ChatPromptTemplate.from_template(
        """
        You are an expert teacher. Answer the user's question strictly based on the context provided below.
        If the answer is not in the context, say "I don't know based on this document."
        
        <context>
        {context}
        </context>

        Question: {question}
        """
    )

    chain = prompt | llm
    response = chain.invoke({"question": question, "context": context})
    return response.content