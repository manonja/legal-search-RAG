from pydantic import BaseModel


class ChatPromptResponse(BaseModel):
    content: str


class ChatPromptRequest(BaseModel):
    system_prompt: str
    user_prompt: str
    max_tokens: int = 1024
    temperature: float = 0.7
