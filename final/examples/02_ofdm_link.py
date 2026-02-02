import os
if os.getenv("CUDA_VISIBLE_DEVICES") is None:
    gpu_num = 0 # Use "" to use the CPU
    os.environ["CUDA_VISIBLE_DEVICES"] = f"{gpu_num}"
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# Import Sionna
import sionna
from sionna.phy.mapping import BinarySource, Constellation, Mapper
from sionna.phy.channel import AWGN
from sionna.phy.utils import ebnodb2no
import matplotlib.pyplot as plt
import numpy as np

print("📡 OFDM Link Simulation - Sionna", sionna.__version__)
print("="*50)

# Generar símbolos binarios
batch_size = 1000
num_bits_per_symbol = 4  # 16-QAM
binary_source = BinarySource()
b = binary_source([batch_size, num_bits_per_symbol])
print(f"✅ Generados {batch_size} símbolos binarios ({num_bits_per_symbol} bits/símbolo)")

# Crear constelación 16-QAM
constellation = Constellation("qam", num_bits_per_symbol)
print(f"✅ Constelación 16-QAM creada")

# Mapear bits a símbolos
mapper = Mapper(constellation=constellation)
x = mapper(b)
print(f"✅ Símbolos mapeados: {x.shape}")

# Agregar ruido AWGN
awgn = AWGN()
ebno_db = 15  # Eb/No deseado en dB
no = ebnodb2no(ebno_db, num_bits_per_symbol, coderate=1)
y = awgn(x, no)
print(f"✅ Canal AWGN aplicado (Eb/No = {ebno_db} dB)")

# Visualizar señal recibida
print("\n📊 Generando gráfico de constelación recibida...")
fig = plt.figure(figsize=(8, 8))
ax = fig.add_subplot(111)
plt.scatter(np.real(y), np.imag(y), alpha=0.5, s=10)
ax.set_aspect("equal", adjustable="box")
plt.xlabel("Parte Real")
plt.ylabel("Parte Imaginaria")
plt.grid(True, which="both", axis="both", alpha=0.3)
plt.title(f"Símbolos Recibidos (16-QAM, Eb/No = {ebno_db} dB)")
plt.tight_layout()
plt.savefig('./tmp/ofdm_constellation.png', dpi=150, bbox_inches='tight')
print("✅ Gráfico guardado en /tmp/ofdm_constellation.png")
plt.close()
print("="*50)
