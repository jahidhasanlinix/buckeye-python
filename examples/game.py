#!/usr/bin/env python3
"""
Text 2048 Example - Four ways to run the environment:

1. Direct Python (no Docker) - Runs in your current environment
2. Docker container - Simpler config but requires building the image first
3. Docker container - Runs in a local container (with buckeye helper)
4. Remote container - Runs in a remote container (with buckeye helper)
"""

import asyncio
import sys
from pathlib import Path
import buckeyelabs
from buckeyelabs.datasets import Task
from buckeyelabs.agents import ClaudeAgent
from buckeyelabs.clients import MCPClient


async def main():
    # THERE ARE A FEW WAYS TO RUN THE LOCAL ENVIRONMENT

    # OPTION 1: Direct Python execution (Not recommended for production use)
    # This is the most basic way to run any MCP server
    # However, it works on your host machine, not in a container
    text_2048 = Path(__file__).parent.parent / "environments/text_2048"
    mcp_config = {
        "local": {
            "command": sys.executable,
            "args": ["-m", "controller.server"],
            "env": {"PYTHONPATH": str(text_2048 / "src")},
            "cwd": str(text_2048),
        }
    }

    # OPTION 2: Needs: docker build -t buckeyepython/buckeye-text-2048:latest environments/text_2048
    # OR: docker pull buckeyepython/buckeye-text-2048:latest
    # This builds the image and allows you to run it directly
    # mcp_config = {
    #     "local": {
    #         "command": "docker",
    #         "args": ["run", "--rm", "-i", "buckeyepython/buckeye-text-2048:latest"]
    #     }
    # }

    # OPTION 3: This is an alias helper for running the above
    # mcp_config = {
    #     "local": {
    #         "command": "buckeye",
    #         "args": ["run", "buckeyepython/buckeye-text-2048:latest", "--local"]
    #     }
    # }

    # OPTION 4: And allows you to easily switch to remote!
    # However, if you are using your own image, make sure to push it to docker hub:
    # (docker push your-username/image-name:latest)
    mcp_config = {
        "remote": {
            "command": "buckeye",
            "args": [
                "run",
                "buckeyepython/buckeye-text-2048:latest",
                "--verbose",
            ],  # this can spin up 100s of remote containers!
        }
    }

    task_dict = {
        "prompt": "Play 2048 and get the highest score possible.",
        "mcp_config": mcp_config,
        # Setup and evaluated tools are defined by the environment (see environments/text_2048/)
        "setup_tool": {
            "name": "setup",
            "arguments": {"name": "board", "arguments": {"board_size": 4}},
        },
        "evaluate_tool": {"name": "evaluate", "arguments": {"name": "max_number"}},
    }
    task = Task(**task_dict)

    # All of our environments use MCP as a generalizeable interface to interact with the environment
    client = MCPClient(mcp_config=task.mcp_config)

    # Define the agent that can call tools via the client
    agent = ClaudeAgent(mcp_client=client, allowed_tools=["move"])

    with buckeyelabs.trace("Hello 2048 Game"):
        try:
            # Running a full Task automatically handles setup and evaluation!
            result = await agent.run(task, max_steps=-1)
            print(f"Game completed! Reward: {result.reward}")
        finally:
            await client.shutdown()


if __name__ == "__main__":
    asyncio.run(main())