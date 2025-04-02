"""A Google Cloud Python Pulumi program for setting up infrastructure on GCP"""

import pulumi

from api_cloud_run import create_api_service, get_api_url
from apis import enable_required_apis
from buckets import create_chroma_datastore_bucket
from registry import create_docker_repository, get_repository_exports

# Get the current stack name to use as the environment name (e.g., dev, staging, prod)
config = pulumi.Config()
stack = pulumi.get_stack()

# Enable required APIs first
enabled_apis = enable_required_apis()

# Create a Docker repository in Artifact Registry
# Note that we add dependencies on the enabled APIs
docker_repository = create_docker_repository(stack, dependencies=enabled_apis)

# Create the Chroma datastore bucket
chroma_bucket = create_chroma_datastore_bucket(stack)

# Create the Cloud Run service for the API
cloud_run_service = create_api_service(
    stack, docker_repository, chroma_bucket, dependencies=enabled_apis
)

# Get repository exports
repo_exports = get_repository_exports(docker_repository)

# Export the repository values
for key, value in repo_exports.items():
    pulumi.export(key, value)

# Export the bucket name
pulumi.export("chroma_bucket_name", chroma_bucket.name)

# Export the API URL
pulumi.export("api_url", get_api_url(cloud_run_service))

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
