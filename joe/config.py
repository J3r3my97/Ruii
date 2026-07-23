from pydantic_settings import BaseSettings, SettingsConfigDict


class JoeSettings(BaseSettings):
    """Runtime configuration for the Joe agent.

    Reads the same ``.env`` file as ``llm_engineering.settings`` but keeps a
    separate ``JOE_``-prefixed namespace so the agent's knobs never collide with
    the dormant pipeline settings. Deliberately free of ZenML so importing this
    module is cheap.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", env_prefix="JOE_", extra="ignore")

    # --- Local model (OpenAI-compatible chat completions) ---
    # Dev: Ollama on the Mac host. Prod: vLLM on a GPU VPC. Swapping between them
    # is purely these three values — no code change.
    LLM_BASE_URL: str = "http://localhost:11434/v1"
    LLM_MODEL: str = "qwen3:8b"
    LLM_API_KEY: str = "ollama"  # dummy for local servers; a real key if pointed at a hosted API

    # --- Generation defaults ---
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 1024
    # Some reasoning models (e.g. Qwen3) emit <think>...</think> blocks. When true,
    # the client strips them so only Joe's user-facing reply is surfaced.
    LLM_STRIP_THINKING: bool = True
    # Qwen3 reasons by default and can spend its whole token budget thinking,
    # returning empty content. When true the client appends Qwen3's `/no_think`
    # directive to the system message so chat replies come back directly. Harmless
    # to non-Qwen models. (Note: on Ollama, `think:false` and chat_template_kwargs
    # are ignored via the OpenAI endpoint — `/no_think` in the system prompt is
    # what actually works.)
    LLM_NO_THINK: bool = True

    # --- Conversation / memory ---
    HISTORY_WINDOW: int = 20  # messages of raw history sent to the model

    # --- Retrieval (persona knowledge) ---
    RAG_ENABLED: bool = True
    RAG_TOP_K: int = 4

    # --- API server ---
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8080


settings = JoeSettings()
