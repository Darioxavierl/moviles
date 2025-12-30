"""
Tests para ResourceMapper - Validar mapeo LTE

Verifica:
- Correcta clasificación de subportadoras
- Mapeo correcto de datos y pilotos
- Cumplimiento con estándar LTE
- Simetría de guardias
- Posición correcta de DC
"""

import numpy as np
import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.resource_mapper import LTEResourceGrid, ResourceMapper, PilotPattern
from core.modulator import QAMModulator
from config.lte_params import LTEConfig


class TestLTEResourceGrid:
    """Tests para la grid de recursos LTE"""
    
    def setup_method(self):
        """Setup antes de cada test"""
        self.grid = LTEResourceGrid(N=512, Nc=300)
    
    def test_grid_initialization(self):
        """Test inicialización de grid"""
        assert self.grid.N == 512
        assert self.grid.Nc == 300
        assert self.grid.dc_index == 256  # N/2
        print(f"✓ Grid inicializada correctamente")
    
    def test_guard_bands_symmetric(self):
        """Test que guardias son simétricos"""
        total_guard = self.grid.num_guard_left + self.grid.num_guard_right + 1  # +1 DC
        expected_guard = 512 - 300
        # DC es parte de los nulls, así que total_guard = guardias + DC
        actual_guard = self.grid.num_guard_left + self.grid.num_guard_right
        
        assert actual_guard == expected_guard
        # Verificar simetría aproximada
        assert abs(self.grid.num_guard_left - self.grid.num_guard_right) <= 1
        print(f"✓ Guard bands simétricos: {self.grid.num_guard_left} | {self.grid.num_guard_right}")
    
    def test_dc_in_center(self):
        """Test que DC está en el centro"""
        assert self.grid.dc_index == self.grid.N // 2
        assert self.grid.get_subcarrier_type(self.grid.dc_index) == 'dc'
        print(f"✓ DC en posición correcta: k={self.grid.dc_index}")
    
    def test_subcarrier_classification(self):
        """Test clasificación de subportadoras"""
        types_count = {}
        for k in range(self.grid.N):
            sc_type = self.grid.get_subcarrier_type(k)
            types_count[sc_type] = types_count.get(sc_type, 0) + 1

        print(f"\nClasificación de subportadoras:")
        for sc_type, count in sorted(types_count.items()):
            print(f"  {sc_type}: {count}")

        assert types_count['dc'] == 1
        # Total útil: datos + pilotos (los pilotos reemplazan datos)
        assert types_count['data'] + types_count['pilot'] == 299  # 300 - 1 (DC)
        assert types_count['guard'] == 212  # N - Nc - 1 (DC)
        # Verificar que hay exactamente 50 pilotos (cada 6 subportadoras en 300 útiles)
        assert types_count['pilot'] == 50

    def test_pilot_spacing(self):
        """Test espaciado de pilotos"""
        pilot_indices = self.grid.get_pilot_indices()
        
        # Verificar que pilotos están espaciados cada 6 subportadoras
        # (dentro del rango útil)
        useful_start = self.grid.num_guard_left
        useful_end = self.grid.N - self.grid.num_guard_right
        
        for k in pilot_indices:
            relative_pos = k - useful_start
            expected_offset = self.grid.pilot_spacing // 2
            assert relative_pos % self.grid.pilot_spacing == expected_offset
        
        print(f"✓ Pilotos espaciados correctamente cada {self.grid.pilot_spacing} subportadoras")
    
    def test_no_overlap_between_types(self):
        """Test que no hay solapamiento entre tipos"""
        data = set(self.grid.get_data_indices())
        pilots = set(self.grid.get_pilot_indices())
        guards = set(self.grid.get_guard_indices())
        dc = {self.grid.dc_index}
        
        # Verificar que no hay intersecciones
        assert len(data & pilots) == 0
        assert len(data & guards) == 0
        assert len(data & dc) == 0
        assert len(pilots & guards) == 0
        assert len(pilots & dc) == 0
        assert len(guards & dc) == 0
        
        print(f"✓ No hay solapamiento entre tipos de subportadoras")
    
    def test_statistics(self):
        """Test estadísticas de la grid"""
        stats = self.grid.get_statistics()

        assert stats['total_subcarriers'] == 512
        assert stats['useful_subcarriers'] == 300
        # Datos + pilotos = subportadoras útiles - DC
        assert stats['data_subcarriers'] + stats['pilot_subcarriers'] == 299
        # Verificar conteos específicos
        assert stats['guard_subcarriers'] == 212
        assert stats['dc_subcarriers'] == 1

        print(f"\nEstadísticas de grid:")
        for key, value in stats.items():
            if not isinstance(value, dict):
                print(f"  {key}: {value}")


