import time
import requests
import redis
import json
from fastapi import FastAPI, HTTPException

app = FastAPI(title="Sistema de Caché")

# Direcciones internas de la red de Docker
REDIS_HOST = "redis-server"
GENERADOR_URL = "http://generador_respuestas:8000"
METRICAS_URL = "http://metricas:8000" 

# Conexión a Redis
cache = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)
DEFAULT_TTL = 60 # TTL en segundos

def registrar_metrica(tipo, latencia, consulta):
    try:
        # Timeout corto para métricas para no retrasar la respuesta al usuario
        requests.post(f"{METRICAS_URL}/log/evento", json={
            "tipo": tipo,
            "latencia_ms": latencia,
            "consulta": consulta
        }, timeout=1) 
    except Exception as e:
        print(f"Error enviando métrica: {e}")

@app.get("/{query}") 
def interceptar_consulta(query: str, zone_id: str, conf_min: float = 0.0):
    start_time = time.time()
    cache_key = f"{query}:{zone_id}:conf={conf_min}"
    
    # 1. Buscar en Redis
    try:
        cached_response = cache.get(cache_key)
    except Exception as e:
        print(f"Error conexión Redis: {e}")
        cached_response = None
    
    if cached_response:
        latencia = (time.time() - start_time) * 1000
        registrar_metrica("HIT", latencia, query)
        return {"source": "cache (HIT)", "data": json.loads(cached_response)}
    
    # 2. Si no está (MISS), buscar en el Generador de Respuestas
    try:
        # CAMBIO CLAVE: Se agrega timeout=30 porque Pandas tardará en procesar el dataset completo
        response = requests.get(
            f"{GENERADOR_URL}/{query}", 
            params={"zone_id": zone_id, "conf_min": conf_min},
            timeout=30 
        )
        response.raise_for_status()
        data = response.json()
        
        # 3. Guardar en Caché con TTL
        cache.setex(cache_key, DEFAULT_TTL, json.dumps(data))
        
        latencia = (time.time() - start_time) * 1000
        registrar_metrica("MISS", latencia, query)
        
        return {"source": "generador (MISS)", "data": data}

    except requests.exceptions.Timeout:
        # Error específico si el Generador de Respuestas se demora más de 30s
        raise HTTPException(status_code=504, detail="El Generador de Respuestas tardó demasiado (Timeout)")
    except requests.exceptions.RequestException as e:
        # Error 503 si el servicio no está disponible o hay error de red
        raise HTTPException(status_code=503, detail=f"Error en generador: {e}")