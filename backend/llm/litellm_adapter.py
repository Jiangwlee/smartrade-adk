import os
import logging
import enum
from pydantic import BaseModel
from google.adk.models.lite_llm import LiteLlm

logger = logging.getLogger("swkj." + __name__)

class LLMConfig(BaseModel):
    model: str
    api_key: str = None
    base_url: str = None

class DOUBAO_CONFIG(LLMConfig):
    model: str = "openai/doubao-1.5-pro-32k-250115"
    api_key: str = os.getenv("DOUBAO_API_KEY")
    base_url: str = "https://ark.cn-beijing.volces.com/api/v3/"

class ZAI_CONFIG(LLMConfig):
    model: str = "openai/glm-4.6"
    api_key: str = os.getenv("ZHIPU_API_KEY")
    base_url: str = "https://open.bigmodel.cn/api/coding/paas/v4"

class LLMProvider(enum.Enum):
    DOUBAO = "doubao-seed-1-6-251015"
    GLM = "glm-4.6"

PROVIDERS_MAP = {
    LLMProvider.DOUBAO: DOUBAO_CONFIG(model=f"openai/{LLMProvider.DOUBAO.value}"),
    LLMProvider.GLM: ZAI_CONFIG(model=f"openai/{LLMProvider.GLM.value}")
}

def get_litellm_model(model: LLMProvider) -> LiteLlm:
    """Returns a LiteLlm instance for the given model name, mapping known providers.

    Args:
        model (LLMProvider): The name of the model to instantiate.
    """
    if model in PROVIDERS_MAP:
        llm_config = PROVIDERS_MAP[model]
        logger.info(f"Using LLM Config: {llm_config.model_dump()}")
        return LiteLlm(model=llm_config.model, api_key=llm_config.api_key, base_url=llm_config.base_url)
    else:
        return None

def get_doubao_model() -> LiteLlm:
    return get_litellm_model(LLMProvider.DOUBAO)

def get_glm_model() -> LiteLlm:
    return get_litellm_model(LLMProvider.GLM)

def get_deepseek_model() -> LiteLlm:
    return LiteLlm(
        model="deepseek/deepseek-chat",
        api_key=os.getenv("DEEPSEEK_API_KEY")
    )