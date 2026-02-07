"""
Height Analysis Tool for 5G NR MIMO UAV Communications
========================================================
Analyzes throughput and path loss variation with UAV altitude
Using Sionna ray tracing for accurate channel modeling
"""

import tensorflow as tf
import numpy as np
import sionna
from sionna.rt import Transmitter, Receiver, PathSolver, PlanarArray, load_scene, Camera
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import os
import traceback

tf.get_logger().setLevel("INFO")

########################################
# CONFIGURATION CLASSES
########################################

class MIMO_Configuration:
    """Define standard 5G NR MIMO array configuration"""
    
    def __init__(self, name, tx_rows, tx_cols, rx_rows, rx_cols, 
                 description="", spacing=0.5, pattern="tr38901", polarization="VH"):
        self.name = name
        self.tx_rows = tx_rows
        self.tx_cols = tx_cols
        self.rx_rows = rx_rows
        self.rx_cols = rx_cols
        self.spacing = spacing
        self.pattern = pattern
        self.polarization = polarization
        self.description = description
        
        self.tx_antennas = tx_rows * tx_cols
        self.rx_antennas = rx_rows * rx_cols
        # VH polarization doubles antenna count in Sionna
        self.tx_antennas_sionna = self.tx_antennas * (2 if polarization == "VH" else 1)
        self.rx_antennas_sionna = self.rx_antennas * (2 if polarization == "VH" else 1)
        # 3GPP 38.211: max_layers limited by antenna count
        self.max_layers = min(self.tx_antennas, self.rx_antennas)

    def __repr__(self):
        return f"{self.name} ({self.tx_rows}x{self.tx_cols} Tx, {self.rx_rows}x{self.rx_cols} Rx)"

# Standard 5G NR MIMO configurations
MIMO_CONFIGS = {
    "SISO": MIMO_Configuration(
        name="SISO (1x1)",
        tx_rows=1, tx_cols=1, rx_rows=1, rx_cols=1,
        description="Single antenna TX and RX"
    ),
    "MIMO_2x2": MIMO_Configuration(
        name="MIMO 2x2",
        tx_rows=2, tx_cols=2, rx_rows=2, rx_cols=2,
        description="2x2 Dual-stream MIMO"
    ),
    "MIMO_4x4": MIMO_Configuration(
        name="MIMO 4x4",
        tx_rows=4, tx_cols=4, rx_rows=4, rx_cols=4,
        description="4x4 Massive MIMO"
    ),
    "MIMO_4x2": MIMO_Configuration(
        name="MIMO 4x2 (Asymmetric)",
        tx_rows=4, tx_cols=4, rx_rows=2, rx_cols=2,
        description="Asymmetric: 4x4 TX, 2x2 RX"
    ),
}

class RFNR_Config:
    """5G NR RF configuration"""
    CARRIER_FREQUENCY = 3.5e9  # Band n78
    BANDWIDTH = 20e6           # 20 MHz
    SUBCARRIER_SPACING = 15e3  # 15 kHz
    NUM_SUBCARRIERS = int(BANDWIDTH / SUBCARRIER_SPACING)

class ScenarioConfig:
    """3D scenario configuration for Munich"""
    GNB_POSITION = [110, 70, 20]      # gNB base station
    UAV1_POSITION = [50, 150, 35]    # Initial UAV position

########################################
# BEAMFORMING FUNCTIONS
########################################

