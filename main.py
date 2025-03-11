import argparse
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from agent.agent import Agent

from tools.math_tools import add, multiply, divide, subtract
from tools.search import search_duck_duck_go

load_dotenv()


def setup_agent():
    llm = ChatOpenAI(model="gpt-4", streaming=True)
    return Agent(
        sys_prompt="You are a helpful assistant that can use tools to answer questions.",
        llm=llm,
        tools=[add, multiply, divide, subtract, search_duck_duck_go],
    )


def main():
    parser = argparse.ArgumentParser(description="AI Agent CLI Tool")
    parser.add_argument(
        "--graph",
        action="store_true",
        help="Save the agent graph as PNG",
        default=False,
    )
    parser.add_argument(
        "--markup", action="store_true", help="Print the graph markup", default=False
    )
    parser.add_argument("--query", type=str, help="Query to send to the agent")
    parser.add_argument(
        "--stream",
        action="store_true",
        help="Stream the agent's thoughts and actions",
        default=False,
    )

    args = parser.parse_args()

    agent = setup_agent()

    if args.graph:
        print("Saving graph to 'graph.png'...")
        agent.print_graph()

    if args.markup:
        print("Graph markup:")
        agent.print_graph_markup()

    if args.query:
        messages = agent.invoke(args.query)
        if not args.stream:
            for message in messages:
                message.pretty_print()
        else:
            agent.stream_and_print(args.query)


if __name__ == "__main__":
    main()
