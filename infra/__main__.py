"""A Google Cloud Python Pulumi program for setting up a Docker registry on GCP"""

import pulumi
from pulumi_gcp import artifactregistry, projects

# Import our API enablement module
from apis import enable_required_apis

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

# Optional: Add IAM permissions for the repository
# Uncomment and modify this section as needed with the appropriate service accounts

# Example: Grant reader access to a service account (e.g., for Kubernetes)
# reader_member = f"serviceAccount:your-service-account@your-project.iam.gserviceaccount.com"
# reader_iam = artifactregistry.RepositoryIamMember(
#     "repository-reader",
#     project=docker_repository.project,
#     location=docker_repository.location,
#     repository=docker_repository.name,
#     role="roles/artifactregistry.reader",
#     member=reader_member,
# )

# Example: Grant writer access to a CI/CD service account
# writer_member = f"serviceAccount:your-cicd-account@your-project.iam.gserviceaccount.com"
# writer_iam = artifactregistry.RepositoryIamMember(
#     "repository-writer",
#     project=docker_repository.project,
#     location=docker_repository.location,
#     repository=docker_repository.name,
#     role="roles/artifactregistry.writer",
#     member=writer_member,
# )

# Export the repository's endpoint
pulumi.export('repository_id', docker_repository.repository_id)
pulumi.export('repository_url', pulumi.Output.concat(
    docker_repository.location, "-docker.pkg.dev/", 
    docker_repository.project, "/", 
    docker_repository.repository_id
))

# Export command examples for documentation
pulumi.export('docker_push_example', pulumi.Output.concat(
    "docker tag myimage:latest ", 
    docker_repository.location, "-docker.pkg.dev/", 
    docker_repository.project, "/", 
    docker_repository.repository_id, "/myimage:latest"
))

pulumi.export('gcloud_auth_command', pulumi.Output.concat(
    "gcloud auth configure-docker ", 
    docker_repository.location, "-docker.pkg.dev"
))
