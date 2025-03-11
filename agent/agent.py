from langgraph.graph import START, StateGraph
from langgraph.prebuilt import (
    tools_condition,
)
from langgraph.prebuilt import ToolNode
from langgraph.graph import MessagesState
from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
    AIMessageChunk,
    ToolMessage,
)
from typing import Callable, List, Dict, Any, Union, Tuple
import json

from langchain_core.messages import AIMessageChunk, ToolMessage


class Agent:
    def __init__(self, sys_prompt: str, llm, tools: list[Callable]):
        self.sys_prompt = SystemMessage(content=sys_prompt)
        self.tools = tools
        self.llm = llm.bind_tools(self.tools)
        self.graph = self.build()

    def build(self):
        builder = StateGraph(MessagesState)
        builder.add_node("reasoner", self.reasoner)
        builder.add_node("tools", ToolNode(self.tools))
        builder.add_edge(START, "reasoner")
        builder.add_conditional_edges(
            "reasoner",
            tools_condition,
        )
        builder.add_edge("tools", "reasoner")
        return builder.compile()

    def print_graph(self):
        graph_data = self.graph.get_graph(xray=True)
        graph_data.draw_png("./graph.png")

    def print_graph_markup(self):
        graph_data = self.graph.get_graph(xray=True)
        print(graph_data.source)

    def reasoner(self, state: MessagesState):
        # Add a prompt suffix that asks for justification when using tools
        tool_prompt = """When you decide to use a tool, please provide a brief justification 
        explaining why you're choosing that specific tool and what you expect to accomplish with it."""

        # Combine the system prompt with the tool justification instruction
        combined_prompt = SystemMessage(
            content=f"{self.sys_prompt.content}\n\n{tool_prompt}"
        )
        return {"messages": [self.llm.invoke([combined_prompt] + state["messages"])]}

    def invoke(self, message: str):
        messages = [HumanMessage(content=message)]
        messages = self.graph.invoke({"messages": messages})
        return messages["messages"]

    def stream(self, message: str, stream_mode: Union[str, List[str]] = "messages"):
        messages = [HumanMessage(content=message)]
        return self.graph.stream({"messages": messages}, stream_mode=stream_mode)

    def stream_and_print(self, message: str, stream_mode: str = "updates"):
        print("\n" + "=" * 80)
        print("HUMAN MESSAGE".center(80))
        print("=" * 80)
        print(message)

        for step in self.stream(message, stream_mode=stream_mode):
            # print(step)
            if "reasoner" in step and step["reasoner"] is not None:
                print("\n" + "=" * 80)
                print("REASONER".center(80))
                print("=" * 80)
                print(step["reasoner"]["messages"][0].content)
                print("-- tool calls --")
                # Extract and print tool calls if they exist
                if (
                    hasattr(step["reasoner"]["messages"][0], "tool_calls")
                    and step["reasoner"]["messages"][0].tool_calls
                ):
                    tool_calls = step["reasoner"]["messages"][0].tool_calls
                    for i, tool_call in enumerate(tool_calls):
                        print(f"Tool Name: {tool_call['name']}")
                        print(f"Arguments: {json.dumps(tool_call['args'], indent=2)}")
                        if i < len(tool_calls) - 1:
                            print("-" * 40)

            # Handle tool steps
            if "tools" in step and step["tools"] is not None:
                print("\n" + "=" * 80)
                print("TOOL RESULTS".center(80))
                print("=" * 80)
                for i, msg in enumerate(step["tools"]["messages"]):
                    if isinstance(msg, ToolMessage):
                        print(f"Tool Name: {msg.name}")
                        print(f"Result: {msg.content}")
                        if i < len(step["tools"]["messages"]) - 1:
                            print("-" * 40)
