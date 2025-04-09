import pulumi
import pulumi_gcp as gcp


def create_firestore_database(stack: str):
    # Ensure the Firebase Management API is enabled
    firebase_api = gcp.projects.Service(
        "firebase-api", service="firebase.googleapis.com", disable_on_destroy=False
    )

    # Ensure the Firestore API is enabled
    firestore_api = gcp.projects.Service(
        "firestore-api", service="firestore.googleapis.com", disable_on_destroy=False
    )

    firebase_project = gcp.firebase.Project(
        "firebase-api", project=f"maja-{stack}", opts=pulumi.ResourceOptions(protect=True)
    )

    maja_law_frontend_webapp = gcp.firebase.WebApp(
        "Maja-law-frontend-webapp",
        api_key_id="bbcd05d4-aea9-4679-897c-42be7c78f986",
        display_name="Maja-law-frontend",
        project=f"maja-{stack}",
        opts=pulumi.ResourceOptions(protect=True),
    )

    # import firestore database
    # Use Database resource to match the imported state
    firestore_database = gcp.firestore.Database(
        "maja-firestore-database",
        app_engine_integration_mode="DISABLED",
        concurrency_mode="PESSIMISTIC",
        point_in_time_recovery_enablement="POINT_IN_TIME_RECOVERY_DISABLED",
        delete_protection_state="DELETE_PROTECTION_ENABLED",
        location_id="us-central1",
        name="(default)",
        project="maja-dev",
        type="FIRESTORE_NATIVE",
        opts=pulumi.ResourceOptions(protect=True, import_="projects/maja-dev/databases/(default)"),
    )

    return (
        firestore_database,
        maja_law_frontend_webapp,
        firebase_project,
        firebase_api,
        firestore_api,
    )
