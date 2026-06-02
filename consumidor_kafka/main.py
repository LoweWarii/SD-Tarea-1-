import time
import json
import requests
import redis
from confluent_kafka import Consumer, Producer, KafkaException

KAFKA_BROKER = 'kafka:29092'
BACKEND_URL = 'http://generador_respuestas:8000'
METRICS_URL = 'http://metricas:8000/log/evento'

TOPIC_PRINCIPAL = "consultas-principales"
TOPIC_REINTENTOS = "consultas-reintentos"
TOPIC_DLQ = "consultas-dlq"

MAX_RETRIES = 3

r_cache = redis.Redis(host='redis-server', port=6379, db=0, decode_responses=True)
consumer_conf = {
    'bootstrap.servers': KAFKA_BROKER,
    'group.id': 'grupo-trabajadores-geo',
    'auto.offset.reset': 'earliest' 
}
consumer = Consumer(consumer_conf)
consumer.subscribe([TOPIC_PRINCIPAL, TOPIC_REINTENTOS])

def reportar_metrica(tipo_evento, latencia, consulta, extra_data=None):
    """ Envía los datos al servicio de métricas para el análisis posterior """
    payload = {
        "tipo": tipo_evento,
        "latencia_ms": latencia,
        "consulta": consulta
    }
    if extra_data:
        payload.update(extra_data)
    try:
        requests.post(METRICS_URL, json=payload, timeout=2)
    except:
        pass 

def procesar_mensaje(msg):
    try:
        data = json.loads(msg.value().decode('utf-8'))
    except Exception as e:
        print(f" Error decodificando {e}")
        return
    req_id = data.get("request_id")
    query_type = data.get("query_type")
    params = data.get("params", {})
    retry_count = data.get("retry_count", 0)
    param_str = ":".join(f"{k}={v}" for k, v in params.items())
    cache_key = f"{query_type}:{param_str}"

    start_time = time.time()
    
    cached_response = r_cache.get(cache_key)
    if cached_response:
        latencia = round((time.time() - start_time) * 1000, 2)
        print(f" [HIT] {cache_key}  Caché.")
        reportar_metrica("HIT", latencia, cache_key)
        return
    
    print(f"[FALLO] {cache_key} no esta en cache, buscando backend")
    try:
        url = f"{BACKEND_URL}/{query_type}"
        response = requests.get(url, params=params, timeout=3)
        response.raise_for_status()

        latencia = round((time.time() - start_time) * 1000, 2)
        resultado = response.json()

        r_cache.setex(cache_key, 60, json.dumps(resultado))

        evento_tipo = "MISS_RECOVERY" if retry_count > 0 else "MISS"
        reportar_metrica(evento_tipo, latencia, cache_key)
        print(f"[EXITO] {cache_key} procesado y guardado en caché.")
        
    except requests.exceptions.RequestException as e:
        latencia = round((time.time() - start_time) * 1000, 2)
        print(f" backend no responde {cache_key}: {e}")

    if retry_count < MAX_RETRIES:
        
            data["retry_count"] += 1
            producer.produce(TOPIC_REINTENTOS, key=req_id, value=json.dumps(data))
            producer.flush()
            print(f" Enviando denuevo {data['retry_count']}/{MAX_RETRIES}")
            reportar_metrica("RETRY", latencia, cache_key)
    else:
         
            producer.produce(TOPIC_DLQ, key=req_id, value=json.dumps(data))
            producer.flush()
            print(f" Límite de reintentos superado. Enviado a DLQ.")
            reportar_metrica("DLQ", latencia, cache_key)

if __name__ == "__main__":
    print(" iniciando kafka")
    try:
        while True:
        
            msg = consumer.poll(1.0)
            
            if msg is None:
                continue
            if msg.error():
                print(f"⚠️ Error de Kafka: {msg.error()}")
                continue
                
            
            procesar_mensaje(msg)

    except KeyboardInterrupt:
       print("detener")
       finally:
     consumer.close()