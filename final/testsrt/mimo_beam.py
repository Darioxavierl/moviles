import tensorflow as tf
import numpy as np
import sionna
from sionna.rt import Transmitter, Receiver, PathSolver, PlanarArray, load_scene, Camera
import matplotlib.pyplot as plt

tf.get_logger().setLevel("INFO")

########################################
# CLASE PARA CONFIGURACIONES MIMO EXPLÍCITA
########################################
class MIMO_Configuration:
    """Define configuración estándar 5G NR de arrays MIMO con descripción explícita"""
    
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
        # Account for dual polarization (VH) which doubles antenna count in Sionna
        self.tx_antennas_sionna = self.tx_antennas * (2 if polarization == "VH" else 1)
        self.rx_antennas_sionna = self.rx_antennas * (2 if polarization == "VH" else 1)
        # 3GPP 38.211: max_layers limited by total antenna count, not spatial dimensions
        # Use actual antenna count including polarization since that's what Sionna produces
        #self.max_layers = min(self.tx_antennas_sionna, self.rx_antennas_sionna)
        self.max_layers = min(self.tx_antennas, self.rx_antennas)

        
    def __repr__(self):
        return f"{self.name} ({self.tx_rows}x{self.tx_cols} Tx, {self.rx_rows}x{self.rx_cols} Rx)"
    
    def get_full_description(self):
        """Retorna descripción completa de la configuración"""
        return f"""
╔════════════════════════════════════════════════════════════════╗
║ CONFIGURACIÓN: {self.name}
╠════════════════════════════════════════════════════════════════╣
║ Antenas TX: {self.tx_antennas} ({self.tx_rows}x{self.tx_cols})
║ Antenas RX: {self.rx_antennas} ({self.rx_rows}x{self.rx_cols})
║ Max Layers (3GPP 38.211): {self.max_layers}
║ Descripción: {self.description}
║ Espaciamiento: λ/{1/self.spacing}
║ Polarización: {self.polarization}
╚════════════════════════════════════════════════════════════════╝
"""

# CONFIGURACIONES ESTÁNDAR 5G NR - EXPLÍCITAS
MIMO_CONFIGS = {
    "SISO": MIMO_Configuration(
        name="SISO (1x1)",
        tx_rows=1, tx_cols=1, rx_rows=1, rx_cols=1,
        description="Single antenna TX and RX. No beamforming, no diversity, no spatial multiplexing."
    ),
    "MIMO_2x2": MIMO_Configuration(
        name="MIMO 2x2 (SU-MIMO)",
        tx_rows=2, tx_cols=2, rx_rows=2, rx_cols=2,
        description="2 TX antennas, 2 RX antennas. Supports up to 2 parallel streams (layers). "
                    "Beamforming with TX/RX diversity and spatial multiplexing."
    ),
    "MIMO_4x4": MIMO_Configuration(
        name="MIMO 4x4 (Massive MIMO)",
        tx_rows=4, tx_cols=4, rx_rows=4, rx_cols=4,
        description="4 TX antennas (4x4 array), 4 RX antennas (4x4 array). Supports up to 4 parallel streams. "
                    "Strong beamforming gains, high diversity, full spatial multiplexing."
    ),
    "MIMO_4x2": MIMO_Configuration(
        name="MIMO 8x8 TX, 2x2 RX (Asymmetric)",
        tx_rows=4, tx_cols=4, rx_rows=2, rx_cols=2,
        description="4x4 TX array (16 antennas), 2x2 RX array (4 antennas). Limited by RX: max 2 layers. "
                    "Massive MIMO on TX side, limited RX diversity."
    ),
}

class ScenarioConfig:
    """Configuración del escenario 3D Munich"""
    
    # Posiciones fijas
    GNB_POSITION = [110, 70, 20]      # gNB sobre edificio más alto (45m) + 5m antenas
    
    # Posiciones iniciales UAV
    UAV1_POSITION = [50, 150, 35]    # UAV1 a 45m altura

class RFNR_Config:
    """Configuración de parámetros 5G NR para simulación"""
    CARRIER_FREQUENCY = 3.5e9  # Band n78
    BANDWIDTH = 20e6           # 20 MHz
    SUBCARRIER_SPACING = 15e3  # 15 kHz
    NUM_SUBCARRIERS = int(BANDWIDTH / SUBCARRIER_SPACING)

########################################
# Helper: obtener matriz MIMO por subportadora
########################################
def get_Hk(Hf, k):
    return Hf[0, :, 0, :, 0, k]

