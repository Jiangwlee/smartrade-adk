import os
import logging
import enum
from pydantic import BaseModel
from google.adk.models.lite_llm import LiteLlm
import httpx

logger = logging.getLogger("swkj." + __name__)

# 全局HTTP客户端配置 - 启用连接池和keep-alive
_http_client = None
_litellm_configured = False

def configure_litellm_http_client():
    """配置LiteLLM使用持久化HTTP客户端，启用连接池"""
    global _http_client, _litellm_configured

    if _litellm_configured:
        return

    # 创建httpx客户端，启用连接池
    _http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(60.0, connect=10.0),
        limits=httpx.Limits(
            max_connections=100,           # 最大连接数
            max_keepalive_connections=20,  # 保持活跃的连接数
            keepalive_expiry=30.0,         # 连接保持30秒
        ),
        http2=False,  # doubao可能不支持HTTP/2，先禁用
    )

    # 配置litellm使用这个client
    import litellm
    try:
        # litellm 1.0+版本支持
        litellm.client_session = _http_client
        litellm.aclient_session = _http_client
        logger.info("✅ Configured LiteLLM with persistent HTTP client (connection pooling enabled)")
    except AttributeError:
        # 旧版本litellm不支持，记录警告
        logger.warning("⚠️ Current litellm version doesn't support custom HTTP client. Connection pooling disabled.")

    _litellm_configured = True

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

model_cache = {}

def get_litellm_model(model: LLMProvider) -> LiteLlm:
    """Returns a LiteLlm instance for the given model name, mapping known providers.

    Args:
        model (LLMProvider): The name of the model to instantiate.
    """
    # 首次调用时配置HTTP连接池
    logger.info("🔧 Configuring LiteLLM HTTP client...")
    configure_litellm_http_client()

    if model in PROVIDERS_MAP:
        llm_config = PROVIDERS_MAP[model]
        logger.info(f"Using LLM Config: {llm_config.model_dump()}")
        if llm_config.model not in model_cache:
            logger.info(f"📦 Creating new LiteLlm instance for model: {llm_config.model}")
            model_cache[llm_config.model] = LiteLlm(model=llm_config.model, api_key=llm_config.api_key, base_url=llm_config.base_url)
        else:
            logger.info(f"♻️ Reusing cached LiteLlm instance for model: {llm_config.model}")
        return model_cache[llm_config.model]
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