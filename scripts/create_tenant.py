#!/usr/bin/env python
"""
Script to create a new tenant with initial setup.
Usage: python create_tenant.py <tenant_name> <admin_email> [description]
"""

import argparse
import json
import logging
import os
import shutil
import sys
from pathlib import Path

# Adjust path to include the API module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.auth.models import TenantCreate
from api.tenant.tenant_service import TenantService
from api.utils.document_processor import DocumentProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Create a new tenant with initial setup")
    parser.add_argument("tenant_name", help="Name of the new tenant")
    parser.add_argument("admin_email", help="Email address for the tenant admin")
    parser.add_argument("--description", help="Description of the tenant", default="")
    parser.add_argument("--docs-dir", help="Directory containing initial documents", default=None)
    parser.add_argument("--process-docs", help="Process documents after setup", action="store_true")
    parser.add_argument("--create-container", help="Create Docker container for tenant", action="store_true")
    return parser.parse_args()

def create_tenant(args):
    """Create a new tenant with the given parameters"""
    logger.info(f"Creating tenant: {args.tenant_name}")

    tenant_service = TenantService()

    # Create tenant data
    tenant_data = TenantCreate(
        name=args.tenant_name,
        admin_email=args.admin_email,
        description=args.description or f"Tenant for {args.tenant_name}"
    )

    # Create tenant
    tenant = tenant_service.create_tenant(tenant_data)

    logger.info(f"Successfully created tenant: {tenant.id}")
    logger.info(f"Admin email: {args.admin_email}")

    return tenant

def process_documents(tenant_id, docs_dir):
    """Process initial documents for the tenant"""
    logger.info(f"Processing documents for tenant {tenant_id} from {docs_dir}")

    if not os.path.exists(docs_dir):
        logger.error(f"Document directory not found: {docs_dir}")
        return False

    # Create document processor
    processor = DocumentProcessor(tenant_id)

    # Process each document
    processed_docs = []
    for file_name in os.listdir(docs_dir):
        file_path = os.path.join(docs_dir, file_name)
        if os.path.isfile(file_path) and file_name.lower().endswith(('.pdf', '.doc', '.docx')):
            try:
                logger.info(f"Processing document: {file_name}")
                doc_metadata = processor.process_document(file_path)
                processed_docs.append(doc_metadata)
                logger.info(f"Successfully processed: {file_name}")
            except Exception as e:
                logger.error(f"Error processing document {file_name}: {e}")

    logger.info(f"Processed {len(processed_docs)} documents for tenant {tenant_id}")

    # Create document list file
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tenant_dir = os.path.join(root_dir, "tenants", tenant_id)
    os.makedirs(tenant_dir, exist_ok=True)

    summary_path = os.path.join(tenant_dir, "document_list.json")
    with open(summary_path, 'w') as f:
        json.dump(processed_docs, f, indent=2)

    logger.info(f"Document summary written to {summary_path}")

    return processed_docs

def run_tenant_setup(tenant_id):
    """Run the embedding and chunking processes for the tenant"""
    try:
        logger.info(f"Running document chunking for tenant {tenant_id}")
        os.environ["TENANT_ID"] = tenant_id

        # Run chunking process
        from api.chunk import run_chunking
        run_chunking(tenant_id=tenant_id)

        # Run embedding process
        logger.info(f"Running embedding generation for tenant {tenant_id}")
        from api.embeddings import run_embeddings
        run_embeddings(tenant_id=tenant_id)

        logger.info(f"Setup complete for tenant {tenant_id}")
        return True
    except Exception as e:
        logger.error(f"Error in tenant setup: {e}")
        return False

def create_tenant_container(tenant_id):
    """Create a Docker container for the tenant"""
    logger.info(f"Creating Docker container for tenant {tenant_id}")

    tenant_service = TenantService()
    result = tenant_service.provision_tenant_container(tenant_id)

    if result:
        logger.info(f"Container provisioned successfully for tenant {tenant_id}")
    else:
        logger.error(f"Failed to provision container for tenant {tenant_id}")

    return result

def main():
    """Main function to create and set up a tenant"""
    args = parse_arguments()

    # Check GCP credentials
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        # Check if there are credentials in the credentials directory
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        creds_dir = os.path.join(root_dir, "credentials")

        if os.path.exists(creds_dir):
            cred_files = [f for f in os.listdir(creds_dir) if f.endswith('.json') and f != "placeholder.json"]
            if cred_files:
                # Use the first JSON file found
                cred_path = os.path.join(creds_dir, cred_files[0])
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path
                logger.info(f"Using GCP credentials: {cred_path}")
            else:
                logger.warning("No GCP credentials found. GCP features will be limited.")
                # Create placeholder if it doesn't exist
                placeholder = os.path.join(creds_dir, "placeholder.json")
                if not os.path.exists(placeholder):
                    with open(placeholder, "w") as f:
                        f.write("{}")
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = placeholder
        else:
            logger.warning("Credentials directory not found. Creating it...")
            os.makedirs(creds_dir, exist_ok=True)
            placeholder = os.path.join(creds_dir, "placeholder.json")
            with open(placeholder, "w") as f:
                f.write("{}")
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = placeholder

    # Create tenant
    tenant = create_tenant(args)

    # Process documents if directory provided
    if args.docs_dir:
        process_documents(tenant.id, args.docs_dir)

        # Run setup if documents were processed
        if args.process_docs:
            run_tenant_setup(tenant.id)

    # Create container if requested
    if args.create_container:
        create_tenant_container(tenant.id)

    # Print summary
    print("\nTenant creation summary:")
    print(f"  Tenant ID: {tenant.id}")
    print(f"  Tenant Name: {tenant.name}")
    print(f"  Admin Email: {args.admin_email}")
    print(f"\nTo use this tenant, run:")
    print(f"  export TENANT_ID={tenant.id}")
    if args.create_container:
        print(f"\nOr access the tenant-specific deployment at:")
        print(f"  http://localhost:<tenant-frontend-port>")
        print(f"\nCheck the logs for the assigned ports.")

if __name__ == "__main__":
    main()
