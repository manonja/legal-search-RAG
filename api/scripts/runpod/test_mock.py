#!/usr/bin/env python3
"""
Test script for the mock Mixtral handler.
"""

import json
import argparse
from mock_handler import mock_handler


def main():
    """Run a test of the mock Mixtral handler with sample inputs."""
    parser = argparse.ArgumentParser(description="Test the mock Mixtral handler")
    parser.add_argument(
        "--prompt",
        type=str,
        default="What are the key elements of a contract?",
        help="Prompt to test",
    )
    parser.add_argument(
        "--system-message",
        type=str,
        default="You are a helpful legal assistant. Keep answers brief.",
        help="System message for chat format",
    )

    args = parser.parse_args()

    # Prepare the input data
    event = {
        "input": {
            "messages": [
                {"role": "system", "content": args.system_message},
                {"role": "user", "content": args.prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 500,
        }
    }

    print("\n===== INPUT =====")
    print(json.dumps(event["input"], indent=2))

    print("\n===== RUNNING MOCK INFERENCE =====")
    result = mock_handler(event)

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

        print("\n===== NOTES =====")
        print("This is running a MOCK handler that simulates Mixtral-8x7B responses.")
        print("In production, this would use the actual Mixtral-8x7B model.")


if __name__ == "__main__":
    main()
