# Tarea 1 - Sistemas Distribuidos: Análisis Geospacial RM

Sistema distribuido para la consulta de datos de edificación en la Región Metropolitana utilizando Docker, Redis y FastAPI.

## 🚀 Instrucciones de Despliegue

1. **Dataset**: Debido a su peso, el archivo `santiago.csv.gz` NO está en el repositorio. Debes colocarlo manualmente en la carpeta `/generador_respuestas/data/`.
2. **Levantar el sistema**: Ejecuta el siguiente comando en la raíz del proyecto:
   ```bash
   docker-compose up --build