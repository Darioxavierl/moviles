"""
Sistema OFDM Completo - Integra modulador, canal y demodulador
"""
import numpy as np
import time
from core.modulator import OFDMModulator, QAMModulator
from core.demodulator import OFDMDemodulator, SymbolDetector
from core.channel import ChannelSimulator
from config.lte_params import LTEConfig


class OFDMSystem:
    """Sistema OFDM completo que integra todos los componentes"""
    
    def __init__(self, config):
        """
        Inicializa el sistema OFDM
        
        Args:
            config: Objeto LTEConfig con parámetros de configuración
        """
        self.config = config
        self.modulator = OFDMModulator(config)
        self.demodulator = OFDMDemodulator(config)
        self.channel = ChannelSimulator('awgn', snr_db=10.0)
        self.symbol_detector = SymbolDetector(
            self.modulator.get_qam_modulator().get_constellation()
        )
        
        # Estadísticas
        self.statistics = {
            'transmitted_bits': 0,
            'received_bits': 0,
            'bit_errors': 0,
            'symbol_errors': 0,
            'total_symbols': 0,
            'transmission_time': 0
        }
    
    def transmit(self, bits, snr_db=10.0, return_time=False):
        """
        Transmite bits a través del sistema OFDM
        
        Proceso:
        1. Modular bits a señal OFDM
        2. Transmitir a través del canal AWGN
        
        Args:
            bits: Array de bits a transmitir
            snr_db: SNR en dB
            return_time: Si True, retorna tiempo de transmisión en dict
            
        Returns:
            dict: Resultados de transmisión con todas las métricas
        """
        start_time = time.time()
        
        # IMPORTANTE: Guardar número ORIGINAL de bits
        original_num_bits = len(bits)
        
        # Configurar SNR
        self.channel.set_snr(snr_db)
        
        # Modular bits (puede rellenar con ceros)
        signal_transmitted, symbols_transmitted = self.modulator.modulate_stream(bits)
        
        # Transmitir a través del canal
        signal_received, _ = self.channel.channel.transmit(signal_transmitted)
        
        # Recibir
        bits_rx, symbols_detected, symbols_rx = self.receive(signal_received)
        
        transmission_time = time.time() - start_time
        self.statistics['transmission_time'] = transmission_time
        
        # IMPORTANTE: Retornar EXACTAMENTE el número original de bits
        # Truncar si recibimos más, rellenar con ceros si recibimos menos
        if len(bits_rx) < original_num_bits:
            bits_rx = np.pad(bits_rx, (0, original_num_bits - len(bits_rx)), 'constant')
        else:
            bits_rx = bits_rx[:original_num_bits]
        
        # Calcular errores solo con los bits originales
        bits_error = np.sum(bits != bits_rx)
        ber = bits_error / original_num_bits if original_num_bits > 0 else 0
        
        # Estadísticas de símbolos
        num_tx_symbols = sum(len(s) for s in symbols_transmitted)
        num_rx_symbols = len(symbols_detected)
        num_symbols_compare = min(num_tx_symbols, num_rx_symbols)
        
        symbols_tx_flat = np.concatenate(symbols_transmitted) if symbols_transmitted else np.array([])
        symbol_errors = 0
        if num_symbols_compare > 0:
            symbol_errors = np.sum(
                symbols_tx_flat[:num_symbols_compare] != symbols_detected[:num_symbols_compare]
            )
        ser = symbol_errors / num_symbols_compare if num_symbols_compare > 0 else 0
        
        results = {
            # Lowercase keys for GUI
            'snr_db': snr_db,
            'n_bits': original_num_bits,
            'transmitted_bits': original_num_bits,
            'received_bits': original_num_bits,
            'bit_errors': bits_error,
            'errors': bits_error,
            'ber': ber,
            'symbol_errors': symbol_errors,
            'ser': ser,
            'transmission_time': transmission_time,
            'evm': 0.0,
            
            # Uppercase keys for compatibility with simulator
            'SNR_dB': snr_db,
            'BER': ber,
            'SER': ser,
            
            # Common keys used by both
            'total_symbols': num_tx_symbols,
            'signal_tx': signal_transmitted,
            'signal_rx': signal_received,
            'symbols_tx': symbols_tx_flat[:num_symbols_compare] if num_symbols_compare > 0 else np.array([]),
            'symbols_rx': symbols_detected[:num_symbols_compare] if num_symbols_compare > 0 else np.array([]),
            'transmitted_symbols': symbols_tx_flat,
            'received_symbols': symbols_detected,
            'bits_tx': bits,  # Bits transmitidos originales
            'bits_rx': bits_rx,  # Bits recibidos (siempre mismo tamaño que bits_tx)
        }
        
        return results
    
    def receive(self, signal_received):
        """
        Recibe y demodula la señal OFDM
        
        Proceso:
        1. Demodular señal a símbolos
        2. Detectar símbolos más cercanos
        3. Convertir a bits
        
        Args:
            signal_received: Señal recibida del canal
            
        Returns:
            tuple: (bits_received, symbols_detected, symbols_demodulated)
        """
        # Calcular número de símbolos OFDM
        samples_per_symbol = self.config.N + self.config.cp_length
        num_ofdm_symbols = int(np.ceil(len(signal_received) / samples_per_symbol))
        
        # Demodular
        symbols_demodulated, bits_received = self.demodulator.demodulate_stream(
            signal_received, num_ofdm_symbols
        )
        
        # Detectar símbolos
        symbols_detected = self.symbol_detector.detect_batch(symbols_demodulated)
        
        return bits_received, symbols_detected, symbols_demodulated
    
    def simulate(self, bits, snr_db):
        """
        Alias para transmit() - mantiene compatibilidad con código anterior
        
        Args:
            bits: Array de bits a transmitir
            snr_db: SNR en dB
            
        Returns:
            dict: Resultados de la simulación
        """
        return self.transmit(bits, snr_db)
    
    def run_ber_sweep(self, num_bits, snr_range, n_iterations, progress_callback=None, bits=None):
        """
        Realiza un barrido de SNR para calcular BER vs SNR
        
        Args:
            num_bits: Número de bits por simulación
            snr_range: Array de valores SNR en dB
            n_iterations: Número de iteraciones por SNR
            progress_callback: Función de callback para progreso
            bits: Array de bits específicos a transmitir (None = generar aleatorios)
            
        Returns:
            dict: Resultados del barrido (ber_mean, snr_range, etc.)
        """
        snr_range = np.atleast_1d(snr_range).astype(float)
        results = {
            'snr_db': snr_range,
            'n_bits': num_bits,
            'n_iterations': n_iterations,
            'ber_mean': [],
            'ber_std': [],
            'ber_ci_lower': [],
            'ber_ci_upper': [],
            'ser_mean': [],
            'ser_std': [],
            'ber_runs': [],
            'ser_runs': []
        }
        
        total_steps = len(snr_range)
        
        for idx, snr_db in enumerate(snr_range):
            ber_values = []
            ser_values = []
            
            # Ejecutar n_iterations corridas para cada SNR
            for run in range(n_iterations):
                # Usar bits proporcionados o generar aleatorios
                if bits is not None:
                    test_bits = bits.copy()
                else:
                    test_bits = np.random.randint(0, 2, num_bits)
                
                # Simular
                sim_results = self.transmit(test_bits, snr_db)
                
                ber_values.append(sim_results['ber'])
                ser_values.append(sim_results['ser'])
                
                # Reportar progreso
                progress = ((idx * n_iterations + run + 1) / (total_steps * n_iterations)) * 100
                if progress_callback:
                    progress_callback(progress, snr_db, run + 1)
            
            # Calcular estadísticas
            ber_array = np.array(ber_values)
            ser_array = np.array(ser_values)
            
            ber_mean = np.mean(ber_array)
            ber_std = np.std(ber_array)
            ser_mean = np.mean(ser_array)
            ser_std = np.std(ser_array)
            
            # Calcular intervalo de confianza (95%)
            from scipy import stats
            if len(ber_array) > 1:
                n = len(ber_array)
                t_value = stats.t.ppf(0.975, n - 1)
                margin = t_value * ber_std / np.sqrt(n)
                ber_ci_lower = max(0, ber_mean - margin)
                ber_ci_upper = ber_mean + margin
            else:
                ber_ci_lower = ber_ci_upper = ber_mean
            
            results['ber_mean'].append(ber_mean)
            results['ber_std'].append(ber_std)
            results['ber_ci_lower'].append(ber_ci_lower)
            results['ber_ci_upper'].append(ber_ci_upper)
            results['ser_mean'].append(ser_mean)
            results['ser_std'].append(ser_std)
            results['ber_runs'].append(ber_values)
            results['ser_runs'].append(ser_values)
        
        # Convertir a arrays numpy
        for key in results:
            if key not in ['ber_runs', 'ser_runs']:
                results[key] = np.array(results[key])
        
        return results
    
    def run_ber_sweep_all_modulations(self, num_bits, snr_range, n_iterations, 
                                      progress_callback=None, bits=None):
        """
        Realiza barrido de SNR para TODAS las modulaciones
        
        Args:
            num_bits: Número de bits por simulación
            snr_range: Array de valores SNR en dB
            n_iterations: Número de iteraciones por SNR
            progress_callback: Función de callback para progreso
            bits: Array de bits específicos a transmitir (None = generar aleatorios)
            
        Returns:
            dict: Resultados agrupados por modulación
        """
        from config.lte_params import MODULATION_SCHEMES
        
        snr_range = np.atleast_1d(snr_range).astype(float)
        all_results = {}
        
        original_modulation = self.config.modulation
        original_bits_per_symbol = self.config.bits_per_symbol
        
        total_modulations = len(MODULATION_SCHEMES)
        total_snrs = len(snr_range)
        total_steps = total_modulations * total_snrs * n_iterations
        current_step = 0
        
        # Para cada modulación
        for mod_idx, modulation in enumerate(MODULATION_SCHEMES):
            # Cambiar modulación
            self.config.modulation = modulation
            self.config.bits_per_symbol = self._get_bits_per_symbol(modulation)
            
            # Reportar inicio de modulación
            if progress_callback:
                progress = (current_step / total_steps) * 100
                progress_callback(int(progress), f"Modulación: {modulation}")
            
            # Crear callback interno para rastrear progreso
            def internal_progress_callback(inner_progress, snr, iteration):
                nonlocal current_step
                # Incrementar counter
                steps_in_this_snr = iteration
                modulation_progress = ((mod_idx * total_snrs * n_iterations + 
                                       (snr_range.tolist().index(snr) if snr in snr_range else 0) * n_iterations + 
                                       steps_in_this_snr) / total_steps) * 100
                if progress_callback:
                    msg = f"{modulation} - SNR: {snr:.1f} dB, Iter: {iteration}/{n_iterations}"
                    progress_callback(int(modulation_progress), msg)
            
            # Ejecutar barrido para esta modulación
            results = self.run_ber_sweep(
                num_bits=num_bits,
                snr_range=snr_range,
                n_iterations=n_iterations,
                progress_callback=internal_progress_callback,
                bits=bits
            )
            
            all_results[modulation] = results
            current_step += total_snrs * n_iterations
        
        # Restaurar modulación original
        self.config.modulation = original_modulation
        self.config.bits_per_symbol = original_bits_per_symbol
        
        return all_results
    
    def _get_bits_per_symbol(self, modulation):
        """Obtiene bits por símbolo para una modulación"""
        bits_map = {
            'QPSK': 2,
            '16-QAM': 4,
            '64-QAM': 6
        }
        return bits_map.get(modulation, 2)
    
    def calculate_transmission_metrics(self, num_bits):
        """
        Calcula métricas de transmisión para throughput
        
        Args:
            num_bits: Número de bits
            
        Returns:
            dict: Métricas de transmisión
        """
        bits_per_ofdm = self.config.Nc * self.config.bits_per_symbol
        num_ofdm_symbols = int(np.ceil(num_bits / bits_per_ofdm))
        duration = num_ofdm_symbols * (self.config.N + self.config.cp_length) * self.config.Ts
        throughput_mbps = (num_bits / duration) / 1e6 if duration > 0 else 0
        
        return {
            'n_ofdm_symbols': num_ofdm_symbols,
            'duration_seconds': duration,
            'throughput_mbps': throughput_mbps
        }
    
    def calculate_signal_power(self, signal):
        """
        Calcula la potencia de una señal
        
        Args:
            signal: Señal (real o compleja)
            
        Returns:
            float: Potencia media
        """
        if np.iscomplexobj(signal):
            return np.mean(np.abs(signal) ** 2)
        else:
            return np.mean(signal ** 2)
    
    def get_statistics(self):
        """Retorna las estadísticas del sistema"""
        return self.statistics.copy()
    
    def reset_statistics(self):
        """Reinicia las estadísticas"""
        for key in self.statistics:
            if isinstance(self.statistics[key], (int, float)):
                self.statistics[key] = 0
    
    def get_config_info(self):
        """Retorna información de la configuración actual"""
        return self.config.get_info()


