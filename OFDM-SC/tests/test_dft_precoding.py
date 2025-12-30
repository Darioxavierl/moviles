"""
Tests para la precodificación DFT (SC-FDM)
Valida que la precodificación funciona correctamente
"""
import pytest
import numpy as np
import sys
import os

# Agregar el path del proyecto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.dft_precoding import DFTPrecodifier, SC_FDMPrecodifier
from core.modulator import OFDMModulator
from core.ofdm_system import OFDMSystem
from config.lte_params import LTEConfig


class TestDFTPrecodifier:
    """Tests para la clase DFTPrecodifier"""
    
    def test_dft_size_configuration(self):
        """Valida que el tamaño M de la DFT se configura correctamente"""
        M = 50
        precoder = DFTPrecodifier(M=M, enable=True)
        
        assert precoder.M == M
        assert precoder.enable == True
        assert precoder._dft_matrix is not None
        assert precoder._dft_matrix.shape == (M, M)
    
    def test_dft_precoding_output_size(self):
        """Valida que la salida de la DFT tiene el tamaño correcto"""
        M = 50
        precoder = DFTPrecodifier(M=M, enable=True)
        
        # Crear símbolos aleatorios
        symbols = np.random.randn(M) + 1j * np.random.randn(M)
        
        # Aplicar precodificación
        precoded = precoder.precoding(symbols)
        
        # Validar tamaño
        assert len(precoded) == M
        assert precoded.dtype == complex
    
    def test_dft_precoding_disabled(self):
        """Valida que cuando está deshabilitado retorna los símbolos sin cambios"""
        M = 50
        precoder = DFTPrecodifier(M=M, enable=False)
        
        # Crear símbolos aleatorios
        symbols = np.random.randn(M) + 1j * np.random.randn(M)
        
        # Aplicar precodificación (debería no hacer nada)
        precoded = precoder.precoding(symbols)
        
        # Validar que son iguales
        np.testing.assert_array_almost_equal(precoded, symbols)
    
    def test_dft_parseval_energy_conservation(self):
        """Valida que la DFT conserva la energía (normalización 1/sqrt(M))"""
        M = 50
        precoder = DFTPrecodifier(M=M, enable=True)
        
        # Crear símbolos con energía conocida
        symbols = np.ones(M)
        
        # Aplicar precodificación
        precoded = precoder.precoding(symbols)
        
        # La energía debe ser conservada (dentro de tolerancia numérica)
        energy_in = np.sum(np.abs(symbols) ** 2)
        energy_out = np.sum(np.abs(precoded) ** 2)
        
        # Energía se conserva con factor de normalización
        np.testing.assert_almost_equal(energy_in, energy_out, decimal=5)
    
    def test_dft_size_mismatch_error(self):
        """Valida que falla si los símbolos no coinciden con M"""
        M = 50
        precoder = DFTPrecodifier(M=M, enable=True)
        
        # Crear símbolos con tamaño incorrecto
        symbols = np.random.randn(30) + 1j * np.random.randn(30)
        
        # Debería lanzar error
        with pytest.raises(ValueError):
            precoder.precoding(symbols)
    
    def test_dft_dynamic_enable_disable(self):
        """Valida que se puede activar/desactivar dinámicamente"""
        M = 50
        precoder = DFTPrecodifier(M=M, enable=True)
        
        # Crear símbolos
        symbols = np.random.randn(M) + 1j * np.random.randn(M)
        
        # Aplicar con DFT habilitado
        precoded_enabled = precoder.precoding(symbols)
        
        # Desabilitar y aplicar
        precoder.enable = False
        precoded_disabled = precoder.precoding(symbols)
        
        # Debería ser diferente
        assert not np.allclose(precoded_enabled, precoded_disabled)
        # Y sin DFT debería ser igual a original
        np.testing.assert_array_almost_equal(precoded_disabled, symbols)


class TestSC_FDMPrecodifier:
    """Tests para la clase SC_FDMPrecodifier"""
    
    def test_sc_fdm_initialization(self):
        """Valida la inicialización del precodificador SC-FDM"""
        num_data_subcarriers = 100
        precoder = SC_FDMPrecodifier(num_data_subcarriers=num_data_subcarriers, enable=True)
        
        assert precoder.num_data_subcarriers == num_data_subcarriers
        assert precoder.enable == True
        assert precoder.dft_precoder is not None
    
    def test_sc_fdm_precoding(self):
        """Valida que SC-FDM aplica precodificación DFT correctamente"""
        num_data_subcarriers = 100
        precoder = SC_FDMPrecodifier(num_data_subcarriers=num_data_subcarriers, enable=True)
        
        # Crear símbolos de datos
        data_symbols = np.random.randn(num_data_subcarriers) + 1j * np.random.randn(num_data_subcarriers)
        
        # Aplicar precodificación
        precoded = precoder.precoding(data_symbols)
        
        # Validar tamaño
        assert len(precoded) == num_data_subcarriers
        assert precoded.dtype == complex


