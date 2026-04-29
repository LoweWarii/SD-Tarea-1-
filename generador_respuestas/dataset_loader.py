import pandas as pd
import numpy as np

class ResponseGenerator:
    def __init__(self, dataset_path):
        # Aplicamos el límite de filas (nrows) para evitar el Out Of Memory en Docker.
        # Además, indicamos que el archivo viene comprimido en gzip.
        print(f"⏳ Cargando una fracción del dataset desde {dataset_path}...")
        self.df = pd.read_csv(dataset_path, compression='gzip', dtype={
    'latitude': 'float32',
    'longitude': 'float32',
    'area_in_meters': 'float32',
    'confidence': 'float32'
})
        print("✅ Dataset cargado exitosamente. ¡Listo para recibir consultas!")
        
        # Definición de zonas geográficas predefinidas
        self.zones = {
            "Z1": {"name": "Providencia", "bbox": (-33.445, -33.420, -70.640, -70.600)},
            "Z2": {"name": "Las Condes", "bbox": (-33.420, -33.390, -70.600, -70.550)},
            "Z3": {"name": "Maipú", "bbox": (-33.530, -33.490, -70.790, -70.740)},
            "Z4": {"name": "Santiago Centro", "bbox": (-33.460, -33.430, -70.670, -70.630)},
            "Z5": {"name": "Pudahuel", "bbox": (-33.470, -33.430, -70.810, -70.760)}
        }
        # Área de cada bounding box en km2 para Q3
        self.zone_areas_km2 = {z_id: 10.0 for z_id in self.zones} 

    def _filter_zone(self, zone_id, conf_min):
        lat_min, lat_max, lon_min, lon_max = self.zones[zone_id]["bbox"]
        return self.df[
            (self.df['latitude'].between(lat_min, lat_max)) &
            (self.df['longitude'].between(lon_min, lon_max)) &
            (self.df['confidence'] >= conf_min)
        ]

    # Q1: Conteo de edificios
    def q1_count(self, zone_id, conf_min=0.0):
        subset = self._filter_zone(zone_id, conf_min)
        return len(subset)

    # Q2: Área promedio y total
    def q2_area(self, zone_id, conf_min=0.0):
        subset = self._filter_zone(zone_id, conf_min)
        areas = subset['area_in_meters']
        return {
            "avg_area": float(areas.mean()) if not areas.empty else 0,
            "total_area": float(areas.sum()),
            "n": len(areas)
        }

    # Q3: Densidad de edificaciones por km2
    def q3_density(self, zone_id, conf_min=0.0):
        count = self.q1_count(zone_id, conf_min)
        return count / self.zone_areas_km2[zone_id]

    # Q4: Comparación de densidad entre dos zonas
    def q4_compare(self, zone_a, zone_b, conf_min=0.0):
        da = self.q3_density(zone_a, conf_min)
        db = self.q3_density(zone_b, conf_min)
        return {
            "zone_a": da, "zone_b": db,
            "winner": zone_a if da > db else zone_b
        }

    # Q5: Distribución de confianza
    def q5_confidence_dist(self, zone_id, bins=5):
        subset = self._filter_zone(zone_id, 0.0) 
        scores = subset['confidence']
        counts, edges = np.histogram(scores, bins=bins, range=(0, 1))
        return [
            {"bucket": i, "min": float(edges[i]), "max": float(edges[i+1]), "count": int(counts[i])}
            for i in range(bins)
        ]