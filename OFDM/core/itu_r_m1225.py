import json
import os
import numpy as np

class ITU_R_M1225:
    def __init__(self, json_path="itu_r_m1225_channels.json"):
        if not os.path.exists(json_path):
            raise FileNotFoundError(f"No se encontró el archivo: {json_path}")
        with open(json_path, "r", encoding="utf-8") as f:
            self.channels = json.load(f)

    def get_models(self):
        """Devuelve la lista de modelos disponibles."""
        return list(self.channels.keys())

    def get_info(self, model_name):
        """Devuelve toda la información del modelo especificado."""
        model = self.channels.get(model_name)
        if model is None:
            raise ValueError(f"Modelo '{model_name}' no encontrado.")
        return model

    def get_delays_and_gains(self, model_name):
        """Devuelve las listas de retardos (en segundos) y ganancias (en dB)."""
        model = self.get_info(model_name)
        delays = [d * 1e-6 for d in model["delays_us"]]  # pasa a segundos
        gains = model["gains_dB"]
        return delays, gains

    def describe(self, model_name):
        """Muestra una descripción formateada del modelo."""
        model = self.get_info(model_name)
        print(f"\n📡 Modelo ITU-R M.1225: {model_name}")
        print(f"Descripción: {model['description']}")
        print(f"Velocidad típica: {model['velocity_kmh']} km/h")
        print(f"Frecuencia típica: {model['frequency_GHz']} GHz")
        print(f"Retardos (µs): {model['delays_us']}")
        print(f"Ganancias (dB): {model['gains_dB']}")
        print("-" * 50)

    def get_recommended_frequencies(self, model_name, n=3):
        """
        Devuelve una lista de 'n' frecuencias en Hz dentro del rango recomendado.
        Si el modelo tiene una sola frecuencia, se repite ese valor 'n' veces.
        """
        model = self.get_info(model_name)
        freq_field = model["frequency_GHz"]

        # Si tiene rango (e.g. "0.9-2")
        if "-" in freq_field:
            fmin, fmax = map(float, freq_field.split("-"))
            freqs = np.linspace(fmin, fmax, n)
        else:
            # Solo una frecuencia
            f = float(freq_field)
            freqs = np.full(n, f)

        # Devuelve en Hz
        return freqs * 1e9
    
    def get_example_velocities(self, model_name, n=3):
        """
        Devuelve una lista de 'n' velocidades dentro del rango recomendado.
        """
        model = self.get_info(model_name)
        vel_field = model["velocity_kmh"]

        if "-" in vel_field:
            vmin, vmax = map(float, vel_field.split("-"))
            vels = np.linspace(vmin, vmax, n)
            return vels/3.6 # Devuelve en m/s
