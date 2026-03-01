from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Mistral
    mistral_api_key: str
    mistral_triage_model: str = "mistral-large-latest"
    mistral_vision_model: str = "pixtral-large-latest"  # Mistral's vision model

    # ElevenLabs
    elevenlabs_api_key: str

    # Supabase
    supabase_url: str
    supabase_service_key: str

    # App
    app_env: str = "development"
    log_level: str = "DEBUG"
    demo_scenario: str = "market_st_crash"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
