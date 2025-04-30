FROM ghcr.io/prefix-dev/pixi:0.46.0-focal-cuda-12.6.3 AS build
# FROM ghcr.io/prefix-dev/pixi:0.41.4 AS build


# ARG PIXI_ENVIRONMENT=cpu
ARG PIXI_ENVIRONMENT=default
# copy source code, pixi.toml and pixi.lock to the container
WORKDIR /app
COPY src /app/src
COPY pyproject.toml /app/pyproject.toml
COPY README.md /app/README.md
COPY pixi.lock /app/pixi.lock

# install dependencies to `/app/.pixi/envs/prod`
# use `--locked` to ensure the lockfile is up to date with pixi.toml
RUN pixi install --locked -e $PIXI_ENVIRONMENT
# create the shell-hook bash script to activate the environment
RUN pixi shell-hook -e $PIXI_ENVIRONMENT -s bash > /shell-hook
RUN echo "#!/bin/bash" > /app/entrypoint.sh
RUN cat /shell-hook >> /app/entrypoint.sh
# extend the shell-hook script to run the command passed to the container
RUN echo 'exec "$@"' >> /app/entrypoint.sh

# FROM ubuntu:24.04 AS production
FROM nvidia/cuda:12.6.3-runtime-ubuntu20.04 AS production

# ARG PIXI_ENVIRONMENT=cpu
ARG PIXI_ENVIRONMENT=default

WORKDIR /app
# only copy the production environment into prod container
# please note that the "prefix" (path) needs to stay the same as in the build container
COPY --from=build /app/.pixi/envs/$PIXI_ENVIRONMENT /app/.pixi/envs/$PIXI_ENVIRONMENT
COPY --from=build /app/src /app/src
COPY --from=build --chmod=0755 /app/entrypoint.sh /app/entrypoint.sh

ENTRYPOINT [ "/app/entrypoint.sh" ]
# run your app inside the pixi environment
CMD [ "python", "-c", "import legalembed; print(legalembed.__VERSION__)"]
