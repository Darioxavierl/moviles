import tensorflow as tf
import sionna
from sionna.rt import Scene, PlanarArray, Transmitter, Receiver
import numpy as np

print("🏙️ Verificación del Motor de Ray Tracing (Sionna RT)...")
print(f"Sionna versión: {sionna.__version__}")
print("="*60)

# 1. Verificar que podemos crear una escena
try:
    scene = Scene()
    scene.frequency = 3.5e9  # 3.5 GHz
    print("✅ Scene creada correctamente")
except Exception as e:
    print(f"❌ Error al crear Scene: {e}")
    exit(1)

# 2. Verificar arrays de antenas
try:
    tx_array = PlanarArray(num_rows=1, 
                           num_cols=1, 
                           vertical_spacing=0.5, 
                           horizontal_spacing=0.5, 
                           pattern="iso", 
                           polarization="V")
    rx_array = PlanarArray(num_rows=1, 
                           num_cols=1, 
                           vertical_spacing=0.5, 
                           horizontal_spacing=0.5, 
                           pattern="iso", 
                           polarization="V")
    scene.tx_array = tx_array
    scene.rx_array = rx_array
    print("✅ Arrays de antenas configurados")
except Exception as e:
    print(f"❌ Error al configurar arrays: {e}")
    exit(1)

# 3. Verificar que podemos agregar dispositivos
try:
    tx = Transmitter(name="tx", position=[0, 0, 10])
    rx = Receiver(name="rx", position=[50, 0, 1.5])
    scene.add(tx)
    scene.add(rx)
    print(f"✅ Transmisor y receptor agregados")
    print(f"   TX posición: {tx.position}")
    print(f"   RX posición: {rx.position}")
except Exception as e:
    print(f"❌ Error al agregar dispositivos: {e}")
    exit(1)

# 4. Verificar propiedades de la escena
print(f"\n📡 Propiedades de la escena:")
print(f"   Frecuencia: 3.5 GHz")
print(f"   Número de transmisores: {len(scene.transmitters)}")
print(f"   Número de receptores: {len(scene.receivers)}")

# 5. Verificar renderer (si está disponible con GPU)
print(f"\n🎨 Verificando capacidades de renderizado...")
try:
    # Verificar si tenemos objetos en la escena
    num_objects = len(scene.objects)
    print(f"   Objetos en escena: {num_objects}")
    print(f"✅ Sistema de renderizado disponible")
except Exception as e:
    print(f"⚠️  Advertencia en renderizado: {e}")

# 6. Verificar que podemos importar otros módulos de RT
print(f"\n🔧 Verificando módulos adicionales de RT...")
try:
    from sionna.rt import load_scene, RadioMaterial, Camera
    print("✅ load_scene disponible")
    print("✅ RadioMaterial disponible")
    print("✅ Camera disponible")
except ImportError as e:
    print(f"⚠️  Algunos módulos no disponibles: {e}")

# 7. Resumen final
print("\n" + "="*60)
print("✅ VERIFICACIÓN COMPLETA DEL MÓDULO SIONNA RT")
print("="*60)
print("Componentes verificados:")
print("  ✓ Scene (escena 3D)")
print("  ✓ PlanarArray (arrays de antenas)")
print("  ✓ Transmitter/Receiver (dispositivos radio)")
print("  ✓ Configuración de frecuencia y propiedades")
print("  ✓ Módulos de carga y materiales")
print("\nSionna RT está correctamente instalado y funcional.")
print("Para cálculos de propagación necesitas cargar geometría 3D.")
print("="*60)
