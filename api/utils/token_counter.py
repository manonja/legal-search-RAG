"""Token counting and cost estimation utilities for the OpenAI API."""

import logging
from typing import Dict, List, Union

import tiktoken

logger = logging.getLogger(__name__)

# Cost per 1,000 tokens in USD
MODEL_COST_PER_1K_TOKENS = {
    # GPT-4 Turbo
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-4-0125-preview": {"input": 0.01, "output": 0.03},
    # GPT-4
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-4-0613": {"input": 0.03, "output": 0.06},
    # GPT-3.5 Turbo
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    "gpt-3.5-turbo-0125": {"input": 0.0005, "output": 0.0015},
    "gpt-3.5-turbo-1106": {"input": 0.001, "output": 0.002},
    "gpt-3.5-turbo-0613": {"input": 0.001, "output": 0.002},
}


def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    """Count the number of tokens in a text string.

    Args:
        text: The text to count tokens for
        model: The model to use for tokenization

    Returns:
        Number of tokens in the text
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception as e:
        logger.warning(f"Error counting tokens: {e}")
        # Fallback to approximate count (1 token ≈ 4 chars)
        return len(text) // 4


def estimate_tokens_and_cost(
    messages: List[Dict[str, str]], model: str = "gpt-3.5-turbo", max_tokens: int = 500
) -> Dict[str, Union[int, float]]:
    """Estimate token usage and cost for a chat completion.

    Args:
        messages: List of message dictionaries with 'role' and 'content' keys
        model: The model to use for the completion
        max_tokens: Maximum expected output tokens

    Returns:
        Dictionary with token counts and cost estimate
    """
    # Sum up tokens from all messages
    input_tokens = 0
    for message in messages:
        # Count tokens in the message content
        content_tokens = count_tokens(message.get("content", ""), model)

        # Add tokens for message metadata
        # Each message has a small overhead for role formatting
        role_overhead = 4  # approximate overhead tokens per message
        input_tokens += content_tokens + role_overhead

    # Add a few tokens for the system message format
    input_tokens += 3

    # Get cost rates for the model
    model_costs = MODEL_COST_PER_1K_TOKENS.get(
        model,
        {"input": 0.002, "output": 0.002},  # Default if model not found
    )

    # Calculate costs
    input_cost = (input_tokens / 1000) * model_costs["input"]
    output_cost = (max_tokens / 1000) * model_costs["output"]
    total_cost = input_cost + output_cost
    total_tokens = input_tokens + max_tokens

    return {
        "input_tokens": input_tokens,
        "output_tokens": max_tokens,
        "total_tokens": total_tokens,
        "input_cost": input_cost,
        "output_cost": output_cost,
        "cost": total_cost,
    }


def format_cost(cost: float) -> str:
    """Format cost as a dollar amount.

    Args:
        cost: The cost value to format

    Returns:
        Formatted cost string with dollar sign
    """
    if cost < 0.01:
        # Use scientific notation for very small amounts
        return f"${cost:.6f}"
    elif cost < 0.1:
        # Show more decimal places for small amounts
        return f"${cost:.4f}"
    else:
        # Standard 2 decimal places for larger amounts
        return f"${cost:.2f}"
