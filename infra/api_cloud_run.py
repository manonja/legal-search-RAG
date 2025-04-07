"""Module for setting up Cloud Run service for the Legal Search RAG API"""

import os

import pulumi
from pulumi_gcp import cloudrunv2, secretmanager, serviceaccount, storage


def create_api_service(stack: str, docker_repository, chroma_bucket, dependencies=None):
    """
    Creates a Cloud Run service for the Legal Search RAG API.

    Args:
        stack (str): The stack/environment name (e.g., dev, staging, prod)
        docker_repository: The Artifact Registry repository for Docker images
        chroma_bucket: The GCS bucket for ChromaDB data
        dependencies: Resources this service depends on

    Returns:
        The created Cloud Run service
    """
    # Read version from file
    version_file = f"VERSION-api_cloud_run-{stack}"
    version = "latest"
    if os.path.exists(version_file):
        with open(version_file, "r") as f:
            version = f.read().strip()

    # Get project ID from config
    config = pulumi.Config("maja-infra")
    project_id = config.require("secret_project_id")

    # Create service account for the Cloud Run service
    service_account = create_service_account(stack, chroma_bucket)

    # Grant access to Secret Manager
    grant_secret_access(service_account)

    # Create Cloud Run service
    service = cloudrunv2.Service(
        f"maja-legal-api-{stack}",
        location="us-central1",
        ingress="INGRESS_TRAFFIC_ALL",
        template=cloudrunv2.ServiceTemplateArgs(
            scaling=cloudrunv2.ServiceTemplateScalingArgs(
                min_instance_count=0,
                max_instance_count=4,
            ),
            session_affinity=True,
            timeout="300s",
            service_account=service_account.email,
            execution_environment="EXECUTION_ENVIRONMENT_GEN2",
            containers=[
                cloudrunv2.ServiceTemplateContainerArgs(
                    image=pulumi.Output.concat(
                        docker_repository.location,
                        "-docker.pkg.dev/",
                        docker_repository.project,
                        "/",
                        docker_repository.repository_id,
                        "/legal-search-api:",
                        version,
                    ),
                    resources=cloudrunv2.ServiceTemplateContainerResourcesArgs(
                        limits={"memory": "2Gi", "cpu": "2"},
                        startup_cpu_boost=True,
                    ),
                    # Health check via probes
                    liveness_probe=cloudrunv2.ServiceTemplateContainerLivenessProbeArgs(
                        http_get=cloudrunv2.ServiceTemplateContainerLivenessProbeHttpGetArgs(
                            path="/api/health",
                            port=8080,
                        ),
                        initial_delay_seconds=10,
                        timeout_seconds=5,
                        period_seconds=30,
                        failure_threshold=3,
                    ),
                    # Startup probe helps during app initialization
                    startup_probe=cloudrunv2.ServiceTemplateContainerStartupProbeArgs(
                        http_get=cloudrunv2.ServiceTemplateContainerStartupProbeHttpGetArgs(
                            path="/api/health",
                            port=8080,
                        ),
                        initial_delay_seconds=0,
                        timeout_seconds=5,
                        period_seconds=10,
                        failure_threshold=10,
                    ),
                    envs=[
                        # Core settings
                        cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="GOOGLE_API_KEY",
                            value_source=cloudrunv2.ServiceTemplateContainerEnvValueSourceArgs(
                                secret_key_ref=cloudrunv2.ServiceTemplateContainerEnvValueSourceSecretKeyRefArgs(
                                    secret=f"projects/{project_id}/secrets/google-gemini-api-key",
                                    version="latest",
                                )
                            ),
                        ),
                        cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="OPENAI_API_KEY",
                            value_source=cloudrunv2.ServiceTemplateContainerEnvValueSourceArgs(
                                secret_key_ref=cloudrunv2.ServiceTemplateContainerEnvValueSourceSecretKeyRefArgs(
                                    secret=f"projects/{project_id}/secrets/openai-api-key",
                                    version="latest",
                                )
                            ),
                        ),
                        cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="SENTRY_DSN",
                            value_source=cloudrunv2.ServiceTemplateContainerEnvValueSourceArgs(
                                secret_key_ref=cloudrunv2.ServiceTemplateContainerEnvValueSourceSecretKeyRefArgs(
                                    secret=f"projects/{project_id}/secrets/sentry-dsn",
                                    version="latest",
                                )
                            ),
                        ),
                        # API Token for authentication
                        cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="API_TOKEN",
                            value_source=cloudrunv2.ServiceTemplateContainerEnvValueSourceArgs(
                                secret_key_ref=cloudrunv2.ServiceTemplateContainerEnvValueSourceSecretKeyRefArgs(
                                    secret=f"projects/{project_id}/secrets/maja-legal-api-token",
                                    version="latest",
                                )
                            ),
                        ),
                        # Data directories
                        cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="DATA_DIR", value="/data/data"
                        ),
                        cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="CHROMA_DIR", value="/data/chroma"
                        ),
                        cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="COLLECTION_NAME", value="legal_docs"
                        ),
                        # Model settings
                        cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="OPENAI_MODEL", value="gpt-4-turbo"
                        ),
                        cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="OPENAI_EMBEDDING_MODEL", value="text-embedding-3-small"
                        ),
                        # Application settings
                        cloudrunv2.ServiceTemplateContainerEnvArgs(name="LOG_LEVEL", value="INFO"),
                        cloudrunv2.ServiceTemplateContainerEnvArgs(name="DEBUG", value="false"),
                        # Authentication settings
                        cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="GCP_PROJECT_ID", value=project_id
                        ),
                        # Removed: API_TOKEN_SECRET_NAME as we now directly use API_TOKEN env var
                    ],
                    volume_mounts=[
                        cloudrunv2.ServiceTemplateContainerVolumeMountArgs(
                            name="legal-data-bucket", mount_path="/data"
                        ),
                    ],
                )
            ],
            volumes=[
                cloudrunv2.ServiceTemplateVolumeArgs(
                    name="legal-data-bucket",
                    gcs=cloudrunv2.ServiceTemplateVolumeGcsArgs(
                        bucket=chroma_bucket.name,
                        read_only=False,
                    ),
                ),
            ],
        ),
        opts=pulumi.ResourceOptions(depends_on=dependencies if dependencies else None),
    )

    # Set up IAM policy for the service
    cloudrunv2.ServiceIamMember(
        f"maja-legal-api-{stack}-invoker",
        location=service.location,
        name=service.name,
        role="roles/run.invoker",
        member="allUsers",  # Public access - could be restricted if needed
    )

    return service


