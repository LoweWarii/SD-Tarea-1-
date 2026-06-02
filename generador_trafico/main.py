import time
import random
import json
import uuid
import numpy as np
from confluent_kafka import Producer

# Apuntamos a la caché
TARGET_URL = "http://cache:8000"

ZONAS = ["Z1", "Z2", "Z3", "Z4", "Z5"]
QUERIES = ["q1", "q2", "q3", "q4", "q5"] 

#setear kafka
conf = {
    'bootstrap.servers': 'kafka:29092', # Apunta al contenedor de Kafka en la red de Docker
    'client.id': 'generador-trafico'
}
producer = Producer(conf)
TOPIC_PRINCIPAL = "consultas-principales"

def delivery_report(err,msg):
    if err is not None:
        printf(f"error al enviar le msg a kafka")


def generar_zona_zipf(alpha=2.0):
    idx = np.random.zipf(alpha)
    while idx > len(ZONAS):
        idx = np.random.zipf(alpha)
    return ZONAS[idx - 1]

def simular_trafico(distribucion="uniforme", num_requests=2500, delay_ms=10):
    print(f" Iniciando simulación | Distribución: {distribucion.upper()} | Peticiones: {num_requests}")
    
    for i in range(num_requests):
    
       zona = random.choice(ZONAS) if distribucion == "uniforme" else generar_zona_zipf(alpha=1.5)
       query = random.choice(QUERIES)
       conf_min = round(random.uniform(0.0, 0.9), 3)

       payload = {
            "request_id": str(uuid.uuid4()),      # Identificador único
            "timestamp": time.time(),             # Timestamp de creación
            "retry_count": 0,                     # Número de reintentos inicial
            "query_type": query,                  # Tipo de consulta (Q1-Q5)
            "params": {
                "conf_min": conf_min
            }
        }
       
       if query == "q4":
            zona_b = random.choice([z for z in ZONAS if z != zona])
            payload["params"]["zone_a"] = zona
            payload["params"]["zone_b"] = zona_b
    else:
            payload["params"]["zone_id"] = zona

            producer.produce(
            topic=TOPIC_PRINCIPAL,
            key=payload["request_id"], # Usar el ID como llave organiza mejor los datos en Kafka
            value=json.dumps(payload),
            callback=delivery_report
        )
        #para que nos e sature kafka con los callbacks
    producer.produce(TOPIC_PRINCIPAL, key=req_id, value=json.dumps(payload))
    producer.poll(0)
    if (i + 1) % 100 == 0:
            print(f"[{i+1}/{num_requests}]  Mensajes encolados en Kafka...")       
            time.sleep(delay_ms / 1000.0)
       
            producer.flush()
    print(f" Simulación {distribucion.upper()} finalizada y entregada a Kafka.\n")

    if __name__ == "__main__":
    
         print(" esperar para que kafka opere")
    time.sleep(10)
 
    print("--- PRUEBA 1: Distribución Uniforme ---")
    simular_trafico(distribucion="uniforme", num_requests=5000, delay_ms=2) 
    
    print("--- PRUEBA 2: Distribución de Zipf ---")
    simular_trafico(distribucion="zipf", num_requests=5000, delay_ms=2)



  
        
        
       