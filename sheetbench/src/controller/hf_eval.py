#!/usr/bin/env python3
"""
Usage examples
──────────────
# Evaluate the FULL SheetBench dataset with Claude (Single Process concurrency)
python hf_eval.py hud-evals/SheetBench-50 --full --agent claude --max-concurrent 25

# Custom max steps per task (useful for complex tasks)
python hf_eval.py hud-evals/SheetBench-50 --full --max-steps 100

python hf_eval.py hud-evals/SheetBench-50 --agent claude --max-steps 5

python hf_eval.py hud-evals/SheetBench-50 --agent claude --max-steps 5 --verbose
"""

from __future__ import annotations

import argparse
import asyncio
import logging
from typing import Any, Literal

import buckeyelabs
from datasets import load_dataset
from buckeyelabs.agents import ClaudeAgent, OperatorAgent
from buckeyelabs.agents.misc.response_agent import ResponseAgent
from buckeyelabs.clients import MCPClient
from buckeyelabs.datasets import Task, run_dataset, run_dataset_parallel, run_dataset_parallel_manual

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Single-task runner
# ---------------------------------------------------------------------------


async def run_single_task(
    dataset_name: str,
    *,
    agent_type: Literal["claude", "openai"] = "claude",
    model: str | None = None,
    allowed_tools: list[str] | None = None,
    max_steps: int = 10,
) -> None:
    """Load *one* task from *dataset_name* and execute it."""

    print("📊 Loading dataset…")
    dataset = load_dataset(dataset_name, split="train")

    # Use the same MCP configuration as full dataset
    mcp_config = {
        "sheetbench": {
            "url": "http://localhost:8765/mcp",
            "headers": {},
        }
    }

    # Get a sample task from the dataset to get structure
    sample_task_dict = dataset[0]  # Get first task as template

    # Override with local MCP config
    sample_task_dict["mcp_config"] = mcp_config

    task = Task(**sample_task_dict)

    # Create MCP client with local config
    client = MCPClient(mcp_config=mcp_config)

    agent = ClaudeAgent(
            mcp_client=client,
            model="claude-3-7-sonnet-20250219",
            allowed_tools=["anthropic_computer"],
            initial_screenshot=True,
        )

    with buckeyelabs.trace(f"Task {task.id}"):
        try:
            result = await agent.run(task, max_steps=max_steps)
            print("✅ Reward:", result.reward)
        finally:
            await client.shutdown()
    print(f"\n✨ Browser environment example complete!")


# ---------------------------------------------------------------------------
# Full-dataset runner
# ---------------------------------------------------------------------------


