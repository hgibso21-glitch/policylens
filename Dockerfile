# PolicyLens container image. Built to run on OpenShift's restricted security context:
# non-root, no privilege escalation, and an arbitrary user id that belongs to group 0.
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app
COPY pyproject.toml README.md ./
COPY app ./app
RUN pip install .

# OpenShift starts the container with a random uid but always gid 0, so group 0 needs
# write access to anything the app writes. The SQLite file lives here (a volume in the cluster).
RUN mkdir /data && chgrp -R 0 /data && chmod -R g=u /data
ENV DATABASE_URL=sqlite:////data/policylens.db

USER 1001
EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