class TestOFDMModulatorWithSC_FDM:
    """Tests para OFDMModulator con SC-FDM"""
    
    def test_modulator_sc_fdm_initialization(self):
        """Valida que el modulador se inicializa con SC-FDM"""
        config = LTEConfig(bandwidth=5.0)
        modulator = OFDMModulator(config, mode='lte', enable_sc_fdm=True)
        
        assert modulator.enable_sc_fdm == True
        assert modulator.sc_fdm_precoder is not None
    
    def test_modulator_sc_fdm_disabled(self):
        """Valida que el modulador puede tener SC-FDM deshabilitado"""
        config = LTEConfig(bandwidth=5.0)
        modulator = OFDMModulator(config, mode='lte', enable_sc_fdm=False)
        
        assert modulator.enable_sc_fdm == False
    
    def test_modulation_with_sc_fdm(self):
        """Valida que la modulación funciona con SC-FDM habilitado"""
        config = LTEConfig(bandwidth=5.0, modulation='QPSK')
        modulator = OFDMModulator(config, mode='lte', enable_sc_fdm=True)
        
        # Crear bits aleatorios
        num_bits = 100
        bits = np.random.randint(0, 2, num_bits)
        
        # Modular
        signal, symbols, mapping_info = modulator.modulate(bits)
        
        # Validar que la señal se genera correctamente
        assert len(signal) > 0
        assert signal.dtype == complex
    
    def test_modulation_without_sc_fdm(self):
        """Valida que la modulación funciona sin SC-FDM"""
        config = LTEConfig(bandwidth=5.0, modulation='QPSK')
        modulator = OFDMModulator(config, mode='lte', enable_sc_fdm=False)
        
        # Crear bits aleatorios
        num_bits = 100
        bits = np.random.randint(0, 2, num_bits)
        
        # Modular
        signal, symbols, mapping_info = modulator.modulate(bits)
        
        # Validar que la señal se genera correctamente
        assert len(signal) > 0
        assert signal.dtype == complex
    
    def test_sc_fdm_dynamic_enable(self):
        """Valida que SC-FDM se puede activar/desactivar dinámicamente"""
        config = LTEConfig(bandwidth=5.0, modulation='QPSK')
        modulator = OFDMModulator(config, mode='lte', enable_sc_fdm=False)
        
        # Inicialmente deshabilitado
        assert modulator.enable_sc_fdm == False
        
        # Activar
        modulator.set_sc_fdm_enabled(True)
        assert modulator.enable_sc_fdm == True
        
        # Desactivar
        modulator.set_sc_fdm_enabled(False)
        assert modulator.enable_sc_fdm == False


class TestOFDMSystemWithSC_FDM:
    """Tests para OFDMSystem con SC-FDM"""
    
    def test_system_sc_fdm_initialization(self):
        """Valida que OFDMSystem se inicializa con SC-FDM"""
        config = LTEConfig(bandwidth=5.0)
        system = OFDMSystem(config, enable_sc_fdm=True)
        
        assert system.enable_sc_fdm == True
        assert len(system.papr_values_sc_fdm) == 0
        assert len(system.papr_values_ofdm) == 0
    
    def test_transmission_with_sc_fdm(self):
        """Valida que la transmisión funciona con SC-FDM"""
        config = LTEConfig(bandwidth=5.0, modulation='QPSK')
        system = OFDMSystem(config, channel_type='awgn', enable_sc_fdm=True, enable_equalization=False)
        
        # Crear bits aleatorios
        bits = np.random.randint(0, 2, 100)
        
        # Transmitir
        results = system.transmit(bits, snr_db=10.0)
        
        # Validar resultados
        assert 'ber' in results
        assert 'papr_no_cp' in results
        assert results['papr_no_cp'] is not None
        
        # Validar que PAPR se almacenó
        assert len(system.papr_values_sc_fdm) > 0
    
    def test_transmission_without_sc_fdm(self):
        """Valida que la transmisión funciona sin SC-FDM"""
        config = LTEConfig(bandwidth=5.0, modulation='QPSK')
        system = OFDMSystem(config, channel_type='awgn', enable_sc_fdm=False, enable_equalization=False)
        
        # Crear bits aleatorios
        bits = np.random.randint(0, 2, 100)
        
        # Transmitir
        results = system.transmit(bits, snr_db=10.0)
        
        # Validar resultados
        assert 'ber' in results
        assert 'papr_no_cp' in results
        
        # Validar que PAPR se almacenó en la lista correcta
        assert len(system.papr_values_ofdm) > 0
    
    def test_papr_calculation_without_cp(self):
        """Valida que el PAPR se calcula correctamente sin CP"""
        config = LTEConfig(bandwidth=5.0)
        system = OFDMSystem(config, channel_type='awgn', enable_sc_fdm=False, enable_equalization=False)
        
        # Crear una señal simple
        signal = np.random.randn(1000) + 1j * np.random.randn(1000)
        
        # Calcular PAPR sin CP
        papr_info = system.calculate_papr_without_cp(signal)
        
        # Validar estructura
        assert 'papr_per_symbol' in papr_info
        assert 'papr_values' in papr_info
        assert 'papr_mean' in papr_info
        assert 'papr_max' in papr_info
        assert 'num_symbols' in papr_info


if __name__ == '__main__':
    # Ejecutar tests
    pytest.main([__file__, '-v'])
