from fastapi import FastAPI
from pydantic import BaseModel
import numpy as np
import time
import redis

app = FastAPI(title="Almacenamiento de Métricas")

# Almacenamiento en memoria para el registro de eventos
# En un entorno real usaríamos Prometheus o una BD de series de tiempo, 
# pero para el entregable, la memoria es suficiente.
logs_eventos = []
inicio_sistema = time.time()

# Modelos de datos esperados
class EventoCache(BaseModel):
    tipo: str  # "HIT" o "MISS"
    latencia_ms: float
    consulta: str

# Endpoints para registrar datos
@app.post("/log/evento")
def registrar_evento(evento: EventoCache):
    logs_eventos.append({
        "timestamp": time.time(),
        "tipo": evento.tipo,
        "latencia": evento.latencia_ms,
        "consulta": evento.consulta
    })
    return {"status": "ok"}

# Endpoint para obtener el reporte que usarás en tu informe LaTeX
@app.get("/reporte")
def generar_reporte():
    if not logs_eventos:
        return {"mensaje": "No hay datos registrados aún."}
    
    total_consultas = len(logs_eventos)
    hits = sum(1 for e in logs_eventos if e["tipo"] == "HIT")
    misses = sum(1 for e in logs_eventos if e["tipo"] == "MISS")
    
    latencias = [e["latencia"] for e in logs_eventos]
    latencias_hits = [e["latencia"] for e in logs_eventos if e["tipo"] == "HIT"]
    latencias_misses = [e["latencia"] for e in logs_eventos if e["tipo"] == "MISS"]
    
    # 1. Cálculos básicos solicitados en el PDF
    hit_rate = hits / total_consultas if total_consultas > 0 else 0
    tiempo_transcurrido = time.time() - inicio_sistema
    throughput = total_consultas / tiempo_transcurrido if tiempo_transcurrido > 0 else 0
    
    p50 = float(np.percentile(latencias, 50)) if latencias else 0.0
    p95 = float(np.percentile(latencias, 95)) if latencias else 0.0

    # 2. Eviction Rate (Evictions/minuto) consultando directamente a Redis
    minutos_ejecucion = tiempo_transcurrido / 60
    total_evictions = 0
    try:
        # Nos conectamos al contenedor de Redis usando su nombre de servicio
        r = redis.Redis(host='redis-server', port=6379, db=0, decode_responses=True)
        stats = r.info('stats')
        total_evictions = int(stats.get('evicted_keys', 0))
        eviction_rate = total_evictions / minutos_ejecucion if minutos_ejecucion > 0 else 0
    except Exception as e:
        print(f"Error conectando a Redis para métricas: {e}")
        eviction_rate = 0.0

    # 3. Eficiencia de Caché (Cache efficiency)
    # Fórmula de la rúbrica: (hits * t_cache + misses * t_db) / total
    t_cache_promedio = sum(latencias_hits) / len(latencias_hits) if latencias_hits else 0.0
    t_db_promedio = sum(latencias_misses) / len(latencias_misses) if latencias_misses else 0.0
    
    if total_consultas > 0:
        cache_efficiency = ((hits * t_cache_promedio) + (misses * t_db_promedio)) / total_consultas
    else:
        cache_efficiency = 0.0
    
    return {
        "resumen": {
            "total_consultas": total_consultas,
            "hits": hits,
            "misses": misses,
            "tiempo_ejecucion_segundos": round(tiempo_transcurrido, 2),
            "evicciones_totales_redis": total_evictions
        },
        "metricas_clave": {
            "hit_rate": round(hit_rate, 4),
            "throughput_req_sec": round(throughput, 2),
            "latencia_p50_ms": round(p50, 2),
            "latencia_p95_ms": round(p95, 2),
            "eviction_rate_per_min": round(eviction_rate, 2),
            "cache_efficiency": round(cache_efficiency, 2)
        }
    }