from dataclasses import dataclass
from typing import Optional
from openai import OpenAI, APIStatusError, APIError as OpenAI_APIError
from config import ModelConfig


@dataclass
class APIError:
    status_code: Optional[int]
    error_message: str
    error_type: str
    suggestion: str


def _get_error_info(status_code: Optional[int], message: str) -> dict:
    """根据HTTP状态码映射错误类型和建议"""
    error_mapping = {
        400: {
            "error_type": "invalid_request",
            "suggestion": "请求参数无效，请检查图片格式或请求内容"
        },
        401: {
            "error_type": "auth_error",
            "suggestion": "请检查config.yaml中的api_key是否正确"
        },
        403: {
            "error_type": "auth_error",
            "suggestion": "权限不足，请检查api_key权限或model_name配置"
        },
        404: {
            "error_type": "not_found",
            "suggestion": "请检查config.yaml中的base_url和model_name配置，确认API端点正确"
        },
        429: {
            "error_type": "rate_limit",
            "suggestion": "请求频率超限，请稍后重试"
        },
        500: {
            "error_type": "server_error",
            "suggestion": "API服务器错误，请稍后重试"
        },
        502: {
            "error_type": "server_error",
            "suggestion": "API网关错误，请稍后重试"
        },
        503: {
            "error_type": "server_error",
            "suggestion": "API服务不可用，请稍后重试"
        }
    }
    
    if status_code and status_code in error_mapping:
        info = error_mapping[status_code]
    else:
        info = {
            "error_type": "unknown",
            "suggestion": "未知错误，请查看错误消息详情"
        }
    
    info["status_code"] = status_code
    info["error_message"] = message
    return info


class VisionClient:
    def __init__(self, config: ModelConfig):
        self._config = config
        self._client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url,
            timeout=config.timeout,
        )

    def call_model(self, messages: list[dict]) -> str:
        response = self._client.chat.completions.create(
            model=self._config.model_name,
            messages=messages,
            max_tokens=self._config.max_tokens,
        )
        if not response.choices:
            raise ValueError("Model returned empty response")
        content = response.choices[0].message.content
        if content is None:
            raise ValueError("Model returned null content")
        return content