async def run_full_dataset(
    dataset_name: str,
    *,
    agent_type: Literal["claude", "openai"] = "claude",
    model: str | None = None,
    allowed_tools: list[str] | None = None,
    max_concurrent: int = 30,
    max_steps: int = 10,
    parallel: bool = False,
    max_workers: int | None = None,
    max_concurrent_per_worker: int = 25,
) -> list[Any]:
    """Run evaluation across the entire dataset.

    Uses either asyncio-based run_dataset or process-based run_dataset_parallel
    depending on the parallel flag.
    """

    # Build agent class + config for run_dataset – we pass the *class* and a minimal
    # config dict, run_dataset will create a fresh agent per task.
    if agent_type == "openai":
        agent_class = OperatorAgent
        agent_config: dict[str, Any] = {
            "allowed_tools": allowed_tools or ["openai_computer"],
        }
    else:
        agent_class = ClaudeAgent
        agent_config = {
            "model": model or "claude-sonnet-4-20250514",
            "allowed_tools": allowed_tools or ["anthropic_computer"],
        }

    # Override to use local MCP server configuration (same as single task)
    agent_config["mcp_config"] = {
        "sheetbench": {
            "url": "http://localhost:8765/mcp",
            "headers": {},
        }
    }

    eval_name = f"Evaluation {dataset_name.split('/')[-1]}"

    if parallel:
        print(f"🚀 Running PARALLEL evaluation (workers: {max_workers or 'auto'})…")
        if max_workers is None:
            # Use auto-optimization (now the default run_dataset_parallel)
            return await run_dataset_parallel(
                name=eval_name,
                dataset=dataset_name,
                agent_class=agent_class,
                agent_config=agent_config,
                metadata={"dataset": dataset_name, "parallel": True},
                max_steps=max_steps,
                auto_respond=True,
            )
        else:
            # Use manual configuration
            return await run_dataset_parallel_manual(
                name=eval_name,
                dataset=dataset_name,
                agent_class=agent_class,
                agent_config=agent_config,
                max_workers=max_workers,
                max_concurrent_per_worker=max_concurrent_per_worker,
                metadata={"dataset": dataset_name, "parallel": True},
                max_steps=max_steps,
                auto_respond=True,
            )
    else:
        print(f"🚀 Running evaluation (max_concurrent: {max_concurrent})…")
        return await run_dataset(
            name=eval_name,
            dataset=dataset_name,
            agent_class=agent_class,
            agent_config=agent_config,
            max_concurrent=max_concurrent,
            metadata={"dataset": dataset_name},
            max_steps=max_steps,
            auto_respond=True,
        )


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:  # type: ignore[valid-type]
    parser = argparse.ArgumentParser(
        description="Evaluate HUD datasets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s hud-evals/SheetBench-50                    # Single task test
  %(prog)s hud-evals/SheetBench-50 --full             # Full dataset (<100 tasks)
  %(prog)s hud-evals/LargeDataset --full --parallel   # Large dataset (100+ tasks)
        """,
    )

    parser.add_argument("dataset", help="HuggingFace dataset ID")
    parser.add_argument("--full", action="store_true", help="Run entire dataset")

    # Agent
    parser.add_argument("--agent", choices=["claude", "openai"], default="claude")
    parser.add_argument("--model", default=None, help="Model override")
    parser.add_argument(
        "--allowed-tools", dest="allowed_tools", help="Tool allowlist (comma-separated)"
    )

    # Concurrency
    parser.add_argument(
        "--max-concurrent",
        dest="max_concurrent",
        type=int,
        default=50,
        help="Max concurrent tasks (default: 50)",
    )

    # Task settings
    parser.add_argument(
        "--max-steps",
        dest="max_steps",
        type=int,
        default=10,
        help="Max steps per task (default: 10)",
    )

    # Parallel mode (100+ tasks)
    parser.add_argument(
        "--parallel", action="store_true", help="Use parallel execution for large datasets"
    )
    parser.add_argument("--max-workers", dest="max_workers", type=int, help="Worker processes")
    parser.add_argument(
        "--max-concurrent-per-worker",
        dest="max_concurrent_per_worker",
        type=int,
        default=25,
        help="Max concurrent tasks per worker",
    )

    # Logging
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed agent step logs"
    )

    return parser.parse_args()


async def main() -> None:
    args = parse_args()

    if args.verbose:
        # Detailed logs - show everything including agent steps
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(name)s - %(message)s", datefmt="%H:%M:%S"
        )
        # Ensure Buckeye agent logs are visible
        logging.getLogger("buckeyelabs.agents").setLevel(logging.INFO)
        logging.getLogger("buckeyelabs.agents.base").setLevel(logging.INFO)

    allowed_tools = (
        [t.strip() for t in args.allowed_tools.split(",") if t.strip()]
        if args.allowed_tools
        else None
    )

    if args.full:
        import time

        start_time = time.time()

        results = await run_full_dataset(
            args.dataset,
            agent_type=args.agent,
            model=args.model,
            allowed_tools=allowed_tools,
            max_concurrent=args.max_concurrent,
            max_steps=args.max_steps,
            parallel=args.parallel,
            max_workers=args.max_workers,
            max_concurrent_per_worker=args.max_concurrent_per_worker,
        )

        elapsed = time.time() - start_time

        # Print statistics
        print("\n" + "=" * 50)
        print("📊 Evaluation Complete!")
        print("=" * 50)
        print(f"Total tasks: {len(results)}")
        print(f"Time elapsed: {elapsed:.2f} seconds")
        print(f"Throughput: {len(results) / elapsed:.2f} tasks/second")

        if args.parallel:
            print(f"Execution mode: PARALLEL (workers: {args.max_workers or 'auto'})")
        else:
            print(f"Execution mode: ASYNCIO (max_concurrent: {args.max_concurrent})")

        # Count successes
        successful = sum(1 for r in results if getattr(r, "reward", 0) > 0)
        print(
            f"Successful tasks: {successful}/{len(results)} ({100 * successful / len(results):.1f}%)"
        )

    else:
        print(f"Execution mode: Single Task (max_steps: {args.max_steps})")
        await run_single_task(
            args.dataset,
            agent_type=args.agent,
            model=args.model,
            allowed_tools=allowed_tools,
            max_steps=args.max_steps,
        )


if __name__ == "__main__":
    asyncio.run(main())