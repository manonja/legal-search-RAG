"""A Google Cloud Python Pulumi program for setting up infrastructure on GCP"""

import pulumi
from pulumi_gcp import artifactregistry

# Import our API enablement module
from apis import enable_required_apis
from buckets import create_chroma_datastore_bucket

# Get the current stack name to use as the environment name (e.g., dev, staging, prod)
config = pulumi.Config()
stack = pulumi.get_stack()

# Enable required APIs first
enabled_apis = enable_required_apis()

# Create a Docker repository in Artifact Registry
# Note that we add dependencies on the enabled APIs
docker_repository = artifactregistry.Repository(
    f"maja-{stack}",
    location="us-central1",  # Choose appropriate region
    repository_id=f"maja-{stack}",
    description=f"Docker repository for Maja - {stack} environment",
    format="DOCKER",
    opts=pulumi.ResourceOptions(depends_on=enabled_apis),  # This ensures APIs are enabled first
)

# Create the Chroma datastore bucket
chroma_bucket = create_chroma_datastore_bucket(stack)

# Export the repository's endpoint
pulumi.export("repository_id", docker_repository.repository_id)
pulumi.export(
    "repository_url",
    pulumi.Output.concat(
        docker_repository.location,
        "-docker.pkg.dev/",
        docker_repository.project,
        "/",
        docker_repository.repository_id,
    ),
)

# Export the bucket name
pulumi.export("chroma_bucket_name", chroma_bucket.name)

# Export command examples for documentation
pulumi.export(
    "docker_push_example",
    pulumi.Output.concat(
        "docker tag myimage:latest ",
        docker_repository.location,
        "-docker.pkg.dev/",
        docker_repository.project,
        "/",
        docker_repository.repository_id,
        "/myimage:latest",
    ),
)

pulumi.export(
    "gcloud_auth_command",
    pulumi.Output.concat(
        "gcloud auth configure-docker ", docker_repository.location, "-docker.pkg.dev"
    ),
)
