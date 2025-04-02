from pulumi_gcp import storage


def create_chroma_datastore_bucket(env: str) -> storage.Bucket:
    """
    Creates a GCP storage bucket for Chroma datastore.

    Args:
        env (str): Environment name (dev/prod)

    Returns:
        storage.Bucket: The created GCP storage bucket
    """
    bucket = storage.Bucket(
        f"maja-chroma-datastore-{env}",
        name=f"maja-chroma-datastore-{env}",
        location="us-central1",
        uniform_bucket_level_access=True,
        versioning={
            "enabled": False  # Disabled versioning as requested
        },
        labels={
            "environment": env,
            "purpose": "chroma-datastore",
            "pulumi-managed": "true",  # Added pulumi-managed label
        },
    )

    # Removed the IAM member that granted public access
    # Users will need explicit permissions granted through IAM policies

    return bucket
