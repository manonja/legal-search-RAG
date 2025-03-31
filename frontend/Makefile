# Docker image configuration
VERSION := $(shell cat VERSION)
APP_NAME := nextjs-legal-search

# Default environment is local
ENV ?= local

# Artifact Registry paths
DEV_REGISTRY := us-central1-docker.pkg.dev/maja-dev/maja-dev
PROD_REGISTRY := us-central1-docker.pkg.dev/maja-prod/maja-prod

# Set registry and tag based on environment
ifeq ($(ENV),local)
    REGISTRY :=
    TAG := local
    FULL_TAG := $(APP_NAME):$(TAG)
else ifeq ($(ENV),dev)
    REGISTRY := $(DEV_REGISTRY)
    TAG := latest
    FULL_TAG := $(REGISTRY)/$(APP_NAME):$(TAG)
else ifeq ($(ENV),prod)
    REGISTRY := $(PROD_REGISTRY)
    TAG := $(VERSION)
    FULL_TAG := $(REGISTRY)/$(APP_NAME):$(TAG)
    LATEST_TAG := $(REGISTRY)/$(APP_NAME):latest
endif

# Default target
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  make ENV=local|dev|prod build  - Build image for specified environment"
	@echo "  make ENV=dev|prod push         - Push image to registry"
	@echo "  make ENV=local run             - Run local container"
	@echo "  make clean                     - Remove local images"
	@echo ""
	@echo "Default ENV is 'local' if not specified"

# Build target
.PHONY: build
build:
	@echo "Building image for $(ENV) environment..."
	docker build -t $(FULL_TAG) .
ifeq ($(ENV),prod)
	docker tag $(FULL_TAG) $(LATEST_TAG)
endif

# Push target
.PHONY: push
push: build
ifeq ($(ENV),local)
	@echo "Cannot push local images. Use ENV=dev or ENV=prod."
else
	@echo "Pushing to $(ENV) registry..."
	docker push $(FULL_TAG)
ifeq ($(ENV),prod)
	docker push $(LATEST_TAG)
endif
endif

# Run local container
.PHONY: run
run:
ifeq ($(ENV),local)
	@echo "Running local container on port 10000..."
	docker run -p 10000:10000 --env-file .env $(FULL_TAG)
else
	@echo "Run is only available for ENV=local"
endif

# Utility targets
.PHONY: clean
clean:
	@echo "Removing images..."
	-docker rmi $(APP_NAME):local
	-docker rmi $(DEV_REGISTRY)/$(APP_NAME):latest
	-docker rmi $(PROD_REGISTRY)/$(APP_NAME):$(VERSION)
	-docker rmi $(PROD_REGISTRY)/$(APP_NAME):latest 