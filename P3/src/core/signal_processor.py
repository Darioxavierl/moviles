"""
Módulo para procesamiento y análisis de señales CDMA.
Incluye operaciones de señales, análisis espectral, filtrado y métricas.
"""

import numpy as np
from typing import List, Tuple, Optional, Dict, Union
import warnings
from scipy import signal as scipy_signal
from scipy.fft import fft, fftfreq, fftshift


class SignalProcessor:
    """
    Clase para procesar y analizar señales en sistemas CDMA.
    """
    
    def __init__(self, sampling_rate: float = 1.0):
        """
        Inicializa el procesador de señales.
        
        Args:
            sampling_rate: Tasa de muestreo (Hz o chips/segundo)
        """
        self.sampling_rate = sampling_rate
    
    # ==================== Operaciones básicas de señales ====================
    
    def add_signals(self, signals: np.ndarray) -> np.ndarray:
        """
        Suma múltiples señales (simulación del canal CDMA).
        
        Args:
            signals: Matriz de señales (n_signals, signal_length)
        
        Returns:
            np.ndarray: Señal total (signal_length,)
        
        Example:
            >>> proc = SignalProcessor()
            >>> signals = np.array([[1, -1, 1], [2, 2, -2]])
            >>> total = proc.add_signals(signals)
            >>> total
            array([3, 1, -1])
        """
        if signals.ndim == 1:
            return signals
        return np.sum(signals, axis=0)
    
    def normalize_signal(self, signal: np.ndarray, method: str = 'peak') -> np.ndarray:
        """
        Normaliza una señal usando diferentes métodos.
        
        Args:
            signal: Señal a normalizar
            method: Método de normalización:
                - 'peak': Normaliza al valor máximo absoluto
                - 'rms': Normaliza a potencia RMS unitaria
                - 'energy': Normaliza a energía unitaria
        
        Returns:
            np.ndarray: Señal normalizada
        
        Example:
            >>> proc = SignalProcessor()
            >>> signal = np.array([2, -4, 6])
            >>> normalized = proc.normalize_signal(signal, method='peak')
            >>> np.max(np.abs(normalized))
            1.0
        """
        if len(signal) == 0:
            return signal
        
        method = method.lower()
        
        if method == 'peak':
            max_val = np.max(np.abs(signal))
            if max_val > 0:
                return signal / max_val
            return signal
        
        elif method == 'rms':
            rms = np.sqrt(np.mean(signal ** 2))
            if rms > 0:
                return signal / rms
            return signal
        
        elif method == 'energy':
            energy = np.sum(signal ** 2)
            if energy > 0:
                return signal / np.sqrt(energy)
            return signal
        
        else:
            raise ValueError(f"Método '{method}' no reconocido. Use: peak, rms, energy")
    
    def calculate_power(self, signal: np.ndarray) -> float:
        """
        Calcula la potencia promedio de la señal.
        
        Args:
            signal: Señal de entrada
        
        Returns:
            float: Potencia promedio
        
        Example:
            >>> proc = SignalProcessor()
            >>> signal = np.array([1, -1, 1, -1])
            >>> proc.calculate_power(signal)
            1.0
        """
        return np.mean(signal ** 2)
    
    def calculate_energy(self, signal: np.ndarray) -> float:
        """
        Calcula la energía total de la señal.
        
        Args:
            signal: Señal de entrada
        
        Returns:
            float: Energía total
        """
        return np.sum(signal ** 2)
    
    def calculate_snr(self, 
                     clean_signal: np.ndarray, 
                     noisy_signal: np.ndarray) -> float:
        """
        Calcula la relación señal-ruido (SNR).
        
        Args:
            clean_signal: Señal limpia
            noisy_signal: Señal con ruido
        
        Returns:
            float: SNR en dB
        
        Example:
            >>> proc = SignalProcessor()
            >>> clean = np.array([1, -1, 1, -1])
            >>> noisy = clean + 0.1 * np.random.randn(4)
            >>> snr = proc.calculate_snr(clean, noisy)
        """
        noise = noisy_signal - clean_signal
        signal_power = self.calculate_power(clean_signal)
        noise_power = self.calculate_power(noise)
        
        if noise_power < 1e-10:
            return float('inf')
        
        snr_linear = signal_power / noise_power
        snr_db = 10 * np.log10(snr_linear)
        
        return snr_db
    
    # ==================== Análisis espectral (FFT) ====================
    
    def compute_spectrum(self, signal: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calcula el espectro de frecuencia de la señal usando FFT.
        
        Args:
            signal: Señal en el dominio del tiempo
        
        Returns:
            Tuple[np.ndarray, np.ndarray]: 
                - Frecuencias (Hz)
                - Magnitudes del espectro
        
        Example:
            >>> proc = SignalProcessor(sampling_rate=100)
            >>> signal = np.sin(2*np.pi*10*np.linspace(0, 1, 100))
            >>> freqs, mags = proc.compute_spectrum(signal)
        """
        n = len(signal)
        
        # Calcular FFT
        spectrum = fft(signal)
        
        # Calcular magnitudes (solo frecuencias positivas)
        magnitudes = np.abs(spectrum[:n//2])
        
        # Frecuencias correspondientes
        frequencies = fftfreq(n, d=1/self.sampling_rate)[:n//2]
        
        return frequencies, magnitudes
    
    def compute_power_spectrum(self, signal: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calcula el espectro de potencia (PSD) de la señal.
        
        Args:
            signal: Señal en el dominio del tiempo
        
        Returns:
            Tuple[np.ndarray, np.ndarray]:
                - Frecuencias (Hz)
                - Densidad espectral de potencia
        
        Example:
            >>> proc = SignalProcessor(sampling_rate=100)
            >>> signal = np.random.randn(100)
            >>> freqs, psd = proc.compute_power_spectrum(signal)
        """
        n = len(signal)
        
        # FFT
        spectrum = fft(signal)
        
        # Espectro de potencia (magnitud al cuadrado)
        power_spectrum = (np.abs(spectrum) ** 2) / n
        
        # Solo frecuencias positivas
        frequencies = fftfreq(n, d=1/self.sampling_rate)[:n//2]
        psd = power_spectrum[:n//2]
        
        return frequencies, psd
    
    def compute_spectrum_db(self, signal: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calcula el espectro en escala logarítmica (dB).
        
        Args:
            signal: Señal en el dominio del tiempo
        
        Returns:
            Tuple[np.ndarray, np.ndarray]:
                - Frecuencias (Hz)
                - Magnitudes en dB
        """
        frequencies, magnitudes = self.compute_spectrum(signal)
        
        # Convertir a dB (evitar log de cero)
        magnitudes_db = 20 * np.log10(magnitudes + 1e-10)
        
        return frequencies, magnitudes_db
    
    def compare_spectra(self, 
                       signals: List[np.ndarray],
                       labels: Optional[List[str]] = None) -> Dict:
        """
        Compara los espectros de múltiples señales.
        
        Args:
            signals: Lista de señales
            labels: Etiquetas opcionales para las señales
        
        Returns:
            Dict: Diccionario con espectros y estadísticas
        
        Example:
            >>> proc = SignalProcessor()
            >>> signals = [np.random.randn(100), np.random.randn(100)]
            >>> comparison = proc.compare_spectra(signals, labels=['S1', 'S2'])
        """
        if labels is None:
            labels = [f"Signal {i+1}" for i in range(len(signals))]
        
        spectra = {}
        for i, (signal, label) in enumerate(zip(signals, labels)):
            freqs, mags = self.compute_spectrum(signal)
            spectra[label] = {
                'frequencies': freqs,
                'magnitudes': mags,
                'peak_frequency': freqs[np.argmax(mags)],
                'bandwidth': self._estimate_bandwidth(freqs, mags)
            }
        
        return spectra
    
    def _estimate_bandwidth(self, 
                           frequencies: np.ndarray, 
                           magnitudes: np.ndarray,
                           threshold_db: float = -3.0) -> float:
        """
        Estima el ancho de banda de la señal (método -3dB).
        
        Args:
            frequencies: Array de frecuencias
            magnitudes: Array de magnitudes
            threshold_db: Umbral en dB para definir ancho de banda
        
        Returns:
            float: Ancho de banda estimado
        """
        if len(magnitudes) == 0:
            return 0.0
        
        # Convertir a dB
        mags_db = 20 * np.log10(magnitudes + 1e-10)
        max_db = np.max(mags_db)
        
        # Encontrar puntos por encima del umbral
        above_threshold = mags_db > (max_db + threshold_db)
        
        if not np.any(above_threshold):
            return 0.0
        
        # Índices donde está por encima del umbral
        indices = np.where(above_threshold)[0]
        
        if len(indices) < 2:
            return 0.0
        
        # Ancho de banda: diferencia entre frecuencias extremas
        bandwidth = frequencies[indices[-1]] - frequencies[indices[0]]
        
        return bandwidth
    
    # ==================== Análisis de autocorrelación ====================
    
    def autocorrelation(self, signal: np.ndarray, normalized: bool = True) -> np.ndarray:
        """
        Calcula la autocorrelación de una señal.
        
        Args:
            signal: Señal de entrada
            normalized: Si True, normaliza al valor máximo
        
        Returns:
            np.ndarray: Función de autocorrelación
        
        Example:
            >>> proc = SignalProcessor()
            >>> signal = np.array([1, -1, 1, -1])
            >>> acf = proc.autocorrelation(signal)
        """
        n = len(signal)
        
        # Autocorrelación usando convolución
        acf = np.correlate(signal, signal, mode='full')
        
        # Tomar solo la mitad positiva
        acf = acf[n-1:]
        
        if normalized:
            acf = acf / acf[0]
        
        return acf
    
    def cross_correlation(self, 
                         signal1: np.ndarray, 
                         signal2: np.ndarray,
                         normalized: bool = True) -> np.ndarray:
        """
        Calcula la correlación cruzada entre dos señales.
        
        Args:
            signal1: Primera señal
            signal2: Segunda señal
            normalized: Si True, normaliza
        
        Returns:
            np.ndarray: Función de correlación cruzada
        """
        ccf = np.correlate(signal1, signal2, mode='full')
        
        if normalized:
            norm_factor = np.sqrt(np.sum(signal1**2) * np.sum(signal2**2))
            if norm_factor > 0:
                ccf = ccf / norm_factor
        
        return ccf
    
    # ==================== Filtrado de señales ====================
    
    def apply_lowpass_filter(self, 
                            signal: np.ndarray,
                            cutoff_freq: float,
                            order: int = 5) -> np.ndarray:
        """
        Aplica un filtro pasa-bajos Butterworth.
        
        Args:
            signal: Señal a filtrar
            cutoff_freq: Frecuencia de corte (Hz)
            order: Orden del filtro
        
        Returns:
            np.ndarray: Señal filtrada
        """
        nyquist = self.sampling_rate / 2
        normalized_cutoff = cutoff_freq / nyquist
        
        if normalized_cutoff >= 1.0:
            warnings.warn("Frecuencia de corte >= frecuencia de Nyquist. Sin filtrado.")
            return signal
        
        b, a = scipy_signal.butter(order, normalized_cutoff, btype='low')
        filtered_signal = scipy_signal.filtfilt(b, a, signal)
        
        return filtered_signal
    
    def apply_highpass_filter(self,
                             signal: np.ndarray,
                             cutoff_freq: float,
                             order: int = 5) -> np.ndarray:
        """
        Aplica un filtro pasa-altos Butterworth.
        
        Args:
            signal: Señal a filtrar
            cutoff_freq: Frecuencia de corte (Hz)
            order: Orden del filtro
        
        Returns:
            np.ndarray: Señal filtrada
        """
        nyquist = self.sampling_rate / 2
        normalized_cutoff = cutoff_freq / nyquist
        
        if normalized_cutoff >= 1.0:
            warnings.warn("Frecuencia de corte >= frecuencia de Nyquist. Sin filtrado.")
            return signal
        
        b, a = scipy_signal.butter(order, normalized_cutoff, btype='high')
        filtered_signal = scipy_signal.filtfilt(b, a, signal)
        
        return filtered_signal
    
    def apply_bandpass_filter(self,
                             signal: np.ndarray,
                             low_freq: float,
                             high_freq: float,
                             order: int = 5) -> np.ndarray:
        """
        Aplica un filtro pasa-banda Butterworth.
        
        Args:
            signal: Señal a filtrar
            low_freq: Frecuencia baja de corte (Hz)
            high_freq: Frecuencia alta de corte (Hz)
            order: Orden del filtro
        
        Returns:
            np.ndarray: Señal filtrada
        """
        nyquist = self.sampling_rate / 2
        low_norm = low_freq / nyquist
        high_norm = high_freq / nyquist
        
        if high_norm >= 1.0:
            warnings.warn("Frecuencia alta >= frecuencia de Nyquist. Sin filtrado.")
            return signal
        
        b, a = scipy_signal.butter(order, [low_norm, high_norm], btype='band')
        filtered_signal = scipy_signal.filtfilt(b, a, signal)
        
        return filtered_signal
    
    # ==================== Análisis de señales CDMA específico ====================
    
    def analyze_cdma_signal(self, signal: np.ndarray, code_length: int) -> Dict:
        """
        Análisis completo de una señal CDMA.
        
        Args:
            signal: Señal CDMA
            code_length: Longitud del código de esparcimiento
        
        Returns:
            Dict: Análisis completo con métricas
        """
        # Métricas básicas
        power = self.calculate_power(signal)
        energy = self.calculate_energy(signal)
        
        # Análisis espectral
        freqs, mags = self.compute_spectrum(signal)
        freqs_db, mags_db = self.compute_spectrum_db(signal)
        
        # Autocorrelación
        acf = self.autocorrelation(signal)
        
        # Calcular factor de esparcimiento
        spreading_factor = code_length
        processing_gain_db = 10 * np.log10(spreading_factor)
        
        analysis = {
            'power': power,
            'energy': energy,
            'peak_value': np.max(np.abs(signal)),
            'rms_value': np.sqrt(power),
            'spreading_factor': spreading_factor,
            'processing_gain_db': processing_gain_db,
            'spectrum': {
                'frequencies': freqs,
                'magnitudes': mags,
                'magnitudes_db': mags_db,
                'peak_frequency': freqs[np.argmax(mags)],
                'bandwidth': self._estimate_bandwidth(freqs, mags)
            },
            'autocorrelation': acf
        }
        
        return analysis
    
    def compare_original_and_decoded_signals(self,
                                            original_signal: np.ndarray,
                                            decoded_signal: np.ndarray) -> Dict:
        """
        Compara señal original vs decodificada.
        
        Args:
            original_signal: Señal original
            decoded_signal: Señal decodificada
        
        Returns:
            Dict: Métricas de comparación
        """
        # Correlación
        correlation = np.corrcoef(original_signal, decoded_signal)[0, 1]
        
        # Error cuadrático medio
        mse = np.mean((original_signal - decoded_signal) ** 2)
        
        # SNR
        snr = self.calculate_snr(original_signal, decoded_signal)
        
        # Diferencia espectral
        freqs1, mags1 = self.compute_spectrum(original_signal)
        freqs2, mags2 = self.compute_spectrum(decoded_signal)
        spectral_diff = np.mean(np.abs(mags1 - mags2))
        
        comparison = {
            'correlation': correlation,
            'mse': mse,
            'snr_db': snr,
            'spectral_difference': spectral_diff
        }
        
        return comparison
    
    # ==================== Utilidades de visualización ====================
    
    def prepare_spectrum_plot_data(self, 
                                   signals: Union[np.ndarray, List[np.ndarray]],
                                   labels: Optional[List[str]] = None) -> Dict:
        """
        Prepara datos de espectros para graficación.
        
        Args:
            signals: Señal o lista de señales
            labels: Etiquetas opcionales
        
        Returns:
            Dict: Datos listos para plotear
        """
        if isinstance(signals, np.ndarray) and signals.ndim == 1:
            signals = [signals]
        
        if labels is None:
            labels = [f"Signal {i+1}" for i in range(len(signals))]
        
        plot_data = {
            'signals': [],
            'labels': labels
        }
        
        for signal in signals:
            freqs, mags = self.compute_spectrum(signal)
            freqs_db, mags_db = self.compute_spectrum_db(signal)
            
            plot_data['signals'].append({
                'frequencies': freqs,
                'magnitudes': mags,
                'magnitudes_db': mags_db
            })
        
        return plot_data
    
    def get_signal_statistics(self, signal: np.ndarray) -> Dict:
        """
        Calcula estadísticas completas de una señal.
        
        Args:
            signal: Señal de entrada
        
        Returns:
            Dict: Estadísticas de la señal
        """
        stats = {
            'length': len(signal),
            'mean': np.mean(signal),
            'std': np.std(signal),
            'variance': np.var(signal),
            'min': np.min(signal),
            'max': np.max(signal),
            'peak_to_peak': np.ptp(signal),
            'rms': np.sqrt(np.mean(signal ** 2)),
            'power': self.calculate_power(signal),
            'energy': self.calculate_energy(signal),
            'crest_factor': np.max(np.abs(signal)) / np.sqrt(np.mean(signal ** 2))
        }
        
        return stats


# ==================== Funciones de utilidad ====================

def compute_spectrum(signal: np.ndarray, 
                    sampling_rate: float = 1.0) -> Tuple[np.ndarray, np.ndarray]:
    """
    Función de conveniencia para calcular espectro.
    
    Args:
        signal: Señal
        sampling_rate: Tasa de muestreo
    
    Returns:
        Tuple[np.ndarray, np.ndarray]: Frecuencias y magnitudes
    """
    proc = SignalProcessor(sampling_rate=sampling_rate)
    return proc.compute_spectrum(signal)


def analyze_signal(signal: np.ndarray, code_length: int = 1) -> Dict:
    """
    Función de conveniencia para análisis completo.
    
    Args:
        signal: Señal a analizar
        code_length: Longitud del código CDMA
    
    Returns:
        Dict: Análisis completo
    """
    proc = SignalProcessor()
    return proc.analyze_cdma_signal(signal, code_length)


if __name__ == "__main__":
    # Ejemplos de uso
    print("=== Procesador de Señales CDMA ===\n")
    
    # Crear procesador
    sampling_rate = 100  # 100 samples/second
    proc = SignalProcessor(sampling_rate=sampling_rate)
    
    # Ejemplo 1: Análisis de señal básica
    print("Ejemplo 1: Análisis de señal básica")
    print("-" * 60)
    
    # Generar señal de prueba (onda cuadrada)
    t = np.linspace(0, 1, 100)
    signal = scipy_signal.square(2 * np.pi * 5 * t)  # 5 Hz
    
    print(f"Longitud de señal: {len(signal)}")
    print(f"Potencia: {proc.calculate_power(signal):.4f}")
    print(f"Energía: {proc.calculate_energy(signal):.4f}")
    
    # Ejemplo 2: Análisis espectral
    print("\n" + "=" * 60)
    print("Ejemplo 2: Análisis espectral")
    print("-" * 60)
    
    freqs, mags = proc.compute_spectrum(signal)
    print(f"Número de bins de frecuencia: {len(freqs)}")
    print(f"Frecuencia pico: {freqs[np.argmax(mags)]:.2f} Hz")
    print(f"Magnitud máxima: {np.max(mags):.4f}")
    
    # Ejemplo 3: Múltiples señales CDMA
    print("\n" + "=" * 60)
    print("Ejemplo 3: Señales CDMA múltiples")
    print("-" * 60)
    
    # Simular 3 usuarios CDMA
    code_length = 4
    n_bits = 8
    
    # Códigos Walsh
    codes = np.array([
        [ 1,  1,  1,  1],
        [ 1, -1,  1, -1],
        [ 1,  1, -1, -1]
    ])
    
    # Mensajes
    messages = np.array([
        [1, 0, 1, 0, 1, 0, 1, 0],
        [0, 1, 1, 0, 0, 1, 1, 0],
        [1, 1, 0, 1, 1, 0, 0, 1]
    ])
    
    # Codificar (versión simple)
    def simple_encode(msg, code):
        msg_bipolar = 2 * msg - 1
        return np.repeat(msg_bipolar, len(code)) * np.tile(code, len(msg))
    
    signals = [simple_encode(messages[i], codes[i]) for i in range(3)]
    
    print("Señales individuales generadas:")
    for i, sig in enumerate(signals):
        stats = proc.get_signal_statistics(sig)
        print(f"  Usuario {i+1}: Potencia={stats['power']:.4f}, RMS={stats['rms']:.4f}")
    
    # Señal total
    total_signal = proc.add_signals(np.array(signals))
    print(f"\nSeñal total: Potencia={proc.calculate_power(total_signal):.4f}")
    
    # Ejemplo 4: Comparación de espectros
    print("\n" + "=" * 60)
    print("Ejemplo 4: Comparación de espectros")
    print("-" * 60)
    
    spectra = proc.compare_spectra(
        signals + [total_signal],
        labels=['Usuario 1', 'Usuario 2', 'Usuario 3', 'Total']
    )
    
    for label, spectrum in spectra.items():
        print(f"\n{label}:")
        print(f"  Frecuencia pico: {spectrum['peak_frequency']:.2f} Hz")
        print(f"  Ancho de banda: {spectrum['bandwidth']:.2f} Hz")
    
    # Ejemplo 5: Análisis CDMA completo
    print("\n" + "=" * 60)
    print("Ejemplo 5: Análisis CDMA completo")
    print("-" * 60)
    
    analysis = proc.analyze_cdma_signal(total_signal, code_length=code_length)
    
    print(f"Factor de esparcimiento: {analysis['spreading_factor']}")
    print(f"Ganancia de procesamiento: {analysis['processing_gain_db']:.2f} dB")
    print(f"Potencia: {analysis['power']:.4f}")
    print(f"Valor RMS: {analysis['rms_value']:.4f}")
    print(f"Ancho de banda: {analysis['spectrum']['bandwidth']:.2f} Hz")
    
    # Ejemplo 6: Autocorrelación
    print("\n" + "=" * 60)
    print("Ejemplo 6: Autocorrelación de códigos")
    print("-" * 60)
    
    for i, code in enumerate(codes):
        acf = proc.autocorrelation(code)
        print(f"Usuario {i+1} - Autocorrelación (primeros 5): {acf[:5]}")
    
    # Ejemplo 7: Normalización
    print("\n" + "=" * 60)
    print("Ejemplo 7: Normalización de señales")
    print("-" * 60)
    
    test_signal = np.array([2, -4, 6, -8])
    
    normalized_peak = proc.normalize_signal(test_signal, method='peak')
    normalized_rms = proc.normalize_signal(test_signal, method='rms')
    normalized_energy = proc.normalize_signal(test_signal, method='energy')
    
    print(f"Original: {test_signal}")
    print(f"Peak norm: {normalized_peak}")
    print(f"RMS norm: {normalized_rms}")
    print(f"Energy norm: {normalized_energy}")
    
    # Ejemplo 8: Datos para visualización
    print("\n" + "=" * 60)
    print("Ejemplo 8: Preparar datos para gráficos")
    print("-" * 60)
    
    plot_data = proc.prepare_spectrum_plot_data(
        signals,
        labels=['Usuario 1', 'Usuario 2', 'Usuario 3']
    )
    
    print(f"Datos preparados para {len(plot_data['signals'])} señales")
    print(f"Etiquetas: {plot_data['labels']}")
    print(f"Cada señal tiene {len(plot_data['signals'][0]['frequencies'])} puntos de frecuencia")