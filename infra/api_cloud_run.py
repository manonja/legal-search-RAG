"""Module for setting up Cloud Run service for the Legal Search RAG API"""

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
                max_instance_count=10,
            ),
            session_affinity=False,
            timeout="300s",
            service_account=service_account.email,
            execution_environment="EXECUTION_ENVIRONMENT_GEN2",
            startup_cpu_boost=True,  # Enable CPU burst at startup
            containers=[
                cloudrunv2.ServiceTemplateContainerArgs(
                    image=pulumi.Output.concat(
                        docker_repository.location,
                        "-docker.pkg.dev/",
                        docker_repository.project,
                        "/",
                        docker_repository.repository_id,
                        "/legal-search-api:latest",
                    ),
                    resources=cloudrunv2.ServiceTemplateContainerResourcesArgs(
                        limits={"memory": "2Gi", "cpu": "1"},
                    ),
                    # Health check via probes
                    liveness_probe=cloudrunv2.ServiceTemplateContainerLivenessProbeArgs(
                        http_get=cloudrunv2.ServiceTemplateContainerLivenessProbeHttpGetArgs(
                            path="/api/health",
                            port=8000,
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
                            port=8000,
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
                                    secret="google-api-key", version="latest"
                                )
                            ),
                        ),
                        cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="OPENAI_API_KEY",
                            value_source=cloudrunv2.ServiceTemplateContainerEnvValueSourceArgs(
                                secret_key_ref=cloudrunv2.ServiceTemplateContainerEnvValueSourceSecretKeyRefArgs(
                                    secret="openai-api-key", version="latest"
                                )
                            ),
                        ),
                        # Data directories
                        cloudrunv2.ServiceTemplateContainerEnvArgs(name="DATA_ROOT", value="/data"),
                        cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="INPUT_DIR", value="/data/input"
                        ),
                        cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="OUTPUT_DIR", value="/data/processed"
                        ),
                        cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="CHUNKS_DIR", value="/data/chunks"
                        ),
                        cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="CHROMA_DATA_DIR", value="/data/chroma"
                        ),
                        cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="COLLECTION_NAME", value="legal_docs"
                        ),
                        # Tenant settings
                        cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="TENANT_ROOT", value="/data/tenants/default"
                        ),
                        cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="CACHE_DIR", value="/data/tenants/default/cache"
                        ),
                        # Model settings
                        cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="OPENAI_MODEL", value="gpt-4-turbo"
                        ),
                        cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="OPENAI_EMBEDDING_MODEL", value="text-embedding-3-small"
                        ),
                        # API settings
                        cloudrunv2.ServiceTemplateContainerEnvArgs(name="HOST", value="0.0.0.0"),
                        cloudrunv2.ServiceTemplateContainerEnvArgs(name="API_PORT", value="8000"),
                        # Cost control
                        cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="OPENAI_MONTHLY_BUDGET", value="30"
                        ),
                        cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="MAX_QUERIES_PER_MONTH", value="100"
                        ),
                        cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="DEFAULT_MODEL", value="gpt-3.5-turbo"
                        ),
                        cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="ENABLE_COST_WARNINGS", value="true"
                        ),
                        # Application settings
                        cloudrunv2.ServiceTemplateContainerEnvArgs(name="LOG_LEVEL", value="INFO"),
                        cloudrunv2.ServiceTemplateContainerEnvArgs(name="DEBUG", value="false"),
                        # Authentication settings
                        cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="GCP_PROJECT_ID", value="952577461734"
                        ),
                        cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="GCP_SECRET_NAME", value="maja-legal-api-token"
                        ),
                        cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="GCP_SECRET_VERSION", value="1"
                        ),
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
                        mount_options=["implicit_dirs", "file_mode=777", "dir_mode=777"],
                    ),
                ),
            ],
        ),
        traffic=[
            cloudrunv2.ServiceTrafficArgs(
                percent=100,
                type="TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST",
            )
        ],
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

    # Grant access to API token secret
    secretmanager.SecretIamMember(
        "maja-legal-api-token-access",
        secret_id="projects/952577461734/secrets/maja-legal-api-token",
        role="roles/secretmanager.secretAccessor",
        member=pulumi.Output.concat("serviceAccount:", sa.email),
    )

    # Grant access to OpenAI API key secret
    secretmanager.SecretIamMember(
        "openai-api-key-access",
        secret_id="projects/952577461734/secrets/openai-api-key",
        role="roles/secretmanager.secretAccessor",
        member=pulumi.Output.concat("serviceAccount:", sa.email),
    )


def get_api_url(service):
    """Get the URL of the Cloud Run service"""
    return service.uri
