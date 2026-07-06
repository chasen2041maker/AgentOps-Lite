from __future__ import annotations

from collections.abc import Callable
from typing import Any


def openai_chat_llm(create: Callable[..., Any], **default_kwargs: Any) -> Callable[[str], str]:
    """Adapt an OpenAI-compatible chat create function to ``llm_call(prompt)``."""

    def llm_call(prompt: str) -> str:
        response = create(
            **default_kwargs,
            messages=[{"role": "user", "content": prompt}],
        )
        return _extract_message_content(response)

    return llm_call


def _extract_message_content(response: Any) -> str:
    if isinstance(response, dict):
        return str(response["choices"][0]["message"]["content"])
    choice = response.choices[0]
    message = choice.message
    return str(message.content)
