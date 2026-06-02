from fastapi import FastAPI
from pydantic import BaseModel
import numpy as np
import time


app = FastAPI(title="Metrica tolerancia a fallos")

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
        return {"mensaje": "no hay datos"}
    tiempo_transcurrido=time.time() - inicio_sistema
    total_eventos= len(logs_eventos)
    
    #contadores por tipo, agregamos recovery retries y dlqs
    hits = sum(1 for e in logs_eventos if e["tipo"] == "HIT")
    misses = sum(1 for e in logs_eventos if e["tipo"] == "MISS")
    recoveries = sum(1 for e in logs_eventos if e["tipo"] == "MISS_RECOVERY")
    retries = sum(1 for e in logs_eventos if e["tipo"] == "RETRY") 
    dlqs = sum(1 for e in logs_Eventos if e["tipo"] == "DLQ")  
    
    
    #exitos en consultas
    exito = hits + misses + recoveries

    #trhoughput
    throughput = exitosos / tiempo_transcurrido if tiempo_transcurrido >0 else 0

    #latencia en consultas exitosas
    latencias_exitosas = [e["latencia"] for e in logs_eventos if e["tipo"]in ["HIT", "MISS", "MISS_RECOVERY"]]
    p50 = float(np.percentile(latencias_exitosas, 50)) if latencias_exitosas else 0.0
    p95 = float(np.percentile(latencias_exitosas, 95)) if latencias_exitosas else 0.0
   
   #tasa de fallo y recuperacion
   retry_rate = (retires / total_eventos) * 100 if total_eventos > 0 else 0.0

   total_fallas = recoveries + dlqs
   recovery_rate = (recoveries/total_fallas) * 100 if total_fallas > 0 else 0.0
   
   dlq_rate = (dlqs / total_eventos) * 100 if total_eventos > 0 else 0.0

   return {
        "resumen": {
            "tiempo_ejecucion_segundos": round(tiempo_transcurrido, 2),
            "total_eventos_registrados": total_eventos,
            "consultas_exitosas": exitosos,
            "hits": hits,
            "misses_directos": misses,
            "misses_recuperados": recoveries,
            "reintentos_ejecutados": retries,
            "consultas_perdidas_dlq": dlqs
        },
        "metricas": {
            "throughput_req_sec": round(throughput, 2),
            "latencia_p50_ms": round(p50, 2),
            "latencia_p95_ms": round(p95, 2),
            "retry_rate_percent": round(retry_rate, 2),
            "recovery_rate_percent": round(recovery_rate, 2),
            "dlq_rate_percent": round(dlq_rate, 2)
        }
    }