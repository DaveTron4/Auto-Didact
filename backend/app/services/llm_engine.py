import os
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
import os
import json
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

# Initialize Groq (Llama 3)
llm = ChatGroq(
    temperature=0.5,  # 0.0 = Robot, 1.0 = Creative
    model_name="llama3-8b-8192",
    groq_api_key=os.getenv("GROQ_API_KEY")
)


def generate_answer(question: str, context: str):
    """Asks the AI to answer the question using ONLY the context provided."""
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


def _strip_code_blocks(text: str) -> str:
    """Remove surrounding ``` fences and language hints if present."""
    if not text:
        return text
    text = text.strip()
    if text.startswith("```") and text.endswith("```"):
        # remove first and last line if they are ``` or ```json
        lines = text.splitlines()
        # drop the first line and last line
        return "\n".join(lines[1:-1]).strip()
    return text


def generate_script(context: str, title: str = "Auto-Didact Video") -> dict:
    """
    Ask the LLM to produce a structured script in JSON. The expected format:

    {
      "title": "...",
      "scenes": [
         {"id": 1, "narrator_text": "...", "image_prompt": "..."},
         ...
      ]
    }

    Returns a parsed dict. If parsing fails, raises ValueError.
    """
    prompt = ChatPromptTemplate.from_template(
        """
        You are an expert instructional designer that converts source material into a short, factual video script.
        Based ONLY on the context below, produce a JSON object with the following schema:

        {
          "title": string,
          "scenes": [
            {"id": integer, "narrator_text": string, "image_prompt": string}
          ]
        }

        Requirements:
        - Each scene should be short (1-2 sentences) and grounded in the context.
        - `image_prompt` should be a concise creative prompt suitable for generating an illustrative image.
        - Output must be valid JSON and contain only the JSON object (no surrounding commentary).

        Context:
        {context}

        """
    )

    chain = prompt | llm
    response = chain.invoke({"context": context, "title": title})
    raw = _strip_code_blocks(response.content)

    try:
        parsed = json.loads(raw)
    except Exception as exc:
        # try to be tolerant: attempt to find first { and last }
        try:
            start = raw.index("{")
            end = raw.rindex("}") + 1
            parsed = json.loads(raw[start:end])
        except Exception:
            raise ValueError(f"Unable to parse JSON from model output: {exc}\nOutput:\n{raw}")

    return parsed