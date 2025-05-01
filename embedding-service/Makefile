# Makefile for building and pushing the legalemb Docker container

# Docker image details
IMAGE_NAME = prae_legalemb
IMAGE_TAG = latest
FULL_IMAGE_NAME = $(IMAGE_NAME):$(IMAGE_TAG)

# Registry details (replace with your registry if needed)
# REGISTRY = your-registry.com
# REGISTRY_IMAGE = $(REGISTRY)/$(FULL_IMAGE_NAME)

# Default target
.PHONY: all
all: build

# Help menu
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  help          Show this help message"
	@echo "  build         Build the Docker image"
	@echo "  push          Push the Docker image to registry"
	@echo "  clean         Remove the Docker image locally"
	@echo "  all           Build the Docker image (default)"

# Build the Docker image
.PHONY: build
build:
	@echo "Building Docker image $(FULL_IMAGE_NAME)..."
	docker build -t $(FULL_IMAGE_NAME) -f Dockerfile .

.PHONY: build-nocache
build-nocache:
	@echo "Building Docker image $(FULL_IMAGE_NAME)..."
	docker build --no-cache -t $(FULL_IMAGE_NAME) -f Dockerfile .

# Push the Docker image to registry
.PHONY: push
push: build
	@echo "Pushing Docker image $(FULL_IMAGE_NAME)..."
	# Uncomment and modify the following lines if using a registry
	# docker tag $(FULL_IMAGE_NAME) $(REGISTRY_IMAGE)
	# docker push $(REGISTRY_IMAGE)
	docker push $(FULL_IMAGE_NAME)

# Clean Docker images
.PHONY: clean
clean:
	@echo "Removing Docker image $(FULL_IMAGE_NAME)..."
	docker rmi $(FULL_IMAGE_NAME) || true
	# Uncomment if using a registry
	# docker rmi $(REGISTRY_IMAGE) || true
