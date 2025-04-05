import pulumi
import pulumi_gcp as gcp

# Ensure the Firebase Management API is enabled
firebase_api = gcp.projects.Service(
    "firebase-api", service="firebase.googleapis.com", disable_on_destroy=False
)

# Ensure the Firestore API is enabled
firestore_api = gcp.projects.Service(
    "firestore-api", service="firestore.googleapis.com", disable_on_destroy=False
)

# Create a new Firebase project resource linked to the GCP project
# This doesn't create a new Firebase project, but links the GCP project to Firebase
firebase_project = gcp.firebase.Project(
    "firebaseProject",
    project=gcp.config.project,  # Use the current GCP project
    opts=pulumi.ResourceOptions(depends_on=[firebase_api]),  # Depends on Firebase API being enabled
)

# Create a Firestore database for the project
firestore_database = gcp.firestore.Database(
    "firestoreDatabase",
    project=firebase_project.project,
    name="(default)",  # Use "(default)" for the default database
    location_id="us-central1",  # Specify the region to match Cloud Run
    type="FIRESTORE_NATIVE",  # Specify the database type
    # Ensure Firestore API is enabled and Firebase project link exists
    opts=pulumi.ResourceOptions(depends_on=[firestore_api, firebase_project]),
)

# Export the Firestore database name
pulumi.export("firestore_database_name", firestore_database.name)
