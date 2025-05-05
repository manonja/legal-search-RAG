FROM ghcr.io/prefix-dev/pixi:0.46.0-noble-cuda-12.6.3 AS build
# FROM ghcr.io/prefix-dev/pixi:0.41.4 AS build

# copy source code, pixi.toml and pixi.lock to the container
WORKDIR /app
COPY src /app/src
COPY pyproject.toml /app/pyproject.toml
COPY README.md /app/README.md
COPY pixi.lock /app/pixi.lock

ENV CONDA_OVERRIDE_CUDA=12.6.3
# install dependencies to `/app/.pixi/envs/prod`
# use `--locked` to ensure the lockfile is up to date with pixi.toml
RUN pixi install --locked -e default
# create the shell-hook bash script to activate the environment
RUN pixi shell-hook -e default -s bash > /shell-hook
RUN echo "#!/bin/bash" > /app/entrypoint.sh && \
      cat /shell-hook >> /app/entrypoint.sh && \
      echo 'exec "$@"' >> /app/entrypoint.sh

FROM nvidia/cuda:12.6.3-runtime-ubuntu24.04 AS production

ENV CONDA_OVERRIDE_CUDA=12.6.3
ENV HF_EMBEDDING_MODEL=nlpaueb/legal-bert-base-uncased

WORKDIR /app
# only copy the production environment into prod container
# please note that the "prefix" (path) needs to stay the same as in the build container
COPY --from=build /app/.pixi/envs/default /app/.pixi/envs/default
COPY --from=build /app/src /app/src
COPY --from=build --chmod=0755 /app/entrypoint.sh /app/entrypoint.sh

RUN mkdir -p /cache && \
      chmod 777 /cache && \
      useradd -m -u 4200 runpod && \
      chown -R runpod:runpod /app /cache

# Switch to non-root user
USER runpod

ENTRYPOINT [ "/app/entrypoint.sh" ]
# run your app inside the pixi environment
CMD ["python", "-c", "import legalembed; import runpod; runpod.serverless.start({'handler': legalembed.handler.handler})"]
