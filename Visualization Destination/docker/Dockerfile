# Define workdir folder for all stages
# Must be renewed in the beggining of each stage
ARG WORKDIR=/app/

# --------------------------------------
# Builder stage to generate .proto files
# --------------------------------------

FROM python:3.8.7-slim-buster as builder
# Renew wrokdir arg
ARG WORKDIR

COPY requirements-build.txt ${WORKDIR}

WORKDIR ${WORKDIR}

RUN pip install --upgrade pip && \
    pip install -r requirements-build.txt && \
    rm requirements-build.txt

# Path for the protos folder to copy
ARG PROTOS_FOLDER_DIR=protos

COPY ${PROTOS_FOLDER_DIR} ${WORKDIR}

# Compile proto file and remove it
RUN python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. visualization.proto && \
    rm visualization.proto

# -----------------------------
# Stage to generate final image
# -----------------------------

FROM python:3.8.7-slim-buster
# Renew wrokdir arg
ARG WORKDIR

ARG USER=runner
ARG GROUP=runner-group
ARG GRPC_SERVICES_DIR=src

# Create non-privileged user to run
RUN addgroup --system ${GROUP} && \
    adduser --system --no-create-home --ingroup ${GROUP} ${USER}

COPY requirements.txt ${WORKDIR}

WORKDIR ${WORKDIR}

RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    rm requirements.txt

# Copy generated .py files
COPY --from=builder --chown=${USER}:${GROUP} ${WORKDIR} ${WORKDIR}
# Copy code
COPY ${GRPC_SERVICES_DIR} ${WORKDIR}

# Change to non-privileged user
USER ${USER}

WORKDIR ${WORKDIR}

EXPOSE ${5000}
EXPOSE ${50051}

CMD ["gunicorn", \
    "--threads", "5", \
    "--workers", "1", \
    "--bind", "0.0.0.0:5000", \
    "app:create_app()"]