########################################
# Helper: Renderizar escena 3D con ray tracing
########################################
def render_scene_3d(scene, tx, rx, paths, title="3D Scene Visualization", return_image=False):
    """
    Renderiza la escena 3D con ray tracing usando una cámara posicionada
    
    Args:
        scene: Escena de Sionna
        tx: Transmisor
        rx: Receptor
        paths: Paths calculados previamente (resultado de PathSolver)
        title: Título de la ventana
        return_image: Si True, devuelve la imagen como numpy array sin mostrarla
    
    Returns:
        img: Imagen renderizada como numpy array (si return_image=True), None en caso contrario
    """
    try:
        # Posicionar cámara a una distancia relativa del TX
        # Offset: 200m en X, 30m en Y, 150m en Z respecto a TX
        tx_pos = tx.position
        cam_pos = (tx_pos[0] + 200, tx_pos[1] + 30, tx_pos[2] + 150)
        
        # Crear cámara
        cam = Camera(position=cam_pos)
        cam.look_at(tx)
        
        # Render de la escena con los paths ya calculados
        # return_bitmap=True devuelve Mitsuba Bitmap en lugar de plt.Figure
        bitmap = scene.render(camera=cam, paths=paths, return_bitmap=True, num_samples=64)
        
        # Convertir Mitsuba Bitmap a numpy array
        # Mitsuba Bitmap tiene método convert() para obtener array
        img = np.array(bitmap)  # Numpy array [height, width, 3 or 4]
        
        if return_image:
            # Devolver imagen como numpy array sin mostrar
            print(f" Render 3D capturado ({img.shape}): {title}")
            return img
        else:
            # Mostrar imagen (modo standalone)
            plt.figure(figsize=(12, 8))
            plt.imshow(img)
            plt.title(title, fontweight='bold', fontsize=14)
            plt.axis("off")
            plt.tight_layout()
            plt.show()
            print(f" Render 3D mostrado: {title}")
            return None
        
    except Exception as e:
        print(f" Error al renderizar escena: {e}")
        print("   Continuando sin visualización 3D...")
        import traceback
        traceback.print_exc()
        return None

########################################
# TÉCNICAS DE PRECODING/BEAMFORMING TRANSMISIÓN
########################################

def svd_multistream_beamforming(H, num_streams_max=None):
    """
    Multi-stream SVD Beamforming using multiple singular vectors
    Utiliza los primeros r valores singulares para múltiples streams en paralelo
    
    H = U Σ V^H
    TX Precoding: W = V[:, 0:r]  (primeras r columnas de V)
    RX Combining: U[:, 0:r]  (primeras r columnas de U)
    
    Cada stream i usa el i-ésimo vector singular para máxima ganancia
    SINR_i = |σ_i|^2 * SNR / Ns
    
    Args:
        H: Canal MIMO [rx_ants, tx_ants]
        num_streams_max: Número máximo de streams (limitado por rank del canal)
    
    Returns:
        W: Precoding matrix [tx_ants, r]
        U_keep: RX combining matrix [rx_ants, r]
        S: Singular values [r]
        r: Número efectivo de streams
    """
    # Compute full SVD decomposition using NumPy
    # WORKAROUND: Use NumPy SVD because tf.linalg.svd has bugs with rectangular matrices
    # where Vh gets transposed for m < n case
    H_np = H.numpy() if hasattr(H, 'numpy') else H
    U_np, S_np, Vh_np = np.linalg.svd(H_np, full_matrices=False)  # NumPy returns (U, S, Vh)
    
    S = tf.constant(S_np, dtype=tf.float32)
    U = tf.constant(U_np, dtype=H.dtype)
    Vh = tf.constant(Vh_np, dtype=H.dtype)
    
    # Determine rank of channel (número de streams independientes)
    # S es float32 (los singular values siempre son reales y positivos)
    S_float = tf.cast(tf.math.abs(S), tf.float32)
    s_threshold = 1e-6 * S_float[0]  # 0.0001% del máximo singular value
    rank = tf.reduce_sum(tf.cast(S_float > s_threshold, tf.int32)).numpy()
    rank = max(rank, 1)  # Al menos 1 stream
    
    # Limitar por número máximo de streams solicitado
    if num_streams_max is not None:
        rank = min(rank, num_streams_max)
    
    # Limitar por dimensiones del canal
    rank = min(rank, H.shape[0], H.shape[1])
    
    # Handle SISO case where U and Vh might be 1D
    if H.shape[0] == 1 or H.shape[1] == 1 or len(U.shape) == 1:
        # SISO: solo 1 stream posible
        rank = 1
        W = tf.ones([H.shape[1]], dtype=H.dtype) / tf.sqrt(tf.cast(H.shape[1], H.dtype))
        W = tf.reshape(W, [-1, 1])  # [tx_ants, 1]
        
        U_keep = tf.ones([H.shape[0]], dtype=H.dtype) / tf.sqrt(tf.cast(H.shape[0], H.dtype))
        U_keep = tf.reshape(U_keep, [-1, 1])  # [rx_ants, 1]
        
        S_keep = tf.abs(S[0:1])  # [1]
        
        return W, U_keep, S_keep, rank
    
    # Extraer los primeros 'rank' vectores singulares
    # V tiene shape [1, tx_ants, tx_ants] después de SVD (full_matrices=False)
    # pero Vh es [min(rx, tx), tx_ants]
    W = tf.math.conj(Vh[:rank, :])  # [rank, tx_ants] - primeras r filas de V^H conjugadas
    W = tf.transpose(W)  # [tx_ants, rank] - transponer para obtener V columnas
    
    U_keep = tf.math.conj(U[:, :rank])  # [rx_ants, rank] - primeras r columnas de U conjugadas
    S_keep = S[:rank]  # [rank] - primeros r singular values
    
    # Normalizar columnas de W para potencia unitaria
    col_norms = tf.sqrt(tf.reduce_sum(tf.abs(W)**2, axis=0, keepdims=True) + 1e-10)
    col_norms = tf.cast(col_norms, W.dtype)
    W_normalized = W / col_norms
    
    return W_normalized, U_keep, S_keep, rank

