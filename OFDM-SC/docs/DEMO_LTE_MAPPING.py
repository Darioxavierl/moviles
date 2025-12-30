"""
Demostración Visual del Mapeo LTE
==================================

Este script visualiza:
1. Distribución de subportadoras (datos, pilotos, DC, guardias)
2. Patrón de pilotos
3. Proceso de modulación LTE
"""

import numpy as np
from config.lte_params import LTEConfig
from core.modulator import OFDMModulator


def print_grid_visual(mapper, title="Grid LTE"):
    """Imprime visualización ASCII de la grid"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")
    
    grid = mapper.resource_mapper.grid
    
    # Crear representación visual
    visual = []
    for k in range(grid.N):
        sc_type = grid.get_subcarrier_type(k)
        
        if sc_type == 'data':
            symbol = '█'  # Datos
        elif sc_type == 'pilot':
            symbol = 'P'  # Pilots
        elif sc_type == 'dc':
            symbol = 'D'  # DC
        else:  # guard
            symbol = '·'  # Guard
        
        visual.append(symbol)
    
    # Imprimir en líneas de 50 caracteres
    line_length = 50
    for i in range(0, len(visual), line_length):
        line = ''.join(visual[i:i+line_length])
        start_idx = i
        end_idx = min(i + line_length - 1, len(visual) - 1)
        print(f"[{start_idx:3d}-{end_idx:3d}] {line}")
    
    print(f"\nLeyenda: █=Datos, P=Piloto, D=DC, ·=Guardia\n")


def print_statistics(mapper):
    """Imprime estadísticas detalladas"""
    stats = mapper.resource_mapper.get_statistics()
    
    print(f"\n{'='*60}")
    print(f"  Estadísticas de Grid LTE")
    print(f"{'='*60}\n")
    
    print(f"Total de subportadoras (N):        {stats['total_subcarriers']:4d}")
    print(f"Subportadoras útiles (Nc):        {stats['useful_subcarriers']:4d}")
    print(f"  ├─ Datos (Nc):                  {stats['data_subcarriers']:4d} ({100*stats['data_subcarriers']/stats['useful_subcarriers']:.1f}%)")
    print(f"  ├─ Pilotos:                     {stats['pilot_subcarriers']:4d} ({100*stats['pilot_subcarriers']/stats['useful_subcarriers']:.1f}%)")
    print(f"  └─ DC:                          {stats['dc_subcarriers']:4d} ({100*stats['dc_subcarriers']/stats['useful_subcarriers']:.1f}%)")
    print(f"Guardias:                         {stats['guard_subcarriers']:4d} ({100*stats['guard_subcarriers']/stats['total_subcarriers']:.1f}%)")
    print(f"  ├─ Izquierda:                   {stats['guard_left']:4d}")
    print(f"  └─ Derecha:                     {stats['guard_right']:4d}")
    print(f"Espaciado de pilotos:             {stats['pilot_spacing']:4d} subportadoras")
    
    # Overhead
    overhead = 100 * stats['pilot_subcarriers'] / stats['data_subcarriers']
    print(f"\nOverhead de pilotos:               {overhead:.2f}%")
    print(f"Eficiencia espectral:             {100*stats['data_subcarriers']/stats['total_subcarriers']:.2f}%\n")


def print_pilot_pattern(mapper):
    """Imprime patrón de pilotos"""
    grid = mapper.resource_mapper.grid
    pilot_idx = grid.get_pilot_indices()
    
    print(f"\n{'='*60}")
    print(f"  Patrón de Pilotos LTE")
    print(f"{'='*60}\n")
    
    print(f"Posiciones de pilotos ({len(pilot_idx)} total):")
    print(f"Índices: {', '.join([str(i) for i in pilot_idx[:10]])}")
    print(f"         ... (mostrando primeros 10 de {len(pilot_idx)})")
    
    # Verificar espaciado
    spacings = np.diff(pilot_idx)
    print(f"\nEspaciado entre pilotos:")
    print(f"  Mínimo:  {np.min(spacings)} subportadoras")
    print(f"  Máximo:  {np.max(spacings)} subportadoras")
    print(f"  Promedio: {np.mean(spacings):.1f} subportadoras")
    
    # Todos deberían ser 6
    if np.all(spacings == 6):
        print(f"  ✓ Espaciado perfectamente regular (cada 6)\n")
    else:
        print(f"  ✗ Espaciado irregular\n")


def compare_modes():
    """Compara modo LTE vs Simple"""
    config = LTEConfig()
    
    print(f"\n{'='*60}")
    print(f"  Comparación: Modo LTE vs Simple")
    print(f"{'='*60}\n")
    
    # Generar bits de prueba
    bits = np.random.randint(0, 2, 100)
    
    # Modo LTE
    modulator_lte = OFDMModulator(config, mode='lte')
    signal_lte, symbols_lte, mapping_lte = modulator_lte.modulate(bits)
    
    # Modo Simple
    modulator_simple = OFDMModulator(config, mode='simple')
    signal_simple, symbols_simple, mapping_simple = modulator_simple.modulate(bits)
    
    print("MODO LTE:")
    print(f"  Señal shape:        {signal_lte.shape}")
    print(f"  Símbolos QAM:       {len(symbols_lte)}")
    print(f"  Mapping info:       {'Sí' if mapping_lte is not None else 'No'}")
    if mapping_lte is not None:
        print(f"    ├─ Datos:        {len(mapping_lte['data_indices'])}")
        print(f"    ├─ Pilotos:      {len(mapping_lte['pilot_indices'])}")
        print(f"    └─ Guardias:     {len(mapping_lte['guard_indices'])}")
    
    print(f"\nMODO SIMPLE:")
    print(f"  Señal shape:        {signal_simple.shape}")
    print(f"  Símbolos QAM:       {len(symbols_simple)}")
    print(f"  Mapping info:       {'Sí' if mapping_simple is not None else 'No'}")
    
    print(f"\nSímbolos QAM idénticos:")
    print(f"  ✓ Sí" if np.allclose(symbols_lte, symbols_simple) else f"  ✗ No")
    
    print(f"\nPotencia de señales:")
    print(f"  LTE:    {np.mean(np.abs(signal_lte)**2):.4f}")
    print(f"  Simple: {np.mean(np.abs(signal_simple)**2):.4f}\n")


def main():
    """Ejecuta demostración completa"""
    
    print("\n" + "="*60)
    print("  DEMOSTRACIÓN: Mapeo de Recursos LTE v2.0")
    print("="*60)
    
    # Configurar
    config = LTEConfig()
    print(f"\nConfiguración:")
    print(f"  FFT Size:            {config.N}")
    print(f"  Subcarriers (Nc):    {config.Nc}")
    print(f"  CP Length:           {config.cp_length}")
    print(f"  Modulation:          {config.modulation}")
    print(f"  Bandwidth:           {config.bandwidth} MHz")
    
    # Crear modulador LTE
    modulator = OFDMModulator(config, mode='lte')
    
    # Mostrar visualización
    print_grid_visual(modulator, "Distribución de Subportadoras")
    print_statistics(modulator)
    print_pilot_pattern(modulator)
    
    # Comparar modos
    compare_modes()
    
    # Modulación completa
    print(f"\n{'='*60}")
    print(f"  Ejemplo de Modulación Completa")
    print(f"{'='*60}\n")
    
    # Generar bits
    num_bits = 498  # 249 datos * 2 bits (QPSK)
    bits = np.random.randint(0, 2, num_bits)
    
    print(f"Entrada:")
    print(f"  Bits:                {len(bits)} ({bits[:20]}...)")
    print(f"  Símbolos esperados:  {len(bits) // config.bits_per_symbol}")
    
    # Modular
    signal, symbols, mapping_info = modulator.modulate(bits)
    
    print(f"\nProceso:")
    print(f"  1. Bits → QAM:       {len(bits)} bits → {len(symbols)} símbolos")
    print(f"  2. Mapeo LTE:        {len(symbols)} datos + {len(mapping_info['pilot_indices'])} pilotos")
    print(f"  3. IFFT (512):       512 subcarriers → 512 time samples")
    print(f"  4. CP (+128):        512 + 128 = 640 samples")
    
    print(f"\nSalida:")
    print(f"  Señal shape:         {signal.shape}")
    print(f"  Potencia (dB):       {10*np.log10(np.mean(np.abs(signal)**2)):.2f} dB")
    print(f"  Peak (dB):           {10*np.log10(np.max(np.abs(signal)**2)):.2f} dB")
    print(f"  PAPR:                {np.max(np.abs(signal)**2)/np.mean(np.abs(signal)**2):.2f}")
    
    print(f"\nMapping info disponible para receptor:")
    print(f"  ✓ data_indices:      Posiciones de datos")
    print(f"  ✓ pilot_indices:     Posiciones de pilotos")
    print(f"  ✓ guard_indices:     Posiciones de guardias")
    print(f"  ✓ stats:             Estadísticas del mapeo")
    
    print(f"\n{'='*60}")
    print(f"  ✅ Demostración Completada")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
