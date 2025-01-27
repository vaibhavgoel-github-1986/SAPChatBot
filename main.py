# main.py
from Utilities.TokenManager import TokenManager
from ChatModels.CiscoAzureOpenAI import CiscoAzureOpenAI

from langchain.chains import LLMChain

from typing import Annotated

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from ChatModels.CiscoAzureOpenAI import CiscoAzureOpenAI
from Utilities.TokenManager import TokenManager
# from DocumentLoaders.Github import GitHubLoader
from Tools.GetDependencies import get_dependencies
import json

# Define the state of the graph
class State(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list, add_messages]


graph_builder = StateGraph(State)

# Get the LLM Chat Model
llm = CiscoAzureOpenAI(
    token_manager=TokenManager(),
).get_llm()


def chatbot(state: State):
    return {"messages": [llm.invoke(state["messages"])]}


# The first argument is the unique node name
# The second argument is the function or object that will be called whenever
# the node is used.
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)
graph = graph_builder.compile()


def stream_graph_updates(user_input: str):
    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
        for value in event.values():
            print("Assistant:", value["messages"][-1].content)


# while True:
#     try:
#         user_input = input("User: ")
#         if user_input.lower() in ["quit", "exit", "q"]:
#             print("Goodbye!")
#             break

#         stream_graph_updates(user_input)
#     except:
#         # fallback if input() is not available
#         user_input = "What do you know about LangGraph?"
#         print("User: " + user_input)
#         stream_graph_updates(user_input)
#         break


def main():
    # Start the Workflow
    # stream_graph_updates("Hi")

    # loader = GitHubLoader(repo="cisco-it-finance/sap-brim-repo", branch="main")
    
    # document = loader.load_files( 
    #     file_filter=lambda file_path: file_path == "zs4intcpq/zcl_cc_rate_plan.clas.abap"
    # )
    
    class_name = input("Enter the ABAP class name: ")

    dependencies = get_dependencies(class_name=class_name)
    print(json.dumps(dependencies, indent=4))

    # print(document.page_content)
    # print(document[0].page_content)
    # print(document[0].metadata)

if __name__ == "__main__":
    main()
