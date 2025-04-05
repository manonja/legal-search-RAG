.PHONY: help build push run clean major minor patch get-version docker-build docker-push docker-build-no-cache lock format check-format lint serve

# App configuration
APP_NAME := legal-search-frontend
VERSION = $$(cat VERSION)

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
	@echo "  make major                     - Bump major version (X.0.0)"
	@echo "  make minor                     - Bump minor version (x.Y.0)"
	@echo "  make patch                     - Bump patch version (x.y.Z)"
	@echo "  make get-version               - Display current version"
	@echo "  make lint                      - Run linting"
	@echo "  make format                    - Format code"
	@echo "  make check-format              - Check formatting"
	@echo "  make lock                      - Lock dependencies"
	@echo "  make serve                     - Run development server"
	@echo ""
	@echo "Default ENV is 'dev' if not specified"

# Version management
get-version:
	@cat VERSION

# Bump major version (X.0.0)
major:
	@./scripts/bump_version.sh major

# Bump minor version (x.Y.0)
minor:
	@./scripts/bump_version.sh minor

# Bump patch version (x.y.Z)
patch:
	@./scripts/bump_version.sh patch

# Development targets
lint:
	npm run lint

format:
	npx prettier --write .

check-format:
	npx prettier --check .

lock:
	npm ci

serve:
	npm run dev

# Build Docker image
docker-build:
ifeq ($(ENV),dev)
	$(MAKE) patch
endif
	docker build -t $(APP_NAME):$(VERSION) \
		--build-arg VERSION_ARG=$(VERSION) \
		--build-arg NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL} \
		--build-arg NEXT_PUBLIC_SENTRY_DSN=${NEXT_PUBLIC_SENTRY_DSN} \
		--build-arg NEXT_PUBLIC_ADMIN_PASSWORD=${NEXT_PUBLIC_ADMIN_PASSWORD} \
		--build-arg NEXT_PUBLIC_USER_PASSWORD=${NEXT_PUBLIC_USER_PASSWORD} \
		--build-arg NEXT_PUBLIC_API_TOKEN=${NEXT_PUBLIC_API_TOKEN} \
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
		--build-arg NEXT_PUBLIC_SENTRY_DSN=${NEXT_PUBLIC_SENTRY_DSN} \
		--build-arg NEXT_PUBLIC_ADMIN_PASSWORD=${NEXT_PUBLIC_ADMIN_PASSWORD} \
		--build-arg NEXT_PUBLIC_USER_PASSWORD=${NEXT_PUBLIC_USER_PASSWORD} \
		--build-arg NEXT_PUBLIC_API_TOKEN=${NEXT_PUBLIC_API_TOKEN} \
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
	docker run -p 3000:8080 \
		-e NODE_ENV=development \
		-e NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL} \
		-e NEXT_PUBLIC_SENTRY_DSN=${NEXT_PUBLIC_SENTRY_DSN} \
		-e NEXT_PUBLIC_ADMIN_PASSWORD=${NEXT_PUBLIC_ADMIN_PASSWORD} \
		-e NEXT_PUBLIC_USER_PASSWORD=${NEXT_PUBLIC_USER_PASSWORD} \
		-e NEXT_PUBLIC_API_TOKEN=${NEXT_PUBLIC_API_TOKEN} \
		-e NEXT_PUBLIC_FIREBASE_API_KEY=${NEXT_PUBLIC_FIREBASE_API_KEY} \
		-e NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=${NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN} \
		-e NEXT_PUBLIC_FIREBASE_PROJECT_ID=${NEXT_PUBLIC_FIREBASE_PROJECT_ID} \
		-e NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=${NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET} \
		-e NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=${NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID} \
		-e NEXT_PUBLIC_FIREBASE_APP_ID=${NEXT_PUBLIC_FIREBASE_APP_ID} \
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
