FROM python:3.11-slim
WORKDIR /app

# Dependencias del sistema (OpenCV necesita libGL)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1 \
    exiftool libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Dependencias Python — primero pyproject.toml (caché de capas Docker)
COPY pyproject.toml .

# Código fuente
COPY src/ src/
RUN pip install --no-cache-dir .

# Añadir src al PYTHONPATH
ENV PYTHONPATH=/app/src

# Directorio de salida para heatmaps y anotaciones
RUN mkdir -p /outputs

# Usuario no-root por seguridad
RUN useradd -m appuser && \
    chown -R appuser:appuser /app /outputs
USER appuser

# El servidor MCP arranca por stdio (no hay EXPOSE de puerto)
CMD ["python", "-m", "forgery_detector.server"]
