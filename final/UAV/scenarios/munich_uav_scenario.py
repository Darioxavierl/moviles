"""
Munich UAV Scenario - Escenario 3D con Ray Tracing
Crea y configura la escena 3D de Munich con gNB y UAVs
"""
import numpy as np
import tensorflow as tf
import sionna

# Importar configuración
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.system_config import ScenarioConfig, AntennaConfig, RFConfig

class MunichUAVScenario:
    """
    Escenario 3D Munich con gNB y UAVs
    Maneja toda la configuración de la escena, posiciones y arrays
    """
    
    def __init__(self, enable_preview=True):
        """Inicializar escenario Munich"""
        self.enable_preview = enable_preview
        self.scene = None
        self.path_solver = None
        
        # Load Munich scene
        print("📍 Cargando escena Munich...")
        self.scene = sionna.rt.load_scene(sionna.rt.scene.munich)
        self.scene.frequency = RFConfig.FREQUENCY
        self.scene.synthetic_array = True
        
        print(f"✅ Escena cargada: {RFConfig.FREQUENCY/1e9:.1f} GHz")
        
        # Setup transmitters and receivers
        self._setup_transmitters()
        self._setup_receivers()
        self._setup_antenna_arrays()
        
        # Initialize ray tracing solver
        print("🔍 Inicializando ray tracing solver...")
        self.path_solver = sionna.rt.PathSolver()
        
        if self.enable_preview:
            self._preview_scene()
    
    def _setup_transmitters(self):
        """Configurar transmisores (gNB)"""
        print("📡 Configurando gNB...")
        
        # gNB principal
        self.scene.add(sionna.rt.Transmitter(
            name="gNB", 
            position=ScenarioConfig.GNB_POSITION
        ))
        
        print(f"✅ gNB: {ScenarioConfig.GNB_POSITION} m")
    
    def _setup_receivers(self):
        """Configurar receptores (UAVs)"""
        print("🚁 Configurando UAVs...")
        
        # UAV1 principal
        self.scene.add(sionna.rt.Receiver(
            name="UAV1", 
            position=ScenarioConfig.UAV1_POSITION
        ))
        
        print(f"✅ UAV1: {ScenarioConfig.UAV1_POSITION} m")
    
    def _setup_antenna_arrays(self):
        """Configurar arrays de antenas"""
        print("📶 Configurando arrays de antenas...")
        
        # Array gNB (MIMO masivo 8x8)
        self.scene.tx_array = sionna.rt.PlanarArray(
            num_rows=AntennaConfig.GNB_ARRAY['num_rows'],
            num_cols=AntennaConfig.GNB_ARRAY['num_cols'],
            vertical_spacing=AntennaConfig.GNB_ARRAY['vertical_spacing'],
            horizontal_spacing=AntennaConfig.GNB_ARRAY['horizontal_spacing'],
            pattern=AntennaConfig.GNB_ARRAY['pattern'],
            polarization=AntennaConfig.GNB_ARRAY['polarization']
        )
        
        # Array UAV (2x2)
        self.scene.rx_array = sionna.rt.PlanarArray(
            num_rows=AntennaConfig.UAV_ARRAY['num_rows'],
            num_cols=AntennaConfig.UAV_ARRAY['num_cols'],
            vertical_spacing=AntennaConfig.UAV_ARRAY['vertical_spacing'],
            horizontal_spacing=AntennaConfig.UAV_ARRAY['horizontal_spacing'],
            pattern=AntennaConfig.UAV_ARRAY['pattern'],
            polarization=AntennaConfig.UAV_ARRAY['polarization']
        )
        
        gnb_elements = AntennaConfig.GNB_ARRAY['num_rows'] * AntennaConfig.GNB_ARRAY['num_cols']
        uav_elements = AntennaConfig.UAV_ARRAY['num_rows'] * AntennaConfig.UAV_ARRAY['num_cols']
        
        print(f"✅ gNB array: {gnb_elements} elementos ({AntennaConfig.GNB_ARRAY['num_rows']}x{AntennaConfig.GNB_ARRAY['num_cols']})")
        print(f"✅ UAV array: {uav_elements} elementos ({AntennaConfig.UAV_ARRAY['num_rows']}x{AntennaConfig.UAV_ARRAY['num_cols']})")
    
    def _preview_scene(self):
        """Preview 3D de la escena"""
        try:
            print("🎬 Generando preview 3D...")
            self.scene.preview()
            print("✅ Preview 3D generado")
        except Exception as e:
            print(f"⚠️  Preview 3D no disponible: {e}")
    
    def move_uav(self, uav_name, new_position):
        """Mover UAV a nueva posición"""
        print(f"🚁 Moviendo {uav_name} a {new_position}")
        
        # Convert to float32 for Mitsuba compatibility
        position_f32 = [float(x) for x in new_position]
        
        # Update receiver position
        for rx in self.scene.receivers.values():
            if rx.name == uav_name:
                rx.position = position_f32
                break
        else:
            print(f"❌ UAV {uav_name} no encontrado")
            return False
        
        return True
    
    def get_paths(self, max_depth=5):
        """Calcular paths ray tracing"""
        print(f"📡 Calculando paths (max_depth={max_depth})...")
        
        paths = self.path_solver(self.scene, max_depth=max_depth)
        
        num_paths = paths.a[0].shape[-1] if paths.a[0].shape else 0
        print(f"✅ {num_paths} paths calculados")
        
        return paths
    
    def get_channel_response(self, paths, bandwidth=RFConfig.BANDWIDTH, num_ofdm_subcarriers=64):
        """Obtener respuesta en frecuencia del canal"""
        print("📊 Calculando respuesta en frecuencia...")
        
        # Generate subcarrier frequencies
        frequencies = sionna.rt.subcarrier_frequencies(
            num_ofdm_subcarriers, 
            bandwidth / num_ofdm_subcarriers
        )
        
        # Compute channel frequency response
        h_freq = paths.cfr(
            frequencies=frequencies,
            num_time_steps=1,
            normalize=False,  # Mantener path loss realista
            out_type='tf'
        )
        
        print(f"✅ Channel shape: {h_freq.shape}")
        print(f"   [num_rx, num_rx_ant, num_tx, num_tx_ant, time_steps, frequencies]")
        
        return h_freq, frequencies
    
    def analyze_channel_conditions(self, paths):
        """Analizar condiciones del canal (LoS/NLoS)"""
        print("🔍 Analizando condiciones del canal...")
        
        # Path powers (first path is usually LoS if exists)
        path_powers = tf.abs(paths.a[0]) ** 2  # Shape: [num_rx, num_rx_ant, num_tx, num_tx_ant, num_paths]
        total_power = tf.reduce_sum(path_powers, axis=-1)  # Sum over paths
        
        # First path (direct) vs total power ratio
        if path_powers.shape[-1] > 0:
            direct_power = path_powers[..., 0]  # First path
            direct_ratio = tf.reduce_mean(direct_power / (total_power + 1e-12))  # Average over antennas
            
            # LoS threshold (first path dominates)
            los_threshold = 0.7
            is_los = direct_ratio > los_threshold
            
            # Convert to scalars
            direct_ratio_scalar = float(direct_ratio.numpy())
            is_los_scalar = bool(is_los.numpy())
            total_power_scalar = float(tf.reduce_mean(total_power).numpy())
            
            print(f"✅ Direct path power ratio: {direct_ratio_scalar:.3f}")
            print(f"✅ Channel condition: {'LoS' if is_los_scalar else 'NLoS'}")
            
            return {
                'is_los': is_los_scalar,
                'direct_ratio': direct_ratio_scalar,
                'total_paths': int(path_powers.shape[-1]),
                'total_power_db': 10 * np.log10(total_power_scalar + 1e-12)
            }
        else:
            print("❌ No paths found")
            return None
    
    def get_scenario_info(self):
        """Información del escenario actual"""
        return {
            'scene': 'Munich',
            'frequency_ghz': self.scene.frequency / 1e9,
            'gnb_position': ScenarioConfig.GNB_POSITION,
            'uav1_position': ScenarioConfig.UAV1_POSITION,
            'gnb_antennas': AntennaConfig.GNB_ARRAY['num_rows'] * AntennaConfig.GNB_ARRAY['num_cols'],
            'uav_antennas': AntennaConfig.UAV_ARRAY['num_rows'] * AntennaConfig.UAV_ARRAY['num_cols']
        }

def test_scenario():
    """Test básico del escenario"""
    print("="*70)
    print("MUNICH UAV SCENARIO - TEST BÁSICO")
    print("="*70)
    
    # Create scenario
    scenario = MunichUAVScenario(enable_preview=False)
    
    # Get scenario info
    info = scenario.get_scenario_info()
    print(f"\n📊 INFORMACIÓN DEL ESCENARIO:")
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    # Compute paths
    paths = scenario.get_paths(max_depth=5)
    
    # Analyze channel conditions
    conditions = scenario.analyze_channel_conditions(paths)
    if conditions:
        print(f"\n📡 CONDICIONES DEL CANAL:")
        for key, value in conditions.items():
            print(f"  {key}: {value}")
    
    # Get channel response
    h_freq, frequencies = scenario.get_channel_response(paths)
    
    print(f"\n✅ ESCENARIO CONFIGURADO EXITOSAMENTE")
    print(f"   - {len(frequencies)} subportadoras")
    print(f"   - Channel shape: {h_freq.shape}")
    
    return scenario, paths, h_freq

if __name__ == "__main__":
    scenario, paths, h_freq = test_scenario()