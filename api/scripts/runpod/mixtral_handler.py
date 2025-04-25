"""
RunPod Serverless handler for Mixtral-8x7B.

This module loads the Mixtral-8x7B model and provides a serverless handler
for text generation via RunPod.
"""

import os
import json
import time
import runpod
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# Configure logging
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Get model configuration from environment variables with defaults
MODEL_ID = os.environ.get("MODEL_ID", "mistralai/Mixtral-8x7B-v0.1")
QUANTIZATION = os.environ.get("QUANTIZATION", "8bit")  # Options: "none", "8bit", "4bit"


def load_model():
    """Load Mixtral model with memory optimizations.

    Returns:
        tuple: (model, tokenizer) - The loaded model and tokenizer
    """
    logger.info(f"Loading model: {MODEL_ID}")
    start_time = time.time()

    # Load tokenizer first
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)

    # Configure model loading based on quantization setting
    model_kwargs = {
        "torch_dtype": torch.float16,
        "device_map": "auto",
    }

    # Apply quantization if specified
    if QUANTIZATION == "8bit":
        logger.info("Using 8-bit quantization")
        model_kwargs["load_in_8bit"] = True
    elif QUANTIZATION == "4bit":
        logger.info("Using 4-bit quantization")
        model_kwargs["load_in_4bit"] = True
        model_kwargs["bnb_4bit_compute_dtype"] = torch.float16
        model_kwargs["bnb_4bit_quant_type"] = "nf4"
    else:
        logger.info("Using full precision (float16)")

    # Load the model with the configured settings
    model = AutoModelForCausalLM.from_pretrained(MODEL_ID, **model_kwargs)

    load_time = time.time() - start_time
    logger.info(f"Model loaded successfully in {load_time:.2f} seconds")

    return model, tokenizer


def format_chat_prompt(messages):
    """Format chat messages into a prompt structure compatible with the model.

    Args:
        messages (list): List of message dictionaries with 'role' and 'content'

    Returns:
        list: Formatted messages ready for the tokenizer's chat template
    """
    if not messages or not isinstance(messages, list):
        return None

    # Extract only valid roles and contents
    formatted_messages = []
    for message in messages:
        if not isinstance(message, dict):
            continue

        role = message.get("role", "")
        content = message.get("content", "")

        if role in ["system", "user", "assistant"] and content:
            formatted_messages.append({"role": role, "content": content})

    return formatted_messages


def mixtral_handler(event):
    """Handle inference requests for Mixtral-8x7B model.

    Args:
        event (dict): The RunPod event containing input data

    Returns:
        dict: Response with generated text or error
    """
    try:
        # Ensure model is loaded
        global model, tokenizer
        if "model" not in globals() or "tokenizer" not in globals():
            model, tokenizer = load_model()

        # Extract inputs
        if not isinstance(event, dict) or "input" not in event:
            return {"error": "Invalid input format"}

        input_data = event.get("input", {})

        # Handle different input formats (OpenAI-like API or direct prompt)
        if "messages" in input_data:
            # Format similar to OpenAI chat completions
            messages = input_data.get("messages", [])
            formatted_msgs = format_chat_prompt(messages)
            if not formatted_msgs:
                return {"error": "Invalid messages format"}

        elif "prompt" in input_data:
            # Single prompt format
            prompt = input_data.get("prompt", "")
            if not prompt:
                return {"error": "No prompt provided"}

            # Add as user message
            formatted_msgs = [{"role": "user", "content": prompt}]

        else:
            return {"error": "Input must contain either 'messages' or 'prompt'"}

        # Extract generation parameters with defaults
        params = {
            "temperature": float(input_data.get("temperature", 0.7)),
            "max_tokens": int(input_data.get("max_tokens", 1000)),
            "top_p": float(input_data.get("top_p", 0.95)),
            "frequency_penalty": float(input_data.get("frequency_penalty", 0.0)),
            "presence_penalty": float(input_data.get("presence_penalty", 0.0)),
        }

        # Log generation parameters
        logger.info(f"Generating response with parameters: {params}")

        # Apply chat template and convert to tensor
        model_inputs = tokenizer.apply_chat_template(
            formatted_msgs, return_tensors="pt"
        ).to(model.device)

        # Save the input length to extract only the new content later
        input_text = tokenizer.decode(model_inputs[0])

        # Run generation with parameters
        generation_config = {
            "max_new_tokens": params["max_tokens"],
            "do_sample": params["temperature"] > 0,
            "temperature": max(params["temperature"], 0.01),  # Avoid 0 temperature
            "top_p": params["top_p"],
            "repetition_penalty": 1.0
            + params["frequency_penalty"],  # Convert to repetition penalty
            "pad_token_id": tokenizer.eos_token_id,
        }

        # Measure generation time
        gen_start = time.time()

        # Generate text
        with torch.no_grad():
            outputs = model.generate(model_inputs, **generation_config)

        gen_time = time.time() - gen_start

        # Decode the generated text
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract only the newly generated part (similar to OpenAI)
        # This requires handling the chat template properly
        assistant_reply = ""

        # Different models use different chat templates, so we need to
        # extract the assistant's reply which comes after the input
        if "<assistant>" in generated_text:
            # Extract text between <assistant> and end
            parts = generated_text.split("<assistant>")
            if len(parts) > 1:
                assistant_reply = parts[-1].strip()
        else:
            # Fallback: just return the new text after the input length
            # This may not be perfect as it depends on tokenization
            assistant_reply = generated_text[len(input_text) :].strip()

        # Format response similar to OpenAI's API format
        response = {
            "id": f"mixtral-{int(time.time())}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": MODEL_ID,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": assistant_reply},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": len(model_inputs[0]),
                "completion_tokens": len(tokenizer.encode(assistant_reply)),
                "total_tokens": len(model_inputs[0])
                + len(tokenizer.encode(assistant_reply)),
            },
            "system_info": {"generation_time": gen_time},
        }

        logger.info(f"Response generated in {gen_time:.2f} seconds")
        return response

    except Exception as e:
        logger.error(f"Error in mixtral_handler: {str(e)}", exc_info=True)
        return {"error": str(e)}


# Start the serverless worker
if __name__ == "__main__":
    runpod.serverless.start({"handler": mixtral_handler})
