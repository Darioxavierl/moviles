import numpy as np
import sys
sys.path.insert(0, '.')

from config.lte_params import LTEConfig
from core.modulator import OFDMModulator

def main():
    print("\n" + "="*60)
    print("  DEMOSTRACION: Mapeo de Recursos LTE v2.0")
    print("="*60)
    
    config = LTEConfig()
    print(f"\nConfiguracion:")
    print(f"  FFT Size:            {config.N}")
    print(f"  Subcarriers (Nc):    {config.Nc}")
    print(f"  CP Length:           {config.cp_length}")
    print(f"  Bandwidth:           {config.bandwidth} MHz")
    
    modulator = OFDMModulator(config, mode='lte')
    grid = modulator.resource_mapper.grid
    
    stats = grid.get_statistics()
    
    print(f"\nEstadisticas de Grid LTE:")
    print(f"  Total subcarriers:   {stats['total_subcarriers']}")
    print(f"  Datos:               {stats['data_subcarriers']}")
    print(f"  Pilotos:             {stats['pilot_subcarriers']}")
    print(f"  DC:                  {stats['dc_subcarriers']}")
    print(f"  Guardias:            {stats['guard_subcarriers']}")
    
    overhead = 100 * stats['pilot_subcarriers'] / stats['data_subcarriers']
    print(f"\nOverhead pilotos:      {overhead:.2f}%")
    
    bits = np.random.randint(0, 2, 100)
    signal, symbols, mapping_info = modulator.modulate(bits)
    
    print(f"\nModulacion:")
    print(f"  Bits entrada:        {len(bits)}")
    print(f"  Simbolos QAM:        {len(symbols)}")
    print(f"  Datos en grid:       {len(mapping_info['data_indices'])}")
    print(f"  Pilotos en grid:     {len(mapping_info['pilot_indices'])}")
    print(f"  Senial salida:       {signal.shape}")
    
    print(f"\n✓ Demostracion completada exitosamente")
    print("="*60 + "\n")

if __name__ == '__main__':
    main()
