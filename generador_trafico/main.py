import time
import random
import requests
import numpy as np

# Apuntamos a la caché
TARGET_URL = "http://cache:8000"

ZONAS = ["Z1", "Z2", "Z3", "Z4", "Z5"]
QUERIES = ["q1", "q2", "q3", "q5"] 

def generar_zona_zipf(alpha=2.0):
    idx = np.random.zipf(alpha)
    while idx > len(ZONAS):
        idx = np.random.zipf(alpha)
    return ZONAS[idx - 1]

def simular_trafico(distribucion="uniforme", num_requests=2500, delay_ms=10):
    print(f"🚀 Iniciando simulación | Distribución: {distribucion.upper()} | Peticiones: {num_requests}")
    
    for i in range(num_requests):
        if distribucion == "uniforme":
            zona = random.choice(ZONAS)
        else:
            zona = generar_zona_zipf(alpha=1.5)
            
        query = random.choice(QUERIES)
        
        # CAMBIO CLAVE: Aumentamos la precisión a 3 decimales.
        # Esto genera miles de combinaciones únicas (ej: 0.123, 0.456...)
        # forzando a Redis a guardar muchísimas llaves distintas hasta llenarse.
        conf_min = round(random.uniform(0.0, 0.9), 3)
        
        url = f"{TARGET_URL}/{query}"
        params = {"zone_id": zona, "conf_min": conf_min}
        
        try:
            start_time = time.time()
            # Timeout de 35s porque el backend con 9.5M de filas puede ser lento en los MISS
            response = requests.get(url, params=params, timeout=35)
            latency = round((time.time() - start_time) * 1000, 2)
            
            if response.status_code == 200:
                source = response.json().get("source", "unknown")
                # Solo imprimimos cada 50 peticiones para no saturar la consola de Docker
                if (i + 1) % 50 == 0 or source == "generador (MISS)":
                    print(f"[{i+1}/{num_requests}] ✅ {query.upper()} | Zona: {zona} | {source} | Latencia: {latency}ms")
            else:
                print(f"[{i+1}/{num_requests}] ❌ Error {response.status_code} | {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"[{i+1}/{num_requests}] ⚠️ Error de conexión: {e}")
            
        # Delay pequeño para mantener throughput alto pero estable
        time.sleep(delay_ms / 1000.0)
        
    print(f"🏁 Simulación {distribucion.upper()} finalizada.\n")

def esperar_sistema():
    """
    Función de Health Check mejorada. 
    Espera hasta que el Generador de Respuestas responda OK.
    """
    print("⏳ Iniciando Health Check: Esperando carga de 9.5M de registros en el backend...")
    # Intentamos pegarle a la caché. Si el backend no está listo, la caché nos dará 503 o 504.
    url_test = f"{TARGET_URL}/q1?zone_id=Z1&conf_min=0.5"
    
    intentos = 0
    max_intentos = 60 # Esperará hasta 5 minutos (Pandas es lento cargando 9.5M)
    
    while intentos < max_intentos:
        try:
            response = requests.get(url_test, timeout=2)
            if response.status_code == 200:
                print("✅ ¡Sistema Distribuido totalmente operativo!")
                return True
        except:
            pass
        
        intentos += 1
        if intentos % 5 == 0:
            print(f"   ... todavía cargando (intento {intentos}/{max_intentos})...")
        time.sleep(5)
            
    print("⚠️ El sistema no respondió a tiempo, pero iniciaremos la simulación de todas formas.")
    return False

if __name__ == "__main__":
    # 1. Esperar a que el sistema esté listo (Warm-up)
    if esperar_sistema():
        print("🚀 Lanzando ráfaga de tráfico real...")
        
        # 2. Prueba Uniforme (Alta variabilidad para llenar la caché)
        print("--- PRUEBA 1: Distribución Uniforme ---")
        simular_trafico(distribucion="uniforme", num_requests=2500, delay_ms=10) 
        
        # 3. Prueba Zipf (Para ver cómo la política LRU/LFU protege lo más usado)
        print("--- PRUEBA 2: Distribución de Zipf ---")
        simular_trafico(distribucion="zipf", num_requests=2500, delay_ms=10)
    else:
        print("❌ Abortando simulación por falta de respuesta del backend.")