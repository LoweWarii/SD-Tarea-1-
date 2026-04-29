from fastapi import FastAPI, HTTPException
from dataset_loader import ResponseGenerator

app = FastAPI(title="Generador de Respuestas API")

# Ruta del dataset dentro del contenedor Docker (lo configuraremos en el Paso 5)
# Si vas a probar localmente antes de usar Docker, cambia esto a "../data/santiago.csv.gz"
DATASET_PATH = "/app/data/santiago.csv.gz"

# Precarga de datos al iniciar el sistema
print("⏳ Iniciando precarga de datos geoespaciales...")
try:
    generador = ResponseGenerator(DATASET_PATH)
    print(f"✅ Datos cargados correctamente. Registros: {len(generador.df)}")
except Exception as e:
    print(f"❌ Error crítico cargando dataset: {e}")
    generador = None

@app.get("/q1")
def q1_endpoint(zone_id: str, conf_min: float = 0.0):
    if not generador:
        raise HTTPException(status_code=500, detail="El dataset no se cargó correctamente.")
    try:
        resultado = generador.q1_count(zone_id, conf_min)
        # Devolvemos un diccionario para que FastAPI lo convierta a JSON
        return {"resultado": resultado}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/q2")
def q2_endpoint(zone_id: str, conf_min: float = 0.0):
    if not generador:
        raise HTTPException(status_code=500, detail="El dataset no se cargó correctamente.")
    try:
        return generador.q2_area(zone_id, conf_min)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/q3")
def q3_endpoint(zone_id: str, conf_min: float = 0.0):
    if not generador:
        raise HTTPException(status_code=500, detail="El dataset no se cargó correctamente.")
    try:
        return {"densidad": generador.q3_density(zone_id, conf_min)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/q4")
def q4_endpoint(zone_a: str, zone_b: str, conf_min: float = 0.0):
    if not generador:
        raise HTTPException(status_code=500, detail="El dataset no se cargó correctamente.")
    try:
        return generador.q4_compare(zone_a, zone_b, conf_min)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/q5")
def q5_endpoint(zone_id: str, bins: int = 5):
    if not generador:
        raise HTTPException(status_code=500, detail="El dataset no se cargó correctamente.")
    try:
        return generador.q5_confidence_dist(zone_id, bins)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))