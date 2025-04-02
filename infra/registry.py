"""Module for setting up Docker repositories in Artifact Registry"""

import pulumi
from pulumi_gcp import artifactregistry


def create_docker_repository(stack: str, dependencies=None):
    """
    Creates a Docker repository in Artifact Registry.

    Args:
        stack (str): The stack/environment name (e.g., dev, staging, prod)
        dependencies (list, optional): Resources this repository depends on

    Returns:
        artifactregistry.Repository: The created Docker repository
    """
    docker_repository = artifactregistry.Repository(
        f"maja-{stack}",
        location="us-central1",  # Choose appropriate region
        repository_id=f"maja-{stack}",
        description=f"Docker repository for Maja - {stack} environment",
        format="DOCKER",
        opts=pulumi.ResourceOptions(depends_on=dependencies) if dependencies else None,
    )

    return docker_repository


def get_repository_exports(repository):
    """
    Generate export values for the repository.

    Args:
        repository (artifactregistry.Repository): The repository to export values for

    Returns:
        dict: Dictionary with export values
    """
    exports = {
        "repository_id": repository.repository_id,
        "repository_url": pulumi.Output.concat(
            repository.location,
            "-docker.pkg.dev/",
            repository.project,
            "/",
            repository.repository_id,
        ),
        "docker_push_example": pulumi.Output.concat(
            "docker tag myimage:latest ",
            repository.location,
            "-docker.pkg.dev/",
            repository.project,
            "/",
            repository.repository_id,
            "/myimage:latest",
        ),
        "gcloud_auth_command": pulumi.Output.concat(
            "gcloud auth configure-docker ", repository.location, "-docker.pkg.dev"
        ),
    }

    return exports
