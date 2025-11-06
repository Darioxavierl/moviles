"""
Módulo de modelos de datos para el sistema CDMA.
Contiene las clases User, Signal y Simulation para estructurar los datos.
"""

import numpy as np
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

from src.models.user import User
from src.models.signal import Signal



class Simulation:
    """
    Representa una simulación completa del sistema CDMA.
    Gestiona usuarios, señales y parámetros de la simulación.
    """
    
    def __init__(self, 
                 n_users: int,
                 n_bits: int,
                 code_type: str = 'walsh',
                 decoder_rate: float = 1.0,
                 simulation_id: Optional[str] = None):
        """
        Inicializa una simulación CDMA.
        
        Args:
            n_users: Número de usuarios
            n_bits: Número de bits por mensaje
            code_type: Tipo de código ('walsh' o 'gold')
            decoder_rate: Tasa del decodificador
            simulation_id: ID único de la simulación
        """
        self.n_users = n_users
        self.n_bits = n_bits
        self.code_type = code_type
        self.decoder_rate = decoder_rate
        self.simulation_id = simulation_id or self._generate_simulation_id()
        
        # Datos de la simulación
        self.users: List[User] = []
        self.codes: Optional[np.ndarray] = None
        self.total_signal: Optional[Signal] = None
        self.noisy_signal: Optional[Signal] = None
        
        # Parámetros adicionales
        self.snr_db: Optional[float] = None
        self.sampling_rate: float = 1.0
        
        # Estado de la simulación
        self.is_encoded: bool = False
        self.is_decoded: bool = False
        self.has_noise: bool = False
        
        # Timestamp
        self.created_at = datetime.now()
        self.last_modified = datetime.now()
        
        # Métricas globales
        self.metrics: Dict[str, Any] = {}
    
    def _generate_simulation_id(self) -> str:
        """Genera un ID único para la simulación."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"sim_{timestamp}"
    
    def initialize_users(self, codes: np.ndarray):
        """
        Inicializa los usuarios con códigos de esparcimiento.
        
        Args:
            codes: Matriz de códigos (n_users, code_length)
        """
        self.codes = codes
        self.users = []
        
        for i in range(self.n_users):
            user = User(
                user_id=i,
                code=codes[i],
                label=f"Usuario {i+1}"
            )
            self.users.append(user)
        
        self.last_modified = datetime.now()
    
    def set_messages(self, messages: np.ndarray):
        """
        Asigna mensajes a los usuarios.
        
        Args:
            messages: Matriz de mensajes (n_users, n_bits)
        """
        if len(messages) != self.n_users:
            raise ValueError(f"Se esperan {self.n_users} mensajes, se recibieron {len(messages)}")
        
        for i, user in enumerate(self.users):
            user.original_message = messages[i]
        
        self.last_modified = datetime.now()
    
    def set_encoded_signals(self, signals: np.ndarray, total_signal: np.ndarray):
        """
        Asigna señales codificadas a los usuarios.
        
        Args:
            signals: Matriz de señales individuales (n_users, signal_length)
            total_signal: Señal total combinada
        """
        if len(signals) != self.n_users:
            raise ValueError(f"Se esperan {self.n_users} señales, se recibieron {len(signals)}")
        
        # Asignar señales a usuarios
        for i, user in enumerate(self.users):
            user.encoded_signal = signals[i]
        
        # Crear objeto Signal para señal total
        self.total_signal = Signal(
            signal_id=0,
            data=total_signal,
            signal_type='total',
            label='Señal Total'
        )
        
        self.is_encoded = True
        self.last_modified = datetime.now()
    
    def set_noisy_signal(self, noisy_signal: np.ndarray, snr_db: float):
        """
        Establece la señal con ruido.
        
        Args:
            noisy_signal: Señal con ruido añadido
            snr_db: SNR en dB
        """
        self.noisy_signal = Signal(
            signal_id=1,
            data=noisy_signal,
            signal_type='noisy',
            label=f'Señal con Ruido (SNR={snr_db}dB)'
        )
        
        self.snr_db = snr_db
        self.has_noise = True
        self.last_modified = datetime.now()
    
    def set_decoded_messages(self, decoded_messages: np.ndarray):
        """
        Asigna mensajes decodificados a los usuarios.
        
        Args:
            decoded_messages: Matriz de mensajes decodificados (n_users, n_bits)
        """
        if len(decoded_messages) != self.n_users:
            raise ValueError(f"Se esperan {self.n_users} mensajes, se recibieron {len(decoded_messages)}")
        
        for i, user in enumerate(self.users):
            user.decoded_message = decoded_messages[i]
        
        self.is_decoded = True
        self.last_modified = datetime.now()
        
        # Calcular métricas globales
        self._calculate_global_metrics()
    
    def _calculate_global_metrics(self):
        """Calcula métricas globales de la simulación."""
        if not self.is_decoded:
            return
        
        # BER promedio
        bers = [user.calculate_ber() for user in self.users if user.calculate_ber() is not None]
        self.metrics['average_ber'] = np.mean(bers) if bers else None
        self.metrics['max_ber'] = np.max(bers) if bers else None
        self.metrics['min_ber'] = np.min(bers) if bers else None
        
        # Total de bits y errores
        total_bits = self.n_users * self.n_bits
        total_errors = sum(np.sum(user.get_errors()) for user in self.users if user.get_errors() is not None)
        self.metrics['total_bits'] = total_bits
        self.metrics['total_errors'] = total_errors
        
        # Usuarios sin errores
        perfect_users = sum(1 for user in self.users if user.calculate_ber() == 0.0)
        self.metrics['perfect_users'] = perfect_users
    
    def get_user(self, user_id: int) -> Optional[User]:
        """
        Obtiene un usuario por su ID.
        
        Args:
            user_id: ID del usuario
        
        Returns:
            User: Usuario o None si no existe
        """
        for user in self.users:
            if user.user_id == user_id:
                return user
        return None
    
    def get_all_original_messages(self) -> Optional[np.ndarray]:
        """
        Obtiene todos los mensajes originales.
        
        Returns:
            np.ndarray: Matriz de mensajes originales
        """
        if not self.users or not self.users[0].has_message:
            return None
        
        messages = np.array([user.original_message for user in self.users])
        return messages
    
    def get_all_decoded_messages(self) -> Optional[np.ndarray]:
        """
        Obtiene todos los mensajes decodificados.
        
        Returns:
            np.ndarray: Matriz de mensajes decodificados
        """
        if not self.users or not self.users[0].has_decoded:
            return None
        
        messages = np.array([user.decoded_message for user in self.users])
        return messages
    
    def get_all_signals(self) -> Optional[np.ndarray]:
        """
        Obtiene todas las señales codificadas.
        
        Returns:
            np.ndarray: Matriz de señales
        """
        if not self.users or not self.users[0].has_signal:
            return None
        
        signals = np.array([user.encoded_signal for user in self.users])
        return signals
    
    def get_signal_for_decoding(self) -> Optional[np.ndarray]:
        """
        Obtiene la señal que se debe usar para decodificación.
        
        Returns:
            np.ndarray: Señal con ruido si existe, sino señal total
        """
        if self.has_noise and self.noisy_signal is not None:
            return self.noisy_signal.data
        elif self.total_signal is not None:
            return self.total_signal.data
        return None
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen de la simulación.
        
        Returns:
            Dict: Resumen con parámetros y métricas
        """
        summary = {
            'simulation_id': self.simulation_id,
            'created_at': self.created_at.isoformat(),
            'last_modified': self.last_modified.isoformat(),
            'parameters': {
                'n_users': self.n_users,
                'n_bits': self.n_bits,
                'code_type': self.code_type,
                'code_length': len(self.codes[0]) if self.codes is not None else None,
                'decoder_rate': self.decoder_rate,
                'snr_db': self.snr_db
            },
            'status': {
                'is_encoded': self.is_encoded,
                'is_decoded': self.is_decoded,
                'has_noise': self.has_noise
            },
            'metrics': self.metrics
        }
        
        return summary
    
    def reset(self):
        """Reinicia la simulación a su estado inicial."""
        self.users = []
        self.codes = None
        self.total_signal = None
        self.noisy_signal = None
        self.is_encoded = False
        self.is_decoded = False
        self.has_noise = False
        self.metrics = {}
        self.last_modified = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte la simulación completa a diccionario.
        
        Returns:
            Dict: Representación completa en diccionario
        """
        return {
            'simulation': self.get_summary(),
            'users': [user.to_dict() for user in self.users],
            'total_signal': self.total_signal.to_dict() if self.total_signal else None,
            'noisy_signal': self.noisy_signal.to_dict() if self.noisy_signal else None
        }
    
    def __str__(self) -> str:
        """Representación en string de la simulación."""
        status = "Encoded" if self.is_encoded else "Not encoded"
        if self.is_decoded:
            status += ", Decoded"
        if self.has_noise:
            status += f", SNR={self.snr_db}dB"
        
        avg_ber = self.metrics.get('average_ber')
        ber_str = f", Avg BER={avg_ber:.4f}" if avg_ber is not None else ""
        
        return (f"Simulation {self.simulation_id}: "
                f"{self.n_users} users, {self.n_bits} bits, "
                f"{self.code_type} codes - "
                f"{status}{ber_str}")