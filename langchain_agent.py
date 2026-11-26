"""Optional LangChain + local Ollama conversational layer."""
def ask_with_langchain(question: str, context: str, model: str = "llama3.2") -> str:
    try:
        from langchain_ollama import ChatOllama
        from langchain_core.messages import SystemMessage, HumanMessage
    except ImportError as exc:
        raise RuntimeError("Install optional dependencies: pip install -r requirements-ai.txt") from exc

    llm = ChatOllama(model=model, temperature=0)
    system = (
        "You are a cautious property security analyst. Answer only from the supplied indexed event context. "
        "Do not invent detections, identities, or times. If the context is insufficient, say so.\n\n"
        f"INDEXED CONTEXT:\n{context}"
    )
    result = llm.invoke([SystemMessage(content=system), HumanMessage(content=question)])
    return str(result.content)
