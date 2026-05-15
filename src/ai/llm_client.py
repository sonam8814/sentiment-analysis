"""LLM client with Groq primary and Gemini fallback, exponential backoff, and structured logging."""

import hashlib
import time

from loguru import logger

from config.settings import Settings, get_settings
from src.utils.exceptions import LLMUnavailableError


class LLMClient:
    """Unified LLM client that tries Groq first, then falls back to Gemini.

    Attributes:
        settings: Application settings instance.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialize the LLM client.

        Args:
            settings: Optional settings override; defaults to get_settings().
        """
        self.settings = settings or get_settings()

    def complete(self, prompt: str, system: str | None = None) -> str:
        """Send a prompt to the LLM and return the response text.

        Tries the primary provider first. On failure (rate limit, timeout, 5xx),
        falls back to the secondary provider. Uses exponential backoff on retries.

        Args:
            prompt: The user prompt to send.
            system: Optional system prompt.

        Returns:
            The LLM response text.

        Raises:
            LLMUnavailableError: If both providers fail after all retries.
        """
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:12]

        providers = self._get_provider_order()
        last_error: Exception | None = None

        for provider_name in providers:
            try:
                result = self._call_with_retries(
                    provider_name, prompt, system, prompt_hash
                )
                return result
            except Exception as exc:
                last_error = exc
                logger.warning(
                    f"Provider {provider_name} failed, " f"trying next. Error: {exc}"
                )

        raise LLMUnavailableError(f"All LLM providers failed. Last error: {last_error}")

    def _get_provider_order(self) -> list[str]:
        """Return provider names in priority order based on settings.

        Returns:
            List of provider names, primary first.
        """
        if self.settings.llm_provider_primary == "groq":
            return ["groq", "gemini"]
        return ["gemini", "groq"]

    def _call_with_retries(
        self,
        provider: str,
        prompt: str,
        system: str | None,
        prompt_hash: str,
    ) -> str:
        """Call a single provider with exponential backoff.

        Args:
            provider: Provider name ("groq" or "gemini").
            prompt: The user prompt.
            system: Optional system prompt.
            prompt_hash: Truncated hash for logging.

        Returns:
            The LLM response text.

        Raises:
            Exception: The last exception if all retries fail.
        """
        max_retries = self.settings.llm_max_retries
        last_exc: Exception | None = None

        for attempt in range(max_retries):
            backoff = 2**attempt  # 1s, 2s, 4s, ...
            try:
                start = time.monotonic()
                result = self._call_provider(provider, prompt, system)
                latency_ms = int((time.monotonic() - start) * 1000)

                logger.info(
                    f"LLM call success | provider={provider} "
                    f"model={self._get_model(provider)} "
                    f"latency_ms={latency_ms} "
                    f"prompt_hash={prompt_hash}"
                )
                return result

            except Exception as exc:
                latency_ms = int((time.monotonic() - start) * 1000)
                last_exc = exc
                logger.warning(
                    f"LLM call failed | provider={provider} "
                    f"model={self._get_model(provider)} "
                    f"latency_ms={latency_ms} "
                    f"prompt_hash={prompt_hash} "
                    f"attempt={attempt + 1}/{max_retries} "
                    f"error={exc}"
                )
                if attempt < max_retries - 1:
                    time.sleep(backoff)

        raise last_exc  # type: ignore[misc]

    def _get_model(self, provider: str) -> str:
        """Return the model name for a provider.

        Args:
            provider: Provider name.

        Returns:
            Model identifier string.
        """
        if provider == "groq":
            return self.settings.groq_model
        return self.settings.gemini_model

    def _call_provider(self, provider: str, prompt: str, system: str | None) -> str:
        """Dispatch a single call to the specified provider.

        Args:
            provider: "groq" or "gemini".
            prompt: User prompt text.
            system: Optional system prompt.

        Returns:
            Response text from the provider.
        """
        if provider == "groq":
            return self._call_groq(prompt, system)
        return self._call_gemini(prompt, system)

    def _call_groq(self, prompt: str, system: str | None) -> str:
        """Call the Groq API.

        Args:
            prompt: User prompt.
            system: Optional system prompt.

        Returns:
            Response text.
        """
        from groq import Groq

        client = Groq(api_key=self.settings.groq_api_key)

        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=self.settings.groq_model,
            messages=messages,
            temperature=0.0,
            timeout=self.settings.llm_timeout_seconds,
        )
        return response.choices[0].message.content or ""

    def _call_gemini(self, prompt: str, system: str | None) -> str:
        """Call the Google Gemini API.

        Args:
            prompt: User prompt.
            system: Optional system prompt.

        Returns:
            Response text.
        """
        import google.generativeai as genai

        genai.configure(api_key=self.settings.gemini_api_key)

        model = genai.GenerativeModel(
            model_name=self.settings.gemini_model,
            system_instruction=system,
        )

        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(temperature=0.0),
        )
        return response.text or ""
