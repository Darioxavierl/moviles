"""
Módulo para codificación de mensajes en sistemas CDMA.
Implementa esparcimiento espectral (spread spectrum) y modulación.
"""

import numpy as np
from typing import List, Tuple, Union, Optional
import warnings


class Encoder:
    """
    Clase para codificar mensajes usando códigos de esparcimiento CDMA.
    """
    
    def __init__(self, chips_per_bit: int = 1):
        """
        Inicializa el codificador.
        
        Args:
            chips_per_bit: Número de chips por bit (para oversample la señal)
                          Por defecto 1 (un chip por símbolo de código)
        """
        self.chips_per_bit = chips_per_bit
    
    def encode_single_user(self, message: np.ndarray, code: np.ndarray) -> np.ndarray:
        """
        Codifica el mensaje de un único usuario usando su código de esparcimiento.
        
        El proceso de codificación CDMA:
        1. Convertir mensaje binario {0,1} a formato bipolar {-1,+1}
        2. Cada bit se multiplica por el código completo (esparcimiento)
        3. Resultado: señal ensanchada en el dominio del tiempo
        
        Args:
            message: Array de bits {0,1} del mensaje a transmitir
                    Shape: (n_bits,)
            code: Código de esparcimiento del usuario {-1,+1}
                 Shape: (code_length,)
        
        Returns:
            np.ndarray: Señal codificada (esparcida)
                       Shape: (n_bits * code_length,)
        
        Raises:
            ValueError: Si los formatos de entrada son inválidos
        
        Example:
            >>> encoder = Encoder()
            >>> message = np.array([1, 0, 1])  # 3 bits
            >>> code = np.array([1, -1, 1, -1])  # Código de longitud 4
            >>> signal = encoder.encode_single_user(message, code)
            >>> signal.shape
            (12,)  # 3 bits * 4 chips/bit
        """
        # Validar entradas
        self._validate_message(message)
        self._validate_code(code)
        
        # Convertir mensaje a formato bipolar {-1, +1}
        message_bipolar = self._binary_to_bipolar(message)
        
        # Esparcimiento espectral: cada bit se multiplica por el código completo
        signal = self._spread_spectrum(message_bipolar, code)
        
        return signal
    
    def encode_all_users(self, 
                        messages: Union[List[np.ndarray], np.ndarray],
                        codes: np.ndarray) -> np.ndarray:
        """
        Codifica mensajes de múltiples usuarios en paralelo.
        
        Esta es la función principal para simulaciones CDMA completas.
        Procesa todos los usuarios de manera eficiente.
        
        Args:
            messages: Lista de mensajes o matriz (n_users, n_bits)
                     Cada mensaje es un array de bits {0,1}
            codes: Matriz de códigos de esparcimiento (n_users, code_length)
                  Cada fila es el código de un usuario
        
        Returns:
            np.ndarray: Matriz de señales codificadas (n_users, signal_length)
                       donde signal_length = n_bits * code_length
        
        Raises:
            ValueError: Si el número de mensajes no coincide con el número de códigos
        
        Example:
            >>> encoder = Encoder()
            >>> messages = np.array([[1, 0], [0, 1], [1, 1]])  # 3 usuarios, 2 bits
            >>> codes = np.array([[1, -1], [-1, 1], [1, 1]])   # 3 códigos de longitud 2
            >>> signals = encoder.encode_all_users(messages, codes)
            >>> signals.shape
            (3, 4)  # 3 usuarios, 4 chips total (2 bits * 2 chips/bit)
        """
        # Convertir mensajes a array si es lista
        if isinstance(messages, list):
            messages = np.array(messages)
        
        # Validar dimensiones
        n_users_msg = messages.shape[0]
        n_users_code = codes.shape[0]
        
        if n_users_msg != n_users_code:
            raise ValueError(
                f"Número de mensajes ({n_users_msg}) no coincide con "
                f"número de códigos ({n_users_code})"
            )
        
        n_users = n_users_msg
        n_bits = messages.shape[1]
        code_length = codes.shape[1]
        signal_length = n_bits * code_length
        
        # Preallocate matriz de señales
        signals = np.zeros((n_users, signal_length), dtype=np.float64)
        
        # Codificar cada usuario
        for i in range(n_users):
            signals[i] = self.encode_single_user(messages[i], codes[i])
        
        return signals
    
    def combine_signals(self, signals: np.ndarray) -> np.ndarray:
        """
        Combina las señales de todos los usuarios en el canal (suma).
        
        En CDMA, todas las señales se transmiten simultáneamente en la misma
        frecuencia y se suman en el canal. Esta es la característica clave
        del acceso múltiple.
        
        Args:
            signals: Matriz de señales (n_users, signal_length)
        
        Returns:
            np.ndarray: Señal total combinada (signal_length,)
        
        Example:
            >>> encoder = Encoder()
            >>> signals = np.array([[1, -1, 1, -1],
            ...                     [-1, 1, -1, 1],
            ...                     [1, 1, -1, -1]])
            >>> total = encoder.combine_signals(signals)
            >>> total.shape
            (4,)
        """
        # Suma de todas las señales (simulación del canal)
        total_signal = np.sum(signals, axis=0)
        return total_signal
    
    def encode_and_combine(self,
                          messages: Union[List[np.ndarray], np.ndarray],
                          codes: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Función de conveniencia: codifica todos los usuarios y combina señales.
        
        Args:
            messages: Mensajes de los usuarios
            codes: Códigos de esparcimiento
        
        Returns:
            Tuple[np.ndarray, np.ndarray]: 
                - Señales individuales (n_users, signal_length)
                - Señal total combinada (signal_length,)
        
        Example:
            >>> encoder = Encoder()
            >>> messages = np.array([[1, 0], [0, 1]])
            >>> codes = np.array([[1, -1], [-1, 1]])
            >>> individual, total = encoder.encode_and_combine(messages, codes)
        """
        signals = self.encode_all_users(messages, codes)
        total_signal = self.combine_signals(signals)
        return signals, total_signal
    
    # ==================== Métodos auxiliares de esparcimiento ====================
    
    def _spread_spectrum(self, message_bipolar: np.ndarray, code: np.ndarray) -> np.ndarray:
        """
        Realiza el esparcimiento espectral del mensaje.
        
        Cada bit del mensaje se multiplica por el código completo,
        expandiendo la señal en el dominio del tiempo.
        
        Args:
            message_bipolar: Mensaje en formato bipolar {-1, +1}
            code: Código de esparcimiento
        
        Returns:
            np.ndarray: Señal esparcida
        """
        n_bits = len(message_bipolar)
        code_length = len(code)
        signal_length = n_bits * code_length
        
        signal = np.zeros(signal_length, dtype=np.float64)
        
        for i, bit in enumerate(message_bipolar):
            start_idx = i * code_length
            end_idx = start_idx + code_length
            # Multiplicar bit por el código completo
            signal[start_idx:end_idx] = bit * code
        
        return signal
    
    # ==================== Métodos de validación y conversión ====================
    
    def _validate_message(self, message: np.ndarray) -> None:
        """Valida que el mensaje sea un array binario válido."""
        if not isinstance(message, np.ndarray):
            raise ValueError("El mensaje debe ser un numpy array")
        
        if message.ndim != 1:
            raise ValueError(f"El mensaje debe ser 1D, recibido: {message.ndim}D")
        
        if len(message) == 0:
            raise ValueError("El mensaje no puede estar vacío")
        
        # Verificar que sea binario {0, 1}
        if not np.all(np.isin(message, [0, 1])):
            raise ValueError("El mensaje debe contener solo bits {0, 1}")
    
    def _validate_code(self, code: np.ndarray) -> None:
        """Valida que el código sea un array bipolar válido."""
        if not isinstance(code, np.ndarray):
            raise ValueError("El código debe ser un numpy array")
        
        if code.ndim != 1:
            raise ValueError(f"El código debe ser 1D, recibido: {code.ndim}D")
        
        if len(code) == 0:
            raise ValueError("El código no puede estar vacío")
        
        # Verificar que sea bipolar {-1, +1}
        if not np.all(np.isin(code, [-1, 1])):
            warnings.warn(
                "El código debería ser bipolar {-1, +1}. "
                "Valores inesperados pueden afectar la decodificación."
            )
    
    def _binary_to_bipolar(self, binary: np.ndarray) -> np.ndarray:
        """
        Convierte representación binaria {0,1} a bipolar {-1,+1}.
        
        Mapeo: 0 -> -1, 1 -> +1
        """
        return 2 * binary - 1
    
    def _bipolar_to_binary(self, bipolar: np.ndarray) -> np.ndarray:
        """
        Convierte representación bipolar {-1,+1} a binaria {0,1}.
        
        Mapeo: -1 -> 0, +1 -> 1
        """
        return ((bipolar + 1) / 2).astype(np.int8)
    
    # ==================== Métodos de información ====================
    
    def get_spreading_factor(self, code_length: int) -> int:
        """
        Retorna el factor de esparcimiento (processing gain).
        
        Args:
            code_length: Longitud del código de esparcimiento
        
        Returns:
            int: Factor de esparcimiento
        """
        return code_length
    
    def get_processing_gain_db(self, code_length: int) -> float:
        """
        Calcula la ganancia de procesamiento en dB.
        
        PG = 10 * log10(code_length)
        
        Args:
            code_length: Longitud del código
        
        Returns:
            float: Ganancia de procesamiento en dB
        """
        return 10 * np.log10(code_length)


# ==================== Funciones de utilidad ====================

def encode_message(message: np.ndarray, code: np.ndarray) -> np.ndarray:
    """
    Función de conveniencia para codificar un mensaje.
    
    Args:
        message: Mensaje binario
        code: Código de esparcimiento
    
    Returns:
        np.ndarray: Señal codificada
    """
    encoder = Encoder()
    return encoder.encode_single_user(message, code)


def encode_multiple_users(messages: Union[List[np.ndarray], np.ndarray],
                         codes: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """
    Función de conveniencia para codificar múltiples usuarios.
    
    Args:
        messages: Mensajes de los usuarios
        codes: Códigos de esparcimiento
    
    Returns:
        Tuple[np.ndarray, np.ndarray]: Señales individuales y señal total
    """
    encoder = Encoder()
    return encoder.encode_and_combine(messages, codes)


    