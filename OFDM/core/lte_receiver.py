"""
LTE Receiver - Receptor OFDM con soporte para mapeo LTE

Implementa:
- Extracción de pilotos
- Estimación de canal (Channel Estimation)
- Ecualización (Equalization)
- Extracción de datos
- Decodificación

Compatible con modo LTE del transmisor
"""

import numpy as np
from typing import Dict, Tuple, Optional
from core.resource_mapper import LTEResourceGrid, PilotPattern
from core.modulator import QAMModulator


class LTEChannelEstimator:
    """
    Estimador de canal basado en señales de referencia (pilotos) LTE
    
    Utiliza pilotos QPSK deterministas para estimar la respuesta del canal
    """
    
    def __init__(self, config, cell_id=0):
        """
        Inicializa el estimador de canal
        
        Args:
            config: Objeto LTEConfig
            cell_id: ID de celda para generar patrón de pilotos (0-167)
        """
        self.config = config
        self.cell_id = cell_id
        self.resource_grid = LTEResourceGrid(config.N, config.Nc)
        self.pilot_pattern = PilotPattern(config.N, config.Nc, config.Nc, cell_id)
    
    def estimate_channel(self, received_signal: np.ndarray, 
                        tx_signal: Optional[np.ndarray] = None) -> Dict:
        """
        Estima la respuesta del canal usando pilotos LTE
        
        Proceso:
        1. Demodular la señal recibida
        2. Extraer símbolos de piloto
        3. Comparar con pilotos conocidos (transmitidos)
        4. Estimar canal en posiciones de piloto (por interpolación)
        5. Interpolar canal a todas las subportadoras
        
        Args:
            received_signal: Señal demodulada recibida (dominio frecuencial)
            tx_signal: Señal transmitida (opcional, para LS estimation)
            
        Returns:
            dict con:
                - 'channel_estimate': Estimación de canal para cada SC
                - 'pilot_snr': SNR estimado de pilotos
                - 'interpolated': Si se usó interpolación
        """
        N = self.config.N
        
        # Generar patrón de pilotos conocidos
        pilot_indices = self.resource_grid.get_pilot_indices()
        known_pilots = self.pilot_pattern.generate_pilots()
        
        # Extraer pilotos recibidos
        received_pilots = received_signal[pilot_indices]
        
        # LS (Least Squares) Channel Estimation en posiciones de piloto
        # H_est = Y / X (división elemento a elemento)
        # donde Y = símbolos piloto recibidos, X = símbolos piloto transmitidos
        pilot_channel_est = received_pilots / known_pilots
        
        # Estimar SNR de los pilotos
        pilot_power = np.mean(np.abs(received_pilots) ** 2)
        estimated_noise_power = np.mean(np.abs(received_pilots - known_pilots) ** 2)
        pilot_snr = pilot_power / (estimated_noise_power + 1e-10)
        
        # Interpolación lineal a todas las subportadoras
        channel_estimate = self._interpolate_channel(
            pilot_indices, 
            pilot_channel_est, 
            N
        )
        
        return {
            'channel_estimate': channel_estimate,
            'pilot_channel': pilot_channel_est,
            'pilot_indices': pilot_indices,
            'pilot_snr_linear': pilot_snr,
            'pilot_snr_db': 10 * np.log10(pilot_snr + 1e-10),
            'interpolated': True
        }
    
    def _interpolate_channel(self, pilot_indices: np.ndarray, 
                            pilot_values: np.ndarray, 
                            total_subcarriers: int) -> np.ndarray:
        """
        Interpola respuesta de canal a todas las subportadoras
        
        Usa interpolación lineal entre pilotos, extrapolación en los bordes
        
        Args:
            pilot_indices: Índices donde tenemos estimación de canal
            pilot_values: Valores de canal en esos índices
            total_subcarriers: Total de subportadoras
            
        Returns:
            Array con estimación de canal para todas las SC
        """
        # Crear array completo inicializado
        channel_full = np.zeros(total_subcarriers, dtype=complex)
        
        # Extrapolación: usar primer/último valor conocido en los bordes
        channel_full[:pilot_indices[0]] = pilot_values[0]
        channel_full[pilot_indices[-1]:] = pilot_values[-1]
        
        # Interpolación lineal entre pilotos
        for i in range(len(pilot_indices) - 1):
            idx1, idx2 = pilot_indices[i], pilot_indices[i + 1]
            val1, val2 = pilot_values[i], pilot_values[i + 1]
            
            # Número de puntos a interpolar
            num_points = idx2 - idx1 + 1
            
            # Interpolación lineal (también funciona para complejos)
            interpolated = np.linspace(val1, val2, num_points)
            channel_full[idx1:idx2 + 1] = interpolated
        
        return channel_full


