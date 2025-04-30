import runpod
from sentence_transformers import SentenceTransformer
import torch
import os

# Load the model during worker initialization
# Use GPU if available (RunPod serverless environment typically has CUDA)
device = "cuda" if torch.cuda.is_available() else "cpu"
model_name = os.getenv(
    "HF_EMBEDDING_MODEL", "nlpaueb/legal-bert-base-uncased"
)  # Allow override via env var
print(f"Loading model {model_name} onto device {device}...")
model = SentenceTransformer(model_name, device=device)
print("Model loaded successfully.")


def handler(job):
    """
    RunPod Serverless handler function to generate embeddings.
    Expects input like: {"input": {"texts": ["text1", "text2", ...]}}
    Returns: {"embeddings": [[emb1], [emb2], ...]} or {"error": "message"}
    """
    job_input = job.get("input", None)

    if not job_input:
        return {"error": "No input provided"}

    texts = job_input.get("texts", None)
    if not texts or not isinstance(texts, list):
        return {
            "error": "Missing or invalid 'texts' field in input. Expected a list of strings."
        }

    print(f"Received {len(texts)} texts for embedding.")

    try:
        # Generate embeddings
        embeddings = model.encode(texts).tolist()
        print(f"Generated {len(embeddings)} embeddings.")
        return {"embeddings": embeddings}
    except Exception as e:
        print(f"Error during embedding generation: {str(e)}")
        # Consider more specific error handling/logging
        return {"error": f"Failed to generate embeddings: {str(e)}"}


# Start the serverless worker
runpod.serverless.start({"handler": handler})
