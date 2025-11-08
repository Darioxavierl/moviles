"""
Módulo de modelos de datos para el sistema CDMA.
Contiene las clases User, Signal y Simulation para estructurar los datos.
"""

import numpy as np
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime




@dataclass
class User:
    """
    Representa un usuario en el sistema CDMA.
    """
    user_id: int
    code: np.ndarray
    original_message: Optional[np.ndarray] = None
    decoded_message: Optional[np.ndarray] = None
    encoded_signal: Optional[np.ndarray] = None
    label: Optional[str] = None
    
    def __post_init__(self):
        """Inicialización adicional después de crear el objeto."""
        if self.label is None:
            self.label = f"Usuario {self.user_id}"
    
    @property
    def code_length(self) -> int:
        """Retorna la longitud del código de esparcimiento."""
        return len(self.code) if self.code is not None else 0
    
    @property
    def message_length(self) -> int:
        """Retorna la longitud del mensaje."""
        if self.original_message is not None:
            return len(self.original_message)
        return 0
    
    @property
    def signal_length(self) -> int:
        """Retorna la longitud de la señal codificada."""
        if self.encoded_signal is not None:
            return len(self.encoded_signal)
        return 0
    
    @property
    def has_message(self) -> bool:
        """Verifica si el usuario tiene un mensaje asignado."""
        return self.original_message is not None
    
    @property
    def has_signal(self) -> bool:
        """Verifica si el usuario tiene una señal codificada."""
        return self.encoded_signal is not None
    
    @property
    def has_decoded(self) -> bool:
        """Verifica si el mensaje ha sido decodificado."""
        return self.decoded_message is not None
    
    def calculate_ber(self) -> Optional[float]:
        """
        Calcula el BER (Bit Error Rate) si hay mensaje original y decodificado.
        
        Returns:
            float: BER o None si no hay datos suficientes
        """
        if not self.has_message or not self.has_decoded:
            return None
        
        if len(self.original_message) != len(self.decoded_message):
            return None
        
        errors = np.sum(self.original_message != self.decoded_message)
        ber = errors / len(self.original_message)
        return ber
    
    def get_errors(self) -> Optional[np.ndarray]:
        """
        Retorna un array booleano indicando posiciones de errores.
        
        Returns:
            np.ndarray: Array booleano con True en posiciones de error
        """
        if not self.has_message or not self.has_decoded:
            return None
        
        return self.original_message != self.decoded_message
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte el usuario a diccionario para serialización.
        
        Returns:
            Dict: Representación en diccionario
        """
        return {
            'user_id': self.user_id,
            'label': self.label,
            'code': self.code.tolist() if self.code is not None else None,
            'code_length': self.code_length,
            'original_message': self.original_message.tolist() if self.original_message is not None else None,
            'decoded_message': self.decoded_message.tolist() if self.decoded_message is not None else None,
            'message_length': self.message_length,
            'ber': self.calculate_ber()
        }
    
    def __str__(self) -> str:
        """Representación en string del usuario."""
        ber = self.calculate_ber()
        ber_str = f"{ber:.4f}" if ber is not None else "N/A"
        return (f"{self.label} (ID: {self.user_id}) - "
                f"Code: {self.code_length} chips, "
                f"Message: {self.message_length} bits, "
                f"BER: {ber_str}")