class OFDMSystemManager:
    """Gestor del sistema OFDM que maneja múltiples configuraciones"""
    
    def __init__(self):
        """Inicializa el gestor del sistema"""
        self.current_system = None
        self.available_configs = {}
    
    def create_system(self, bandwidth, delta_f, modulation, cp_type):
        """
        Crea un nuevo sistema OFDM con la configuración especificada
        
        Args:
            bandwidth: Ancho de banda en MHz
            delta_f: Separación entre subportadoras en kHz
            modulation: Esquema de modulación
            cp_type: Tipo de prefijo cíclico
            
        Returns:
            OFDMSystem: Sistema OFDM creado
        """
        config = LTEConfig(bandwidth, delta_f, modulation, cp_type)
        system = OFDMSystem(config)
        self.current_system = system
        return system
    
    def get_current_system(self):
        """Retorna el sistema actual"""
        return self.current_system
    
    def update_system_snr(self, snr_db):
        """
        Actualiza el SNR del sistema actual
        
        Args:
            snr_db: SNR en dB
        """
        if self.current_system:
            self.current_system.channel.set_snr(snr_db)
    
    def get_available_presets(self):
        """Retorna los perfiles LTE disponibles"""
        from config.lte_params import LTE_PROFILES
        return LTE_PROFILES
