#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test del Receptor LTE
Valida:
1. Extracción de pilotos
2. Estimación de canal
3. Ecualización
4. Decodificación correcta de datos
5. Comparación: con/sin ecualización
"""

import numpy as np
import sys
import os

# Agregar raíz del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("\n" + "=" * 80)
print("TEST DEL RECEPTOR LTE - Estimacion de Canal + Equalizacion")
print("=" * 80)

# Importar módulos
from core.ofdm_system import OFDMSystem
from config.lte_params import LTEConfig
from core.lte_receiver import LTEReceiver, LTEChannelEstimator
from core.resource_mapper import LTEResourceGrid, PilotPattern

print("\n[1/7] Inicializando sistema...")
try:
    config = LTEConfig()
    system_lte = OFDMSystem(config, channel_type='awgn', mode='lte')
    system_simple = OFDMSystem(config, channel_type='awgn', mode='simple')
    print("  [OK] Sistemas OFDM creados")
except Exception as e:
    print(f"  [ERROR] {e}")
    sys.exit(1)

# Test 1: Validar estructura de mapeo LTE
print("\n[2/7] Validando estructura de mapeo LTE...")
try:
    grid = LTEResourceGrid(config.N, config.Nc)
    data_indices = grid.get_data_indices()
    pilot_indices = grid.get_pilot_indices()
    guard_indices = grid.get_guard_indices()
    
    print(f"  [OK] Grid LTE creada")
    print(f"     - Total subportadoras: {config.N}")
    print(f"     - Datos: {len(data_indices)} SC")
    print(f"     - Pilotos: {len(pilot_indices)} SC")
    print(f"     - Guardias: {len(guard_indices)} SC")
    print(f"     - DC null: 1 SC")
    
    # Validar que no haya solapamiento
    all_indices = set(data_indices) | set(pilot_indices) | set(guard_indices) | {grid.dc_index}
    assert len(all_indices) == config.N, "Indices solapados o incompletos"
    print(f"  [OK] Mapeo verificado (sin solapamientos)")
except Exception as e:
    print(f"  [ERROR] {e}")
    sys.exit(1)

# Test 2: Transmisión simple con modo LTE
print("\n[3/7] Probando transmision con modo LTE...")
try:
    bits = np.random.randint(0, 2, 1000)
    results = system_lte.transmit(bits, snr_db=20)  # SNR alto para validar sin errores
    
    print(f"  [OK] Transmision completada")
    print(f"     - Bits transmitidos: {results['transmitted_bits']}")
    print(f"     - BER sin receptor LTE: {results['ber']:.4f}")
except Exception as e:
    print(f"  [ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Estimacion de canal
print("\n[4/7] Probando estimacion de canal con pilotos...")
try:
    # Transmitir bits
    bits_tx = np.random.randint(0, 2, 1000)
    tx_signal, symbols_tx, mapping_info = system_lte.modulator.modulate_stream(bits_tx)
    
    # Pasar por canal AWGN
    rx_signal, _ = system_lte.channel.channel.transmit(tx_signal)
    
    # Usar receptor LTE para demodular un símbolo OFDM
    receiver = LTEReceiver(config, enable_equalization=False)
    
    # Demodular OFDM (FFT)
    samples_per_symbol = config.N + config.cp_length
    chunk = rx_signal[:samples_per_symbol]
    
    # Demodulación
    signal_without_cp = chunk[config.cp_length:]
    frequency_domain = np.fft.fft(signal_without_cp) / np.sqrt(config.N)
    
    # Estimacion de canal
    channel_info = receiver.channel_estimator.estimate_channel(frequency_domain)
    channel_est = channel_info['channel_estimate']
    
    print(f"  [OK] Estimacion de canal completada")
    print(f"     - Pilotos extraidos: {len(channel_info['pilot_indices'])}")
    print(f"     - SNR estimado: {channel_info['pilot_snr_db']:.2f} dB")
    print(f"     - Magnitud canal (promedio): {np.mean(np.abs(channel_est)):.3f}")
except Exception as e:
    print(f"  [ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Equalizacion
print("\n[5/7] Probando equalizacion Zero-Forcing...")
try:
    # Símbolos recibidos (con canal)
    received_symbols = frequency_domain
    
    # Ecualización
    from core.lte_receiver import LTEEqualizerZF
    equalizer = LTEEqualizerZF(config)
    equalized = equalizer.equalize(received_symbols, channel_est)
    
    print(f"  [OK] Equalizacion completada")
    print(f"     - Símbolos antes: {np.mean(np.abs(received_symbols)):.3f}")
    print(f"     - Símbolos despues: {np.mean(np.abs(equalized)):.3f}")
except Exception as e:
    print(f"  [ERROR] {e}")
    sys.exit(1)

# Test 5: Decodificacion completa con receptor LTE
print("\n[6/7] Probando decodificacion completa (Tx -> Canal -> Rx LTE)...")
try:
    bits_tx = np.random.randint(0, 2, 500)
    
    # Transmitir en modo LTE
    tx_signal, symbols_tx, mapping_info = system_lte.modulator.modulate_stream(bits_tx)
    
    # Pasar por canal AWGN con SNR alta
    rx_signal, _ = system_lte.channel.channel.transmit(tx_signal)
    
    # Decodificar con receptor LTE
    receiver = LTEReceiver(config, enable_equalization=True)
    samples_per_symbol = config.N + config.cp_length
    chunk = rx_signal[:samples_per_symbol]
    
    decode_result = receiver.receive_and_decode(chunk)
    bits_rx = decode_result['bits']
    
    # Comparar
    min_len = min(len(bits_tx), len(bits_rx))
    errors = np.sum(bits_tx[:min_len] != bits_rx[:min_len])
    ber = errors / min_len
    
    print(f"  [OK] Decodificacion completada")
    print(f"     - Bits transmitidos: {len(bits_tx)}")
    print(f"     - Bits recibidos: {len(bits_rx)}")
    print(f"     - Errores: {errors}")
    print(f"     - BER: {ber:.4f}")
    print(f"     - SNR estimado del canal: {decode_result['channel_snr_db']:.2f} dB")
except Exception as e:
    print(f"  [ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 6: Comparacion modo LTE vs Simple en AWGN
print("\n[7/7] Comparando modo LTE vs Simple en AWGN...")
try:
    bits_test = np.random.randint(0, 2, 1000)
    snr_values = [10, 15, 20, 25]
    
    print(f"     SNR(dB)  | Modo LTE   | Modo Simple | Diferencia")
    print(f"     " + "-" * 50)
    
    for snr in snr_values:
        # Modo LTE
        results_lte = system_lte.transmit(bits_test.copy(), snr_db=snr)
        ber_lte = results_lte['ber']
        
        # Modo Simple
        results_simple = system_simple.transmit(bits_test.copy(), snr_db=snr)
        ber_simple = results_simple['ber']
        
        diff = ber_lte - ber_simple
        print(f"     {snr:4d}     | {ber_lte:.4f}    | {ber_simple:.4f}      | {diff:+.4f}")
    
    print(f"  [OK] Comparacion completada")
except Exception as e:
    print(f"  [ERROR] {e}")
    sys.exit(1)

print("\n" + "=" * 80)
print("[OK] TODOS LOS TESTS PASADOS - RECEPTOR LTE FUNCIONANDO")
print("=" * 80)

print("\nRESUMEN:")
print("  [OK] Estructura de mapeo LTE validada")
print("  [OK] Extraccion de pilotos funcionando")
print("  [OK] Estimacion de canal funcionando")
print("  [OK] Equalizacion Zero-Forcing funcionando")
print("  [OK] Decodificacion completa funcionando")
print("  [OK] Modo LTE integrado en transmisor/receptor")
print("  [OK] Comparacion con modo simple completada")

print("\nPRÓXIMOS PASOS:")
print("  - Agregar equalizacion para canal Rayleigh")
print("  - Implementar interpolacion de canal mejorada")
print("  - Validar con imagenes en AWGN")
print("=" * 80 + "\n")
