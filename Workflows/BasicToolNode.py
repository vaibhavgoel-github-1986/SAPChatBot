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

            for tool_call in getattr(message, "tool_calls", []):
                tool_name = tool_call.get("name", "")
                tool_args = tool_call.get("args", {})

                if tool_name in self.tools_by_name:
                    tool_result = self.tools_by_name[tool_name].invoke(tool_args)

                    outputs.append(
                        ToolMessage(
                            content=json.dumps(tool_result, indent=2),
                            name=tool_name,
                            tool_call_id=tool_call["id"],
                        )
                    )

                else:
                    return {
                        "messages": [
                            ToolMessage(
                                content=f"Tool '{tool_name}' not found.",
                                name=tool_name,
                                tool_call_id=tool_call["id"],
                            )
                        ]
                    }

            return {"messages": outputs}

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
