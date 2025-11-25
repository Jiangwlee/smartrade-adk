from typing import Optional
from google.genai import types

def format_content(content: Optional[types.Content], max_length: int = 200) -> str:
    """Format content for logging, truncating if too long."""
    if not content or not content.parts:
        return "None"

    parts = []
    for part in content.parts:
        if part.text:
            text = part.text
            if len(text) > max_length:
                text = text[:max_length] + "..."
            parts.append(f"text: '{text}'")
        elif part.function_call:
            parts.append(f"function_call: {part.function_call.name}")
        elif part.function_response:
            parts.append(f"function_response: {part.function_response.name}")
        elif part.code_execution_result:
            parts.append("code_execution_result")
        else:
            parts.append("other_part")

    return " | ".join(parts)