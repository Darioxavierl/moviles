"""
Test rápido del barrido SNR con progreso - verificar que no se cuelga
"""
import numpy as np
from core.ofdm_system import OFDMSystem
from config.lte_params import LTEConfig
from utils.image_processing import ImageProcessor
import time

print("=== TEST: BARRIDO SNR CON PROGRESO ===\n")

# Crear sistema
config = LTEConfig(5.0, 15.0, 'QPSK', 'normal')
system = OFDMSystem(config)

# Cargar imagen
print("Cargando imagen...")
bits, metadata = ImageProcessor.image_to_bits('entre-ciel-et-terre.jpg')
print(f"Imagen cargada: {metadata['width']}x{metadata['height']}")
print(f"Bits de imagen: {len(bits)}\n")

# Callback de progreso
def progress_callback(progress, message):
    print(f"[{progress:3d}%] {message}")

# Realizar barrido SNR con pocas iteraciones
print("Iniciando barrido SNR (0-10 dB, paso 5)...\n")
start_time = time.time()

snr_range = np.array([0, 5, 10])
all_results = system.run_ber_sweep_all_modulations(
    num_bits=len(bits),
    snr_range=snr_range,
    n_iterations=2,  # Solo 2 iteraciones para test rápido
    progress_callback=progress_callback,
    bits=bits
)

elapsed = time.time() - start_time
print(f"\n✓ Barrido completado en {elapsed:.2f} segundos")

# Mostrar resultados
print("\nResultados por modulación:")
print("="*60)
for modulation in ['QPSK', '16-QAM', '64-QAM']:
    if modulation not in all_results:
        continue
    
    results = all_results[modulation]
    print(f"\n{modulation}:")
    
    for snr, ber_mean in zip(results['snr_db'], results['ber_mean']):
        print(f"  SNR {snr:5.1f} dB: BER = {ber_mean:.6e}")

print("\n✓ TEST COMPLETADO SIN CUELGUES")