def svd_multistream_beamforming(H, num_streams_max=None, beamforming_rank=None):
    """
    SVD-based multi-stream beamforming using NumPy (workaround for TensorFlow rectangular matrix bug)
    
    H: Channel matrix [rx_antennas, tx_antennas]
    num_streams_max: Maximum number of streams to allow
    beamforming_rank: If 1, use rank-1 beamforming (single best stream)
                     If None or >1, use spatial multiplexing (all available streams)
    
    Returns: (V, S_all, U, num_valid_streams, S_active)
    """
    try:
        # Use NumPy for SVD to avoid TensorFlow rectangular matrix bug
        H_np = H.numpy() if hasattr(H, 'numpy') else H
        U, S, Vh = np.linalg.svd(H_np, full_matrices=False)
        
        # Clamp small singular values to prevent numerical issues
        S_threshold = np.max(S) * 1e-5
        S_clamped = np.maximum(S, S_threshold)
        
        # Cap number of streams
        max_rank = min(U.shape[1], Vh.shape[0])
        if num_streams_max is not None:
            max_rank = min(max_rank, num_streams_max)
        
        # PROBLEMA 2 FIX: Select rank for beamforming vs spatial multiplexing
        if beamforming_rank == 1:
            # Beamforming: use only the strongest singular value
            active_rank = 1
        else:
            # Spatial multiplexing: use all available streams up to max_rank
            active_rank = max_rank
        
        # Count valid streams (S > threshold)
        valid_streams = np.sum(S_clamped > S_threshold)
        
        # Return: all singular values (for reference) + active ones for SINR calc
        return Vh.T, S_clamped, U, valid_streams, S_clamped[:active_rank]
        
    except Exception as e:
        print(f"SVD error: {e}")
        traceback.print_exc()
        return None, None, None, 0, np.array([-50.0])

def mrc_beamforming(H):
    """Maximum Ratio Combining beamforming"""
    H_conj_T = tf.transpose(tf.math.conj(H))
    # MRC: beamforming vector is conjugate of dominant right singular vector
    _, _, Vh = tf.linalg.svd(H, full_matrices=False)
    v_mrc = Vh[-1, :]  # Dominant right singular vector
    
    # SINR calculation
    channel_gain = tf.norm(tf.matmul(H, tf.expand_dims(v_mrc, 1)))
    interference = tf.norm(tf.matmul(H, tf.expand_dims(v_mrc, 1))) / tf.cast(H.shape[0], tf.float32)
    sinr = (channel_gain ** 2) / (1.0 + interference)
    sinr_db = 10 * tf.math.log10(sinr + 1e-10)
    sinr_db = tf.clip_by_value(sinr_db, -50.0, 50.0)  # CRITICAL: Clip
    
    return sinr_db

def zero_forcing_precoding(H):
    """
    Zero Forcing (ZF) Precoding - W = H^H (H H^H)^-1
    
    Cancels Inter-Stream Interference, optimal for spatial multiplexing
    """
    H_h = tf.transpose(tf.math.conj(H))
    HH_h = tf.matmul(H, H_h)
    HH_h_inv = tf.linalg.inv(HH_h + 1e-8 * tf.eye(tf.shape(HH_h)[0], dtype=H.dtype))
    W = tf.matmul(H_h, HH_h_inv)
    
    # Normalize columns to unit power
    col_norms = tf.sqrt(tf.reduce_sum(tf.abs(W)**2, axis=0, keepdims=True) + 1e-10)
    col_norms = tf.cast(col_norms, W.dtype)
    W_normalized = W / col_norms
    
    return W_normalized

def zero_forcing_beamforming(H):
    """Zero Forcing beamforming for multi-stream transmission"""
    try:
        W = zero_forcing_precoding(H)
        
        # Effective channel after ZF
        H_eff = tf.matmul(H, W)
        
        # SINR per stream (diagonal elements after ZF)
        diagonal_elements = tf.linalg.diag_part(H_eff)
        sinr_values = tf.cast(tf.abs(diagonal_elements) ** 2, tf.float32)
        
        sinr_db = 10 * tf.math.log10(sinr_values + 1e-10)
        sinr_db = tf.clip_by_value(sinr_db, -50.0, 50.0)  # CRITICAL: Clip
        
        # Count streams where SINR > threshold
        num_streams = tf.reduce_sum(tf.cast(sinr_values > 1e-3, tf.int32))
        
        return sinr_db, num_streams
        
    except Exception as e:
        print(f"Zero Forcing error: {e}")
        return tf.constant([-50.0]), tf.constant(1)

