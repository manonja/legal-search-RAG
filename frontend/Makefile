.PHONY: help build push run clean minor patch get-version docker-build docker-push docker-build-no-cache

# App configuration
APP_NAME := legal-search-frontend
VERSION := $(shell cat VERSION)

# Docker repository paths
DEV_REPO := us-central1-docker.pkg.dev/maja-dev/maja-dev
PROD_REPO := us-central1-docker.pkg.dev/maja-dev/maja-prod
ENV ?= dev

# Set repository based on environment
ifeq ($(ENV),dev)
	REPO=$(DEV_REPO)
else ifeq ($(ENV),prod)
	REPO=$(PROD_REPO)
else ifeq ($(ENV),local)
	REPO=
else
	$(error ENV must be 'local', 'dev', or 'prod')
endif

# Default target
help:
	@echo "Available targets:"
	@echo "  make ENV=local|dev|prod build  - Build image for specified environment"
	@echo "  make ENV=dev|prod push         - Push image to registry"
	@echo "  make ENV=local run             - Run local container"
	@echo "  make clean                     - Remove local images"
	@echo "  make minor                     - Bump minor version (x.Y.0)"
	@echo "  make patch                     - Bump patch version (x.y.Z)"
	@echo "  make get-version               - Display current version"
	@echo ""
	@echo "Default ENV is 'dev' if not specified"

# Version management
get-version:
	@cat VERSION

# Bump minor version (x.Y.0): increments minor and resets patch to 0
minor:
	@v=$$(cat VERSION | awk -F. '{print $$1"."($$2+1)".0"}'); \
	echo $$v > VERSION; \
	echo "Version updated to $$v"

# Bump patch version (x.y.Z): increments patch
patch:
	@v=$$(cat VERSION | awk -F. '{print $$1"."$$2"."($$3+1)}'); \
	echo $$v > VERSION; \
	echo "Version updated to $$v"

# Build Docker image
docker-build:
ifeq ($(ENV),dev)
	$(MAKE) patch
endif
	docker build -t $(APP_NAME):$(VERSION) \
		--build-arg VERSION_ARG=$(VERSION) \
		--build-arg NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL} \
		--build-arg SENTRY_DSN=${SENTRY_DSN} \
		--build-arg ADMIN_PASSWORD=${ADMIN_PASSWORD} \
		--build-arg USER_PASSWORD=${USER_PASSWORD} \
		--build-arg API_TOKEN=${API_TOKEN} \
		.
ifeq ($(ENV),local)
	@echo "Built local image $(APP_NAME):$(VERSION)"
else
	docker tag $(APP_NAME):$(VERSION) $(REPO)/$(APP_NAME):$(VERSION)
	@echo "Built and tagged image $(REPO)/$(APP_NAME):$(VERSION)"
endif

# Push Docker image to repository
docker-push: docker-build
ifeq ($(ENV),local)
	@echo "Cannot push local images. Use ENV=dev or ENV=prod."
else
	docker push $(REPO)/$(APP_NAME):$(VERSION)
	@echo "Pushed image $(REPO)/$(APP_NAME):$(VERSION)"
endif

# Build Docker image without cache
docker-build-no-cache:
ifeq ($(ENV),dev)
	$(MAKE) patch
endif
	docker build --no-cache -t $(APP_NAME):$(VERSION) \
		--build-arg VERSION_ARG=$(VERSION) \
		--build-arg NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL} \
		--build-arg SENTRY_DSN=${SENTRY_DSN} \
		--build-arg ADMIN_PASSWORD=${ADMIN_PASSWORD} \
		--build-arg USER_PASSWORD=${USER_PASSWORD} \
		--build-arg API_TOKEN=${API_TOKEN} \
		.
ifeq ($(ENV),local)
	@echo "Built local image $(APP_NAME):$(VERSION)"
else
	docker tag $(APP_NAME):$(VERSION) $(REPO)/$(APP_NAME):$(VERSION)
	@echo "Built and tagged image $(REPO)/$(APP_NAME):$(VERSION)"
endif

# Build target (alias for docker-build)
build: docker-build

# Push target (alias for docker-push)
push: docker-push

# Run local container
run:
ifeq ($(ENV),local)
	@echo "Running local container on port 3000..."
	docker run -p 3000:10000 \
		-e NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL} \
		-e SENTRY_DSN=${SENTRY_DSN} \
		-e ADMIN_PASSWORD=${ADMIN_PASSWORD} \
		-e USER_PASSWORD=${USER_PASSWORD} \
		-e API_TOKEN=${API_TOKEN} \
		$(APP_NAME):$(VERSION)
else
	@echo "Run is only available for ENV=local"
endif

# Utility targets
clean:
	@echo "Removing images..."
	-docker rmi $(APP_NAME):$(VERSION)
	-docker rmi $(DEV_REPO)/$(APP_NAME):$(VERSION)
	-docker rmi $(PROD_REPO)/$(APP_NAME):$(VERSION)
