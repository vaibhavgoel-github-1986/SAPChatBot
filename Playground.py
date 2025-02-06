from langchain_community.callbacks import get_openai_callback
from Workflows.UTMWorkflow import create_graph


graph = create_graph()

total_token = 0

def get_total_token_usage():
    # Fetches token usage statistics from the graph state.
    try:
        snapshot = graph.get_state({"configurable": {"thread_id": "1"}})
        if snapshot:
            response_metadata = snapshot.values.get("messages", [])[
                -1
            ].response_metadata
            if response_metadata:
                token_usage = response_metadata.get("token_usage", {})
                if token_usage:
                    total_token = int(total_token) + int(token_usage.get("total_tokens", 0))
                    print(f"Token Usage: {token_usage["total_tokens"]}")
                    # return token_usage["total_tokens"]
            else:
                return 0
    except Exception as e:
        return 0


with get_openai_callback() as cb:
    for event in graph.stream(
        {"messages": [{"role": "user", "content": "zcl_jira_issues"}]},
        config={"configurable": {"thread_id": "1"}},
        stream_mode="values",
    ):
        if "messages" in event and event["messages"]:
            message = event["messages"][-1]
            print(message.content)
            get_total_token_usage()

    for event in graph.stream(
        {"messages": [{"role": "user", "content": "zif_jira_issues~create_issue"}]},
        config={"configurable": {"thread_id": "1"}},
        stream_mode="values",
    ):
        if "messages" in event and event["messages"]:
            message = event["messages"][-1]
            print(message.content)
            get_total_token_usage()
            
print()
print("---")
print(f"Total My Tokens: {total_token}")

print()
print("---")
print(f"Total Tokens: {cb.total_tokens}")
print(f"Prompt Tokens: {cb.prompt_tokens}")
print(f"Completion Tokens: {cb.completion_tokens}")
print(f"Total Cost (USD): ${cb.total_cost}")