class LTEEqualizerZF:
    """
    Ecualizador Zero-Forcing (ZF) para LTE
    
    Compensa la distorsión del canal estimado
    """
    
    def __init__(self, config, regularization=1e-6):
        """
        Inicializa el ecualizador ZF
        
        Args:
            config: Objeto LTEConfig
            regularization: Parámetro de regularización para evitar división por cero
        """
        self.config = config
        self.regularization = regularization
    
    def equalize(self, received_symbols: np.ndarray, 
                channel_estimate: np.ndarray) -> np.ndarray:
        """
        Aplica ecualización Zero-Forcing
        
        H_inv = 1 / H_est
        x_eq = Y * H_inv = Y / H_est
        
        Args:
            received_symbols: Símbolos recibidos (todo el espectro)
            channel_estimate: Estimación de canal
            
        Returns:
            Símbolos ecualizados
        """
        # Ecualización ZF simple: división por el canal estimado
        # Agregar regularización para evitar amplificación de ruido
        channel_mag = np.abs(channel_estimate)
        
        # Zero-Forcing directo
        equalized = received_symbols / (channel_estimate + self.regularization)
        
        # Opcional: normalizar potencia
        # (comentado: mantener potencia original)
        # equalized = equalized / np.mean(np.abs(equalized))
        
        return equalized