def create_service_account(stack: str, chroma_bucket):
    """Create a service account for the Cloud Run service"""

    # Create service account
    service_account_id = f"maja-legal-api-{stack}"
    sa = serviceaccount.Account(
        service_account_id,
        account_id=service_account_id,
        display_name=f"Maja Legal API Service Account - {stack}",
    )

    # Grant bucket access permissions
    storage.BucketIAMMember(
        f"maja-legal-api-{stack}-bucket-access",
        bucket=chroma_bucket.name,
        role="roles/storage.objectAdmin",
        member=pulumi.Output.concat("serviceAccount:", sa.email),
    )

    return sa


def grant_secret_access(sa):
    """Grant access to the Secret Manager secrets for the API token and API keys"""

    # Get the project ID from config instead of hardcoding
    config = pulumi.Config("maja-infra")
    secret_project_id = config.require("secret_project_id")

    # Get current stack for resource naming
    stack = pulumi.get_stack()

    # Grant access to API token secret
    secretmanager.SecretIamMember(
        f"maja-legal-api-token-access-{stack}",
        secret_id=f"projects/{secret_project_id}/secrets/maja-legal-api-token",
        role="roles/secretmanager.secretAccessor",
        member=pulumi.Output.concat("serviceAccount:", sa.email),
    )

    # Grant access to OpenAI API key secret
    secretmanager.SecretIamMember(
        f"openai-api-key-access-{stack}",
        secret_id=f"projects/{secret_project_id}/secrets/openai-api-key",
        role="roles/secretmanager.secretAccessor",
        member=pulumi.Output.concat("serviceAccount:", sa.email),
    )

    # Grant access to Google Gemini API key secret
    secretmanager.SecretIamMember(
        f"google-gemini-api-key-access-{stack}",
        secret_id=f"projects/{secret_project_id}/secrets/google-gemini-api-key",
        role="roles/secretmanager.secretAccessor",
        member=pulumi.Output.concat("serviceAccount:", sa.email),
    )

    # Grant access to Sentry DSN secret
    secretmanager.SecretIamMember(
        f"sentry-dsn-access-{stack}",
        secret_id=f"projects/{secret_project_id}/secrets/sentry-dsn",
        role="roles/secretmanager.secretAccessor",
        member=pulumi.Output.concat("serviceAccount:", sa.email),
    )


def get_api_url(service):
    """Get the URL of the Cloud Run service"""
    return service.uri
