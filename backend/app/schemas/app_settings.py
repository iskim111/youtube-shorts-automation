from pydantic import BaseModel, Field


class ApiKeysUpdateRequest(BaseModel):
    openai_api_key: str = ""
    youtube_api_key: str = ""
    elevenlabs_api_key: str = ""
    heygen_api_key: str = ""
    pexels_api_key: str = ""
    pixabay_api_key: str = ""
    youtube_client_id: str = ""
    youtube_client_secret: str = ""
    video_mode: str = "ai_character"


class ApiKeysResponse(BaseModel):
    openai_api_key: str = ""
    youtube_api_key: str = ""
    elevenlabs_api_key: str = ""
    heygen_api_key: str = ""
    pexels_api_key: str = ""
    pixabay_api_key: str = ""
    youtube_client_id: str = ""
    youtube_client_secret: str = ""
    video_mode: str = "ai_character"
    configured: dict[str, bool] = Field(default_factory=dict)
