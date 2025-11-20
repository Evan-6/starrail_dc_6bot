from typing import List, Iterable, Tuple
from google import genai
from google.genai import types

from NEW import config


async def generate_with_gemini(prompt: str, max_chars: int = 1800) -> str:
    try:
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        model = "gemini-2.5-flash"

        requirements = (
            f"請遵守以下要求：\n"
            f"- 回覆字數請控制在 {max_chars} 字以內（包含 Markdown 標記）。\n"
            f"- 若不確定答案，請先說明不知道，不要亂編。\n"
            f"- 重點式回答，避免冗長或不實資訊。\n"
        )
        final_prompt = f"{requirements}\n\n使用者提問：\n{prompt}"

        contents: List[types.Content] = [
            types.Content(role="user", parts=[types.Part.from_text(text=final_prompt)])
        ]
        config_gc = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=-1),
            image_config=types.ImageConfig(image_size="1K"),
        )

        text = ""
        for chunk in client.models.generate_content_stream(
            model=model, contents=contents, config=config_gc
        ):
            if chunk.text:
                text += chunk.text
        text = (text or "").strip()
        if len(text) > max_chars:
            text = text[:max_chars]
        return text or "沒有收到回應。"
    except Exception as e:
        return f"Gemini 發生錯誤：{e}"


async def generate_with_gemini_vision(
    prompt: str,
    images: Iterable[Tuple[bytes, str]],
    max_chars: int = 1800,
) -> str:
    """Multimodal generation with images.

    images: iterable of (data_bytes, mime_type) tuples, e.g. (b"...", "image/png").
    """
    try:
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        model = "gemini-2.5-flash"

        requirements = (
            f"請遵守以下要求：\n"
            f"- 回覆字數請控制在 {max_chars} 字以內（包含 Markdown 標記）。\n"
            f"- 優先依據圖片與提問作答，不確定時請直接說明。\n"
            f"- 重點式回答，避免冗長或不實資訊。\n"
        )
        final_prompt = f"{requirements}\n\n使用者提問：\n{prompt}"

        parts: List[types.Part] = [types.Part.from_text(text=final_prompt)]
        for data, mime in images or []:
            if not data:
                continue
            parts.append(types.Part.from_bytes(data=data, mime_type=mime))

        contents: List[types.Content] = [types.Content(role="user", parts=parts)]
        config_gc = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=-1),
            image_config=types.ImageConfig(image_size="1K"),
        )

        text = ""
        for chunk in client.models.generate_content_stream(
            model=model, contents=contents, config=config_gc
        ):
            if chunk.text:
                text += chunk.text
        text = (text or "").strip()
        if len(text) > max_chars:
            text = text[:max_chars]
        return text or "沒有收到回應。"
    except Exception as e:
        return f"Gemini 發生錯誤：{e}"


async def generate_gemini_image(
    prompt: str,
    image_size: str = "1K",
    max_chars: int = 1800,
) -> Tuple[str, List[Tuple[bytes, str]]]:
    """Generate an image (and optional text) with Gemini image preview."""
    try:
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        model = "gemini-3-pro-image-preview"

        contents: List[types.Content] = [
            types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
        ]
        config_gc = types.GenerateContentConfig(
            response_modalities=[
                "IMAGE",
                "TEXT",
            ],
            image_config=types.ImageConfig(image_size=image_size),
        )

        text_parts: List[str] = []
        images: List[Tuple[bytes, str]] = []

        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=config_gc,
        ):
            if chunk.text:
                text_parts.append(chunk.text)

            candidate = (chunk.candidates or [None])[0]
            if not candidate or not candidate.content or not candidate.content.parts:
                continue

            for part in candidate.content.parts:
                inline_data = getattr(part, "inline_data", None)
                if inline_data and inline_data.data:
                    images.append((inline_data.data, inline_data.mime_type or "image/png"))
                if part.text:
                    text_parts.append(part.text)

        text = "".join(text_parts).strip()
        if len(text) > max_chars:
            text = text[:max_chars]
        return text, images
    except Exception as e:
        return f"Gemini 發生錯誤：{e}", []
