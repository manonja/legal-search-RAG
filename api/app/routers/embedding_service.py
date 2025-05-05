# app/routers/embedding_service.py
from fastapi import APIRouter, Depends
from app.models.embedding_service import EmbeddingRequest, EmbeddingResponse
from app.services.embedding_service import EmbeddingService

router = APIRouter(prefix="/embeddings", tags=["embeddings"])


def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()


@router.post("/generate", response_model=EmbeddingResponse)
async def generate_embeddings(
    request: EmbeddingRequest,
    embedding_service: EmbeddingService = Depends(get_embedding_service),  # noqa: B008
) -> EmbeddingResponse:
    embeddings = await embedding_service.generate_embeddings(request.texts)
    return EmbeddingResponse(embeddings=embeddings)
