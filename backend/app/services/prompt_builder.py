from langchain_core.prompts import ChatPromptTemplate

GROUNDED_RAG_PROMPT_TEMPLATE = ChatPromptTemplate.from_template(
    """You are a helpful AI study assistant. Your task is to answer the user's question using ONLY the provided document context.

Rules:
1. Ground your answers strictly in the provided DOCUMENT CONTEXT.
2. You MUST include source citations in your answer when referencing specific information. Format citations exactly like this: [Source: filename, Page X, Paragraph Y].
3. Do NOT make up information or reference external knowledge not present in the context.
4. If the provided context does not contain the answer, reply EXACTLY with: "I couldn't find this information in the selected documents."

DOCUMENT CONTEXT:
{context}

USER QUESTION: {query}

ANSWER:"""
)

SUMMARY_PROMPT_TEMPLATE = ChatPromptTemplate.from_template(
    """You are summarizing only the provided knowledge context.

Rules:
- Summarize only what appears in the context.
- If the context is weak or empty, say "Unknown based on the provided context."
- Organize the response with short bullets.

Focus request:
{query}

Context:
{context}

Summary:"""
)

QUIZ_PROMPT_TEMPLATE = ChatPromptTemplate.from_template(
    """You are generating a quiz from the provided context only.

Rules:
- Use only the given context.
- Return valid JSON only.
- Return an array of objects with this exact structure: {{"question":"...","answer":"...","difficulty":"easy|medium|hard"}}.
- Generate exactly {count} items.
- If the context is insufficient, return [].

Topic:
{query}

Context:
{context}

Respond with valid JSON array only:"""
)

SUGGESTED_PROMPTS_TEMPLATE = ChatPromptTemplate.from_template(
    """Based on the provided AI answer context, generate exactly 5 relevant, smart, and specific follow-up questions the user might ask next.

Rules:
- Generate exactly 5 questions.
- One question per line.
- Do NOT add numbers, bullet points, prefix, or extra conversational text. Just output the questions directly.
- Make them highly contextual and relevant to the study material.

AI Answer Context:
{context}

Follow-up Questions:"""
)

FLASHCARD_PROMPT_TEMPLATE = ChatPromptTemplate.from_template(
    """You are an expert educator. Create flashcards to help study the provided document content.

Rules:
- Return a valid JSON array only.
- Do not wrap in markdown tags like ```json or anything else. Just start with [ and end with ].
- Generate exactly {count} flashcards.
- Each flashcard MUST have: 'front' (the question/concept) and 'back' (the explanation/definition).
- Each flashcard should have a 'difficulty' ('easy', 'medium', or 'hard') based on content complexity.
- Rely ONLY on the provided context.

Context:
{context}

Respond with valid JSON array only:"""
)


def build_rag_prompt(*, query: str, context: str) -> str:
    return GROUNDED_RAG_PROMPT_TEMPLATE.format(query=query, context=context)


def build_summary_prompt(*, query: str, context: str) -> str:
    return SUMMARY_PROMPT_TEMPLATE.format(query=query, context=context)


def build_quiz_prompt(*, query: str, context: str, count: int) -> str:
    return QUIZ_PROMPT_TEMPLATE.format(query=query, context=context, count=count)


def build_suggested_prompts_prompt(*, query: str, context: str) -> str:
    return SUGGESTED_PROMPTS_TEMPLATE.format(context=context)


def build_flashcard_prompt(*, context: str, count: int) -> str:
    return FLASHCARD_PROMPT_TEMPLATE.format(context=context, count=count)


STUDY_NOTES_PROMPT_TEMPLATE = ChatPromptTemplate.from_template(
    """You are a senior educator. Your task is to generate comprehensive, well-structured study notes on the topic "{query}" using the provided document context.

Rules:
1. Ground the notes strictly in the provided document context.
2. Structure the notes beautifully in Markdown with the following exact sections:
   - # [Topic Title]
   - ## Definition
     Provide a clear, detailed explanation of the concept based on the document context.
   - ## Advantages
     List the benefits, advantages, or key use cases.
   - ## Architecture
     Describe the architecture, structure, or working mechanism.
   - ## Example Code / Practical Application
     Provide a code example (e.g. Java, Python, SQL) or a concrete step-by-step application of the concept.
   - ## Architectural Diagram (Mermaid)
     Provide a clean, valid Mermaid flowchart representing the architecture. Format it as:
     ```mermaid
     graph TD
       A[...] --> B[...]
     ```
   - ## Interview Questions
     Provide 3-5 potential interview questions along with concise answers.
3. If the context does not contain enough information to complete all sections, fill them to the best of your ability using general knowledge but clearly demarcate grounded info.

DOCUMENT CONTEXT:
{context}

STUDY NOTES:"""
)


def build_study_notes_prompt(*, query: str, context: str) -> str:
    return STUDY_NOTES_PROMPT_TEMPLATE.format(query=query, context=context)


