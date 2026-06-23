import os
from dotenv import load_dotenv

load_dotenv()

SUPPORTED_PROVIDERS = "groq, gemini, openai, anthropic, ollama"


def _env(name, default=None):
    value = os.getenv(name)
    if value is None:
        return default

    # Be forgiving of values copied with quotes or inline comments in .env files.
    value = value.split("#", 1)[0].strip().strip("'\"")
    return value or default


def _missing_package_error(provider, package):
    return ImportError(
        f"The '{provider}' LLM provider requires the '{package}' package. "
        f"Install it with: pip install {package}"
    )


def _require_env(name, provider):
    value = _env(name)
    if value:
        return value

    raise RuntimeError(
        f"The '{provider}' LLM provider requires {name}. "
        f"Add {name}=your_api_key to your .env file."
    )


def get_llm():
    provider = _env("LLM_PROVIDER", "groq").lower()

    if provider in {"google", "google-genai"}:
        provider = "gemini"

    if provider == "groq":
        try:
            from langchain_groq import ChatGroq
        except ModuleNotFoundError as exc:
            raise _missing_package_error("groq", "langchain-groq") from exc

        return ChatGroq(
            model=_env("GROQ_MODEL", "llama-3.3-70b-versatile"),
            api_key=_require_env("GROQ_API_KEY", "groq"),
            temperature=0,
        )

    elif provider == "gemini":
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
        except ModuleNotFoundError as exc:
            raise _missing_package_error("gemini", "langchain-google-genai") from exc

        return ChatGoogleGenerativeAI(
            model=_env("GEMINI_MODEL", "gemini-1.5-flash"),
            google_api_key=_require_env("GOOGLE_API_KEY", "gemini"),
            temperature=0,
        )

    elif provider == "openai":
        try:
            from langchain_openai import ChatOpenAI
        except ModuleNotFoundError as exc:
            raise _missing_package_error("openai", "langchain-openai") from exc

        return ChatOpenAI(
            model=_env("OPENAI_MODEL", "gpt-4o-mini"),
            api_key=_require_env("OPENAI_API_KEY", "openai"),
            temperature=0,
        )

    elif provider == "anthropic":
        try:
            from langchain_anthropic import ChatAnthropic
        except ModuleNotFoundError as exc:
            raise _missing_package_error("anthropic", "langchain-anthropic") from exc

        return ChatAnthropic(
            model=_env("ANTHROPIC_MODEL", "claude-3-haiku-20240307"),
            api_key=_require_env("ANTHROPIC_API_KEY", "anthropic"),
            temperature=0,
        )

    elif provider == "ollama":
        try:
            from langchain_ollama import ChatOllama
        except ModuleNotFoundError as exc:
            raise _missing_package_error("ollama", "langchain-ollama") from exc

        return ChatOllama(
            model=_env("OLLAMA_MODEL", "llama3"),
            temperature=0,
        )

    raise ValueError(f"Unknown provider '{provider}'. Supported providers: {SUPPORTED_PROVIDERS}")
