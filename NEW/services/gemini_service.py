from typing import List, Iterable, Tuple
from google import genai
from google.genai import types

from NEW import config


async def generate_with_gemini(prompt: str, max_chars: int = 1800) -> str:
    try:
        client = genai.Client(api_key=config.GEMINI_API_KEY)
        model = "gemini-2.5-flash"

        requirements = (
            f"需求：\n"
            f"- 回覆長度請控制在 {max_chars} 個字元以內（含 Markdown 符號）。\n"
            f"- 若內容過長，請摘要重點。\n"
            f"- 請避免多餘前言與客套，專注結果本身。\n"
        )
        final_prompt = f"{requirements}\n任務：\n{prompt}"

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
        return text or "（無回覆）"
    except Exception as e:
        return f"Gemini 錯誤：{e}"


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
            f"需求：\n"
            f"- 回覆長度請控制在 {max_chars} 個字元以內（含 Markdown 符號）。\n"
            f"- 若內容過長，請摘要重點。\n"
            f"- 專注在圖片與題意本身，避免多餘前言。\n"
        )
        final_prompt = f"{requirements}\n任務：\n{prompt}"

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
        return text or "（無回覆）"
    except Exception as e:
        return f"Gemini 錯誤：{e}"

