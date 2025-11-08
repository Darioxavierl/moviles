"""
Módulo para decodificación de señales CDMA.
Implementa correlación cruzada y recuperación de mensajes.
"""

import numpy as np
from typing import List, Tuple, Union, Optional
import warnings


class Decoder:
    """
    Clase para decodificar señales CDMA usando correlación cruzada.
    """
    
    def __init__(self, decision_threshold: float = 0.0):
        """
        Inicializa el decodificador.
        
        Args:
            decision_threshold: Umbral para decisión de bits
                              Valores > threshold → bit 1
                              Valores ≤ threshold → bit 0
                              Por defecto 0.0 (óptimo sin ruido)
        """
        self.decision_threshold = decision_threshold
    
    def decode_single_user(self, 
                          total_signal: np.ndarray,
                          code: np.ndarray,
                          n_bits: int) -> np.ndarray:
        """
        Decodifica el mensaje de un usuario específico desde la señal total.
        
        Proceso de decodificación CDMA:
        1. Correlacionar la señal total con el código del usuario
        2. Integrar sobre cada período de bit
        3. Aplicar umbral de decisión para recuperar bits
        
        Args:
            total_signal: Señal total del canal (suma de todas las señales)
                         Shape: (signal_length,)
            code: Código de esparcimiento del usuario a decodificar
                 Shape: (code_length,)
            n_bits: Número de bits en el mensaje original
        
        Returns:
            np.ndarray: Mensaje decodificado en formato binario {0,1}
                       Shape: (n_bits,)
        
        Raises:
            ValueError: Si las dimensiones son inconsistentes
        
        Example:
            >>> decoder = Decoder()
            >>> total_signal = np.array([2, 0, 2, 0, 0, 2, 0, 2])
            >>> code = np.array([1, -1, 1, -1])
            >>> message = decoder.decode_single_user(total_signal, code, n_bits=2)
            >>> message
            array([1, 0])
        """
        # Validar entradas
        self._validate_signal(total_signal)
        self._validate_code(code)
        self._validate_dimensions(total_signal, code, n_bits)
        
        # Desesparcir la señal (correlación con el código)
        despread_signal = self._despread_spectrum(total_signal, code, n_bits)
        
        # Aplicar umbral de decisión
        decoded_bits = self._apply_decision_threshold(despread_signal)
        
        return decoded_bits
    
    def decode_all_users(self,
                        total_signal: np.ndarray,
                        codes: np.ndarray,
                        n_bits: int) -> np.ndarray:
        """
        Decodifica mensajes de múltiples usuarios desde la señal total.
        
        Esta es la función principal para simulaciones CDMA completas.
        Cada usuario es decodificado usando su código único.
        
        Args:
            total_signal: Señal total del canal
            codes: Matriz de códigos (n_users, code_length)
                  Cada fila es el código de un usuario
            n_bits: Número de bits por mensaje
        
        Returns:
            np.ndarray: Matriz de mensajes decodificados (n_users, n_bits)
                       Cada fila es el mensaje de un usuario
        
        Example:
            >>> decoder = Decoder()
            >>> total_signal = np.array([1, 1, 1, 1, -1, -1, -1, -1])
            >>> codes = np.array([[1, -1, 1, -1], [-1, 1, -1, 1]])
            >>> messages = decoder.decode_all_users(total_signal, codes, n_bits=2)
            >>> messages.shape
            (2, 2)
        """
        n_users = codes.shape[0]
        
        # Preallocate matriz de mensajes
        decoded_messages = np.zeros((n_users, n_bits), dtype=np.int8)
        
        # Decodificar cada usuario
        for i in range(n_users):
            decoded_messages[i] = self.decode_single_user(
                total_signal, 
                codes[i], 
                n_bits
            )
        
        return decoded_messages
    
    def decode_with_metrics(self,
                           total_signal: np.ndarray,
                           code: np.ndarray,
                           n_bits: int,
                           original_message: Optional[np.ndarray] = None) -> dict:
        """
        Decodifica un usuario y retorna métricas de calidad.
        
        Args:
            total_signal: Señal total del canal
            code: Código del usuario
            n_bits: Número de bits
            original_message: Mensaje original (opcional, para calcular BER)
        
        Returns:
            dict: Diccionario con:
                - 'decoded_message': Mensaje decodificado
                - 'correlation_values': Valores de correlación antes del umbral
                - 'ber': Bit Error Rate (si se proporciona original_message)
                - 'snr_estimate': Estimación del SNR
        """
        # Decodificar
        decoded_message = self.decode_single_user(total_signal, code, n_bits)
        
        # Obtener valores de correlación
        correlation_values = self._despread_spectrum(total_signal, code, n_bits)
        
        # Calcular métricas
        metrics = {
            'decoded_message': decoded_message,
            'correlation_values': correlation_values,
        }
        
        # BER si se proporciona mensaje original
        if original_message is not None:
            ber = self.calculate_ber(original_message, decoded_message)
            metrics['ber'] = ber
        
        # Estimación de SNR basada en valores de correlación
        snr_estimate = self._estimate_snr(correlation_values)
        metrics['snr_estimate'] = snr_estimate
        
        return metrics
    
    # ==================== Métodos de correlación y desesparcimiento ====================
    
    def _despread_spectrum(self, 
                          total_signal: np.ndarray,
                          code: np.ndarray,
                          n_bits: int) -> np.ndarray:
        """
        Desesparcir la señal mediante correlación con el código.
        
        Para cada bit:
        1. Extraer segmento de la señal (longitud = code_length)
        2. Correlacionar con el código: sum(signal_segment * code)
        3. Normalizar por la longitud del código
        
        Args:
            total_signal: Señal total
            code: Código de esparcimiento
            n_bits: Número de bits a recuperar
        
        Returns:
            np.ndarray: Valores de correlación (uno por bit)
        """
        code_length = len(code)
        correlation_values = np.zeros(n_bits, dtype=np.float64)
        
        for i in range(n_bits):
            # Extraer segmento correspondiente al bit i
            start_idx = i * code_length
            end_idx = start_idx + code_length
            signal_segment = total_signal[start_idx:end_idx]
            
            # Correlación: producto punto normalizado
            correlation = np.dot(signal_segment, code) / code_length
            correlation_values[i] = correlation
        
        return correlation_values
    
    def _despread_spectrum_vectorized(self,
                                     total_signal: np.ndarray,
                                     code: np.ndarray,
                                     n_bits: int) -> np.ndarray:
        """
        Versión vectorizada del desesparcimiento (más eficiente).
        """
        code_length = len(code)
        
        # Reshape señal en matriz (n_bits, code_length)
        signal_matrix = total_signal.reshape(n_bits, code_length)
        
        # Correlación vectorizada
        correlation_values = np.dot(signal_matrix, code) / code_length
        
        return correlation_values
    
    def correlate(self, 
                 signal1: np.ndarray, 
                 signal2: np.ndarray) -> float:
        """
        Calcula la correlación cruzada normalizada entre dos señales.
        
        Args:
            signal1: Primera señal
            signal2: Segunda señal (deben tener la misma longitud)
        
        Returns:
            float: Correlación normalizada [-1, 1]
        
        Example:
            >>> decoder = Decoder()
            >>> sig1 = np.array([1, -1, 1, -1])
            >>> sig2 = np.array([1, -1, 1, -1])
            >>> decoder.correlate(sig1, sig2)
            1.0
        """
        if len(signal1) != len(signal2):
            raise ValueError("Las señales deben tener la misma longitud")
        
        correlation = np.dot(signal1, signal2) / len(signal1)
        return correlation
    
    # ==================== Métodos de decisión y umbral ====================
    
    def _apply_decision_threshold(self, correlation_values: np.ndarray) -> np.ndarray:
        """
        Aplica umbral de decisión para recuperar bits.
        
        Mapeo:
            correlation > threshold → bit 1
            correlation ≤ threshold → bit 0
        
        Args:
            correlation_values: Valores de correlación
        
        Returns:
            np.ndarray: Bits decodificados {0, 1}
        """
        decoded_bits = (correlation_values > self.decision_threshold).astype(np.int8)
        return decoded_bits
    
    def set_decision_threshold(self, threshold: float) -> None:
        """
        Actualiza el umbral de decisión.
        
        Args:
            threshold: Nuevo umbral
        """
        self.decision_threshold = threshold
    
    def adaptive_threshold(self, correlation_values: np.ndarray) -> float:
        """
        Calcula umbral adaptativo basado en los valores de correlación.
        
        Usa la media de los valores como umbral (útil con ruido).
        
        Args:
            correlation_values: Valores de correlación
        
        Returns:
            float: Umbral adaptativo
        """
        return np.mean(correlation_values)
    
    # ==================== Métodos de métricas y evaluación ====================
    
    def calculate_ber(self, 
                     original: np.ndarray, 
                     decoded: np.ndarray) -> float:
        """
        Calcula la Tasa de Error de Bits (Bit Error Rate - BER).
        
        BER = (número de bits erróneos) / (número total de bits)
        
        Args:
            original: Mensaje original
            decoded: Mensaje decodificado
        
        Returns:
            float: BER [0.0, 1.0]
        
        Example:
            >>> decoder = Decoder()
            >>> original = np.array([1, 0, 1, 1, 0])
            >>> decoded = np.array([1, 0, 0, 1, 0])
            >>> decoder.calculate_ber(original, decoded)
            0.2  # 1 error en 5 bits
        """
        if len(original) != len(decoded):
            raise ValueError("Los mensajes deben tener la misma longitud")
        
        errors = np.sum(original != decoded)
        ber = errors / len(original)
        return ber
    
    def calculate_ber_all_users(self,
                               original_messages: np.ndarray,
                               decoded_messages: np.ndarray) -> np.ndarray:
        """
        Calcula BER para múltiples usuarios.
        
        Args:
            original_messages: Mensajes originales (n_users, n_bits)
            decoded_messages: Mensajes decodificados (n_users, n_bits)
        
        Returns:
            np.ndarray: BER para cada usuario (n_users,)
        """
        n_users = original_messages.shape[0]
        bers = np.zeros(n_users)
        
        for i in range(n_users):
            bers[i] = self.calculate_ber(original_messages[i], decoded_messages[i])
        
        return bers
    
    def _estimate_snr(self, correlation_values: np.ndarray) -> float:
        """
        Estima el SNR basándose en los valores de correlación.
        
        Usa la varianza de los valores como indicador del ruido.
        
        Args:
            correlation_values: Valores de correlación
        
        Returns:
            float: Estimación de SNR en dB
        """
        signal_power = np.mean(correlation_values ** 2)
        noise_power = np.var(correlation_values)
        
        if noise_power < 1e-10:
            return float('inf')  # Sin ruido
        
        snr_linear = signal_power / noise_power
        snr_db = 10 * np.log10(snr_linear)
        
        return snr_db
    
    # ==================== Métodos de validación ====================
    
    def _validate_signal(self, signal: np.ndarray) -> None:
        """Valida que la señal sea válida."""
        if not isinstance(signal, np.ndarray):
            raise ValueError("La señal debe ser un numpy array")
        
        if signal.ndim != 1:
            raise ValueError(f"La señal debe ser 1D, recibido: {signal.ndim}D")
        
        if len(signal) == 0:
            raise ValueError("La señal no puede estar vacía")
    
    def _validate_code(self, code: np.ndarray) -> None:
        """Valida que el código sea válido."""
        if not isinstance(code, np.ndarray):
            raise ValueError("El código debe ser un numpy array")
        
        if code.ndim != 1:
            raise ValueError(f"El código debe ser 1D, recibido: {code.ndim}D")
        
        if len(code) == 0:
            raise ValueError("El código no puede estar vacío")
    
    def _validate_dimensions(self, 
                           signal: np.ndarray,
                           code: np.ndarray,
                           n_bits: int) -> None:
        """Valida que las dimensiones sean consistentes."""
        code_length = len(code)
        expected_signal_length = n_bits * code_length
        
        if len(signal) != expected_signal_length:
            raise ValueError(
                f"Longitud de señal inconsistente: esperado {expected_signal_length} "
                f"(n_bits={n_bits} * code_length={code_length}), "
                f"recibido {len(signal)}"
            )
    
    # ==================== Métodos de análisis avanzado ====================
    
    def analyze_interference(self,
                           total_signal: np.ndarray,
                           codes: np.ndarray,
                           target_user_idx: int,
                           n_bits: int) -> dict:
        """
        Analiza la interferencia de otros usuarios sobre un usuario objetivo.
        
        Args:
            total_signal: Señal total
            codes: Todos los códigos
            target_user_idx: Índice del usuario objetivo
            n_bits: Número de bits
        
        Returns:
            dict: Análisis de interferencia
        """
        n_users = codes.shape[0]
        target_code = codes[target_user_idx]
        
        # Correlación con otros códigos
        interference_levels = []
        for i in range(n_users):
            if i != target_user_idx:
                correlation = self.correlate(target_code, codes[i])
                interference_levels.append(abs(correlation))
        
        analysis = {
            'target_user': target_user_idx,
            'n_interferers': n_users - 1,
            'max_interference': max(interference_levels) if interference_levels else 0.0,
            'avg_interference': np.mean(interference_levels) if interference_levels else 0.0,
            'interference_levels': interference_levels
        }
        
        return analysis