def svd_beamforming(H):
    """
    SVD-based Beamforming (Transmit + Receive)
    Óptimo para maximizar SNR en SINGLE STREAM
    
    H = U Σ V^H
    TX Beamforming: w_tx = conj(V[:, 0])  (right singular vector)
    RX Beamforming: w_rx = conj(U[:, 0])  (left singular vector)
    """
    # Compute full SVD decomposition using NumPy
    # WORKAROUND: Use NumPy SVD because tf.linalg.svd has bugs with rectangular matrices
    H_np = H.numpy() if hasattr(H, 'numpy') else H
    U_np, S_np, Vh_np = np.linalg.svd(H_np, full_matrices=False)  # NumPy returns (U, S, Vh)
    
    S = tf.constant(S_np, dtype=tf.float32)
    U = tf.constant(U_np, dtype=H.dtype)
    Vh = tf.constant(Vh_np, dtype=H.dtype)
    
    # Handle SISO (1×1) case where SVD returns scalars or 1D arrays
    if len(H.shape) == 1 or (H.shape[0] == 1 and H.shape[1] == 1) or len(U.shape) == 1:
        # SISO or edge case: just use uniform weights
        w_tx = tf.ones([H.shape[-1]], dtype=H.dtype) / tf.sqrt(tf.cast(H.shape[-1], H.dtype))
        w_rx = tf.ones([H.shape[0]], dtype=H.dtype) / tf.sqrt(tf.cast(H.shape[0], H.dtype))
        sigma_max = S[0] if len(S.shape) > 0 else S
    else:
        # MIMO: Extract dominant singular vectors
        # Ensure correct shapes: Vh[0, :] should be [tx_antennas]
        w_tx = tf.math.conj(Vh[0, :])
        # Handle case where U is 1D (shouldn't happen but just in case)
        w_rx = tf.math.conj(U[:, 0]) if len(U.shape) > 1 else tf.math.conj(U)
        
        # Reshape to 1D to ensure correct vector format
        w_tx = tf.reshape(w_tx, [-1])
        w_rx = tf.reshape(w_rx, [-1])
        
        # Normalize to unit power (with proper dtype casting)
        norm_tx = tf.sqrt(tf.reduce_sum(tf.abs(w_tx)**2) + 1e-10)
        norm_rx = tf.sqrt(tf.reduce_sum(tf.abs(w_rx)**2) + 1e-10)
        
        # Cast norms to complex dtype to match w vectors
        norm_tx = tf.cast(norm_tx, w_tx.dtype)
        norm_rx = tf.cast(norm_rx, w_rx.dtype)
        
        w_tx = w_tx / norm_tx
        w_rx = w_rx / norm_rx
        
        sigma_max = S[0]
    
    return w_tx, w_rx, sigma_max

def mrc_beamforming_tx(H):
    """
    Maximum Ratio Transmission (MRT) - Transmit Beamforming
    w_tx = conj(H.T) / ||H||
    
    Proporciona TX diversity
    """
    H_h = tf.transpose(tf.math.conj(H))
    w_tx = tf.reduce_sum(H_h, axis=1)
    norm = tf.sqrt(tf.reduce_sum(tf.abs(w_tx)**2) + 1e-8)
    w_tx = w_tx / tf.cast(norm, w_tx.dtype)
    return w_tx

