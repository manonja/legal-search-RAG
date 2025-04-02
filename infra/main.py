import pulumi

from buckets import create_chroma_datastore_bucket

# Get the environment from Pulumi config
config = pulumi.Config()
env = config.require("env")  # This will be set in Pulumi.dev.yaml or Pulumi.prod.yaml

# Create the Chroma datastore bucket
chroma_bucket = create_chroma_datastore_bucket(env)

# Export the bucket name
pulumi.export("chroma_bucket_name", chroma_bucket.name)


def main():
    print("Hello from infra!")


if __name__ == "__main__":
    main()
