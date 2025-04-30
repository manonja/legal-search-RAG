# Embedding Service

This project is managed with [Pixi](https://pixi.sh/), a package management tool for developers.

## Project Structure

- Source files are located in the `src/embedding-service` directory
- The project uses `pyproject.toml` for Pixi configuration (no separate `pixi.toml` file is used)

## Development

To install dependencies and set up the environment:

```
pixi install
```

To run the embedding service:

```
pixi run python src/embedding-service/main.py
```

## Docker

A Makefile is provided to simplify Docker operations for this project.

### Makefile Usage

The following commands are available:

- `make build` - Builds the Docker image as `prae_legalemb:latest`
- `make push` - Builds and pushes the Docker image
- `make clean` - Removes the Docker image locally
- `make help` - Shows all available targets with descriptions

Examples:

```bash
# Build the Docker image
make build

# Build and push the Docker image
make push

# Remove the Docker image
make clean
```

To configure a custom Docker registry, edit the `REGISTRY` variable in the Makefile.
