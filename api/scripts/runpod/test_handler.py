#!/usr/bin/env python3
"""
Test script for Mixtral handler.

This script allows testing the Mixtral handler locally before deploying to RunPod.
"""

import json
import argparse
from mixtral_handler import mixtral_handler


def main():
    """Run a test of the Mixtral handler with sample inputs."""
    parser = argparse.ArgumentParser(
        description="Test the Mixtral RunPod handler locally"
    )
    parser.add_argument(
        "--prompt", type=str, help="Single prompt to test (alternative to --input-file)"
    )
    parser.add_argument(
        "--system-message",
        type=str,
        default="You are a helpful legal assistant.",
        help="Optional system message for chat format",
    )
    parser.add_argument(
        "--input-file",
        type=str,
        help="JSON file with test input data (alternative to --prompt)",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Temperature for generation (default: 0.7)",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=500,
        help="Maximum tokens to generate (default: 500)",
    )

    args = parser.parse_args()

    # Prepare the input data
    if args.input_file:
        # Load from file
        with open(args.input_file, "r") as f:
            event = json.load(f)
    elif args.prompt:
        # Create from prompt
        event = {
            "input": {
                "messages": [
                    {"role": "system", "content": args.system_message},
                    {"role": "user", "content": args.prompt},
                ],
                "temperature": args.temperature,
                "max_tokens": args.max_tokens,
            }
        }
    else:
        # Use default example
        event = {
            "input": {
                "messages": [
                    {"role": "system", "content": "You are a helpful legal assistant."},
                    {
                        "role": "user",
                        "content": "What are the key elements of a contract?",
                    },
                ],
                "temperature": 0.7,
                "max_tokens": 500,
            }
        }

    print("\n===== INPUT =====")
    print(json.dumps(event["input"], indent=2))

    print("\n===== RUNNING INFERENCE =====")
    result = mixtral_handler(event)

    print("\n===== OUTPUT =====")
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        # Get the assistant's message
        assistant_message = result["choices"][0]["message"]["content"]
        print(assistant_message)

        print("\n===== METADATA =====")
        # Print usage information
        usage = result.get("usage", {})
        print(f"Prompt tokens: {usage.get('prompt_tokens', 'N/A')}")
        print(f"Completion tokens: {usage.get('completion_tokens', 'N/A')}")
        print(f"Total tokens: {usage.get('total_tokens', 'N/A')}")

        # Print time information
        system_info = result.get("system_info", {})
        print(
            f"Generation time: {system_info.get('generation_time', 'N/A'):.2f} seconds"
        )


if __name__ == "__main__":
    main()
