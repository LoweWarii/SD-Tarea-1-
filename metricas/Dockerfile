FROM python:3.9-slim

WORKDIR /app


# Instalar librerías básicas necesarias
RUN pip install --no-cache-dir fastapi uvicorn pydantic numpy redis
COPY . /app

# Exponer el puerto por defecto
EXPOSE 8000

# Comando para iniciar la API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]