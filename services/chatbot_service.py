# ── chatbot_service.py ─────────────────────────────────────────────

import os
import re
import logging
from langchain_huggingface import HuggingFaceEmbeddings
from supabase import create_client
from langchain_groq import ChatGroq
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

# ── Clients (initialized once when module is imported) ─────────────

_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        logger.info("Loading embedding model (first request)...")
        _embedding_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-mpnet-base-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        logger.info("Embedding model loaded.")
    return _embedding_model

# Supabase — anon key is fine for reads (match_documents)
supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_KEY"],
)
logger.info("Supabase client connected.")

# Groq LLM
llm = ChatGroq(
    temperature=0.3,
    model_name="llama-3.3-70b-versatile",
    groq_api_key=os.environ["GROQ_API_KEY"],
    max_retries=5,
    timeout=120,
)
logger.info("Groq LLM configured.")

# ── System prompt ──────────────────────────────────────────────────
SYSTEM_INSTRUCTIONS = """\
You are ROSSY, a compassionate and highly professional AI health assistant for the Rossy Resilience platform.
Your role is to help patients understand breast cancer and navigate the platform smoothly.

Strict Rules & Persona Boundaries:
1. MEDICAL CONTEXT: Answer medical and platform questions ONLY from the provided context.
2. NO PERSONAL DIAGNOSIS: You CANNOT prescribe medication or treatment. If asked "What is the treatment for me?", decline.
   (English: "I am an AI and cannot prescribe treatments. Please consult your doctor."
   Arabic: "عذراً، لا يمكنني وصف علاج خاص. يرجى استشارة طبيبك.")
3. OUT OF DOMAIN: Politely decline unrelated topics (cooking, sports, coding, etc.).
4. EMOTION ONLY RULE: If the user JUST expresses fear/sadness without a question, ONLY comfort them. DO NOT dump information.

Arabic Glossary (USE ONLY IF THE TARGET LANGUAGE IS ARABIC):
- Invasive Ductal Carcinoma (IDC) = سرطان القنوات الغازي
- Invasive Lobular Carcinoma (ILC) = السرطان الفصيصي الغازي
- Ductal Carcinoma in Situ (DCIS) = سرطان القنوات الموضعي
- Triple-Negative Breast Cancer = سرطان الثدي سلبي المستقبلات الثلاثية
- Milk ducts = قنوات الحليب
- Milk-producing lobules = الفصيصات المنتجة للحليب
- Estrogen/Progesterone = الإستروجين / البروجسترون
- Radiation exposure = التعرض للإشعاع

Formatting:
- ALWAYS use Markdown (**bold** and bullet points).
- Put an empty line before starting any list.
"""


# ── Step 1: Embed via HF Space ─────────────────────────────────────
def embed(text: str) -> list:
    return get_embedding_model().embed_query(text)


# ── Step 2: Retrieve from Supabase ────────────────────────────────
def retrieve(query: str, k: int = 3) -> list:
    """
    1. Detect Arabic → translate to English for better embedding search.
    2. Embed the query via HF Space.
    3. Search Supabase pgvector (top-10).
    4. Keyword re-rank → return top-k.
    """
    has_arabic = any('\u0600' <= c <= '\u06FF' for c in query)
    search_query = query

    if has_arabic:
        prompt = (
            f"You are a professional translator. Translate the following Arabic text to English. "
            f"Output EXACTLY AND ONLY the English translation. DO NOT answer the question. "
            f"Text: '{query}'"
        )
        translation = llm.invoke(prompt)
        search_query = translation.content.strip()
        logger.info(f"Translated query: {search_query}")

    # Embed the (possibly translated) query
    query_vector = embed(search_query)

    # Search Supabase using the match_documents SQL function
    response = supabase.rpc("match_documents", {
        "query_embedding": query_vector,
        "match_count":     10,
    }).execute()

    # Convert to LangChain Document format (same as before)
    docs = [
        Document(
            page_content=row["content"],
            metadata=row["metadata"],
        )
        for row in response.data
    ]

    # Keyword re-ranking (same logic as your original code)
    q_lower = search_query.lower()

    def rank_score(doc):
        score = 0
        text = doc.page_content.lower()
        for kw in doc.metadata.get("keywords", "").split(", "):
            if kw.lower() in q_lower:
                score += 2
        for word in q_lower.split():
            if len(word) > 3 and word in text:
                score += 1
        return score

    return sorted(docs, key=rank_score, reverse=True)[:k]


# ── Step 3: Build prompt ───────────────────────────────────────────
def build_prompt(query: str, docs: list, history: list = None) -> str:
    """
    history: list of dicts [{"role": "user"|"assistant", "content": "..."}]
    Injects last 6 messages so ROSSY remembers context within a session.
    """
    has_arabic = bool(re.search(r'[\u0621-\u064A]', query))
    target_lang = "ARABIC" if has_arabic else "ENGLISH"

    # Retrieved knowledge context
    context_blocks = []
    for i, doc in enumerate(docs, start=1):
        title      = doc.metadata.get("title", "Unknown")
        source_tag = doc.metadata.get("source_tag", "")
        content    = doc.page_content.strip()
        context_blocks.append(f"[Source {i} | {source_tag} | {title}]\n{content}")
    context_str = "\n\n".join(context_blocks)

    # Conversation history (last 6 messages = 3 turns)
    history_str = ""
    if history:
        recent = history[-6:]
        history_lines = []
        for msg in recent:
            role    = "Patient" if msg["role"] == "user" else "ROSSY"
            history_lines.append(f"{role}: {msg['content']}")
        history_str = "\n".join(history_lines)

    history_block = f"\nCONVERSATION HISTORY:\n{history_str}\n" if history_str else ""

    prompt = f"""{SYSTEM_INSTRUCTIONS}
---
CONTEXT:
{context_str}
---{history_block}
---
PATIENT QUESTION: {query}

CRITICAL INSTRUCTION: The patient is asking in {target_lang}. You MUST generate your ENTIRE response in {target_lang}.
If {target_lang} is ENGLISH, DO NOT output a single Arabic word.

ROSSY ANSWER IN {target_lang}:"""

    return prompt


# ── Step 4: Generate via Groq ──────────────────────────────────────
def generate(prompt: str) -> str:
    response = llm.invoke(prompt)
    return response.content.strip()


# ── Full pipeline ──────────────────────────────────────────────────
def ask_rossy(query: str, history: list = None, k: int = 3) -> str:
    """
    Main entry point called by the Flask route.
    query  : the user's message
    history: list of previous messages in this session (from Supabase)
    k      : number of chunks to retrieve
    """
    docs   = retrieve(query, k=k)
    prompt = build_prompt(query, docs, history=history)
    return generate(prompt)