"""
Demodulador OFDM - Recupera símbolos de la señal OFDM recibida

Soporta dos modos:
- Modo 'simple': Demodulación OFDM clásica (sin estimación de canal)
- Modo 'lte': Demodulación OFDM con estimación de canal y ecualización (usando LTEReceiver)
"""
import numpy as np
from core.modulator import QAMModulator


class OFDMDemodulator:
    """Demodulador OFDM que implementa sincronización y FFT con soporte LTE"""
    
    def __init__(self, config, mode='simple', enable_equalization=False):
        """
        Inicializa el demodulador OFDM
        
        Args:
            config: Objeto LTEConfig con parámetros de configuración
            mode: 'simple' (clásico) o 'lte' (con estimación de canal y ecualización)
            enable_equalization: Si True, habilita ecualización en modo LTE
        """
        self.config = config
        self.mode = mode
        self.enable_equalization = enable_equalization
        self.qam_demodulator = QAMModulator(config.modulation)
        
        # Inicializar receptor LTE si es necesario
        if self.mode == 'lte':
            try:
                from core.lte_receiver import LTEReceiver
                self.lte_receiver = LTEReceiver(config, cell_id=0, 
                                               enable_equalization=enable_equalization)
            except ImportError:
                # Si no se puede importar LTEReceiver, usar modo simple
                print("Warning: LTEReceiver no disponible, usando modo simple")
                self.mode = 'simple'
                self.lte_receiver = None
        else:
            self.lte_receiver = None
    
    def demodulate(self, received_signal):
        """
        Demodula una señal OFDM recibida
        
        Proceso:
        1. Sincronización y muestreo (asumimos sincronización perfecta)
        2. Remover prefijo cíclico
        3. Aplicar FFT
        4. Recuperar símbolos QAM
        
        Args:
            received_signal: Señal recibida (después del canal)
            
        Returns:
            Array de símbolos demodulados
        """
        # Asegurarse de que el tamaño es correcto
        expected_length = self.config.N + self.config.cp_length
        
        if len(received_signal) < expected_length:
            # Rellenar con ceros si es necesario
            received_signal = np.pad(received_signal, 
                                   (0, expected_length - len(received_signal)), 
                                   'constant')
        
        # Paso 1: Tomar solo la primera muestra de símbolo OFDM con CP
        received_ofdm = received_signal[:expected_length]
        
        # Paso 2: Remover prefijo cíclico
        signal_without_cp = received_ofdm[self.config.cp_length:]
        
        # Paso 3: Aplicar FFT
        frequency_domain = np.fft.fft(signal_without_cp) / np.sqrt(self.config.N)
        
        # Paso 4: Recuperar símbolos útiles (los primeros Nc)
        received_symbols = frequency_domain[:self.config.Nc]
        
        return received_symbols
    
    def demodulate_stream(self, received_signal, num_ofdm_symbols=None, resource_grid=None):
        """
        Demodula un stream de señales OFDM
        
        En modo LTE, usa el receptor LTE con estimación de canal y ecualización.
        En modo simple, usa FFT clásica.
        
        Args:
            received_signal: Stream de señal recibida
            num_ofdm_symbols: Número de símbolos OFDM a demodular (para modo simple)
            resource_grid: Grid de recursos LTE (para modo LTE, opcional)
            
        Returns:
            tuple: (all_symbols_demodulated, bits_recovered)
        """
        # Si estamos en modo LTE y tenemos el receptor disponible
        if self.mode == 'lte' and self.lte_receiver is not None:
            # Usar receptor LTE con estimación de canal y ecualización
            result = self.lte_receiver.receive_and_decode(received_signal)
            
            # Extraer datos
            symbols_data = result['symbols_data_only']
            bits = self.qam_demodulator.symbols_to_bits(symbols_data)
            
            return symbols_data, bits
        
        # Modo simple: FFT clásica
        if num_ofdm_symbols is None:
            # Calcular automáticamente
            samples_per_symbol = self.config.N + self.config.cp_length
            num_ofdm_symbols = int(np.ceil(len(received_signal) / samples_per_symbol))
        
        samples_per_symbol = self.config.N + self.config.cp_length
        all_symbols = []
        all_bits = []
        
        for i in range(num_ofdm_symbols):
            start_idx = i * samples_per_symbol
            end_idx = start_idx + samples_per_symbol
            
            # Extraer la porción correspondiente
            if end_idx > len(received_signal):
                # Rellenar con ceros si es necesario
                chunk = np.pad(received_signal[start_idx:],
                             (0, end_idx - len(received_signal)),
                             'constant')
            else:
                chunk = received_signal[start_idx:end_idx]
            
            # Demodular
            symbols = self.demodulate(chunk)
            all_symbols.append(symbols)
            
            # Convertir a bits
            bits = self.qam_demodulator.symbols_to_bits(symbols)
            all_bits.append(bits)
        
        # Concatenar todos los símbolos y bits
        all_symbols_array = np.concatenate(all_symbols)
        all_bits_array = np.concatenate(all_bits)
        
        return all_symbols_array, all_bits_array
    
    def get_qam_demodulator(self):
        """Retorna el demodulador QAM para acceso directo"""
        return self.qam_demodulator


class SymbolDetector:
    """Detector de símbolos con decisión dura (hard decision)"""
    
    def __init__(self, constellation):
        """
        Inicializa el detector
        
        Args:
            constellation: Array de símbolos de la constelación
        """
        self.constellation = constellation
    
    def detect(self, received_symbol):
        """
        Detecta el símbolo más cercano
        
        Args:
            received_symbol: Símbolo recibido
            
        Returns:
            Símbolo detectado
        """
        distances = np.abs(self.constellation - received_symbol)
        nearest_idx = np.argmin(distances)
        return self.constellation[nearest_idx]
    
    def detect_batch(self, received_symbols):
        """
        Detecta símbolos para un batch de datos
        
        Args:
            received_symbols: Array de símbolos recibidos
            
        Returns:
            Array de símbolos detectados
        """
        detected = np.zeros_like(received_symbols)
        for i, symbol in enumerate(received_symbols):
            detected[i] = self.detect(symbol)
        return detected
    
    def calculate_error_rate(self, transmitted_symbols, received_symbols):
        """
        Calcula la tasa de error de símbolo (SER)
        
        Args:
            transmitted_symbols: Símbolos transmitidos
            received_symbols: Símbolos recibidos/detectados
            
        Returns:
            float: Tasa de error
        """
        errors = np.sum(transmitted_symbols != received_symbols)
        ser = errors / len(transmitted_symbols)
        return ser
