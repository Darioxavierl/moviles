import tensorflow as tf
import sionna
import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Silenciar logs menores de TF

print("\n" + "="*60)
print("🔍 DIAGNÓSTICO DE SISTEMA SIONNA")
print("="*60)

# 1. Verificar GPU
gpus = tf.config.list_physical_devices('GPU')
if gpus:
    print(f"GPU DETECTADA: {len(gpus)} dispositivo(s)")
    details = tf.config.experimental.get_device_details(gpus[0])
    print(f"   Nombre: {details.get('device_name', 'Desconocido')}")
    print(f"   Compute Capability: {details.get('compute_capability', 'N/A')}")
else:
    print("ERROR CRÍTICO: No se detecta GPU. Sionna será muy lento.")

# 2. Verificar XLA (Aceleración de compilación)
print("\nProbando compilación XLA (jit_compile)...")
try:
    @tf.function(jit_compile=True)
    def test_xla(x, y):
        return tf.matmul(x, y)

    a = tf.random.normal((100, 100))
    b = tf.random.normal((100, 100))
    # Primera ejecución (compilación)
    _ = test_xla(a, b)
    # Segunda ejecución (caché)
    _ = test_xla(a, b)
    print("XLA Funciona correctamente (Tu GPU está procesando grafos optimizados).")
except Exception as e:
    print(f"Error en XLA: {e}")

# 3. Versiones
print(f"\nVersiones:")
print(f"   TensorFlow: {tf.__version__}")
print(f"   Sionna:     {sionna.__version__}")
print("="*60 + "\n")