def get_physical_metrics(paths, bandwidth):
    """
    Extract RT-derived equivalent path loss from Sionna paths CIR
    
    ⚠️ This is NOT a 3GPP path loss model
    It's derived from total received power in the RT simulation
    
    Uses: P_rx = sum(|a_l|^2) where a_l are path gains
    """
    try:
        cir_result = paths.cir()
        # cir() returns tuple (a, tau) but handle both cases
        if isinstance(cir_result, (list, tuple)):
            a = cir_result[0]
        else:
            a = cir_result
        
        # Convert to numpy
        if hasattr(a, 'numpy'):
            a_np = a.numpy()
        else:
            a_np = np.array(a)
        
        # Total received power across all paths, RX and TX antennas
        power_rx_lin = np.sum(np.abs(a_np) ** 2)
        
        # Equivalent path loss: PL = TX_dBm - RX_dBm
        # This is derived from RT-simulated received power, not a model
        tx_power_dbm = 35.0  # 5G typical TX power
        power_rx_dbm = 10 * np.log10(power_rx_lin + 1e-12)
        path_loss_db = tx_power_dbm - power_rx_dbm
        
        # Ensure realistic range
        path_loss_db = np.clip(path_loss_db, 0, 150)
        
        return path_loss_db, power_rx_lin
        
    except Exception as e:
        print(f"Path loss calc error: {e}")
        return 100.0, 1e-6

def calculate_thermal_noise(bandwidth, nf_db=7.0, temp_k=290):
    """
    Thermal noise power: N = k*T*B*NF
    k = Boltzmann constant = 1.38e-23 J/K
    T = Temperature (K)
    B = Bandwidth (Hz)
    NF = Noise Figure (linear scale)
    """
    k_boltzmann = 1.38064852e-23
    nf_linear = 10 ** (nf_db / 10)
    noise_power = k_boltzmann * temp_k * bandwidth * nf_linear
    return noise_power

def calculate_sinr_with_noise(channel_gains, noise_power, tx_power_w, num_streams):
    """
    SINR físicamente correcto (MODELO B - Link Budget)
    
    SINR_i = (P_tx/N_s * |σ_i|²) / N
    
    Donde:
    - P_tx = potencia TX total en watts
    - N_s = número de streams
    - σ_i = valor singular (con path loss, fading, array gain)
    - N = ruido térmico en watts
    
    IMPORTANTE: normalize=False en CFR para que σ² tenga unidades de potencia
    """
    channel_gains = np.array(channel_gains)
    
    # Clip singular values para evitar overflow
    channel_gains = np.clip(channel_gains, 0, 1e3)
    
    # Potencia por stream
    tx_power_per_stream = tx_power_w / num_streams
    
    # Ecuación física correcta (con unidades coherentes)
    signal_power = tx_power_per_stream * (channel_gains ** 2)
    
    sinr_linear = signal_power / (noise_power + 1e-15)
    sinr_db = 10 * np.log10(sinr_linear + 1e-12)
    
    # NO clipear: dejar que el canal determine el SINR
    return sinr_db

def calculate_throughput(sinr_db_array, bandwidth=20e6):
    """
    Calculate throughput from SINR using Shannon capacity
    For SVD multi-stream: SUM capacities across streams
    
    Shannon capacity per stream: C_i = B * log2(1 + SINR_i)
    Total: C_total = sum(C_i) * BW
    """
    sinr_linear = tf.pow(10.0, sinr_db_array / 10.0)
    
    # Shannon capacity per stream (NO artificial cap - let physics work)
    capacity_per_stream = tf.math.log(1.0 + sinr_linear) / tf.math.log(2.0)
    
    # SUM capacities across all streams (proper MIMO gain)
    total_capacity = tf.reduce_sum(capacity_per_stream)
    
    # Total throughput
    throughput = total_capacity * bandwidth
    
    return throughput

