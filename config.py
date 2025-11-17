from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    # RAG settings
    USE_RAG: bool = Field(default=True)
    EMBEDDING_MODEL: str = Field(default="sentence-transformers/all-MiniLM-L6-v2")
    FAISS_INDEX_PATH: str = Field(default="vector_store/faiss.index")
    FAISS_META_PATH: str = Field(default="vector_store/metadata.json")
    CHUNK_TOKEN_TARGET: int = Field(default=220)
    CHUNK_OVERLAP: int = Field(default=40)
    TOP_K: int = Field(default=5)

    # Optional persistence (future)
    MONGO_URI: str | None = Field(default=None)
    MONGO_DB_NAME: str = Field(default="asktube")
    MONGO_VECTOR_COLLECTION: str = Field(default="transcript_chunks")
    VECTOR_INDEX_NAME: str = Field(default="vector_index")

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")


settings = Settings()
