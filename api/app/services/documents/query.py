"""Query service for document search and retrieval.

This module provides functionality to query documents using vector similarity search
and generate responses using the LLM chat service.
"""

from typing import Optional, List
import os

from app.core.struct_logger import log

from app.core.config import get_settings
from app.models.query import QueryResponse, SourceInfo
from app.models.search import SearchQuery
from app.services.documents.search import search_documents
from app.services.llm_chat_service import LlmChatService
from app.models.llm_chat_service import ChatPromptRequest


async def process_query(
    query: str,
    max_results: Optional[int] = 5,
    temperature: Optional[float] = 0.7,
    max_tokens: Optional[int] = 1000,
) -> QueryResponse:
    """Process a query and generate a response using RAG.

    Args:
        query: The query text
        max_results: Maximum number of results to return
        temperature: Temperature for response generation
        max_tokens: Maximum tokens in the response

    Returns:
        QueryResponse containing the answer, sources, and confidence
    """
    settings = get_settings()
    log.info("Processing query", query=query)

    try:
        # First, search for relevant documents
        search_limit = (
            max_results if max_results is not None else 5
        )  # Use default if None
        search_results = await search_documents(
            SearchQuery(query=query, limit=search_limit)
        )

        if not search_results:
            log.warning("No search results found for query")
            return QueryResponse(
                answer="I couldn't find any relevant information to answer your question.",
                sources=[],
                confidence=0.0,
            )

        # Format context from search results with proper source and page info
        context_parts = []
        for result in search_results:
            # Prioritize the direct original_filename metadata key
            clean_source_name = result.metadata.get("original_filename")

            # If clean name isn't directly available, fallback to path cleaning
            if not clean_source_name:
                source_path = result.metadata.get(
                    "original_source"
                ) or result.metadata.get("source")
                if source_path:
                    base_name = os.path.basename(source_path)
                    if base_name.startswith("chunked_"):
                        clean_source_name = base_name[len("chunked_") :]
                    else:
                        clean_source_name = base_name
                    if clean_source_name.endswith(".txt"):
                        clean_source_name = clean_source_name[:-4]
                # Keep clean_source_name as None if no path found

            # Page number handling (remains the same)
            page_number_val = result.metadata.get("page_number")
            page_info = (
                f"Page: {page_number_val}" if page_number_val is not None else ""
            )

            # Format context part using the determined clean source name
            context_parts.append(
                f"Source Document: {clean_source_name}\n{page_info}\nExcerpt:\n{result.text}".strip()
            )
        # Use '---' as a clear separator between excerpts
        context = "\n---\n".join(context_parts)

        # Log the retrieved context for debugging
        log.debug("Context retrieved for LLM", context=context)

        # Create sources list for response using ORIGINAL filenames and Document IDs
        sources: List[SourceInfo] = []  # Type hint for clarity
        seen_document_ids = set()
        for result in search_results:
            doc_id = result.metadata.get("document_id")
            original_filename = result.metadata.get("original_filename")

            # Ensure we have both ID and filename, and haven't seen this ID
            if doc_id and original_filename and doc_id not in seen_document_ids:
                sources.append(
                    SourceInfo(filename=original_filename, document_id=doc_id)
                )
                seen_document_ids.add(doc_id)

        # Define the main prompt using a standard f-string for clarity
        prompt = f"""
        You are a highly proficient legal assistant specializing in analysing legal documents and providing answers based on the content of the documents.

        ### Instructions ###
        Answer the user's question based ONLY on the provided document excerpts.
        1.  Analyze the QUESTION carefully.
        2.  Use ONLY information from the provided excerpts
        3.  Structure answers with headings or lists for readability
        4.  **Crucially, whenever you state a fact or principle derived from an excerpt, you MUST cite the source. Use the format (Source Document: [Document Name]).
        5.  If the excerpts do not contain the information needed to answer the question, state clearly: "Based on the provided documents, I cannot answer this question."
        6.  Maintain a professional, objective tone.

        ### Document Excerpts ###
        <<<
        {context}
        >>>

        ### Question ###
        {query}
        """

        # Initialize LlmChatService
        llm_service = LlmChatService()

        # Prepare request
        request = ChatPromptRequest(
            system_prompt="You are a highly proficient legal assistant specializing in analysing legal documents.",
            user_prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        # Get response using LlmChatService
        log.info("Generating response with LlmChatService")
        service_response = llm_service.prompt(
            system_prompt=request.system_prompt,
            user_prompt=request.user_prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )

        # Extract answer
        answer = service_response.content.strip() if service_response.content else ""

        # Calculate confidence based on similarity scores
        # Higher similarity (lower distance) = higher confidence
        avg_distance = sum(result.distance for result in search_results) / len(
            search_results
        )
        # Convert to confidence (1.0 - normalized distance)
        confidence = max(0.0, min(1.0, 1.0 - (avg_distance / 2.0)))

        log.info("Query processed successfully", confidence=round(confidence, 2))

        return QueryResponse(
            answer=answer,
            sources=sources,
            confidence=confidence,
        )

    except Exception as e:
        log.error("Error processing query", error=str(e))
        raise