class TestPilotPattern:
    """Tests para el patrón de pilotos"""
    
    def test_pilot_generation(self):
        """Test generación de pilotos"""
        pattern = PilotPattern(cell_id=0)
        pilots = pattern.generate_pilots(50)
        
        assert len(pilots) == 50
        assert all(isinstance(p, (complex, np.complexfloating)) for p in pilots)
        assert all(abs(p) > 0 for p in pilots)  # No todos cero
        print(f"✓ Pilotos generados correctamente: {len(pilots)} pilotos")
    
    def test_pilot_deterministic(self):
        """Test que pilotos son determinísticos (reproducibles)"""
        pattern1 = PilotPattern(cell_id=5)
        pattern2 = PilotPattern(cell_id=5)
        
        pilots1 = pattern1.generate_pilots(100)
        pilots2 = pattern2.generate_pilots(100)
        
        assert np.allclose(pilots1, pilots2)
        print(f"✓ Pilotos son determinísticos (mismos para mismo cell_id)")
    
    def test_pilot_different_for_different_cells(self):
        """Test que pilotos cambian con cell_id"""
        pattern1 = PilotPattern(cell_id=0)
        pattern2 = PilotPattern(cell_id=1)
        
        pilots1 = pattern1.generate_pilots(100)
        pilots2 = pattern2.generate_pilots(100)
        
        assert not np.allclose(pilots1, pilots2)
        print(f"✓ Pilotos diferentes para distintos cell_id")


class TestResourceMapper:
    """Tests para el mapeador de recursos"""
    
    def setup_method(self):
        """Setup antes de cada test"""
        self.config = LTEConfig(5, 15, 'QPSK', 'normal')
        self.mapper = ResourceMapper(self.config)
        self.qam_mod = QAMModulator('QPSK')
    
    def test_mapper_initialization(self):
        """Test inicialización del mapeador"""
        assert self.mapper.config == self.config
        assert self.mapper.grid is not None
        assert self.mapper.pilot_pattern is not None
        print(f"✓ Mapeador inicializado correctamente")
    
    def test_map_symbols_size(self):
        """Test que mapeo produce salida del tamaño correcto"""
        bits = np.random.randint(0, 2, 600)  # 600 bits para 300 símbolos QPSK
        symbols = self.qam_mod.bits_to_symbols(bits)
        
        grid_mapped, info = self.mapper.map_symbols(symbols)
        
        assert len(grid_mapped) == self.config.N
        assert grid_mapped.dtype == complex
        print(f"✓ Mapeo produce grid de tamaño correcto: {len(grid_mapped)}")
    
    def test_map_symbols_data_placement(self):
        """Test que datos se colocan en posiciones correctas"""
        bits = np.random.randint(0, 2, 600)
        symbols = self.qam_mod.bits_to_symbols(bits)
        
        grid_mapped, info = self.mapper.map_symbols(symbols)
        
        # Verificar que datos están en posiciones de datos
        data_indices = info['data_indices']
        for idx in data_indices:
            assert grid_mapped[idx] != 0
        
        print(f"✓ Datos colocados en {len(data_indices)} posiciones")
    
    def test_map_symbols_pilot_placement(self):
        """Test que pilotos se colocan correctamente"""
        bits = np.random.randint(0, 2, 600)
        symbols = self.qam_mod.bits_to_symbols(bits)
        
        grid_mapped, info = self.mapper.map_symbols(symbols)
        
        # Verificar que pilotos están en posiciones de pilotos
        pilot_indices = info['pilot_indices']
        for idx in pilot_indices:
            assert grid_mapped[idx] != 0
        
        print(f"✓ Pilotos colocados en {len(pilot_indices)} posiciones")
    
    def test_dc_and_guards_null(self):
        """Test que DC y guardias son nulos"""
        bits = np.random.randint(0, 2, 600)
        symbols = self.qam_mod.bits_to_symbols(bits)
        
        grid_mapped, info = self.mapper.map_symbols(symbols)
        
        # DC debe ser cero
        assert grid_mapped[info['dc_index']] == 0
        
        # Guardias deben ser cero
        guard_indices = info['guard_indices']
        for idx in guard_indices:
            assert grid_mapped[idx] == 0
        
        print(f"✓ DC (índice {info['dc_index']}) y {len(guard_indices)} guardias son nulos")
    
    def test_mapping_info_consistency(self):
        """Test consistencia de información de mapeo"""
        bits = np.random.randint(0, 2, 600)
        symbols = self.qam_mod.bits_to_symbols(bits)
        
        grid_mapped, info = self.mapper.map_symbols(symbols)
        
        # Suma de categorías debe ser N
        total = (info['num_data_mapped'] + info['num_pilots_mapped'] + 
                info['num_nulls'])
        
        assert total == self.config.N
        print(f"✓ Mapeo consistente: {info['num_data_mapped']} datos + "
              f"{info['num_pilots_mapped']} pilotos + {info['num_nulls']} nulos = "
              f"{self.config.N}")
    
    def test_extract_pilots(self):
        """Test extracción de pilotos"""
        bits = np.random.randint(0, 2, 600)
        symbols = self.qam_mod.bits_to_symbols(bits)
        
        grid_mapped, info = self.mapper.map_symbols(symbols)
        
        pilot_indices, pilot_symbols = self.mapper.extract_pilots(grid_mapped)
        
        assert len(pilot_indices) == len(pilot_symbols)
        assert len(pilot_indices) > 0
        print(f"✓ Extracción de pilotos: {len(pilot_indices)} pilotos extraídos")


