# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Optional
from google.adk.agents.callback_context import CallbackContext
from google.genai.types import Content, Part
from google.adk.models import LlmResponse, LlmRequest
from google.genai import types 


def suppress_output_callback(callback_context: CallbackContext) -> Content:
    """Suppresses the output of the agent by returning an empty Content object."""
    return Content(parts=[Part(text=f"[{callback_context.agent_name}]: 完成任务")], role="assistant")

# --- 检查LLM调用信息 ---
def print_before_model_information(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """Inspects/modifies the LLM request or skips the call."""
    agent_name = callback_context.agent_name
    print(f"[Callback] Before model call for agent: {agent_name}")

    # print(f"[Callback] LLM Request: {llm_request.config}")

    # Inspect the last user message in the request contents
    # last_user_message = ""
    # if llm_request.contents and llm_request.contents[-1].role == 'user':
    #      if llm_request.contents[-1].parts:
    #         last_user_message = llm_request.contents[-1].parts[0].text
    # print(f"[Callback] Inspecting last user message: '{last_user_message}'")

    print(f"[Callback] LLM Contents:")
    for content in llm_request.contents:
      print(f"[Callback] Content Role: {content.role}")
      for part in content.parts:
        print(f"[Callback] Content Part: {part.text[:100] if part.text else part.text}")
        if getattr(part, "function_call", None):
          print(
              "[Callback] Function Call -> "
              f"    name: {part.function_call.name}, id: {part.function_call.id}, "
              f"    args: {part.function_call.args}"
          )
        if getattr(part, "function_response", None):
          fr = part.function_response
          print(
              "[Callback] Function Response -> "
              f"    id: {fr.id}, name: {fr.name}"
          )

    # --- Modification Example ---
    # Add a prefix to the system instruction
    # original_instruction = llm_request.config.system_instruction or types.Content(role="system", parts=[])
    # prefix = "[Modified by Callback] "
    # # Ensure system_instruction is Content and parts list exists
    # if not isinstance(original_instruction, types.Content):
    #      # Handle case where it might be a string (though config expects Content)
    #      original_instruction = types.Content(role="system", parts=[types.Part(text=str(original_instruction))])
    # if not original_instruction.parts:
    #     original_instruction.parts.append(types.Part(text="")) # Add an empty part if none exist

    # # Modify the text of the first part
    # modified_text = prefix + (original_instruction.parts[0].text or "")
    # original_instruction.parts[0].text = modified_text
    # llm_request.config.system_instruction = original_instruction
    # print(f"[Callback] Modified system instruction to: '{modified_text}'")

    # --- Skip Example ---
    # Check if the last user message contains "BLOCK"
    # if "BLOCK" in last_user_message.upper():
    #     print("[Callback] 'BLOCK' keyword found. Skipping LLM call.")
    #     # Return an LlmResponse to skip the actual LLM call
    #     return LlmResponse(
    #         content=types.Content(
    #             role="model",
    #             parts=[types.Part(text="LLM call was blocked by before_model_callback.")],
    #         )
    #     )
    # else:
    #     print("[Callback] Proceeding with LLM call.")
    #     # Return None to allow the (modified) request to go to the LLM
    #     return None
    return None
