from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.local", extra="ignore")

    APP_NAME: str = "tuna-starlink-app"

    # Local art gallery (Beelink bind-mount or ./art in dev)
    ART_STORAGE_PATH: str = "./art"

    # xAI — short chat calls + Imagine for images
    XAI_API_KEY: str = ""
    XAI_BASE_URL: str = "https://api.x.ai/v1"
    # Non-reasoning is enough for art brief + caption (reasoning wastes tokens).
    XAI_CHAT_MODEL: str = "grok-4-1-fast-non-reasoning"
    XAI_IMAGE_MODEL: str = "grok-imagine-image"
    # Keep series posts landscape (16:9). Portrait shows as a thin middle bar.
    XAI_IMAGE_SIZE: str = "1792x1024"
    XAI_IMAGE_ASPECT_RATIO: str = "16:9"

    # Dry run: fake events + placeholder PNG, zero API spend
    DRY_RUN: bool = False

    # Scheduler: short peak evening, few posts, then done.
    # Interval + window + hard nightly cap are the main cost levers (Imagine $).
    # Scheduler OFF by default — no unattended fires (each generate costs Imagine $).
    # Leave knobs below for optional re-enable; they do nothing while ENABLED=false.
    SCHEDULE_CRON: str = "off (manual generate only)"
    SCHEDULE_TIMEZONE: str = "America/New_York"
    SCHEDULE_INTERVAL_MINUTES: int = 40
    SCHEDULE_PEAK_START_HOUR: int = 19
    SCHEDULE_PEAK_END_HOUR: int = 22
    SCHEDULE_MAX_RUNS_PER_DAY: int = 5
    SCHEDULE_ENABLED: bool = False

    # After a successful generate (manual), post to X automatically when true.
    AUTO_PUBLISH: bool = False

    # Default art style key from prompts/styles.yaml (Planet Hack series)
    DEFAULT_STYLE: str = "data-tunnel"

    # News intake:
    #   rss|stream — lean RSS wire (default; free)
    #   xai        — ask Grok (often no live news → refuse; costs tokens)
    #   hybrid     — stream first, Grok if empty
    #   x|x-search — force X recent-search only when X_SEARCH_ENABLED
    EVENTS_SOURCE: str = "stream"

    # Re-fetch RSS at most this often (seconds of network saved on Starlink too).
    RSS_INGEST_TTL_MINUTES: int = 45

    # X Recent Search is PAID. Keep OFF. Publish/post still works without it.
    X_SEARCH_ENABLED: bool = False
    X_SEARCH_TTL_MINUTES: int = 120
    X_SEARCH_MAX_RESULTS: int = 10

    # Optional local Lemonade on Beelink (text only — not image gen)
    EDGE_TEXT: str = "xai"  # xai | lemonade
    LEMONADE_URL: str = "http://127.0.0.1:13305"
    LEMONADE_MODEL: str = "Qwen3-4B-GGUF"

    # X OAuth 1.0a — @tunastarlink access tokens (post + media only by default)
    X_API_KEY: str = ""
    X_API_SECRET: str = ""
    X_ACCESS_TOKEN: str = ""
    X_ACCESS_TOKEN_SECRET: str = ""
    X_ACCOUNT_HANDLE: str = "@tunastarlink"


settings = Settings()