class TestLTECompliance:
    """Tests para cumplimiento con estándar LTE"""
    
    def setup_method(self):
        """Setup antes de cada test"""
        self.config = LTEConfig(5, 15, 'QPSK', 'normal')
        self.mapper = ResourceMapper(self.config)
    
    def test_lte_bandwidth_5mhz(self):
        """Test configuración para 5 MHz (300 subportadoras)"""
        stats = self.mapper.get_statistics()
        
        assert stats['useful_subcarriers'] == 300
        # Datos + pilotos + DC = subportadoras útiles
        assert stats['data_subcarriers'] + stats['pilot_subcarriers'] + \
               stats['dc_subcarriers'] == 300
        print(f"✓ Ancho de banda 5 MHz: {stats['useful_subcarriers']} subportadoras útiles")
    
    def test_lte_pilot_overhead(self):
        """Test overhead de pilotos según LTE (~8%)"""
        stats = self.mapper.get_statistics()
        
        pilot_overhead = stats['pilot_subcarriers'] / stats['total_subcarriers']
        
        # LTE típicamente tiene ~8% de overhead de pilotos
        assert 0.05 < pilot_overhead < 0.15
        print(f"✓ Overhead de pilotos: {pilot_overhead*100:.1f}% "
              f"(esperado ~8% en LTE)")
    
    def test_lte_guard_spectrum(self):
        """Test que guardias protegen espectro adyacente"""
        stats = self.mapper.get_statistics()
        
        guard_total = stats['guard_subcarriers'] + 1  # +1 para DC
        useful = stats['useful_subcarriers']
        
        assert guard_total > 0
        assert useful < self.config.N
        print(f"✓ Protección espectral: {stats['guard_left']} guardia izq, "
              f"{stats['guard_right']} guardia der, DC")


def run_all_tests():
    """Ejecuta todos los tests con reporte detallado"""
    print("\n" + "="*80)
    print("TESTS DE RESOURCE MAPPER - LTE")
    print("="*80)
    
    pytest.main([__file__, '-v', '-s'])


if __name__ == '__main__':
    run_all_tests()
