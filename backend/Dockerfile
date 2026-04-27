FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH /app

# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the phase modules and backend code
COPY phase1 /app/phase1
COPY phase2 /app/phase2
COPY phase3 /app/phase3
COPY phase4 /app/phase4
COPY backend /app/backend

# Use non-root user
RUN adduser --disabled-password appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