# ==================== Funciones de utilidad ====================

def decode_message(total_signal: np.ndarray, 
                  code: np.ndarray, 
                  n_bits: int) -> np.ndarray:
    """
    Función de conveniencia para decodificar un mensaje.
    
    Args:
        total_signal: Señal total del canal
        code: Código de esparcimiento
        n_bits: Número de bits
    
    Returns:
        np.ndarray: Mensaje decodificado
    """
    decoder = Decoder()
    return decoder.decode_single_user(total_signal, code, n_bits)


def decode_multiple_users(total_signal: np.ndarray,
                         codes: np.ndarray,
                         n_bits: int) -> np.ndarray:
    """
    Función de conveniencia para decodificar múltiples usuarios.
    
    Args:
        total_signal: Señal total del canal
        codes: Códigos de esparcimiento
        n_bits: Número de bits por mensaje
    
    Returns:
        np.ndarray: Mensajes decodificados
    """
    decoder = Decoder()
    return decoder.decode_all_users(total_signal, codes, n_bits)


if __name__ == "__main__":
    # Ejemplo de uso completo con encoder
    print("=== Decodificador CDMA ===\n")
    
    # Simular escenario CDMA completo
    print("Simulación completa de sistema CDMA")
    print("=" * 60)
    
    # Parámetros
    n_users = 3
    n_bits = 4
    
    # Mensajes originales
    original_messages = np.array([
        [1, 0, 1, 0],  # Usuario 1
        [0, 1, 1, 0],  # Usuario 2
        [1, 1, 0, 1]   # Usuario 3
    ])
    
    # Códigos ortogonales (Walsh)
    codes = np.array([
        [ 1,  1,  1,  1],
        [ 1, -1,  1, -1],
        [ 1,  1, -1, -1]
    ])
    
    print(f"Número de usuarios: {n_users}")
    print(f"Bits por mensaje: {n_bits}")
    print(f"\nMensajes originales:")
    for i, msg in enumerate(original_messages):
        print(f"  Usuario {i+1}: {msg}")
    
    # Paso 1: Codificar (simulación simple)
    print("\n" + "-" * 60)
    print("PASO 1: Codificación")
    print("-" * 60)
    
    # Codificar manualmente (versión simplificada)
    def simple_encode(message, code):
        message_bipolar = 2 * message - 1
        signal = np.repeat(message_bipolar, len(code)) * np.tile(code, len(message))
        return signal
    
    signals = np.array([simple_encode(original_messages[i], codes[i]) 
                       for i in range(n_users)])
    
    print("Señales codificadas generadas")
    
    # Combinar señales (canal CDMA)
    total_signal = np.sum(signals, axis=0)
    print(f"Señal total en el canal (longitud {len(total_signal)}):")
    print(f"  {total_signal}")
    
    # Paso 2: Decodificar
    print("\n" + "-" * 60)
    print("PASO 2: Decodificación")
    print("-" * 60)
    
    decoder = Decoder()
    decoded_messages = decoder.decode_all_users(total_signal, codes, n_bits)
    
    print("Mensajes decodificados:")
    for i, msg in enumerate(decoded_messages):
        print(f"  Usuario {i+1}: {msg}")
    
    # Paso 3: Verificar resultados
    print("\n" + "-" * 60)
    print("PASO 3: Verificación")
    print("-" * 60)
    
    # Calcular BER para cada usuario
    bers = decoder.calculate_ber_all_users(original_messages, decoded_messages)
    
    print("\nComparación Original vs Decodificado:")
    print(f"{'Usuario':<10} {'Original':<20} {'Decodificado':<20} {'BER':<10}")
    print("-" * 60)
    for i in range(n_users):
        orig_str = ''.join(map(str, original_messages[i]))
        dec_str = ''.join(map(str, decoded_messages[i]))
        print(f"Usuario {i+1:<3} {orig_str:<20} {dec_str:<20} {bers[i]:.4f}")
    
    # Análisis de interferencia
    print("\n" + "-" * 60)
    print("PASO 4: Análisis de interferencia")
    print("-" * 60)
    
    for user_idx in range(n_users):
        analysis = decoder.analyze_interference(total_signal, codes, user_idx, n_bits)
        print(f"\nUsuario {user_idx + 1}:")
        print(f"  Interferidores: {analysis['n_interferers']}")
        print(f"  Interferencia máxima: {analysis['max_interference']:.4f}")
        print(f"  Interferencia promedio: {analysis['avg_interference']:.4f}")
    
    # Ejemplo con métricas detalladas
    print("\n" + "-" * 60)
    print("PASO 5: Métricas detalladas (Usuario 1)")
    print("-" * 60)
    
    metrics = decoder.decode_with_metrics(
        total_signal, 
        codes[0], 
        n_bits,
        original_messages[0]
    )
    
    print(f"Mensaje decodificado: {metrics['decoded_message']}")
    print(f"Valores de correlación: {metrics['correlation_values']}")
    print(f"BER: {metrics['ber']:.4f}")
    print(f"SNR estimado: {metrics['snr_estimate']:.2f} dB")