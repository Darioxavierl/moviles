"""
Módulo para generación de mensajes para sistemas CDMA.
Soporta mensajes aleatorios, patrones de prueba y conversión de texto.
"""

import numpy as np
from typing import List, Union, Optional
import warnings


class MessageGenerator:
    """
    Clase para generar diferentes tipos de mensajes para simulaciones CDMA.
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Inicializa el generador de mensajes.
        
        Args:
            seed: Semilla para reproducibilidad (opcional)
        """
        if seed is not None:
            np.random.seed(seed)
        self.seed = seed
    
    # ==================== Generación de mensajes aleatorios ====================
    
    def generate_random_messages(self, 
                                 n_users: int, 
                                 n_bits: int) -> np.ndarray:
        """
        Genera mensajes aleatorios para múltiples usuarios.
        
        Args:
            n_users: Número de usuarios
            n_bits: Número de bits por mensaje
        
        Returns:
            np.ndarray: Matriz de mensajes (n_users, n_bits)
        
        Example:
            >>> gen = MessageGenerator(seed=42)
            >>> messages = gen.generate_random_messages(3, 4)
            >>> messages.shape
            (3, 4)
        """
        if n_users < 1:
            raise ValueError("n_users debe ser al menos 1")
        if n_bits < 1:
            raise ValueError("n_bits debe ser al menos 1")
        
        messages = np.random.randint(0, 2, size=(n_users, n_bits), dtype=np.int8)
        return messages
    
    def generate_text_messages(self, 
                              texts: List[str], 
                              pad_to_length: Optional[int] = None) -> np.ndarray:
        """
        Convierte múltiples textos a mensajes binarios.
        
        Args:
            texts: Lista de textos
            pad_to_length: Longitud objetivo (rellena con ceros si es necesario)
        
        Returns:
            np.ndarray: Matriz de mensajes binarios
        
        Example:
            >>> gen = MessageGenerator()
            >>> messages = gen.generate_text_messages(['Hi', 'OK'], pad_to_length=20)
            >>> messages.shape
            (2, 20)
        """
        bit_arrays = []
        
        for text in texts:
            bits = self.text_to_bits(text)
            
            # Padding si es necesario
            if pad_to_length is not None:
                if len(bits) > pad_to_length:
                    warnings.warn(
                        f"Texto '{text}' truncado de {len(bits)} a {pad_to_length} bits"
                    )
                    bits = bits[:pad_to_length]
                elif len(bits) < pad_to_length:
                    padding = np.zeros(pad_to_length - len(bits), dtype=np.int8)
                    bits = np.concatenate([bits, padding])
            
            bit_arrays.append(bits)
        
        return np.array(bit_arrays, dtype=np.int8)

# ==================== Funciones de utilidad ====================

def generate_random_bits(n_bits: int, seed: Optional[int] = None) -> np.ndarray:
    """
    Función de conveniencia para generar bits aleatorios.
    
    Args:
        n_bits: Número de bits
        seed: Semilla opcional
    
    Returns:
        np.ndarray: Bits aleatorios
    """
    gen = MessageGenerator(seed=seed)
    return gen.generate_random_bits(n_bits)


def generate_random_messages(n_users: int, 
                            n_bits: int, 
                            seed: Optional[int] = None) -> np.ndarray:
    """
    Función de conveniencia para generar múltiples mensajes aleatorios.
    
    Args:
        n_users: Número de usuarios
        n_bits: Bits por mensaje
        seed: Semilla opcional
    
    Returns:
        np.ndarray: Matriz de mensajes
    """
    gen = MessageGenerator(seed=seed)
    return gen.generate_random_messages(n_users, n_bits)
