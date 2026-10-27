"""
QForge Backend — Application Configuration
Reads all settings from the .env file using Pydantic-Settings.
Never hardcode secrets — always use environment variables.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Google Gemini ──────────────────────────────────────────
    gemini_api_key: str = Field(..., description="Google Gemini API Key")
    gemini_model: str = Field("gemini-2.5-flash", description="Gemini model name")

    # ── MongoDB ────────────────────────────────────────────────
    mongodb_url: str = Field(..., description="MongoDB connection string")
    mongodb_db_name: str = Field("qforge_db", description="Database name")

    # ── Ollama ─────────────────────────────────────────────────
    ollama_base_url: str = Field("http://localhost:11434", description="Ollama server URL")
    ollama_router_model: str = Field("mistral", description="Model used for routing decisions")
    ollama_generator_model: str = Field("codellama", description="Model used for code generation")
    ollama_validator_model: str = Field("codellama", description="Model used for validation")

    # ── Agent Orchestration ────────────────────────────────────
    max_repair_cycles: int = Field(3, description="Max self-heal retry cycles in LangGraph")
    complexity_threshold: int = Field(
        7, description="Score >= this routes to Gemini cloud tier (0-10 scale)"
    )

    # ── FastAPI ────────────────────────────────────────────────
    api_host: str = Field("0.0.0.0")
    api_port: int = Field(8000)
    debug: bool = Field(True)

    # ── FAISS Vector Store ─────────────────────────────────────
    faiss_index_path: str = Field("data/faiss_index/guidelines.index")
    faiss_metadata_path: str = Field("data/faiss_index/chunk_metadata.json")
    embedding_model: str = Field("BAAI/bge-small-en-v1.5")
    top_k_retrieval: int = Field(5)

    # ── GitHub App Integration ──────────────────────────────────
    github_client_id: str = Field("", description="GitHub OAuth / App Client ID")
    github_client_secret: str = Field("", description="GitHub Client Secret")
    github_app_id: str = Field("", description="GitHub App ID")
    github_app_installation_id: str = Field("", description="GitHub App Installation ID")
    github_webhook_secret: str = Field("", description="GitHub Webhook Secret")
    github_private_key_path: str = Field("data/github/app.private-key.pem", description="Path to PEM private key")
    github_token: str = Field("", description="GitHub Personal Access Token")


# Singleton settings instance
settings = Settings()