def mrc_beamforming_rx(H):
    """
    Maximum Ratio Combining (MRC) - Receive Beamforming
    w_rx = conj(H) / ||H||
    
    Proporciona RX diversity: suma coherentemente todas las antenas RX
    """
    H_conj = tf.math.conj(H)
    w_rx = tf.reduce_sum(H_conj, axis=1)
    norm = tf.sqrt(tf.reduce_sum(tf.abs(w_rx)**2) + 1e-8)
    w_rx = w_rx / tf.cast(norm, w_rx.dtype)
    return w_rx

def zero_forcing_precoding(H):
    """
    Zero Forcing (ZF) Precoding - Transmit Beamforming para MIMO
    W = H^H (H H^H)^-1
    
    Cancela Inter-Stream Interference (ISI)
    Óptimo para SPATIAL MULTIPLEXING (multi-stream)
    
    Con normalización de columnas para evitar amplificación de ruido
    """
    H_h = tf.transpose(tf.math.conj(H))
    HH_h = tf.matmul(H, H_h)
    HH_h_inv = tf.linalg.inv(HH_h + 1e-8 * tf.eye(tf.shape(HH_h)[0], dtype=H.dtype))
    W = tf.matmul(H_h, HH_h_inv)
    
    # NUEVO: Normalize columns to unit power (critical for fair comparison)
    col_norms = tf.sqrt(tf.reduce_sum(tf.abs(W)**2, axis=0, keepdims=True) + 1e-10)
    col_norms = tf.cast(col_norms, W.dtype)  # Cast to complex
    W_normalized = W / col_norms
    
    return W_normalized

