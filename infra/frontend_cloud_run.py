"""Module for setting up Cloud Run service for the Legal Search RAG Frontend"""

import os

import pulumi
from pulumi_gcp import cloudrunv2, secretmanager, serviceaccount


def create_frontend_service(stack: str, docker_repository, api_service, dependencies=None):
    """
    Creates a Cloud Run service for the Legal Search RAG Frontend.

    Args:
        stack (str): The stack/environment name (e.g., dev, staging, prod)
        docker_repository: The Artifact Registry repository for Docker images
        api_service: The Cloud Run service for the API
        dependencies: Resources this service depends on

    Returns:
        The created Cloud Run service
    """
    # Read version from file
    version_file = f"VERSION-frontend_cloud_run-{stack}"
    version = "latest"
    if os.path.exists(version_file):
        with open(version_file, "r") as f:
            version = f.read().strip()

    # Get project ID from config
    config = pulumi.Config("maja-infra")
    secret_project_id = config.require("secret_project_id")

    # Create service account for the Cloud Run service
    service_account = create_service_account(stack)

    # Grant access to secrets
    secret_iam_bindings = grant_secret_access(service_account)

    # Combine explicit dependencies with secret bindings
    all_dependencies = (dependencies or []) + secret_iam_bindings

    # Create Cloud Run service
    service = cloudrunv2.Service(
        f"maja-legal-frontend-{stack}",
        location="us-central1",
        ingress="INGRESS_TRAFFIC_ALL",
        template=cloudrunv2.ServiceTemplateArgs(
            scaling=cloudrunv2.ServiceTemplateScalingArgs(
                min_instance_count=0,
                max_instance_count=2,
            ),
            session_affinity=True,  # Important for NextJS apps to maintain session state
            timeout="60s",
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
                        "/legal-search-frontend:",
                        version,
                    ),
                    resources=cloudrunv2.ServiceTemplateContainerResourcesArgs(
                        limits={"memory": "1Gi", "cpu": "1"},
                        startup_cpu_boost=True,
                    ),
                    # Health check via probes
                    liveness_probe=cloudrunv2.ServiceTemplateContainerLivenessProbeArgs(
                        http_get=cloudrunv2.ServiceTemplateContainerLivenessProbeHttpGetArgs(
                            path="/api/health",  # NextJS app should have a health endpoint
                            port=8080,
                        ),
                        initial_delay_seconds=10,
                        timeout_seconds=5,
                        period_seconds=30,
                        failure_threshold=3,
                    ),
                    # Startup probe
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
                        # Set API URL environment variable
                        cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="NEXT_PUBLIC_API_URL",
                            value=api_service.uri,
                        ),
                        # Base env vars
                        cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="NODE_ENV",
                            value="production",
                        ),
                        cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="NEXT_TELEMETRY_DISABLED",
                            value="1",
                        ),
                        cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="NEXT_PUBLIC_ENVIRONMENT",
                            value=stack,
                        ),
                        # Secret environment variables
                        cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="NEXT_PUBLIC_SENTRY_DSN",
                            value_source=cloudrunv2.ServiceTemplateContainerEnvValueSourceArgs(
                                secret_key_ref=cloudrunv2.ServiceTemplateContainerEnvValueSourceSecretKeyRefArgs(
                                    secret=f"projects/{secret_project_id}/secrets/sentry-dsn",
                                    version="latest",
                                )
                            ),
                        ),
                        cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="NEXT_PUBLIC_API_TOKEN",
                            value_source=cloudrunv2.ServiceTemplateContainerEnvValueSourceArgs(
                                secret_key_ref=cloudrunv2.ServiceTemplateContainerEnvValueSourceSecretKeyRefArgs(
                                    secret=f"projects/{secret_project_id}/secrets/maja-legal-api-token",
                                    version="latest",
                                )
                            ),
                        ),
                        cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="NEXT_PUBLIC_ADMIN_PASSWORD",
                            value_source=cloudrunv2.ServiceTemplateContainerEnvValueSourceArgs(
                                secret_key_ref=cloudrunv2.ServiceTemplateContainerEnvValueSourceSecretKeyRefArgs(
                                    secret=f"projects/{secret_project_id}/secrets/frontend-admin-password",
                                    version="latest",
                                )
                            ),
                        ),
                        cloudrunv2.ServiceTemplateContainerEnvArgs(
                            name="NEXT_PUBLIC_USER_PASSWORD",
                            value_source=cloudrunv2.ServiceTemplateContainerEnvValueSourceArgs(
                                secret_key_ref=cloudrunv2.ServiceTemplateContainerEnvValueSourceSecretKeyRefArgs(
                                    secret=f"projects/{secret_project_id}/secrets/frontend-user-password",
                                    version="latest",
                                )
                            ),
                        ),
                    ],
                )
            ],
        ),
        opts=pulumi.ResourceOptions(depends_on=all_dependencies),
    )

    # Set up IAM policy for the service to be publicly accessible
    cloudrunv2.ServiceIamMember(
        f"maja-legal-frontend-{stack}-invoker",
        location=service.location,
        name=service.name,
        role="roles/run.invoker",
        member="allUsers",  # Public access
    )

    return service


def create_service_account(stack: str):
    """Create a service account for the Frontend Cloud Run service"""

    # Create service account
    service_account_id = f"maja-legal-frontend-{stack}"
    sa = serviceaccount.Account(
        service_account_id,
        account_id=service_account_id,
        display_name=f"Maja Legal Frontend Service Account - {stack}",
    )

    return sa


def grant_secret_access(sa):
    """Grant access to the Secret Manager secrets for the API token and API keys"""

    # Get the project ID from config instead of hardcoding
    config = pulumi.Config("maja-infra")
    secret_project_id = config.require("secret_project_id")

    # Get current stack for resource naming
    stack = pulumi.get_stack()

    bindings = []

    # Grant access to API token secret
    api_token_binding = secretmanager.SecretIamMember(
        f"frontend-api-token-access-{stack}",
        secret_id=f"projects/{secret_project_id}/secrets/maja-legal-api-token",
        role="roles/secretmanager.secretAccessor",
        member=pulumi.Output.concat("serviceAccount:", sa.email),
    )
    bindings.append(api_token_binding)

    # Grant access for admin password secret
    admin_password_binding = secretmanager.SecretIamMember(
        f"frontend-admin-password-access-{stack}",
        secret_id=f"projects/{secret_project_id}/secrets/frontend-admin-password",
        role="roles/secretmanager.secretAccessor",
        member=pulumi.Output.concat("serviceAccount:", sa.email),
    )
    bindings.append(admin_password_binding)

    # Grant access for user password secret
    user_password_binding = secretmanager.SecretIamMember(
        f"frontend-user-password-access-{stack}",
        secret_id=f"projects/{secret_project_id}/secrets/frontend-user-password",
        role="roles/secretmanager.secretAccessor",
        member=pulumi.Output.concat("serviceAccount:", sa.email),
    )
    bindings.append(user_password_binding)

    # Grant access to Sentry DSN secret
    sentry_binding = secretmanager.SecretIamMember(
        f"frontend-sentry-dsn-access-{stack}",
        secret_id=f"projects/{secret_project_id}/secrets/sentry-dsn",
        role="roles/secretmanager.secretAccessor",
        member=pulumi.Output.concat("serviceAccount:", sa.email),
    )
    bindings.append(sentry_binding)

    return bindings


def get_frontend_url(service):
    """Get the URL of the Cloud Run service"""
    return service.uri
