"""
Módulo de modelos de datos para el sistema CDMA.
Contiene las clases User, Signal y Simulation para estructurar los datos.
"""

import numpy as np
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Signal:
    """
    Representa una señal en el sistema CDMA.
    """
    signal_id: int
    data: np.ndarray
    signal_type: str  # 'individual', 'total', 'noisy'
    label: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Inicialización adicional."""
        if self.label is None:
            self.label = f"Signal {self.signal_id}"
        
        # Calcular métricas automáticamente
        self._calculate_basic_metrics()
    
    def _calculate_basic_metrics(self):
        """Calcula métricas básicas de la señal."""
        if self.data is not None and len(self.data) > 0:
            self.metadata['length'] = len(self.data)
            self.metadata['power'] = np.mean(self.data ** 2)
            self.metadata['energy'] = np.sum(self.data ** 2)
            self.metadata['peak'] = np.max(np.abs(self.data))
            self.metadata['rms'] = np.sqrt(self.metadata['power'])
    
    @property
    def length(self) -> int:
        """Retorna la longitud de la señal."""
        return len(self.data) if self.data is not None else 0
    
    @property
    def power(self) -> float:
        """Retorna la potencia de la señal."""
        return self.metadata.get('power', 0.0)
    
    @property
    def energy(self) -> float:
        """Retorna la energía de la señal."""
        return self.metadata.get('energy', 0.0)
    
    @property
    def peak(self) -> float:
        """Retorna el valor pico de la señal."""
        return self.metadata.get('peak', 0.0)
    
    @property
    def rms(self) -> float:
        """Retorna el valor RMS de la señal."""
        return self.metadata.get('rms', 0.0)
    
    def normalize(self, method: str = 'peak') -> 'Signal':
        """
        Crea una nueva señal normalizada.
        
        Args:
            method: Método de normalización ('peak', 'rms', 'energy')
        
        Returns:
            Signal: Nueva señal normalizada
        """
        if method == 'peak':
            normalized_data = self.data / self.peak if self.peak > 0 else self.data
        elif method == 'rms':
            normalized_data = self.data / self.rms if self.rms > 0 else self.data
        elif method == 'energy':
            normalized_data = self.data / np.sqrt(self.energy) if self.energy > 0 else self.data
        else:
            normalized_data = self.data
        
        return Signal(
            signal_id=self.signal_id,
            data=normalized_data,
            signal_type=f"{self.signal_type}_normalized",
            label=f"{self.label} (normalized)",
            metadata=self.metadata.copy()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte la señal a diccionario.
        
        Returns:
            Dict: Representación en diccionario
        """
        return {
            'signal_id': self.signal_id,
            'label': self.label,
            'signal_type': self.signal_type,
            'length': self.length,
            'power': self.power,
            'energy': self.energy,
            'peak': self.peak,
            'rms': self.rms,
            'metadata': self.metadata
        }
    
    def __str__(self) -> str:
        """Representación en string de la señal."""
        return (f"{self.label} ({self.signal_type}) - "
                f"Length: {self.length}, "
                f"Power: {self.power:.4f}, "
                f"Peak: {self.peak:.4f}")
