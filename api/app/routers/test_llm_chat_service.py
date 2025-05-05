from fastapi import APIRouter, Depends

from app.models.llm_chat_service import ChatPromptRequest, ChatPromptResponse
from app.services.llm_chat_service import LlmChatService

router = APIRouter(prefix="/test", tags=["test"])


def get_llm_service() -> LlmChatService:
    """Dependency to get LLM service instance."""
    return LlmChatService()


@router.post("/chat", response_model=ChatPromptResponse)
async def test_llm_chat(
    request: ChatPromptRequest,
    llm_service: LlmChatService = Depends(get_llm_service),  # noqa: B008
) -> ChatPromptResponse:
    """
    Test endpoint for the LLM chat service.

    Send a test message to the LLM and get a response back.
    """
    # Get the response from the service
    service_response = llm_service.prompt(
        system_prompt=request.system_prompt,
        user_prompt=request.user_prompt,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
    )

    # Convert to the model-level response type
    return ChatPromptResponse(content=service_response.content)
