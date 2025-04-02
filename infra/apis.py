"""Module to enable required GCP APIs for the project"""

from pulumi_gcp import projects


def enable_required_apis():
    """
    Enable all required APIs for this project.
    Returns a list of enabled service resources that can be used as dependencies.
    """
    # List of APIs that need to be enabled
    required_apis = [
        "artifactregistry.googleapis.com",  # Artifact Registry API
        "containerregistry.googleapis.com",  # Container Registry API (related dependency)
        "storage.googleapis.com",  # Storage API (required by Artifact Registry)
        "iam.googleapis.com",  # IAM API for permissions
        "run.googleapis.com",  # Cloud Run API
        "secretmanager.googleapis.com",  # Secret Manager API
    ]

    # Enable each API
    enabled_apis = []
    for api in required_apis:
        service_name = f"enable-{api.replace('.googleapis.com', '')}"
        enabled_service = projects.Service(
            service_name,
            service=api,
            disable_on_destroy=False,  # Keep API enabled when Pulumi stack is destroyed
        )
        enabled_apis.append(enabled_service)

    return enabled_apis
