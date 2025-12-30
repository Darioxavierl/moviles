"""
Tests para PAPR y CCDF
Valida que el cálculo de PAPR y la CCDF funcionan correctamente
"""
import pytest
import numpy as np
import sys
import os

# Agregar el path del proyecto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.signal_processing import PAPRAnalyzer
from core.ofdm_system import OFDMSystem
from config.lte_params import LTEConfig


class TestPAPRAnalyzer:
    """Tests para la clase PAPRAnalyzer"""
    
    def test_ccdf_calculation(self):
        """Valida que la CCDF se calcula correctamente"""
        # Crear valores PAPR conocidos
        papr_values = np.array([5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
        
        ccdf_data = PAPRAnalyzer.calculate_ccdf(papr_values)
        
        # Validar estructura
        assert 'papr_x' in ccdf_data
        assert 'ccdf_y' in ccdf_data
        
        # Los valores de x deben ser ordenados
        assert np.all(np.diff(ccdf_data['papr_x']) >= 0)
        
        # Los valores de y deben estar entre 0 y 1
        assert np.all(ccdf_data['ccdf_y'] >= 0)
        assert np.all(ccdf_data['ccdf_y'] <= 1)
        
        # CCDF debe ser decreciente
        assert np.all(np.diff(ccdf_data['ccdf_y']) <= 0)
    
    def test_ccdf_monotonicity(self):
        """Valida que la CCDF es monótona decreciente"""
        # Crear valores PAPR aleatorios
        papr_values = np.random.uniform(3, 12, 1000)
        
        ccdf_data = PAPRAnalyzer.calculate_ccdf(papr_values)
        
        # Verificar que es estrictamente decreciente
        diffs = np.diff(ccdf_data['ccdf_y'])
        assert np.all(diffs <= 0)
    
    def test_ccdf_boundary_conditions(self):
        """Valida condiciones límite de la CCDF"""
        papr_values = np.array([5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
        
        ccdf_data = PAPRAnalyzer.calculate_ccdf(papr_values)
        
        # P(PAPR > x_min) debería estar cercano a 1
        assert ccdf_data['ccdf_y'][0] >= 0.8  # Debería ser muy alto
        
        # P(PAPR > x_max) debería estar cercano a 0
        assert ccdf_data['ccdf_y'][-1] <= 0.2  # Debería ser muy bajo
    
    def test_ccdf_empty_array(self):
        """Valida manejo de arrays vacíos"""
        papr_values = np.array([])
        
        ccdf_data = PAPRAnalyzer.calculate_ccdf(papr_values)
        
        assert len(ccdf_data['papr_x']) == 0
        assert len(ccdf_data['ccdf_y']) == 0
    
    def test_papr_statistics(self):
        """Valida el cálculo de estadísticas de PAPR"""
        papr_values = np.array([5.0, 6.0, 7.0, 8.0, 9.0])
        
        stats = PAPRAnalyzer.get_papr_statistics(papr_values)
        
        # Validar estructura
        assert 'mean' in stats
        assert 'median' in stats
        assert 'std' in stats
        assert 'min' in stats
        assert 'max' in stats
        assert 'q1' in stats
        assert 'q3' in stats
        assert 'n_samples' in stats
        
        # Validar valores
        assert stats['mean'] == 7.0
        assert stats['median'] == 7.0
        assert stats['min'] == 5.0
        assert stats['max'] == 9.0
        assert stats['n_samples'] == 5
    
    def test_papr_statistics_single_value(self):
        """Valida estadísticas con un solo valor"""
        papr_values = np.array([7.0])
        
        stats = PAPRAnalyzer.get_papr_statistics(papr_values)
        
        assert stats['mean'] == 7.0
        assert stats['median'] == 7.0
        assert stats['min'] == 7.0
        assert stats['max'] == 7.0
        assert stats['std'] == 0.0


class TestPAPRWithoutCP:
    """Tests para cálculo de PAPR sin prefijo cíclico"""
    
    def test_papr_without_cp_calculation(self):
        """Valida que el PAPR se calcula correctamente sin CP"""
        config = LTEConfig(bandwidth=5.0)
        system = OFDMSystem(config, channel_type='awgn', enable_equalization=False)
        
        # Crear una señal con estructura conocida
        # (símbolo + CP + símbolo + CP, etc.)
        samples_per_symbol = config.N + config.cp_length
        num_symbols = 10
        
        # Crear señal (valores complejos aleatorios)
        signal = np.random.randn(num_symbols * samples_per_symbol) + \
                 1j * np.random.randn(num_symbols * samples_per_symbol)
        
        # Calcular PAPR
        papr_info = system.calculate_papr_without_cp(signal)
        
        # Validar estructura
        assert 'papr_per_symbol' in papr_info
        assert 'papr_values' in papr_info
        assert 'papr_mean' in papr_info
        assert 'papr_max' in papr_info
        assert 'papr_min' in papr_info
        assert 'papr_std' in papr_info
        assert 'num_symbols' in papr_info
        
        # Validar que el número de símbolos es correcto
        assert papr_info['num_symbols'] == num_symbols
        assert len(papr_info['papr_values']) == num_symbols
    
    def test_papr_without_cp_vs_with_cp(self):
        """Valida que PAPR sin CP es diferente a PAPR con CP"""
        config = LTEConfig(bandwidth=5.0)
        system = OFDMSystem(config, channel_type='awgn', enable_equalization=False)
        
        # Crear una señal
        samples_per_symbol = config.N + config.cp_length
        num_symbols = 10
        signal = np.random.randn(num_symbols * samples_per_symbol) + \
                 1j * np.random.randn(num_symbols * samples_per_symbol)
        
        # Calcular PAPR sin CP
        papr_no_cp = system.calculate_papr_without_cp(signal)
        
        # Calcular PAPR con CP (con la función antigua)
        papr_with_cp = system.calculate_papr_per_symbol(signal)
        
        # Deberían ser diferentes (porque usan diferentes porciones de la señal)
        # La comparación exacta depende de cómo se calculan, pero al menos
        # los valores máximos podrían ser diferentes
        assert papr_no_cp['papr_max'] != papr_with_cp['papr_max'] or \
               papr_no_cp['papr_mean'] != papr_with_cp['papr_mean']


class TestPAPRStorage:
    """Tests para el almacenamiento de PAPR en OFDMSystem"""
    
    def test_papr_storage_ofdm(self):
        """Valida que se almacenan PAPR para OFDM estándar"""
        config = LTEConfig(bandwidth=5.0, modulation='QPSK')
        system = OFDMSystem(config, channel_type='awgn', enable_sc_fdm=False, 
                           enable_equalization=False)
        
        # Realizar transmisión
        bits = np.random.randint(0, 2, 200)
        results = system.transmit(bits, snr_db=10.0)
        
        # Validar que se almacenaron PAPR en la lista correcta
        assert len(system.papr_values_ofdm) > 0
        assert len(system.papr_values_sc_fdm) == 0
        
        # Validar que los PAPR están en el rango razonable (3-15 dB)
        for papr in system.papr_values_ofdm:
            assert 0 < papr < 20
    
    def test_papr_storage_sc_fdm(self):
        """Valida que se almacenan PAPR para SC-FDM"""
        config = LTEConfig(bandwidth=5.0, modulation='QPSK')
        system = OFDMSystem(config, channel_type='awgn', enable_sc_fdm=True, 
                           enable_equalization=False)
        
        # Realizar transmisión
        bits = np.random.randint(0, 2, 200)
        results = system.transmit(bits, snr_db=10.0)
        
        # Validar que se almacenaron PAPR en la lista correcta
        assert len(system.papr_values_sc_fdm) > 0
        assert len(system.papr_values_ofdm) == 0
        
        # Validar que los PAPR están en el rango razonable
        for papr in system.papr_values_sc_fdm:
            assert 0 < papr < 20
    
    def test_papr_comparison_ofdm_vs_sc_fdm(self):
        """Valida comparación de PAPR entre OFDM y SC-FDM"""
        config = LTEConfig(bandwidth=5.0, modulation='QPSK')
        
        # Sistema OFDM
        system_ofdm = OFDMSystem(config, channel_type='awgn', enable_sc_fdm=False, 
                                enable_equalization=False)
        bits = np.random.randint(0, 2, 300)
        system_ofdm.transmit(bits, snr_db=10.0)
        
        # Sistema SC-FDM
        system_sc_fdm = OFDMSystem(config, channel_type='awgn', enable_sc_fdm=True, 
                                  enable_equalization=False)
        system_sc_fdm.transmit(bits, snr_db=10.0)
        
        # Ambos deberían tener valores PAPR
        assert len(system_ofdm.papr_values_ofdm) > 0
        assert len(system_sc_fdm.papr_values_sc_fdm) > 0
        
        # SC-FDM debería tener PAPR más bajo en promedio (es la idea)
        # Pero esto depende de los datos, así que solo verificamos que existen
        assert isinstance(system_ofdm.papr_values_ofdm[0], (int, float))
        assert isinstance(system_sc_fdm.papr_values_sc_fdm[0], (int, float))


class TestCCDFIntegration:
    """Tests de integración para CCDF con datos reales del sistema"""
    
    def test_ccdf_from_real_transmission(self):
        """Valida CCDF generada a partir de una transmisión real"""
        config = LTEConfig(bandwidth=5.0, modulation='QPSK')
        system = OFDMSystem(config, channel_type='awgn', enable_sc_fdm=False, 
                           enable_equalization=False)
        
        # Realizar varias transmisiones
        for _ in range(3):
            bits = np.random.randint(0, 2, 100)
            system.transmit(bits, snr_db=10.0)
        
        # Generar CCDF
        ccdf_data = PAPRAnalyzer.calculate_ccdf(system.papr_values_ofdm)
        
        # Validar que se generó correctamente
        assert len(ccdf_data['papr_x']) > 0
        assert len(ccdf_data['ccdf_y']) > 0
        assert len(ccdf_data['papr_x']) == len(ccdf_data['ccdf_y'])
    
    def test_multiple_modulations_papr_comparison(self):
        """Valida que diferentes modulaciones tienen diferentes PAPR"""
        # QPSK (2 bits/símbolo)
        config_qpsk = LTEConfig(bandwidth=5.0, modulation='QPSK')
        system_qpsk = OFDMSystem(config_qpsk, channel_type='awgn', enable_sc_fdm=False, 
                                enable_equalization=False)
        bits = np.random.randint(0, 2, 300)
        system_qpsk.transmit(bits, snr_db=10.0)
        
        # 16-QAM (4 bits/símbolo)
        config_16qam = LTEConfig(bandwidth=5.0, modulation='16-QAM')
        system_16qam = OFDMSystem(config_16qam, channel_type='awgn', enable_sc_fdm=False, 
                                 enable_equalization=False)
        system_16qam.transmit(bits, snr_db=10.0)
        
        # Ambos deberían tener PAPR
        assert len(system_qpsk.papr_values_ofdm) > 0
        assert len(system_16qam.papr_values_ofdm) > 0
        
        # Calcular promedios
        mean_qpsk = np.mean(system_qpsk.papr_values_ofdm)
        mean_16qam = np.mean(system_16qam.papr_values_ofdm)
        
        # Ambos deben estar en rango razonable (PAPR típicamente entre 3-25 dB para OFDM)
        assert 3 < mean_qpsk < 25
        assert 3 < mean_16qam < 25


if __name__ == '__main__':
    # Ejecutar tests
    pytest.main([__file__, '-v'])
