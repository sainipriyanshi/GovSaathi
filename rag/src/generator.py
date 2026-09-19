from __future__ import annotations


import os
from typing import Any


from groq import Groq


class LLMGenerator:
    def __init__(
        self,
        model_name: str | None = None,
    ) -> None:
        api_key = os.getenv(
            "GROQ_API_KEY"
        )

        if not api_key:
            raise RuntimeError(
                "GROQ_API_KEY is not configured."
            )

        self.client = Groq(
            api_key=api_key
        )

        self.model_name = (
            model_name
            or os.getenv(
                "GROQ_MODEL",
                "qwen/qwen3.8-27b",
            )
        )

    def generate(
        self,
        query: str,
        contexts: list[dict[str, Any]],
    ) -> str:
        context_text = self._format_context(
        contexts
    )

        prompt = f"""
You are GovSaathi, an assistant for
Indian government schemes.

Answer the user's question using only
the retrieved documents.

Rules:
- If the user asks about one scheme,
  explain that scheme.
- If the user asks broadly about schemes,
  summarize all distinct schemes supported
  by the retrieved documents.
- Do not invent facts.
- If a requested detail is missing,
  say that it is not available in the
  retrieved documents.
- Do not refuse merely because multiple
  schemes appear in the context.
- Keep the answer clear and concise.

User question:
{query}

Retrieved documents:
{context_text}
"""

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Answer only from the "
                        "provided documents."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.1,
        )

        return (
            response.choices[0]
            .message
            .content
            .strip()
        )


    def stream_generate(
        self,
        query: str,
        contexts: list[dict[str, Any]],
    ):
        context_text = self._format_context(contexts)

        prompt = f"""
You are GovSaathi, an assistant for
Indian government schemes.

Answer the user's question using only
the retrieved documents.

Rules:
- If the user asks about one scheme,
  explain that scheme.
- If the user asks broadly about schemes,
  summarize all distinct schemes supported
  by the retrieved documents.
- Do not invent facts.
- If a requested detail is missing,
  say that it is not available in the
  retrieved documents.
- Do not refuse merely because multiple
  schemes appear in the context.
- Keep the answer clear and concise.

User question:
{query}

Retrieved documents:
{context_text}
"""

        stream = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Answer only from the "
                        "provided documents."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.1,
            stream=True,
        )

        for chunk in stream:
            if not chunk.choices:
                continue

            content = chunk.choices[0].delta.content

            if content:
                yield content    
    

    @staticmethod
    def _format_context(
        contexts: list[dict[str, Any]],
    ) -> str:
        sections: list[str] = []

        for position, item in enumerate(
            contexts,
            start=1,
        ):
            file_name = item.get(
                "file_name",
                "Unknown",
            )

            source = item.get(
                "source",
                "Unknown",
            )

            chunk = item.get(
                "chunk",
                0,
            )

            text = item.get(
                "text",
                "",
            ).strip()

            sections.append(
                f"[Reference {position}]\n"
                f"File: {file_name}\n"
                f"Path: {source}\n"
                f"Chunk: {chunk}\n"
                f"{text}"
            )

        return "\n\n".join(sections)