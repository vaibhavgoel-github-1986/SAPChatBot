from langchain_core.messages import ToolMessage, trim_messages

import json


class BasicToolNode:
    """A node that runs the tools requested in the last AIMessage."""

    def __init__(self, tools: list) -> None:
        self.tools_by_name = {tool.name: tool for tool in tools}

    def __call__(self, inputs: dict):
        try:
            if messages := inputs.get("messages", []):
                message = messages[-1]
            else:
                raise ValueError("No message found in input")

            outputs = []

            # Ensure tool_outputs is initialized
            # tool_outputs = inputs.get("tool_outputs", [])

            for tool_call in getattr(message, "tool_calls", []):
                tool_name = tool_call.get("name", "")
                tool_args = tool_call.get("args", {})

                if tool_name in self.tools_by_name:
                    tool_result = self.tools_by_name[tool_name].invoke(tool_args)

                    tool_message = ToolMessage(
                        content=json.dumps(tool_result, indent=2),
                        name=tool_name,
                        tool_call_id=tool_call["id"],
                    )
                    
                    outputs.append(tool_message)
                
                else:
                    raise ValueError(f"Tool '{tool_name}' not found.")

            return {
                "messages": outputs,
                # "tool_outputs": tool_outputs,
            }  # Ensure tool_outputs is returned

        except Exception as e:
            return {
                "messages": [
                    ToolMessage(
                        content=f"Error occurred in tool '{tool_name}': {str(e)}",
                        name=tool_name,
                        tool_call_id=tool_call["id"],
                    )
                ]
            }
