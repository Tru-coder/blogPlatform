FROM python:3.12.5-alpine3.19

RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /app

# Install OpenSSL for key generation
USER root
RUN apk add --no-cache openssl
USER appuser

# Generate private and public keys
RUN mkdir -p /app/envs && \
    openssl genpkey -algorithm RSA -out /app/envs/private_key.pem -pkeyopt rsa_keygen_bits:2048 && \
    openssl rsa -pubout -in /app/envs/private_key.pem -out /app/envs/public_key.pem && \
    chmod 600 /app/envs/private_key.pem && \
    chmod 644 /app/envs/public_key.pem


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# ensures that the alembic command (and any other user-installed scripts) are available in the PATH for the appuser
ENV PATH="/home/appuser/.local/bin:$PATH"

COPY alembic.ini .
COPY alembic alembic
COPY envs/ envs/

COPY src/ src/
COPY tests/ tests/

ENV PYTHONPATH="$PYTHONPATH:/app"

EXPOSE 8002

CMD ["sh", "-c", "alembic upgrade head && python src/main.py"]
