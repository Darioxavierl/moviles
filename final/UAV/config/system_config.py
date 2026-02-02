"""
UAV 5G NR System Configuration
Sistema de configuración centralizada para simulaciones UAV con Sionna SYS
"""
import numpy as np

# =============================================================================
# CONFIGURACIÓN DE FRECUENCIAS Y RF
# =============================================================================
class RFConfig:
    """Configuración de parámetros RF"""
    FREQUENCY = 3.5e9           # 3.5 GHz (5G NR band n78)
    BANDWIDTH = 100e6           # 100 MHz
    TX_POWER_GNB = 43          # 43 dBm (20W) para gNB
    TX_POWER_UAV = 23          # 23 dBm (200mW) para UAV
    NOISE_FIGURE = 7           # 7 dB noise figure
    THERMAL_NOISE = -174       # dBm/Hz

# =============================================================================
# CONFIGURACIÓN DE ANTENAS Y MIMO
# =============================================================================
class AntennaConfig:
    """Configuración de arrays de antenas"""
    
    # gNB (Base Station) - MIMO Masivo
    GNB_ARRAY = {
        'num_rows': 8,
        'num_cols': 8,           # 64 antenas total
        'vertical_spacing': 0.5,  # λ/2
        'horizontal_spacing': 0.5,
        'pattern': 'iso',
        'polarization': 'V'
    }
    
    # UAV - Array compacto
    UAV_ARRAY = {
        'num_rows': 2,
        'num_cols': 2,           # 4 antenas total
        'vertical_spacing': 0.5,
        'horizontal_spacing': 0.5,
        'pattern': 'iso',
        'polarization': 'V'
    }

# =============================================================================
# POSICIONES 3D ESCENARIO
# =============================================================================
class ScenarioConfig:
    """Configuración del escenario 3D Munich"""
    
    # Posiciones fijas
    GNB_POSITION = [0, 0, 30]          # gNB a 30m altura
    
    # Posiciones iniciales UAV
    UAV1_POSITION = [100, 100, 100]    # UAV1 a 100m altura
    UAV2_POSITION = [200, 200, 150]    # UAV2 para relay (Fase 5)
    
    # Rangos para análisis
    HEIGHT_RANGE = [50, 75, 100, 125, 150, 175, 200]  # Alturas a probar
    COVERAGE_AREA = {
        'x_range': [-200, 200],         # 400m x 400m coverage area
        'y_range': [-200, 200],
        'resolution': 20                # 20x20 grid points
    }

# =============================================================================
# CONFIGURACIÓN DE SIMULACIÓN
# =============================================================================
class SimulationConfig:
    """Parámetros de simulación"""
    
    # Ray Tracing
    RT_MAX_DEPTH = 5                    # Máximo 5 reflexiones
    RT_NUM_SAMPLES = 1e6               # Samples para ray launching
    
    # Sistema SYS
    BATCH_SIZE = 100                   # Batch size para simulación
    NUM_BATCHES = 3                    # Batches por punto SNR
    SNR_RANGE = np.arange(-10, 31, 5)  # -10 a 30 dB, step 5dB
    
    # Métricas objetivo
    TARGET_BLER = 0.1                  # 10% BLER target
    TARGET_THROUGHPUT = 100            # Mbps minimum target

# =============================================================================
# CONFIGURACIÓN DE VISUALIZACIÓN
# =============================================================================
class VisualizationConfig:
    """Configuración para gráficos y visualización"""
    
    # Colores
    COLORS = {
        'gnb': 'red',
        'uav1': 'blue', 
        'uav2': 'green',
        'los': 'orange',
        'nlos': 'purple'
    }
    
    # Resolución de gráficos
    DPI = 150
    FIGSIZE = (12, 8)
    
    # Paths para outputs
    OUTPUT_DIR = './outputs'
    PLOTS_DIR = './outputs/plots'
    DATA_DIR = './outputs/data'

# =============================================================================
# UTILIDADES
# =============================================================================
def get_config_summary():
    """Retorna resumen de configuración para logging"""
    return {
        'frequency_ghz': RFConfig.FREQUENCY / 1e9,
        'gnb_antennas': AntennaConfig.GNB_ARRAY['num_rows'] * AntennaConfig.GNB_ARRAY['num_cols'],
        'uav_antennas': AntennaConfig.UAV_ARRAY['num_rows'] * AntennaConfig.UAV_ARRAY['num_cols'],
        'coverage_area_m2': (ScenarioConfig.COVERAGE_AREA['x_range'][1] - 
                             ScenarioConfig.COVERAGE_AREA['x_range'][0]) ** 2,
        'height_range': f"{min(ScenarioConfig.HEIGHT_RANGE)}-{max(ScenarioConfig.HEIGHT_RANGE)}m",
        'snr_range_db': f"{SimulationConfig.SNR_RANGE[0]}-{SimulationConfig.SNR_RANGE[-1]}"
    }

if __name__ == "__main__":
    print("=== UAV 5G NR System Configuration ===")
    print(f"Frequency: {RFConfig.FREQUENCY/1e9:.1f} GHz")
    print(f"gNB Array: {AntennaConfig.GNB_ARRAY['num_rows']}x{AntennaConfig.GNB_ARRAY['num_cols']} = {AntennaConfig.GNB_ARRAY['num_rows']*AntennaConfig.GNB_ARRAY['num_cols']} elements")
    print(f"UAV Array: {AntennaConfig.UAV_ARRAY['num_rows']}x{AntennaConfig.UAV_ARRAY['num_cols']} = {AntennaConfig.UAV_ARRAY['num_rows']*AntennaConfig.UAV_ARRAY['num_cols']} elements") 
    print(f"Coverage: {ScenarioConfig.COVERAGE_AREA['x_range'][1]*2}m x {ScenarioConfig.COVERAGE_AREA['y_range'][1]*2}m")
    print(f"Height Range: {min(ScenarioConfig.HEIGHT_RANGE)}-{max(ScenarioConfig.HEIGHT_RANGE)}m")