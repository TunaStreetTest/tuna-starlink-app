from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.local", extra="ignore")

    APP_NAME: str = "tuna-starlink-app"

    # Local art gallery (Beelink bind-mount or ./art in dev)
    ART_STORAGE_PATH: str = "./art"

    # xAI — chat for events/prompts, Imagine for images
    XAI_API_KEY: str = ""
    XAI_BASE_URL: str = "https://api.x.ai/v1"
    XAI_CHAT_MODEL: str = "grok-4-1-fast-reasoning"
    XAI_IMAGE_MODEL: str = "grok-imagine-image"

    # Dry run: fake events + placeholder PNG, zero API spend
    DRY_RUN: bool = False

    # Scheduler (in-process). Empty = disabled until you turn it on.
    # Example hourly: "0 * * * *"
    SCHEDULE_CRON: str = ""
    SCHEDULE_ENABLED: bool = False

    # After a successful generate (manual or scheduled), post to X automatically.
    AUTO_PUBLISH: bool = False

    # Default art style key from prompts/styles.yaml (Planet Hack series)
    DEFAULT_STYLE: str = "data-tunnel"

    # Where world events come from for the art director:
    #   rss    — live public news feeds (default, reliable)
    #   xai    — ask Grok (often no live news → refusal)
    #   hybrid — RSS first, Grok if RSS fails
    EVENTS_SOURCE: str = "rss"

    # Optional local Lemonade on Beelink (text only — not image gen)
    EDGE_TEXT: str = "xai"  # xai | lemonade
    LEMONADE_URL: str = "http://127.0.0.1:13305"
    LEMONADE_MODEL: str = "Qwen3-4B-GGUF"

    # Optional X OAuth 1.0a for later auto-post (@tunastarlink).
    # v1 is gallery-first; you can download + post by hand.
    X_API_KEY: str = ""
    X_API_SECRET: str = ""
    X_ACCESS_TOKEN: str = ""
    X_ACCESS_TOKEN_SECRET: str = ""
    X_ACCOUNT_HANDLE: str = "@tunastarlink"


settings = Settings()
