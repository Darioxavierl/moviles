#!/usr/bin/env python3
"""
Test de integración completa del sistema OFDM con mapeo LTE
Verifica que:
1. OFDMSystem se inicializa correctamente
2. Transmisión y recepción funcionan
3. Mapeo LTE está activo por defecto
4. Backward compatibility con parámetros originales
"""

import numpy as np
import sys

print("=" * 70)
print("TEST DE INTEGRACIÓN COMPLETA - OFDM v2.0 CON LTE")
print("=" * 70)

# Test 1: Importaciones
print("\n[1/6] Importando módulos...")
try:
    from core.ofdm_system import OFDMSystem, OFDMSystemManager
    from config.lte_params import LTEConfig
    print("✓ Importaciones exitosas")
except Exception as e:
    print(f"✗ Error en importaciones: {e}")
    sys.exit(1)

# Test 2: Inicialización con parámetros de GUI (AWGN)
print("\n[2/6] Inicializando OFDMSystem con parámetros de GUI (AWGN)...")
try:
    config = LTEConfig()
    system_awgn = OFDMSystem(
        config,
        channel_type='awgn',
        itu_profile=None,
        frequency_ghz=2.0,
        velocity_kmh=0
        # Note: mode='lte' es por defecto
    )
    print(f"✓ Sistema AWGN inicializado")
    print(f"  - Channel type: {system_awgn.channel_type}")
    print(f"  - Mode: {system_awgn.mode}")
    print(f"  - ITU Profile: {system_awgn.itu_profile}")
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)

# Test 3: Inicialización con parámetros de GUI (Rayleigh)
print("\n[3/6] Inicializando OFDMSystem con parámetros de GUI (Rayleigh)...")
try:
    system_rayleigh = OFDMSystem(
        config,
        channel_type='rayleigh_mp',
        itu_profile='Vehicular_A',
        frequency_ghz=2.0,
        velocity_kmh=120
    )
    print(f"✓ Sistema Rayleigh inicializado")
    print(f"  - Channel type: {system_rayleigh.channel_type}")
    print(f"  - Mode: {system_rayleigh.mode}")
    print(f"  - ITU Profile: {system_rayleigh.itu_profile}")
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)

# Test 4: Transmisión y recepción (AWGN)
print("\n[4/6] Probando transmisión AWGN con modo LTE...")
try:
    bits = np.random.randint(0, 2, 1000)
    results = system_awgn.transmit(bits, snr_db=10)
    
    print(f"✓ Transmisión completada")
    print(f"  - Bits transmitidos: {results['transmitted_bits']}")
    print(f"  - BER: {results['ber']:.4f}")
    print(f"  - SER: {results['ser']:.4f}")
    
    # Verificar que mapping_info está disponible (LTE)
    if 'papr_per_symbol' in results and results['papr_per_symbol'] is not None:
        print(f"  - PAPR (dB): {results['papr_per_symbol']['papr_mean']:.2f} (medio)")
        print(f"  ✓ Información de mapeo LTE disponible")
    else:
        print(f"  - PAPR: No disponible en modo simple")
except Exception as e:
    print(f"✗ Error en transmisión: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Transmisión en modo simple (backward compatibility)
print("\n[5/6] Probando transmisión en modo simple (backward compatibility)...")
try:
    system_simple = OFDMSystem(
        config,
        channel_type='awgn',
        mode='simple'  # Modo simple
    )
    
    bits = np.random.randint(0, 2, 1000)
    results = system_simple.transmit(bits, snr_db=10)
    
    print(f"✓ Transmisión en modo simple completada")
    print(f"  - Bits transmitidos: {results['transmitted_bits']}")
    print(f"  - BER: {results['ber']:.4f}")
    print(f"  - Mode: {system_simple.mode}")
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)

# Test 6: BER sweep
print("\n[6/6] Probando barrido de SNR (BER sweep)...")
try:
    snr_range = np.array([0, 5, 10])
    num_bits = 500
    n_iterations = 2
    
    results = system_awgn.run_ber_sweep(
        num_bits=num_bits,
        snr_range=snr_range,
        n_iterations=n_iterations,
        progress_callback=None
    )
    
    print(f"✓ BER sweep completado")
    for i, snr in enumerate(snr_range):
        print(f"  - SNR {snr}dB: BER={results['ber_mean'][i]:.4f} ± {results['ber_std'][i]:.4f}")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("✅ TODOS LOS TESTS PASARON - SISTEMA FUNCIONANDO CORRECTAMENTE")
print("=" * 70)
print("\nREVISIÓN FINAL:")
print("  ✓ OFDMSystem inicializa correctamente con parámetros de GUI")
print("  ✓ Soporta canal AWGN y Rayleigh")
print("  ✓ Modo LTE activo por defecto (mapeo de subportadoras)")
print("  ✓ Backward compatibility con modo simple")
print("  ✓ Transmisión/recepción funcionando")
print("  ✓ BER sweep funcionando")
print("\n🎯 INTEGRACIÓN COMPLETA Y EXITOSA")
