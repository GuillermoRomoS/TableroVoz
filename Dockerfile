# TableroVoz — imagen lista para desplegar en la nube.
# Sirve la web accesible y la API desde FastAPI/uvicorn en el puerto $PORT.
FROM python:3.12-slim

# opencv-python-headless necesita libGL y glib incluso en headless.
RUN apt-get update && apt-get install -y --no-install-recommends \
      libgl1 \
      libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependencias primero (mejor cacheo de capas).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código, samples (para los sprites de entrenamiento) y web.
COPY tablerovoz/ ./tablerovoz/
COPY web/ ./web/
COPY samples/ ./samples/
COPY eval.py pytest.ini ./

# Entrenar el clasificador en build para que la imagen quede lista para reconocer.
# (Usa solo samples de desarrollo; nunca samples/holdout.)
RUN python -m tablerovoz.train --n 200 --seed 0

# Puerto configurable por la plataforma (Cloud Run, Render, Fly, etc.).
ENV PORT=8080
EXPOSE 8080

# Arranque: uvicorn en 0.0.0.0:$PORT sirviendo la app FastAPI (web incluida).
CMD ["sh", "-c", "uvicorn tablerovoz.api:app --host 0.0.0.0 --port ${PORT}"]