def render_scene_3d(scene, tx, rx, paths, title="", return_image=False, num_samples=64):
    """
    Render 3D scene with ray tracing visualization
    Camera height adjusts dynamically with RX (UAV) altitude
    
    Args:
        scene: Sionna RT scene
        tx, rx: Transmitter and Receiver objects
        paths: Ray paths
        title: Plot title
        return_image: If True, return numpy array; if False, display plot
        num_samples: Number of ray samples for rendering (lower = faster but noisier)
    
    Returns:
        numpy array [H, W, 3] RGB if return_image=True, else None
    """
    try:
        # Define camera position - adjusted for RX height
        tx_pos = tx.position
        rx_pos = rx.position
        rx_height = rx_pos[2]  # Z-coordinate of RX (UAV altitude)
        
        # Camera positioned relative to TX but with Z adjusted to match RX height + offset
        # This ensures camera stays at proper distance to view both TX and RX at different altitudes
        cam_height = rx_height + 200  # Camera 200m above UAV for good perspective
        cam_pos = (tx_pos[0] + 200, tx_pos[1] + 30, cam_height)
        
        # Create camera
        cam = Camera(position=cam_pos)
        cam.look_at(tx)
        
        # Render scene - returns Mitsuba Bitmap
        bitmap = scene.render(camera=cam, paths=paths, return_bitmap=True, num_samples=num_samples)
        
        # Convert Mitsuba bitmap to numpy array [H, W, channels]
        img = np.array(bitmap)  # Usually [H, W, 3] or [H, W, 4]
        
        # Ensure proper dtype for imshow - matplotlib works best with uint8
        if img.dtype != np.uint8:
            # If float, convert to 0-255 range
            if np.issubdtype(img.dtype, np.floating):
                img = (np.clip(img, 0, 1) * 255).astype(np.uint8)
            else:
                img = img.astype(np.uint8)
        
        # Drop alpha channel if present, keep only RGB
        if img.shape[2] == 4:
            img = img[:, :, :3]  # [H, W, 3]
        
        if return_image:
            return img
        else:
            plt.figure(figsize=(12, 7))
            plt.imshow(img)
            plt.title(title, fontweight='bold', fontsize=14)
            plt.axis('off')
            plt.tight_layout()
            plt.show()
            return None
            
    except Exception as e:
        print(f"Render error: {e}")
        traceback.print_exc()
        return None if return_image else None

########################################
# HEIGHT ANALYSIS SIMULATION
########################################

