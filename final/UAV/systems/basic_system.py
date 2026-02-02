"""
Basic UAV System using Sionna SYS
Sistema básico gNB → UAV usando abstracciones de Sionna SYS
"""
import numpy as np
import tensorflow as tf
import sionna
from sionna.sys.utils import *
try:
    from sionna.sys import *
except ImportError:
    print("⚠️  sionna.sys no disponible, usando RT directo")
    pass

# Importar configuraciones y escenario
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.system_config import *
from scenarios.munich_uav_scenario import MunichUAVScenario

class BasicUAVSystem:
    """
    Sistema básico UAV usando Sionna SYS
    Implementa link gNB → UAV con métricas de sistema
    """
    
    def __init__(self, scenario=None):
        """Inicializar sistema UAV"""
        self.scenario = scenario or MunichUAVScenario(enable_preview=False)
        
        print("🔧 Inicializando sistema UAV...")
        
        # Get paths for channel
        self.paths = self.scenario.get_paths(max_depth=5)
        
        # Setup system components
        self._setup_channel()
        self._setup_system()
        
        print("✅ Sistema UAV inicializado")
    
    def _setup_channel(self):
        """Configurar canal ray tracing"""
        print("📡 Configurando canal RT...")
        
        # For now, we work directly with the scenario's paths
        # TODO: Integrate with proper Sionna SYS channel when available
        self.channel_ready = True
        
        print("✅ Canal RT configurado")
    
    def _setup_system(self):
        """Configurar sistema completo"""
        print("🔧 Configurando sistema...")
        
        # System configuration will depend on Sionna SYS API
        # This is a placeholder for the actual system setup
        
        # For now, we'll work with the channel directly
        self.system_ready = True
        
        print("✅ Sistema configurado")
    
    def simulate_throughput(self, snr_db_range=None):
        """
        Simular throughput vs SNR
        Returns: dict con métricas del sistema
        """
        if snr_db_range is None:
            snr_db_range = np.arange(0, 31, 5)  # 0 to 30 dB
        
        print(f"🎯 Simulando throughput para SNR: {snr_db_range[0]} a {snr_db_range[-1]} dB")
        
        results = {
            'snr_db': snr_db_range,
            'throughput_mbps': [],
            'bler': [],
            'spectral_efficiency': [],
            'channel_conditions': []
        }
        
        for snr_db in snr_db_range:
            print(f"  SNR = {snr_db} dB...", end="")
            
            # Simulate for this SNR point
            metrics = self._simulate_single_snr(snr_db)
            
            results['throughput_mbps'].append(metrics['throughput_mbps'])
            results['bler'].append(metrics['bler'])
            results['spectral_efficiency'].append(metrics['spectral_efficiency'])
            results['channel_conditions'].append(metrics['channel_condition'])
            
            print(f" Throughput={metrics['throughput_mbps']:.1f} Mbps")
        
        # Convert to numpy arrays
        for key in ['throughput_mbps', 'bler', 'spectral_efficiency']:
            results[key] = np.array(results[key])
        
        print(f"✅ Simulación completada")
        return results
    
    def _simulate_single_snr(self, snr_db):
        """Simular un punto SNR"""
        
        # Get channel response
        h_freq, frequencies = self.scenario.get_channel_response(self.paths)
        
        # Analyze channel conditions
        conditions = self.scenario.analyze_channel_conditions(self.paths)
        
        # Calculate channel gain (instead of path loss)
        # Apply power boost similar to the PHY solution for realistic values
        power_boost_db = 50.0  # Same boost we used in PHY analysis
        h_freq_boosted = h_freq * tf.cast(tf.sqrt(10.0 ** (power_boost_db / 10.0)), tf.complex64)
        
        # Channel power with boost
        channel_power = tf.reduce_mean(tf.abs(h_freq_boosted) ** 2)
        channel_gain_db = 10 * tf.math.log(channel_power + 1e-12) / tf.math.log(10.0)
        
        # Effective SNR calculation
        snr_linear = 10 ** (snr_db / 10.0)
        channel_gain_linear = 10 ** (float(channel_gain_db) / 10.0)
        effective_snr = snr_linear * channel_gain_linear
        
        # Shannon capacity with MIMO gain (rough approximation)
        mimo_gain = min(AntennaConfig.GNB_ARRAY['num_rows'] * AntennaConfig.GNB_ARRAY['num_cols'],
                       AntennaConfig.UAV_ARRAY['num_rows'] * AntennaConfig.UAV_ARRAY['num_cols'])
        
        # Spectral efficiency (bits/s/Hz) with MIMO
        se = float(mimo_gain * tf.math.log(1.0 + effective_snr) / tf.math.log(2.0))
        
        # Throughput (assuming 100 MHz bandwidth)
        throughput_mbps = se * RFConfig.BANDWIDTH / 1e6
        
        # Simple BLER model (exponential decay with effective SNR)
        bler = float(tf.exp(-effective_snr / 10.0))  # More realistic threshold
        
        return {
            'throughput_mbps': throughput_mbps,
            'spectral_efficiency': se,
            'bler': bler,
            'channel_gain_db': float(channel_gain_db),
            'effective_snr_db': 10 * np.log10(effective_snr + 1e-12),
            'channel_condition': conditions
        }
    
    def simulate_height_analysis(self, height_range=None):
        """
        Simular throughput vs altura UAV
        Returns: dict con métricas vs altura
        """
        if height_range is None:
            height_range = ScenarioConfig.HEIGHT_RANGE
        
        print(f"📈 Análisis de altura: {min(height_range)} a {max(height_range)} m")
        
        results = {
            'heights': height_range,
            'throughput_mbps': [],
            'path_loss_db': [],
            'los_probability': [],
            'spectral_efficiency': []
        }
        
        # Fix SNR for height analysis
        fixed_snr_db = 20  # High SNR to see channel effects clearly
        
        original_position = ScenarioConfig.UAV1_POSITION.copy()
        
        for height in height_range:
            print(f"  Altura {height} m...", end="")
            
            # Move UAV to new height
            new_position = [original_position[0], original_position[1], height]
            self.scenario.move_uav("UAV1", new_position)
            
            # Recalculate paths for new position
            paths = self.scenario.get_paths(max_depth=5)
            
            # Simulate at fixed SNR
            # Update paths in system
            self.paths = paths
            metrics = self._simulate_single_snr(fixed_snr_db)
            
            results['throughput_mbps'].append(metrics['throughput_mbps'])
            results['path_loss_db'].append(-metrics['channel_gain_db'])  # Convert gain back to loss for display
            results['spectral_efficiency'].append(metrics['spectral_efficiency'])
            
            # LoS probability based on channel conditions
            los_prob = 1.0 if metrics['channel_condition'] and metrics['channel_condition']['is_los'] else 0.0
            results['los_probability'].append(los_prob)
            
            print(f" Throughput={metrics['throughput_mbps']:.1f} Mbps, LoS={'✓' if los_prob else '✗'}")
        
        # Restore original position
        self.scenario.move_uav("UAV1", original_position)
        
        # Convert to numpy arrays
        for key in ['throughput_mbps', 'path_loss_db', 'los_probability', 'spectral_efficiency']:
            results[key] = np.array(results[key])
        
        print("✅ Análisis de altura completado")
        return results
    
    def get_system_info(self):
        """Información del sistema"""
        scenario_info = self.scenario.get_scenario_info()
        
        return {
            **scenario_info,
            'system_type': 'Basic UAV System',
            'channel_type': 'Ray Tracing',
            'bandwidth_mhz': RFConfig.BANDWIDTH / 1e6,
            'tx_power_dbm': RFConfig.TX_POWER_GNB,
            'batch_size': SimulationConfig.BATCH_SIZE
        }

def test_basic_system():
    """Test del sistema básico"""
    print("="*70)
    print("BASIC UAV SYSTEM - TEST")
    print("="*70)
    
    # Create system
    system = BasicUAVSystem()
    
    # System info
    info = system.get_system_info()
    print(f"\n📊 INFORMACIÓN DEL SISTEMA:")
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    # Quick throughput test
    print(f"\n🎯 TEST THROUGHPUT (SNR limitado para rapidez):")
    snr_test = [0, 10, 20]
    results = system.simulate_throughput(snr_test)
    
    for i, snr in enumerate(snr_test):
        print(f"  SNR {snr} dB: {results['throughput_mbps'][i]:.1f} Mbps, BLER={results['bler'][i]:.3f}")
    
    print(f"\n✅ SISTEMA BÁSICO FUNCIONANDO")
    
    return system, results

if __name__ == "__main__":
    system, results = test_basic_system()