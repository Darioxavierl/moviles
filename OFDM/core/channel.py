"""
Canal AWGN - Simula el canal de comunicación con ruido blanco gaussiano
"""
import numpy as np


class AWGNChannel:
    """Canal AWGN que añade ruido gaussiano a la señal"""
    
    def __init__(self, snr_db=10.0):
        """
        Inicializa el canal AWGN
        
        Args:
            snr_db: Relación Señal-Ruido en dB
        """
        self.snr_db = snr_db
        self.snr_linear = 10 ** (snr_db / 10)
        self.noise_power = None
    
    def set_snr(self, snr_db):
        """
        Establece el SNR del canal
        
        Args:
            snr_db: Relación Señal-Ruido en dB
        """
        self.snr_db = snr_db
        self.snr_linear = 10 ** (snr_db / 10)
    
    def transmit(self, signal):
        """
        Transmite una señal a través del canal AWGN
        
        Args:
            signal: Señal a transmitir (puede ser real o compleja)
            
        Returns:
            tuple: (signal_received, noise_added)
        """
        # Calcular potencia de señal
        if np.iscomplexobj(signal):
            signal_power = np.mean(np.abs(signal) ** 2)
        else:
            signal_power = np.mean(signal ** 2)
        
        # Calcular potencia de ruido necesaria
        # SNR = signal_power / noise_power
        noise_power = signal_power / self.snr_linear
        self.noise_power = noise_power
        
        # Generar ruido blanco gaussiano complejo
        if np.iscomplexobj(signal):
            # Para señales complejas: ruido en componente I y Q
            noise_real = np.random.normal(0, np.sqrt(noise_power / 2), len(signal))
            noise_imag = np.random.normal(0, np.sqrt(noise_power / 2), len(signal))
            noise = noise_real + 1j * noise_imag
        else:
            # Para señales reales
            noise = np.random.normal(0, np.sqrt(noise_power), len(signal))
        
        # Señal recibida = Señal transmitida + Ruido
        signal_received = signal + noise
        
        return signal_received, noise
    
    def get_noise_power(self):
        """Retorna la potencia de ruido del último símbolo transmitido"""
        return self.noise_power
    
    def get_snr_info(self):
        """Retorna información del SNR actual"""
        return {
            'SNR (dB)': self.snr_db,
            'SNR (lineal)': self.snr_linear,
            'Potencia de ruido': self.noise_power
        }


class FadingChannel:
    """Canal con desvanecimiento (extensión futura)"""
    
    def __init__(self, snr_db=10.0, fading_type='rayleigh'):
        """
        Inicializa el canal con desvanecimiento
        
        Args:
            snr_db: Relación Señal-Ruido en dB
            fading_type: Tipo de desvanecimiento ('rayleigh', 'rician', etc.)
        """
        self.snr_db = snr_db
        self.snr_linear = 10 ** (snr_db / 10)
        self.fading_type = fading_type
        self.awgn_channel = AWGNChannel(snr_db)
    
    def transmit(self, signal):
        """
        Transmite a través del canal con desvanecimiento
        
        Args:
            signal: Señal a transmitir
            
        Returns:
            tuple: (signal_received, channel_response)
        """
        # Generar respuesta del canal según tipo
        if self.fading_type == 'rayleigh':
            h_real = np.random.normal(0, 1/np.sqrt(2), len(signal))
            h_imag = np.random.normal(0, 1/np.sqrt(2), len(signal))
            channel_response = h_real + 1j * h_imag
        else:
            # Por defecto, usar desvanecimiento de Rayleigh
            h_real = np.random.normal(0, 1/np.sqrt(2), len(signal))
            h_imag = np.random.normal(0, 1/np.sqrt(2), len(signal))
            channel_response = h_real + 1j * h_imag
        
        # Aplicar desvanecimiento
        signal_faded = signal * channel_response
        
        # Añadir ruido AWGN
        signal_received, _ = self.awgn_channel.transmit(signal_faded)
        
        return signal_received, channel_response


class ChannelSimulator:
    """Simulador de canal que gestiona múltiples canales"""
    
    def __init__(self, channel_type='awgn', snr_db=10.0):
        """
        Inicializa el simulador de canal
        
        Args:
            channel_type: 'awgn' o 'fading'
            snr_db: SNR en dB
        """
        self.channel_type = channel_type
        
        if channel_type == 'awgn':
            self.channel = AWGNChannel(snr_db)
        elif channel_type == 'fading':
            self.channel = FadingChannel(snr_db)
        else:
            raise ValueError(f"Tipo de canal desconocido: {channel_type}")
    
    def transmit(self, signal):
        """
        Transmite a través del canal
        
        Args:
            signal: Señal a transmitir
            
        Returns:
            Signal recibida
        """
        received, _ = self.channel.transmit(signal)
        return received
    
    def set_snr(self, snr_db):
        """Establece el SNR"""
        self.channel.set_snr(snr_db)
    
    def get_channel(self):
        """Retorna el objeto del canal actual"""
        return self.channel
