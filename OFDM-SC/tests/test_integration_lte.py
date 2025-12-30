"""
Test de integración del modulador OFDM con ResourceMapper
Valida que el modo LTE funciona correctamente
"""

import numpy as np
import pytest
from config.lte_params import LTEConfig
from core.modulator import OFDMModulator
from core.resource_mapper import ResourceMapper


class TestModulatorLTEMode:
    """Tests de integración del modulador con modo LTE"""
    
    @pytest.fixture
    def setup(self):
        """Inicializar configuración"""
        self.config = LTEConfig()
        self.modulator_lte = OFDMModulator(self.config, mode='lte')
        self.modulator_simple = OFDMModulator(self.config, mode='simple')
    
    def test_modulator_lte_mode_initialization(self, setup):
        """Test que el modulador se inicializa correctamente en modo LTE"""
        assert self.modulator_lte.mode == 'lte'
        assert hasattr(self.modulator_lte, 'resource_mapper')
        assert isinstance(self.modulator_lte.resource_mapper, ResourceMapper)
    
    def test_modulator_simple_mode_initialization(self, setup):
        """Test que el modulador se inicializa correctamente en modo simple"""
        assert self.modulator_simple.mode == 'simple'
        assert not hasattr(self.modulator_simple, 'resource_mapper') or \
               self.modulator_simple.resource_mapper is None
    
    def test_modulate_lte_returns_mapping_info(self, setup):
        """Test que modulación LTE retorna mapping_info"""
        # Generar bits aleatorios
        bits_per_symbol = self.config.bits_per_symbol
        num_symbols = 50
        bits = np.random.randint(0, 2, bits_per_symbol * num_symbols)
        
        # Modular
        signal, symbols, mapping_info = self.modulator_lte.modulate(bits)
        
        # Validar
        assert signal is not None
        assert len(signal) == self.config.N + self.config.cp_length
        assert mapping_info is not None
        assert isinstance(mapping_info, dict)
        assert 'data_indices' in mapping_info
        assert 'pilot_indices' in mapping_info
    
    def test_modulate_simple_returns_none_mapping_info(self, setup):
        """Test que modulación simple retorna None para mapping_info"""
        # Generar bits aleatorios
        bits_per_symbol = self.config.bits_per_symbol
        num_symbols = 50
        bits = np.random.randint(0, 2, bits_per_symbol * num_symbols)
        
        # Modular
        signal, symbols, mapping_info = self.modulator_simple.modulate(bits)
        
        # Validar
        assert signal is not None
        assert len(signal) == self.config.N + self.config.cp_length
        assert mapping_info is None
    
    def test_modulate_stream_lte(self, setup):
        """Test modulación de stream en modo LTE"""
        # Generar stream de bits
        bits_per_ofdm = self.config.Nc * self.config.bits_per_symbol
        num_symbols = 3
        bits = np.random.randint(0, 2, bits_per_ofdm * num_symbols)
        
        # Modular stream
        signal, all_symbols, mapping_infos = self.modulator_lte.modulate_stream(bits, num_symbols)
        
        # Validar
        assert signal is not None
        assert len(all_symbols) == num_symbols
        assert mapping_infos is not None
        assert len(mapping_infos) == num_symbols
        
        # Validar estructura de mapping_info
        for mapping_info in mapping_infos:
            assert isinstance(mapping_info, dict)
            assert 'data_indices' in mapping_info
            assert 'pilot_indices' in mapping_info
            # mapping_info puede contener otros campos como 'stats', 'guard_indices'
    
    def test_modulate_stream_simple(self, setup):
        """Test modulación de stream en modo simple"""
        # Generar stream de bits
        bits_per_ofdm = self.config.Nc * self.config.bits_per_symbol
        num_symbols = 3
        bits = np.random.randint(0, 2, bits_per_ofdm * num_symbols)
        
        # Modular stream
        signal, all_symbols, mapping_infos = self.modulator_simple.modulate_stream(bits, num_symbols)
        
        # Validar
        assert signal is not None
        assert len(all_symbols) == num_symbols
        assert mapping_infos is None
    
    def test_lte_signal_length(self, setup):
        """Test que la señal LTE tiene la longitud esperada"""
        bits_per_symbol = self.config.bits_per_symbol
        bits = np.random.randint(0, 2, bits_per_symbol * 50)
        
        signal, _, _ = self.modulator_lte.modulate(bits)
        
        # Longitud esperada = FFT + CP
        expected_length = self.config.N + self.config.cp_length
        assert len(signal) == expected_length
    
    def test_lte_pilots_are_placed(self, setup):
        """Test que los pilotos se colocan correctamente en la grid LTE"""
        bits_per_symbol = self.config.bits_per_symbol
        bits = np.random.randint(0, 2, bits_per_symbol * 50)
        
        signal, symbols, mapping_info = self.modulator_lte.modulate(bits)
        
        # Verificar que hay pilotos
        pilot_indices = mapping_info['pilot_indices']
        assert len(pilot_indices) == 50  # 300 útiles / 6 espaciado
        
        # Pilotos están distribuidos correctamente
        pilot_set = set(pilot_indices)
        data_set = set(mapping_info['data_indices'])
        
        # No hay solapamiento
        assert len(pilot_set & data_set) == 0


class TestLTEModeConsistency:
    """Tests de consistencia entre modos"""
    
    @pytest.fixture
    def setup(self):
        """Inicializar"""
        self.config = LTEConfig()
        self.modulator_lte = OFDMModulator(self.config, mode='lte')
        self.modulator_simple = OFDMModulator(self.config, mode='simple')
    
    def test_both_modes_use_same_qam_modulator(self, setup):
        """Test que ambos modos usan el mismo tipo de modulador QAM"""
        assert type(self.modulator_lte.qam_modulator) == \
               type(self.modulator_simple.qam_modulator)
    
    def test_both_modes_preserve_data_symbols(self, setup):
        """Test que ambos modos preservan los símbolos QAM"""
        bits = np.array([0, 1, 1, 0, 0, 1, 1, 0])  # 8 bits
        
        # Modular con ambos modos
        _, symbols_lte, _ = self.modulator_lte.modulate(bits)
        _, symbols_simple, _ = self.modulator_simple.modulate(bits)
        
        # Los primeros símbolos deberían ser idénticos (simple tiene solo los datos)
        num_symbols = min(len(symbols_simple), len(symbols_lte))
        np.testing.assert_array_almost_equal(symbols_lte[:num_symbols], symbols_simple[:num_symbols])


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
