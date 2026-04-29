FROM python:3.9-slim

WORKDIR /app

# Instalar librerías básicas necesarias
RUN pip install fastapi uvicorn requests redis pandas numpy pydantic

COPY . /app

# Exponer el puerto por defecto
EXPOSE 8000

# Comando para iniciar la API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]