def run_height_analysis(mimo_config_name="MIMO_4x4", beamforming_technique="SVD", 
                       num_heights=5, height_min=20, height_max=150):
    """
    Run height analysis for UAV communications
    
    Args:
        mimo_config_name: MIMO configuration ("SISO", "MIMO_2x2", "MIMO_4x4", "MIMO_4x2")
        beamforming_technique: "SVD" or "ZF"
        num_heights: Number of height points to analyze
        height_min, height_max: Height range in meters
    
    Returns:
        results dict with height analysis data
    """
    
    print(f"\n{'='*70}")
    print(f"HEIGHT ANALYSIS FOR {mimo_config_name} WITH {beamforming_technique}")
    print(f"{'='*70}")
    
    # Get MIMO configuration
    if mimo_config_name not in MIMO_CONFIGS:
        print(f"Error: Unknown MIMO config {mimo_config_name}")
        return None
    
    config = MIMO_CONFIGS[mimo_config_name]
    print(f"\nConfiguration: {config}")
    print(f"Beamforming: {beamforming_technique}")
    print(f"Heights: {num_heights} points from {height_min}m to {height_max}m")
    
    # Create height range
    heights = np.linspace(height_min, height_max, num_heights)
    
    # Load Munich scene
    print("\nLoading Sionna Munich scene...")
    try:
        scene = load_scene(sionna.rt.scene.munich)
        carrier_frequency = RFNR_Config.CARRIER_FREQUENCY
        scene.frequency = carrier_frequency
        scene.tx_array = PlanarArray(num_rows=config.tx_rows, num_cols=config.tx_cols,
                                    vertical_spacing=config.spacing,
                                    horizontal_spacing=config.spacing,
                                    pattern=config.pattern,
                                    polarization=config.polarization)
        scene.rx_array = PlanarArray(num_rows=config.rx_rows, num_cols=config.rx_cols,
                                    vertical_spacing=config.spacing,
                                    horizontal_spacing=config.spacing,
                                    pattern=config.pattern,
                                    polarization=config.polarization)
        print("✓ Scene loaded successfully")
    except Exception as e:
        print(f"Error loading scene: {e}")
        return None
    
    # Create transmitter and receiver
    gnb_pos = np.array(ScenarioConfig.GNB_POSITION, dtype=np.float32)
    uav_2d_pos = np.array([50, 150], dtype=np.float32)
    
    tx = Transmitter(name="GNB", position=gnb_pos)
    scene.add(tx)
    
    # Initialize results storage
    results = {
        'heights': heights,
        'throughput_mbps': [],
        'path_loss_db': [],
        'snr_db': [],
        'channel_gain_db': [],
        'los_condition': [],
        'renders': []  # Usar lista indexada por i, no por altura (evita problemas de floats)
    }
    
    # Analyze each height
    rx = None  # Track current RX to remove later
    
    for i, height in enumerate(heights):
        print(f"\n[{i+1}/{num_heights}] Height: {height:.1f}m", end=" ")
        
        try:
            # Remove previous RX if it exists
            if rx is not None:
                scene.remove(rx.name)
            
            # Set UAV position
            uav_pos = np.concatenate([uav_2d_pos, np.array([height])])
            
            # Create new receiver with unique name per iteration
            rx_name = f"UAV_{i}"
            rx = Receiver(name=rx_name, position=uav_pos)
            scene.add(rx)
            
            # Make TX look at RX
            tx.look_at(rx)
            
            # Compute paths using PathSolver
            paths = PathSolver()(scene)
            
            if paths is None:
                print("⚠ No paths found")
                results['throughput_mbps'].append(100.0)
                results['path_loss_db'].append(140.0)
                results['snr_db'].append(-20.0)
                results['channel_gain_db'].append(-140.0)
                results['los_condition'].append('None')
                results['renders'].append(None)
                continue
            
            # Extract channel matrix using CFR at multiple frequencies
            try:
                # Create frequency range for 5G NR
                carrier_frequency = RFNR_Config.CARRIER_FREQUENCY
                bandwidth = RFNR_Config.BANDWIDTH
                num_subcarriers = RFNR_Config.NUM_SUBCARRIERS
                
                # Reduce subcarriers at extreme heights to avoid GPU exhaustion
                if height > 110:
                    num_subcarriers = 256  # Reduce from 1333 to avoid GPU memory exhaustion
                
                subcarrier_spacing = RFNR_Config.SUBCARRIER_SPACING
                
                frequencies = tf.linspace(
                    carrier_frequency - (num_subcarriers//2) * subcarrier_spacing,
                    carrier_frequency + (num_subcarriers//2 - 1) * subcarrier_spacing,
                    num_subcarriers
                )
                
                # Get channel frequency response
                # MODELO B (físico): normalize=False para consistencia de unidades
                # H contendrá path loss, fading y array gain reales
                cfr = paths.cfr(frequencies=frequencies, normalize=False, out_type="tf")
                
                # Extract channel matrix for first subcarrier
                #H = cfr[0, :, :, 0]  # [num_rx, num_tx]
                H = tf.reduce_mean(cfr[:, :, :, 0], axis=0)
                H = tf.cast(H, tf.complex64)
                
                #  CORRECTO: Obtener path loss desde paths CIR, no desde H
                path_loss_db, power_rx_lin = get_physical_metrics(paths, RFNR_Config.BANDWIDTH)

                
                #  CORRECTO: Calcular ruido térmico físico
                noise_power = calculate_thermal_noise(RFNR_Config.BANDWIDTH, nf_db=7.0)
                
                #  TX power REAL en watts (necesario para Modelo B físico)
                tx_power_dbm = 35.0  # 5G typical
                tx_power_w = 10 ** ((tx_power_dbm - 30) / 10)  # Convert dBm to watts
                
                
                # Beamforming + SINR con ruido físico
                if beamforming_technique == "SVD":
                    V, S_all, U, valid_streams, S_active = svd_multistream_beamforming(
                        H, config.max_layers, beamforming_rank=None  # Spatial multiplexing
                    )
                    
                    #  CORRECCIÓN: SNR FÍSICO desde power_rx_lin (del CIR, no desde H)
                    # power_rx_lin es la potencia recibida REAL del ray tracing
                    # Los valores singulares SOLO reparten esa potencia entre streams
                    snr_linear_global = power_rx_lin / (noise_power + 1e-15)
                    snr_db_global = 10 * np.log10(snr_linear_global + 1e-12)
                    
                    # Repartir potencia proporcional por stream (ganancia modal relativa)
                    # IMPORTANTE: Normalizar sigma para evitar overflow
                    sigma_norm = S_active / (np.max(S_active) + 1e-12)
                    sigma2_norm = (sigma_norm ** 2) / (np.sum(sigma_norm ** 2) + 1e-12)
                    
                    # SINR por stream = SNR global + redistribución modal
                    # ESTO ES CORRECTO FÍSICAMENTE: no creas potencia, solo reparte la que hay
                    sinr_db_svd = snr_db_global + 10 * np.log10(sigma2_norm + 1e-12)
                    sinr_db = np.mean(sinr_db_svd)
                    
                    #  Throughput suma streams correctamente
                    throughput = calculate_throughput(tf.constant(sinr_db_svd, dtype=tf.float32), 
                                                     bandwidth=RFNR_Config.BANDWIDTH).numpy() / 1e6
                else:  # ZF
                    sinr_db_zf, num_streams_zf = zero_forcing_beamforming(H)
                    sinr_db = tf.reduce_mean(sinr_db_zf).numpy()
                    throughput = calculate_throughput(sinr_db_zf, 
                                                     bandwidth=RFNR_Config.BANDWIDTH).numpy() / 1e6
                
                #  ELIMINADO: Umbral artificial que mata la física
                # El throughput debe decaer suavemente con path loss, no de golpe a cero
                
                # Cálculos finales
                snr_db = sinr_db
                channel_gain_db = -path_loss_db
                
                # Determine LoS
                los_condition = 'LoS' if hasattr(paths, 'los') and paths.los else 'NLoS'
                
                # Capture render - reduce samples for high altitudes to avoid GPU exhaustion
                try:
                    print(f"   Capturing 3D render...", end="")
                    # Use fewer samples at extreme heights to avoid GPU memory exhaustion
                    num_render_samples = 16 if height > 120 else 64
                    scene_3d_image = render_scene_3d(scene, tx, rx, paths, 
                                                     title=f"Height: {height:.0f}m, Throughput: {throughput:.0f} Mbps",
                                                     return_image=True,
                                                     num_samples=num_render_samples)
                    results['renders'].append(scene_3d_image)
                    if scene_3d_image is not None:
                        print(f" ✓ Captured ({scene_3d_image.shape[1]}×{scene_3d_image.shape[0]})")
                    else:
                        print(f" ✗ Failed")
                except Exception as e:
                    print(f" ✗ Error: {str(e)[:50]}")
                    results['renders'].append(None)
                

                results['throughput_mbps'].append(throughput)
                results['path_loss_db'].append(path_loss_db)
                results['snr_db'].append(snr_db)
                results['channel_gain_db'].append(channel_gain_db)
                results['los_condition'].append(los_condition)
                
                print(f"✓ {throughput:.0f} Mbps, PL={path_loss_db:.1f}dB, SNR={snr_db:.1f}dB ({los_condition})")
                
            except Exception as e:
                print(f"Channel extraction error: {e}")
                results['throughput_mbps'].append(100.0)
                results['path_loss_db'].append(140.0)
                results['snr_db'].append(-20.0)
                results['channel_gain_db'].append(-140.0)
                results['los_condition'].append('Error')
                results['renders'].append(None)
                
        except Exception as e:
            print(f"Error at height {height}: {e}")
            results['throughput_mbps'].append(100.0)
            results['path_loss_db'].append(140.0)
            results['snr_db'].append(-20.0)
            results['channel_gain_db'].append(-140.0)
            results['los_condition'].append('Error')
            results['renders'].append(None)
    
    # Convert to numpy arrays
    results['throughput_mbps'] = np.array(results['throughput_mbps'])
    results['path_loss_db'] = np.array(results['path_loss_db'])
    results['snr_db'] = np.array(results['snr_db'])
    results['channel_gain_db'] = np.array(results['channel_gain_db'])
    
    return results

########################################
# VISUALIZATION
########################################

def plot_height_analysis(results, mimo_config_name, beamforming_technique):
    """
    Generate dual-axis plot: Throughput + Path Loss vs Height
    """
    heights = results['heights']
    throughput = results['throughput_mbps']
    path_loss = results['path_loss_db']
    snr = results['snr_db']
    los = results['los_condition']
    
    # Create figure with dual y-axes
    fig, ax1 = plt.subplots(figsize=(14, 8))
    
    # Plot 1: Throughput (left axis)
    color1 = 'tab:blue'
    ax1.set_xlabel('UAV Height [m]', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Throughput [Mbps]', color=color1, fontsize=14, fontweight='bold')
    line1 = ax1.plot(heights, throughput, color=color1, marker='o', linewidth=3, 
                     markersize=10, label='Throughput')
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.grid(True, alpha=0.3)
    
    # Highlight optimal height
    opt_idx = np.argmax(throughput)
    opt_height = heights[opt_idx]
    opt_throughput = throughput[opt_idx]
    ax1.scatter([opt_height], [opt_throughput], color='red', s=300, marker='*', 
               zorder=5, edgecolors='darkred', linewidth=2)
    ax1.annotate(f'Optimal: {opt_height:.0f}m\n{opt_throughput:.0f} Mbps',
                xy=(opt_height, opt_throughput), xytext=(10, 10),
                textcoords='offset points', fontsize=11, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.8),
                arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0', color='red'))
    
    # Plot 2: Path Loss (right axis)
    ax2 = ax1.twinx()
    color2 = 'tab:red'
    ax2.set_ylabel('Path Loss [dB]', color=color2, fontsize=14, fontweight='bold')
    line2 = ax2.plot(heights, path_loss, color=color2, marker='s', linewidth=3, 
                     markersize=8, linestyle='--', label='Path Loss')
    ax2.tick_params(axis='y', labelcolor=color2)
    
    # Title and legend
    title = f'Height Analysis: {mimo_config_name} with {beamforming_technique}\nThroughput & Path Loss vs UAV Altitude'
    fig.suptitle(title, fontsize=16, fontweight='bold', y=0.98)
    
    # Combined legend
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax1.legend(lines, labels, loc='upper left', fontsize=12, framealpha=0.9)
    
    # Add table with statistics
    table_data = []
    for i, h in enumerate(heights):
        table_data.append([
            f'{h:.1f}',
            f'{throughput[i]:.1f}',
            f'{path_loss[i]:.1f}',
            f'{snr[i]:.1f}'
        ])
    
    # Table position
    table = ax1.table(cellText=table_data,
                     colLabels=['Height (m)', 'TP (Mbps)', 'PL (dB)', 'SNR (dB)'],
                     cellLoc='center',
                     loc='bottom',
                     bbox=[0, -0.35, 1, 0.25])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.8)
    
    # Color header
    for i in range(4):
        table[(0, i)].set_facecolor('#40466e')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.35)
    
    return fig

def plot_height_renders_grid(results, mimo_config_name, beamforming_technique):
    """
    Generate grid of 3D renders at each height
    Matches mimo_beam.py exactly: imshow() → set_title() → axis('off')
    """
    heights = results['heights']
    renders = results['renders']  # Lista con imágenes numpy uint8 [H, W, 3]
    num_heights = len(heights)
    throughputs = results['throughput_mbps']
    path_losses = results['path_loss_db']
    
    # Determine grid layout (1xN or 2xN)
    if num_heights <= 3:
        rows, cols = 1, num_heights
    else:
        rows = 2
        cols = (num_heights + 1) // 2
    
    fig = plt.figure(figsize=(6*cols, 5*rows))
    
    for i, height in enumerate(heights):
        ax = plt.subplot(rows, cols, i+1)
        
        img = renders[i]  # Get render by index from list [H, W, 3]
        
        # EXACTLY like mimo_beam.py: imshow first, then set_title, then axis('off')
        if img is not None and isinstance(img, np.ndarray) and img.size > 0:
            # Validate image
            if len(img.shape) == 3 and img.shape[2] >= 3:
                try:
                    ax.imshow(img)  # Display the render image [H, W, 3] uint8
                    tp_val = throughputs[i]
                    pl_val = path_losses[i]
                    ax.set_title(f'Height: {height:.0f}m | TP: {tp_val:.0f} Mbps | PL: {pl_val:.1f} dB',
                                fontsize=11, fontweight='bold', color='darkblue')
                except Exception as e:
                    ax.text(0.5, 0.5, f'Display Error:\n{str(e)[:40]}', 
                           ha='center', va='center', fontsize=10, color='red', transform=ax.transAxes)
                    ax.set_title(f'Height: {height:.0f}m (Error)', fontsize=11, fontweight='bold', color='red')
            else:
                # Invalid image shape
                ax.text(0.5, 0.5, f'Invalid Image\nShape: {img.shape}', 
                       ha='center', va='center', fontsize=10, color='red', transform=ax.transAxes)
                ax.set_title(f'Height: {height:.0f}m (Invalid)', fontsize=11, fontweight='bold', color='red')
        else:
            # Fallback: show text placeholder
            ax.text(0.5, 0.5, f'No Render\nHeight: {height:.0f}m', 
                   ha='center', va='center', fontsize=12, color='red', transform=ax.transAxes)
            ax.set_title(f'Height: {height:.0f}m (Not Captured)', fontsize=11, fontweight='bold', color='red')
        
        ax.axis('off')  # Turn off axis AFTER imshow()
    
    fig.suptitle(f'3D Ray Tracing Renders - {mimo_config_name} ({beamforming_technique})',
                fontsize=14, fontweight='bold', y=0.98)
    
    plt.tight_layout()
    
    return fig

########################################
# MAIN EXECUTION
########################################

if __name__ == "__main__":
    # Configuration
    MIMO_CONFIG = "MIMO_4x4"
    BEAMFORMING = "SVD"  # or "ZF"
    NUM_HEIGHTS = 5
    HEIGHT_MIN = 14
    HEIGHT_MAX = 120  # Reduced from 150 to avoid GPU memory exhaustion at extreme heights
    
    print(f"\n{'#'*70}")
    print(f"# 5G NR MIMO UAV HEIGHT ANALYSIS")
    print(f"#{'='*68}#")
    print(f"# MIMO Config: {MIMO_CONFIG:40}")
    print(f"# Beamforming: {BEAMFORMING:40}")
    print(f"# Heights: {NUM_HEIGHTS} points [{HEIGHT_MIN}m - {HEIGHT_MAX}m]")
    print(f"{'#'*70}\n")
    
    # Run analysis
    results = run_height_analysis(mimo_config_name=MIMO_CONFIG,
                                 beamforming_technique=BEAMFORMING,
                                 num_heights=NUM_HEIGHTS,
                                 height_min=HEIGHT_MIN,
                                 height_max=HEIGHT_MAX)
    
    if results is None:
        print("Height analysis failed!")
        exit(1)
    
    # Generate plots
    print("\nGenerating visualizations...")
    
    fig1 = plot_height_analysis(results, MIMO_CONFIG, BEAMFORMING)
    output_file1 = f"height_analysis_{MIMO_CONFIG}_{BEAMFORMING}.png"
    fig1.savefig(output_file1, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✓ Saved: {output_file1}")
    plt.show()
    plt.close(fig1)
    
    fig2 = plot_height_renders_grid(results, MIMO_CONFIG, BEAMFORMING)
    output_file2 = f"height_renders_{MIMO_CONFIG}_{BEAMFORMING}.png"
    fig2.savefig(output_file2, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✓ Saved: {output_file2}")
    plt.show()
    plt.close(fig2)
    
    # Summary
    print(f"\n{'='*70}")
    print("HEIGHT ANALYSIS SUMMARY")
    print(f"{'='*70}")
    opt_idx = np.argmax(results['throughput_mbps'])
    min_tp = np.min(results['throughput_mbps'])
    max_tp = results['throughput_mbps'][opt_idx]
    
    print(f"Optimal height: {results['heights'][opt_idx]:.1f}m")
    print(f"Max throughput: {max_tp:.1f} Mbps")
    print(f"Min throughput: {min_tp:.1f} Mbps")
    print(f"Avg throughput: {np.mean(results['throughput_mbps']):.1f} Mbps")
    if min_tp > 0:
        print(f"Throughput gain (max/min): {max_tp/min_tp:.2f}x")
    else:
        print(f"Throughput gain (max/min): Infinite (min=0)")
    print(f"{'='*70}\n")