########################################
# FUNCIÓN PRINCIPAL DE SIMULACIÓN
########################################
def run_mimo_simulation(config_name="MIMO_4x4", mcs_index=16):
    """
    Ejecuta simulación MIMO con 3 técnicas de beamforming:
    1. SVD Beamforming: Single stream óptimo (TX+RX BF)
    2. MRC Beamforming: Single stream robusto (TX diversity + RX diversity)
    3. Zero Forcing: Multi-stream (Spatial Multiplexing con precoding)
    
    Returns: tuple (results, scene_3d_image)
    """
    
    config = MIMO_CONFIGS[config_name]
    
    # Mostrar configuración explícita
    print(config.get_full_description())
    
    ########################################
    # SETUP: Scene & Ray Tracing
    ########################################
    scene = load_scene(sionna.rt.scene.munich)
    
    scene.tx_array = PlanarArray(
        num_rows=config.tx_rows, num_cols=config.tx_cols, 
        vertical_spacing=config.spacing, horizontal_spacing=config.spacing,
        pattern=config.pattern, polarization=config.polarization
    )
    scene.rx_array = PlanarArray(
        num_rows=config.rx_rows, num_cols=config.rx_cols, 
        vertical_spacing=config.spacing, horizontal_spacing=config.spacing,
        pattern=config.pattern, polarization=config.polarization
    )
    scene.frequency = RFNR_Config.CARRIER_FREQUENCY
    
    tx = Transmitter("gNB", position=(ScenarioConfig.GNB_POSITION))
    rx = Receiver("UAV", position=(ScenarioConfig.UAV1_POSITION))
    
    scene.add(tx)
    scene.add(rx)
    tx.look_at(rx)
    
    ########################################
    # RAY TRACING - Calcular paths UNA SOLA VEZ
    ########################################
    paths = PathSolver()(scene)
    
    # Renderizar escena 3D y capturar imagen
    print("\n Capturando escena 3D...")
    scene_3d_image = render_scene_3d(scene, tx, rx, paths, 
                                     title=f"3D Ray Tracing - {config.name}",
                                     return_image=True)  # ← Devuelve imagen, no muestra
    
    ########################################
    # 5G NR CONFIGURATION
    ########################################
    carrier_frequency = RFNR_Config.CARRIER_FREQUENCY  # Band n78
    bandwidth = RFNR_Config.BANDWIDTH
    num_subcarriers = RFNR_Config.NUM_SUBCARRIERS
    subcarrier_spacing = RFNR_Config.SUBCARRIER_SPACING
    
    frequencies = tf.linspace(
        carrier_frequency - (num_subcarriers//2) * subcarrier_spacing,
        carrier_frequency + (num_subcarriers//2 - 1) * subcarrier_spacing,
        num_subcarriers
    )
    Hf = paths.cfr(frequencies=frequencies, normalize=False, out_type="tf")
    
    ########################################
    # LINK BUDGET
    ########################################
    tx_power_dbm = 35.0
    tx_antenna_gain_dbi = 10.0 * np.log10(max(config.tx_antennas, 1))
    tx_eirp_dbm = tx_power_dbm + tx_antenna_gain_dbi
    
    noise_figure_db = 7.0
    kT_dbm = -174 + 10*np.log10(bandwidth)
    noise_dbm = kT_dbm + noise_figure_db
    noise_lin = 10**((noise_dbm - 30) / 10.0)
    
    tx_power_lin = 10**((tx_eirp_dbm - 30) / 10.0)
    
    ########################################
    # 1. SVD BEAMFORMING (Multi-Stream with Singular Value Decomposition)
    ########################################
    print("\n TÉCNICA 1: SVD MULTI-STREAM BEAMFORMING")
    print("   ├─ TX Precoding: W = V[:, 0:r] (primeras r columnas)")
    print("   ├─ RX Combining: U[:, 0:r] (primeras r columnas)")
    print(f"   ├─ Streams: Dinámico (1 a {config.max_layers} según rank del canal)")
    print("   ├─ Optimal for: Capacity maximization with channel structure")
    print("   └─ Gain: Utiliza múltiples singular vectors para mejor throughput")
    
    sinr_svd_list = []
    num_streams_svd_list = []
    
    for k in range(num_subcarriers):
        Hk = get_Hk(Hf, k)
        Hk = tf.cast(Hk, tf.complex64)  # Asegurar tipo
        
        # Multi-stream SVD: usar hasta config.max_layers streams
        W, U_keep, S_keep, num_streams = svd_multistream_beamforming(Hk, num_streams_max=config.max_layers)
        
        # Calcular canal efectivo para cada stream: H_eff = U^H @ H @ W
        # H_eff debería ser diagonal (ideal) o triangular
        H_eff = tf.matmul(tf.transpose(tf.math.conj(U_keep)), Hk)  # [num_streams, tx_ants]
        H_eff = tf.matmul(H_eff, W)  # [num_streams, num_streams]
        
        # Extraer ganancias de cada stream (diagonal principal idealmente)
        h_eff_streams = tf.abs(tf.linalg.diag_part(H_eff))**2  # [num_streams]
        
        sinr_streams = []
        for i in range(num_streams):
            h_i = h_eff_streams[i]
            # Potencia distribuida entre streams
            sinr_i = h_i * (tx_power_lin / num_streams) / (noise_lin + 1e-10)
            sinr_i_db = 10 * tf.math.log(sinr_i + 1e-10) / tf.math.log(10.0)
            sinr_i_db = tf.clip_by_value(sinr_i_db, -50.0, 50.0)  # ← CLIPPING AQUÍ
            sinr_streams.append(sinr_i_db)
        
        # Rellenar con -100 dB si hay menos streams que max_layers
        while len(sinr_streams) < config.max_layers:
            sinr_streams.append(tf.constant(-100.0))
        
        sinr_svd_list.append(tf.stack(sinr_streams[:config.max_layers]))
        num_streams_svd_list.append(num_streams)
    
    sinr_svd = tf.stack(sinr_svd_list)
    num_streams_svd_avg = np.mean(num_streams_svd_list)
    
    ########################################
    # 2. MRC BEAMFORMING (TX Diversity + RX Diversity, Single Stream)
    ########################################
    print("\n TÉCNICA 2: MRC BEAMFORMING (Single Stream with Diversity)")
    print("   ├─ TX Beamforming: w_tx = conj(H.T)/||H|| (Matched Filter - TX Diversity)")
    print("   ├─ RX Beamforming: w_rx = conj(H)/||H|| (MRC - RX Diversity)")
    print("   ├─ Streams: 1")
    print("   ├─ Optimal for: Robust single stream with TX and RX diversity")
    print("   └─ Gain: Improved SNR through combined TX/RX diversity")
    
    sinr_mrc = []
    for k in range(num_subcarriers):
        Hk = get_Hk(Hf, k)
        
        w_tx = mrc_beamforming_tx(Hk)
        w_rx = mrc_beamforming_rx(Hk)
        
        h_eff = tf.matmul(
            tf.matmul(tf.reshape(w_rx, [1, -1]), Hk),
            tf.reshape(w_tx, [-1, 1])
        )[0, 0]
        
        channel_gain_lin = tf.abs(h_eff)**2
        sinr = channel_gain_lin * tx_power_lin / (noise_lin + 1e-10)
        sinr_db = 10 * tf.math.log(sinr + 1e-10) / tf.math.log(10.0)
        sinr_db = tf.clip_by_value(sinr_db, -50.0, 50.0)  # ← CLIPPING AQUÍ
        sinr_mrc.append(sinr_db)
    
    sinr_mrc = tf.stack(sinr_mrc)
    
    ########################################
    # 3. ZERO FORCING (Spatial Multiplexing, Multi-Stream)
    ########################################
    print("\n TÉCNICA 3: ZERO FORCING PRECODING (Spatial Multiplexing)")
    print(f"   ├─ TX Precoding: W = H^H(HH^H)^-1")
    print(f"   ├─ Streams: {config.max_layers} (parallel layers)")
    print("   ├─ Optimal for: Multi-stream transmission without ISI")
    print("   └─ Gain: Cancels Inter-Stream Interference (ISI), linear throughput scaling")
    
    sinr_zf_list = []
    
    for k in range(num_subcarriers):
        Hk = get_Hk(Hf, k)
        
        W = zero_forcing_precoding(Hk)
        
        H_eff = tf.matmul(Hk, W)
        
        h_eff_streams = tf.abs(tf.linalg.diag_part(H_eff))**2
        
        Ns = min(config.max_layers, len(h_eff_streams.numpy()))
        
        sinr_streams = []
        for i in range(Ns):
            h_i = h_eff_streams[i]
            sinr_i = h_i * (tx_power_lin / Ns) / (noise_lin + 1e-10)
            # Proteger contra valores extremos: clipping en dB a rango realista [-50, 50]
            sinr_i_db = 10 * tf.math.log(sinr_i + 1e-10) / tf.math.log(10.0)
            sinr_i_db = tf.clip_by_value(sinr_i_db, -50.0, 50.0)  # ← CLIPPING AQUÍ
            sinr_streams.append(sinr_i_db)
        
        while len(sinr_streams) < config.max_layers:
            sinr_streams.append(tf.constant(-100.0))
        
        sinr_zf_list.append(tf.stack(sinr_streams[:config.max_layers]))
    
    sinr_zf = tf.stack(sinr_zf_list)
    
    ########################################
    # CÁLCULO DE THROUGHPUT
    ########################################
    def calculate_throughput(sinr_db, num_streams=1, mcs_index=16, use_mcs_cap=False):
        """Calculate throughput with optional MCS capacity ceiling
        
        use_mcs_cap=False → Modo análisis MIMO (Shannon capacity sin límite)
        use_mcs_cap=True  → Modo 5G real (con límite MCS)
        
        NOTA: SINR ya viene clipeado a [-50, 50] dB
        """
        mcs_efficiency = {
            0: 0.23, 1: 0.38, 2: 0.60, 3: 0.88, 4: 1.18, 5: 1.48, 6: 1.91, 7: 2.41,
            8: 2.73, 9: 3.32, 10: 3.90, 11: 4.52, 12: 5.12, 13: 5.55, 14: 6.02, 15: 6.52,
            16: 4.52, 17: 5.12, 18: 5.55, 19: 6.02, 20: 6.52, 21: 7.08, 22: 7.64, 23: 8.16,
            24: 8.75, 25: 9.15, 26: 9.58, 27: 10.03
        }
        
        spectral_eff_mcs = mcs_efficiency.get(mcs_index, 4.5)
        
        # SINR ya está clipeado, convertir a lineal
        sinr_lin = tf.pow(10.0, sinr_db / 10.0)
        
        # Shannon capacity (without MCS constraint by default)
        capacity_per_subcarrier = tf.math.log(1.0 + sinr_lin) / tf.math.log(2.0)
        
        # Optional MCS ceiling for realism
        if use_mcs_cap:
            capacity_per_subcarrier = tf.minimum(capacity_per_subcarrier, spectral_eff_mcs)
        
        # Cap máximo realista a 12 bits/s/Hz (más realista que 15)
        capacity_per_subcarrier = tf.minimum(capacity_per_subcarrier, 12.0)
        
        throughput = tf.reduce_mean(capacity_per_subcarrier) * bandwidth * num_streams
        return throughput
    
    # SVD: sumar throughput de todos los streams válidos
    throughput_svd = 0.0
    num_valid_streams_svd = 0
    for stream_idx in range(config.max_layers):
        sinr_stream = sinr_svd[:, stream_idx]
        if tf.reduce_mean(sinr_stream) > -5.0:  # Stream válido
            throughput_stream = calculate_throughput(sinr_stream, num_streams=1, mcs_index=mcs_index, use_mcs_cap=False)
            throughput_svd += throughput_stream
            num_valid_streams_svd += 1
    
    throughput_mrc = calculate_throughput(sinr_mrc, num_streams=1, mcs_index=mcs_index, use_mcs_cap=False)
    
    throughput_zf = 0.0
    num_valid_streams = 0
    for stream_idx in range(config.max_layers):
        sinr_stream = sinr_zf[:, stream_idx]
        if tf.reduce_mean(sinr_stream) > -5.0:
            throughput_stream = calculate_throughput(sinr_stream, num_streams=1, mcs_index=mcs_index, use_mcs_cap=False)
            throughput_zf += throughput_stream
            num_valid_streams += 1
    
    ########################################
    # RESULTADOS
    ########################################
    # Proteger contra inf/nan en SINR para el reporte
    sinr_svd_mean = tf.reduce_mean(sinr_svd).numpy()
    sinr_mrc_mean = tf.reduce_mean(sinr_mrc).numpy()
    sinr_zf_mean = tf.reduce_mean(sinr_zf).numpy()
    
    # Clipping de valores extremos para visualización
    sinr_svd_mean = np.clip(sinr_svd_mean, -50, 50) if not (np.isinf(sinr_svd_mean) or np.isnan(sinr_svd_mean)) else 50.0
    sinr_mrc_mean = np.clip(sinr_mrc_mean, -50, 50) if not (np.isinf(sinr_mrc_mean) or np.isnan(sinr_mrc_mean)) else 50.0
    sinr_zf_mean = np.clip(sinr_zf_mean, -50, 50) if not (np.isinf(sinr_zf_mean) or np.isnan(sinr_zf_mean)) else 50.0
    
    # Proteger throughput contra inf/nan
    throughput_svd_val = throughput_svd.numpy() / 1e6
    throughput_mrc_val = throughput_mrc.numpy() / 1e6
    throughput_zf_val = throughput_zf.numpy() / 1e6
    
    # Clipping de throughput
    throughput_svd_val = np.clip(throughput_svd_val, 0, 20000) if not (np.isinf(throughput_svd_val) or np.isnan(throughput_svd_val)) else 5000.0
    throughput_mrc_val = np.clip(throughput_mrc_val, 0, 20000) if not (np.isinf(throughput_mrc_val) or np.isnan(throughput_mrc_val)) else 5000.0
    throughput_zf_val = np.clip(throughput_zf_val, 0, 20000) if not (np.isinf(throughput_zf_val) or np.isnan(throughput_zf_val)) else 5000.0
    
    results = {
        'config': config_name,
        'config_obj': config,
        'throughput_svd': throughput_svd_val,
        'throughput_mrc': throughput_mrc_val,
        'throughput_zf': throughput_zf_val,
        'sinr_svd_avg': sinr_svd_mean,
        'sinr_mrc_avg': sinr_mrc_mean,
        'sinr_zf_avg': sinr_zf_mean,
        'num_layers': config.max_layers,
        'num_valid_streams_svd': num_valid_streams_svd,
        'num_streams_svd_avg': num_streams_svd_avg,
        'num_valid_streams_zf': num_valid_streams,
        'tx_antennas': config.tx_antennas,
        'rx_antennas': config.rx_antennas,
    }
    
    print(f"\nRESULTADOS - {config_name}:")
    print(f"   SVD Multi-Stream:    {results['throughput_svd']:.2f} Mbps ({num_valid_streams_svd} active streams, avg {num_streams_svd_avg:.1f})")
    print(f"   MRC Beamforming:     {results['throughput_mrc']:.2f} Mbps (1 stream with TX+RX diversity)")
    print(f"   Zero Forcing:        {results['throughput_zf']:.2f} Mbps ({num_valid_streams} parallel streams)")
    print(f"   SINR (SVD/MRC/ZF):   {results['sinr_svd_avg']:.1f} / {results['sinr_mrc_avg']:.1f} / {results['sinr_zf_avg']:.1f} dB")
    
    return results, scene_3d_image

########################################
# EJECUTAR COMPARATIVA
########################################
if __name__ == "__main__":
    all_results = []
    scene_3d_images = {}  # Guardar imágenes 3D por config
    
    for config_name in MIMO_CONFIGS.keys():
        results, scene_3d_image = run_mimo_simulation(config_name, mcs_index=4)
        all_results.append(results)
        scene_3d_images[config_name] = scene_3d_image
    
    ########################################
    # TABLA COMPARATIVA DETALLADA
    ########################################
    print("\n" + "="*160)
    print("TABLA COMPARATIVA COMPLETA - 5G NR MIMO CONFIGURATIONS (con Multi-Stream SVD)")
    print("="*160)
    print(f"{'Config':<20} {'TX':<8} {'RX':<8} {'SVD Str':<10} {'SVD (Mbps)':<15} {'MRC (Mbps)':<15} {'ZF (Mbps)':<15} {'Gain ZF/SVD':<12}")
    print("-"*160)
    
    for res in all_results:
        gain = res['throughput_zf'] / max(res['throughput_svd'], 0.01)
        config_name = res['config']
        svd_streams = f"{res['num_valid_streams_svd']}/{int(res['num_streams_svd_avg'])}"
        print(f"{config_name:<20} {res['tx_antennas']:<8} {res['rx_antennas']:<8} {svd_streams:<10} "
              f"{res['throughput_svd']:<15.2f} {res['throughput_mrc']:<15.2f} {res['throughput_zf']:<15.2f} {gain:<12.2f}x")
    
    ########################################
    # GRÁFICAS MEJORADAS - CON RENDER 3D ACTUALIZADO
    ########################################
    configs = [r['config'] for r in all_results]
    svd_values = [r['throughput_svd'] for r in all_results]
    mrc_values = [r['throughput_mrc'] for r in all_results]
    zf_values = [r['throughput_zf'] for r in all_results]
    
    # Crear figura: 2 filas x 2 columnas
    # Fila 1: Throughput + SINR
    # Fila 2: Configuration Details + Último Render 3D
    
    fig = plt.figure(figsize=(18, 12))
    gs = fig.add_gridspec(2, 2, hspace=0.35, wspace=0.3)
    
    # FILA 1: Gráficos principales
    # ============================================
    
    # Gráfico 1: Throughput comparison
    ax1 = fig.add_subplot(gs[0, :])
    x = np.arange(len(configs))
    width = 0.25
    
    bars1 = ax1.bar(x - width, svd_values, width, label='SVD Multi-Stream (Dynamic streams)', 
                    alpha=0.85, color='#1f77b4', edgecolor='black', linewidth=1.5)
    bars2 = ax1.bar(x, mrc_values, width, label='MRC Beamforming (1 stream, TX+RX Diversity)', 
                    alpha=0.85, color='#ff7f0e', edgecolor='black', linewidth=1.5)
    bars3 = ax1.bar(x + width, zf_values, width, label='Zero Forcing (Multi-stream, Spatial Multiplexing)', 
                    alpha=0.85, color='#2ca02c', edgecolor='black', linewidth=1.5)
    
    ax1.set_xlabel('MIMO Configuration', fontweight='bold', fontsize=11)
    ax1.set_ylabel('Throughput [Mbps]', fontweight='bold', fontsize=11)
    ax1.set_title('5G NR MIMO: Throughput by Technique', fontweight='bold', fontsize=12)
    ax1.set_xticks(x)
    ax1.set_xticklabels(configs, fontsize=10, fontweight='bold')
    ax1.legend(fontsize=9, loc='upper left')
    ax1.grid(True, alpha=0.3, axis='y', linestyle='--')
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0f}'))
    
    # Agregar valores en barras
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            if not np.isinf(height) and not np.isnan(height):
                ax1.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.0f}', ha='center', va='bottom', fontsize=8, fontweight='bold')
    
    
    
    # FILA 2: Configuration Details + Último Render 3D
    # ============================================
    
    # Gráfico 3: Configuration details
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.axis('off')
    config_text = "CONFIGURATION SPECIFICATIONS\n" + "═"*40 + "\n"
    for i, res in enumerate(all_results):
        config_text += f"\n{res['config'].upper()}\n"
        config_text += f"  • TX Antennas: {res['tx_antennas']}\n"
        config_text += f"  • RX Antennas: {res['rx_antennas']}\n"
        config_text += f"  • Max Layers: {res['num_layers']}\n"
        config_text += f"  • SVD Streams: {res['num_valid_streams_svd']}/{int(res['num_streams_svd_avg'])}\n"
    ax3.text(0.05, 0.95, config_text, transform=ax3.transAxes, fontsize=10,
            verticalalignment='top', fontfamily='monospace', fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8, edgecolor='black', linewidth=2))
    
    # Gráfico 4: Último Render 3D (se actualiza conforme corre la simulación)
    ax4 = fig.add_subplot(gs[1, 1])
    
    # Obtener último config (el último que se procesó)
    last_config = configs[-1]
    last_scene_img = scene_3d_images.get(last_config)
    
    if last_scene_img is not None:
        # Mostrar imagen 3D
        ax4.imshow(last_scene_img)
        ax4.set_title(f'3D Scene: {last_config}\n(Última configuración procesada)', 
                     fontweight='bold', fontsize=11, color='darkblue')
    else:
        # Fallback si no hay imagen
        ax4.text(0.5, 0.5, f'3D Scene', 
                ha='center', va='center', fontsize=12, transform=ax4.transAxes)
        ax4.set_title(f'3D Scene', fontweight='bold', fontsize=11)
    
    ax4.axis('off')
    
    plt.suptitle('5G NR MIMO Transmission: Complete Analysis with 3D Ray Tracing', 
                 fontsize=16, fontweight='bold', y=0.995)
    
    plt.savefig('mimo_beamforming_comprehensive.png', dpi=150, bbox_inches='tight')
    print("\nGráficas guardadas en 'mimo_beamforming_comprehensive.png'")
    
    # Mostrar figura
    plt.show()