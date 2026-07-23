"""The single point through which Joe talks to a language model.

Everything is an OpenAI-compatible chat-completions call, so pointing at Ollama
(dev), vLLM (prod), or any hosted provider is a matter of ``base_url`` / model /
key in :mod:`joe.config` — no code change anywhere else.
"""

from collections.abc import AsyncIterator

from loguru import logger
from openai import AsyncOpenAI

from joe.config import settings

from .think import ThinkStripper, strip_thinking

Message = dict[str, str]


class LLMClient:
    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self.model = model or settings.LLM_MODEL
        self._client = AsyncOpenAI(
            base_url=base_url or settings.LLM_BASE_URL,
            api_key=api_key or settings.LLM_API_KEY,
        )
        logger.debug(f"LLMClient ready: model={self.model} base_url={base_url or settings.LLM_BASE_URL}")

    @staticmethod
    def _prepare(messages: list[Message]) -> list[Message]:
        """Apply model quirks that belong to the wire layer, not the caller.

        Currently: append Qwen3's ``/no_think`` directive to the system message so
        chat replies come back directly instead of the model reasoning until its
        token budget is exhausted. No-op for non-Qwen models.
        """

        if not settings.LLM_NO_THINK:
            return messages

        prepared = [dict(m) for m in messages]
        for m in prepared:
            if m.get("role") == "system":
                m["content"] = f"{m['content']}\n\n/no_think"
                return prepared
        # No system message present — add one carrying just the directive.
        return [{"role": "system", "content": "/no_think"}, *prepared]

    async def chat(
        self,
        messages: list[Message],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Return the full assistant reply as a string (think blocks removed)."""

        response = await self._client.chat.completions.create(
            model=self.model,
            messages=self._prepare(messages),
            temperature=settings.LLM_TEMPERATURE if temperature is None else temperature,
            max_tokens=max_tokens or settings.LLM_MAX_TOKENS,
        )
        content = response.choices[0].message.content or ""

        return strip_thinking(content) if settings.LLM_STRIP_THINKING else content

    async def stream_chat(
        self,
        messages: list[Message],
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        """Yield user-facing text as it streams in (think blocks removed on the fly)."""

        stripper = ThinkStripper(enabled=settings.LLM_STRIP_THINKING)
        stream = await self._client.chat.completions.create(
            model=self.model,
            messages=self._prepare(messages),
            temperature=settings.LLM_TEMPERATURE if temperature is None else temperature,
            max_tokens=max_tokens or settings.LLM_MAX_TOKENS,
            stream=True,
        )
        async for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta.content or ""
            if not delta:
                continue
            visible = stripper.feed(delta)
            if visible:
                yield visible

        tail = stripper.flush()
        if tail:
            yield tail
