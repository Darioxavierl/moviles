"""
Parámetros y configuraciones LTE para el simulador OFDM
"""
import numpy as np

# Perfiles LTE predefinidos
LTE_PROFILES = {
    1.25: {'Nc': 76, 'N': 128},
    2.5: {'Nc': 150, 'N': 256},
    5.0: {'Nc': 300, 'N': 512},
    10.0: {'Nc': 600, 'N': 1024},
    15.0: {'Nc': 900, 'N': 2048},
    20.0: {'Nc': 1200, 'N': 2048}
}

# Valores de prefijo cíclico (en microsegundos)
CP_VALUES = {
    'normal': 4.7,
    'extended_15khz': 16.6,
    'extended_7.5khz': 33.0
}

# Esquemas de modulación disponibles
MODULATION_SCHEMES = ['QPSK', '16-QAM', '64-QAM']

# Separación entre subportadoras (en kHz)
SUBCARRIER_SPACING = [15.0, 7.5]


class LTEConfig:
    """Clase para gestionar la configuración de parámetros LTE"""
    
    def __init__(self, bandwidth=5.0, delta_f=15.0, modulation='QPSK', cp_type='normal'):
        """
        Inicializa la configuración LTE
        
        Args:
            bandwidth: Ancho de banda en MHz
            delta_f: Separación entre subportadoras en kHz
            modulation: Esquema de modulación
            cp_type: Tipo de prefijo cíclico
        """
        self.bandwidth = bandwidth
        self.delta_f = delta_f  # kHz
        self.modulation = modulation
        self.cp_type = cp_type
        
        # Calcular parámetros derivados
        self._calculate_parameters()
    
    def _calculate_parameters(self):
        """Calcula los parámetros derivados de la configuración"""
        # Obtener perfil LTE
        if self.bandwidth in LTE_PROFILES:
            profile = LTE_PROFILES[self.bandwidth]
            self.Nc = profile['Nc']
            self.N = profile['N']
        else:
            # Calcular manualmente si no hay perfil predefinido
            self.Nc = int((self.bandwidth * 1e3) / self.delta_f)
            self.N = self._next_power_of_2(self.Nc)
        
        # Frecuencia de muestreo (Hz)
        self.fs = self.N * self.delta_f * 1e3  # kHz a Hz
        
        # Período de muestreo (segundos)
        self.Ts = 1 / self.fs
        
        # Duración del símbolo OFDM sin CP (segundos)
        self.T_symbol = self.N * self.Ts
        
        # Longitud del prefijo cíclico
        self.cp_duration = self._get_cp_duration()  # microsegundos
        self.cp_length = int(self.cp_duration * 1e-6 * self.fs)  # muestras
        
        # Bits por símbolo según modulación
        self.bits_per_symbol = self._get_bits_per_symbol()
        
        # Número total de muestras por símbolo OFDM (con CP)
        self.samples_per_ofdm_symbol = self.N + self.cp_length
        
    def _next_power_of_2(self, x):
        """Calcula la siguiente potencia de 2"""
        return int(2**np.ceil(np.log2(x)))
    
    def _get_cp_duration(self):
        """Obtiene la duración del prefijo cíclico según configuración"""
        if self.cp_type == 'normal':
            return CP_VALUES['normal']
        elif self.cp_type == 'extended':
            if self.delta_f == 15.0:
                return CP_VALUES['extended_15khz']
            else:  # 7.5 kHz
                return CP_VALUES['extended_7.5khz']
        return CP_VALUES['normal']
    
    def _get_bits_per_symbol(self):
        """Retorna el número de bits por símbolo según el esquema de modulación"""
        if self.modulation == 'QPSK':
            return 2
        elif self.modulation == '16-QAM':
            return 4
        elif self.modulation == '64-QAM':
            return 6
        else:
            raise ValueError(f"Modulación no soportada: {self.modulation}")
    
    def get_info(self):
        """Retorna un diccionario con toda la información de configuración"""
        return {
            'Ancho de banda (MHz)': self.bandwidth,
            'Separación subportadoras (kHz)': self.delta_f,
            'Modulación': self.modulation,
            'Tipo CP': self.cp_type,
            'Subportadoras útiles (Nc)': self.Nc,
            'Puntos FFT (N)': self.N,
            'Frecuencia muestreo (MHz)': self.fs / 1e6,
            'Período muestreo (ns)': self.Ts * 1e9,
            'Duración símbolo OFDM (μs)': self.T_symbol * 1e6,
            'Duración CP (μs)': self.cp_duration,
            'Longitud CP (muestras)': self.cp_length,
            'Bits por símbolo': self.bits_per_symbol,
            'Muestras por símbolo OFDM': self.samples_per_ofdm_symbol
        }
    
    def __str__(self):
        """Representación en string de la configuración"""
        info = self.get_info()
        lines = ["Configuración LTE OFDM:"]
        lines.extend([f"  {k}: {v}" for k, v in info.items()])
        return "\n".join(lines)