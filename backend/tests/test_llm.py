import os
import litellm
from ..llm.litellm_adapter import QWEN3_CONFIG

os.environ["LOG_LEVEL"] = "DEBUG"
litellm._turn_on_debug()

config = QWEN3_CONFIG()

resp = litellm.completion(
    api_key=config.api_key, 
    model=config.model, 
    api_base=config.base_url, 
    messages=[{"role": "user", "content": "你好"}],
    max_tokens=1024)
print(resp)