class LTEReceiver:
    """
    Receptor OFDM completo con soporte LTE
    
    Integra:
    - Demodulación FFT
    - Estimación de canal usando pilotos
    - Ecualización
    - Detección de símbolos
    - Descodificación QAM
    """
    
    def __init__(self, config, cell_id=0, enable_equalization=True):
        """
        Inicializa el receptor LTE
        
        Args:
            config: Objeto LTEConfig
            cell_id: ID de celda para generar pilotos (0-167)
            enable_equalization: Si True, usa ecualización; si False, asume canal AWGN
        """
        self.config = config
        self.cell_id = cell_id
        self.enable_equalization = enable_equalization
        
        # Componentes
        self.resource_grid = LTEResourceGrid(config.N, config.Nc)
        self.pilot_pattern = PilotPattern(config.N, config.Nc, config.Nc, cell_id)
        self.channel_estimator = LTEChannelEstimator(config, cell_id)
        self.equalizer = LTEEqualizerZF(config)
        self.qam_demodulator = QAMModulator(config.modulation)
        
        # Historial de estimaciones
        self.channel_estimates = []
        self.equalization_info = []
    
    def receive_and_decode(self, received_ofdm_signal: np.ndarray) -> Dict:
        """
        Recibe y decodifica una señal OFDM con mapeo LTE
        
        Proceso completo:
        1. FFT (demodulación OFDM)
        2. Estimación de canal usando pilotos
        3. Ecualización (si está habilitada)
        4. Extracción de datos (ignorar DC, guardias, pilotos)
        5. Detección y decodificación
        
        Args:
            received_ofdm_signal: Señal OFDM recibida (dominio tiempo)
            
        Returns:
            dict con:
                - 'symbols_received': Símbolos recibidos (todos los SC)
                - 'symbols_equalized': Símbolos ecualizados (si aplica)
                - 'symbols_data_only': Solo símbolos de datos (sin pilotos/DC/guardias)
                - 'channel_estimate': Estimación de canal
                - 'channel_snr_db': SNR estimado del canal
                - 'bits': Bits decodificados
                - 'symbols_detected': Símbolos detectados
        """
        # Paso 1: Demodulación OFDM (FFT)
        received_symbols = self._demodulate_ofdm(received_ofdm_signal)
        
        # Paso 2: Estimación de canal
        channel_info = self.channel_estimator.estimate_channel(received_symbols)
        channel_estimate = channel_info['channel_estimate']
        
        # Paso 3: Ecualización (opcional)
        if self.enable_equalization:
            symbols_equalized = self.equalizer.equalize(received_symbols, channel_estimate)
        else:
            symbols_equalized = received_symbols
        
        # Paso 4: Extracción de datos (solo posiciones de datos)
        data_indices = self.resource_grid.get_data_indices()
        symbols_data = symbols_equalized[data_indices]
        
        # Paso 5: Detección y decodificación
        symbols_detected = self._detect_symbols(symbols_data)
        bits = self.qam_demodulator.symbols_to_bits(symbols_detected)
        
        # Guardar en historial
        self.channel_estimates.append(channel_estimate)
        self.equalization_info.append({
            'channel_snr_db': channel_info['pilot_snr_db'],
            'num_data_symbols': len(symbols_data)
        })
        
        return {
            'symbols_received': received_symbols,
            'symbols_equalized': symbols_equalized,
            'symbols_data_only': symbols_data,
            'symbols_detected': symbols_detected,
            'bits': bits,
            'channel_estimate': channel_estimate,
            'channel_snr_db': channel_info['pilot_snr_db'],
            'pilot_snr_db': channel_info['pilot_snr_db'],
            'num_data_symbols': len(symbols_data),
            'num_pilot_symbols': len(self.resource_grid.get_pilot_indices()),
            'equalization_enabled': self.enable_equalization
        }
    
    def _demodulate_ofdm(self, received_signal: np.ndarray) -> np.ndarray:
        """
        Demodulación OFDM: FFT en dominio frecuencial
        
        Asume sincronización perfecta (conocemos dónde está el símbolo OFDM)
        """
        expected_length = self.config.N + self.config.cp_length
        
        # Tomar primera muestra de símbolo OFDM
        received_ofdm = received_signal[:expected_length]
        
        # Remover prefijo cíclico
        signal_without_cp = received_ofdm[self.config.cp_length:]
        
        # FFT
        frequency_domain = np.fft.fft(signal_without_cp) / np.sqrt(self.config.N)
        
        return frequency_domain
    
    def _detect_symbols(self, received_symbols: np.ndarray) -> np.ndarray:
        """
        Detección de símbolos con decisión dura (hard decision)
        Busca el símbolo de constelación más cercano
        """
        constellation = self.qam_demodulator.get_constellation()
        detected = np.zeros_like(received_symbols)
        
        for i, symbol in enumerate(received_symbols):
            distances = np.abs(constellation - symbol)
            nearest_idx = np.argmin(distances)
            detected[i] = constellation[nearest_idx]
        
        return detected
    
    def calculate_ber(self, transmitted_bits: np.ndarray, 
                      received_bits: np.ndarray) -> Dict:
        """
        Calcula tasa de error de bit (BER)
        
        Args:
            transmitted_bits: Bits transmitidos originales
            received_bits: Bits recibidos y decodificados
            
        Returns:
            dict con BER y errores
        """
        # Asegurar mismo tamaño
        min_len = min(len(transmitted_bits), len(received_bits))
        tx_bits = transmitted_bits[:min_len]
        rx_bits = received_bits[:min_len]
        
        # Contar errores
        errors = np.sum(tx_bits != rx_bits)
        ber = errors / min_len if min_len > 0 else 0
        
        return {
            'ber': ber,
            'errors': errors,
            'total_bits': min_len
        }
    
    def reset_history(self):
        """Limpia el historial de estimaciones"""
        self.channel_estimates = []
        self.equalization_info = []
    
    def get_channel_estimate_history(self) -> np.ndarray:
        """Retorna historial de estimaciones de canal"""
        return np.array(self.channel_estimates)
