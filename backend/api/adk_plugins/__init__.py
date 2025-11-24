
from typing import List
from google.adk.plugins import BasePlugin

from .message_validation import MessageValidationPlugin

def get_default_plugins() -> List[BasePlugin]:
    return [
        MessageValidationPlugin(),
    ]