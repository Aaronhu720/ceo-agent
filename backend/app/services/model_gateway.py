from abc import ABC, abstractmethod
from typing import AsyncIterator
from dataclasses import dataclass

from app.core.config import settings


@dataclass
class ChatMessage:
    role: str
    content: str  # text content
    image_urls: list[str] | None = None  # optional image URLs for vision


@dataclass
class ChatResponse:
    content: str
    model: str
    provider: str
    prompt_tokens: int = 0
    completion_tokens: int = 0


@dataclass
class ChatStreamDelta:
    content: str
    finish_reason: str | None = None


class ChatModelProvider(ABC):
    @abstractmethod
    async def chat(self, messages: list[ChatMessage], **kwargs) -> ChatResponse:
        pass

    @abstractmethod
    async def chat_stream(self, messages: list[ChatMessage], **kwargs) -> AsyncIterator[ChatStreamDelta]:
        pass


class OpenAIProvider(ChatModelProvider):
    def __init__(self, api_key: str = "", base_url: str = "", model: str = ""):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.base_url = base_url or settings.OPENAI_BASE_URL
        self.model = model or settings.OPENAI_DEFAULT_MODEL

    @staticmethod
    def _format_message(m: ChatMessage) -> dict:
        if m.image_urls:
            content = [{"type": "text", "text": m.content}]
            for url in m.image_urls:
                content.append({"type": "image_url", "image_url": {"url": url, "detail": "auto"}})
            return {"role": m.role, "content": content}
        return {"role": m.role, "content": m.content}

    async def chat(self, messages: list[ChatMessage], **kwargs) -> ChatResponse:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        response = await client.chat.completions.create(
            model=kwargs.get("model", self.model),
            messages=[self._format_message(m) for m in messages],
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 4096),
        )
        choice = response.choices[0]
        return ChatResponse(
            content=choice.message.content or "",
            model=response.model,
            provider="openai",
            prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
            completion_tokens=response.usage.completion_tokens if response.usage else 0,
        )

    async def chat_stream(self, messages: list[ChatMessage], **kwargs) -> AsyncIterator[ChatStreamDelta]:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        stream = await client.chat.completions.create(
            model=kwargs.get("model", self.model),
            messages=[self._format_message(m) for m in messages],
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 4096),
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield ChatStreamDelta(
                    content=chunk.choices[0].delta.content,
                    finish_reason=chunk.choices[0].finish_reason,
                )


class AnthropicProvider(ChatModelProvider):
    def __init__(self, api_key: str = "", model: str = ""):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.model = model or settings.ANTHROPIC_DEFAULT_MODEL

    async def chat(self, messages: list[ChatMessage], **kwargs) -> ChatResponse:
        from anthropic import AsyncAnthropic
        client = AsyncAnthropic(api_key=self.api_key)

        system_msg = ""
        chat_messages = []
        for m in messages:
            if m.role == "system":
                system_msg = m.content
            else:
                chat_messages.append({"role": m.role, "content": m.content})

        response = await client.messages.create(
            model=kwargs.get("model", self.model),
            max_tokens=kwargs.get("max_tokens", 4096),
            system=system_msg,
            messages=chat_messages,
            temperature=kwargs.get("temperature", 0.7),
        )
        return ChatResponse(
            content=response.content[0].text if response.content else "",
            model=response.model,
            provider="anthropic",
            prompt_tokens=response.usage.input_tokens,
            completion_tokens=response.usage.output_tokens,
        )

    async def chat_stream(self, messages: list[ChatMessage], **kwargs) -> AsyncIterator[ChatStreamDelta]:
        from anthropic import AsyncAnthropic
        client = AsyncAnthropic(api_key=self.api_key)

        system_msg = ""
        chat_messages = []
        for m in messages:
            if m.role == "system":
                system_msg = m.content
            else:
                chat_messages.append({"role": m.role, "content": m.content})

        async with client.messages.stream(
            model=kwargs.get("model", self.model),
            max_tokens=kwargs.get("max_tokens", 4096),
            system=system_msg,
            messages=chat_messages,
            temperature=kwargs.get("temperature", 0.7),
        ) as stream:
            async for text in stream.text_stream:
                yield ChatStreamDelta(content=text)


class GeminiProvider(ChatModelProvider):
    def __init__(self, api_key: str = "", model: str = ""):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_DEFAULT_MODEL

    async def chat(self, messages: list[ChatMessage], **kwargs) -> ChatResponse:
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(kwargs.get("model", self.model))

        history = []
        for m in messages:
            if m.role == "system":
                history.append({"role": "user", "parts": [f"[System]: {m.content}"]})
                history.append({"role": "model", "parts": ["Understood."]})
            elif m.role == "user":
                history.append({"role": "user", "parts": [m.content]})
            else:
                history.append({"role": "model", "parts": [m.content]})

        last_msg = history.pop()
        chat = model.start_chat(history=history)
        response = chat.send_message(last_msg["parts"][0])

        return ChatResponse(
            content=response.text,
            model=self.model,
            provider="gemini",
        )

    async def chat_stream(self, messages: list[ChatMessage], **kwargs) -> AsyncIterator[ChatStreamDelta]:
        response = await self.chat(messages, **kwargs)
        yield ChatStreamDelta(content=response.content, finish_reason="stop")


_providers: dict[str, ChatModelProvider] = {}


def get_model_provider(provider: str | None = None) -> ChatModelProvider:
    provider = provider or settings.DEFAULT_MODEL_PROVIDER
    if provider not in _providers:
        if provider == "openai":
            _providers[provider] = OpenAIProvider()
        elif provider == "anthropic":
            _providers[provider] = AnthropicProvider()
        elif provider == "gemini":
            _providers[provider] = GeminiProvider()
        else:
            raise ValueError(f"Unknown provider: {provider}")
    return _providers[provider]
