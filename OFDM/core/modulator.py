"""
Modulador OFDM - Convierte símbolos QAM/QPSK a señal OFDM
"""
import numpy as np
from config.lte_params import LTEConfig


class QAMModulator:
    """Modulador QAM/QPSK que genera símbolos complejos"""
    
    def __init__(self, modulation_type='QPSK'):
        """
        Inicializa el modulador QAM/QPSK
        
        Args:
            modulation_type: 'QPSK', '16-QAM' o '64-QAM'
        """
        self.modulation_type = modulation_type
        self.constellation = self._generate_constellation()
    
    def _generate_constellation(self):
        """Genera la constelación de símbolos"""
        if self.modulation_type == 'QPSK':
            # QPSK: 4 símbolos
            constellation = np.array([
                1+1j, 1-1j, -1+1j, -1-1j
            ]) / np.sqrt(2)
        
        elif self.modulation_type == '16-QAM':
            # 16-QAM: 16 símbolos en grid 4x4
            real_vals = np.array([-3, -1, 1, 3])
            imag_vals = np.array([-3, -1, 1, 3])
            symbols = []
            for r in real_vals:
                for i in imag_vals:
                    symbols.append(r + 1j*i)
            constellation = np.array(symbols) / np.sqrt(10)
        
        elif self.modulation_type == '64-QAM':
            # 64-QAM: 64 símbolos en grid 8x8
            real_vals = np.array([-7, -5, -3, -1, 1, 3, 5, 7])
            imag_vals = np.array([-7, -5, -3, -1, 1, 3, 5, 7])
            symbols = []
            for r in real_vals:
                for i in imag_vals:
                    symbols.append(r + 1j*i)
            constellation = np.array(symbols) / np.sqrt(42)
        
        else:
            raise ValueError(f"Modulación no soportada: {self.modulation_type}")
        
        return constellation
    
    def bits_to_symbols(self, bits):
        """
        Convierte bits a símbolos complejos
        
        Args:
            bits: Array de bits (0 y 1)
            
        Returns:
            Array de símbolos complejos
        """
        bits_per_symbol = int(np.log2(len(self.constellation)))
        
        # Rellenar bits si es necesario
        if len(bits) % bits_per_symbol != 0:
            bits = np.pad(bits, (0, bits_per_symbol - len(bits) % bits_per_symbol), 'constant')
        
        num_symbols = len(bits) // bits_per_symbol
        symbols = np.zeros(num_symbols, dtype=complex)
        
        for i in range(num_symbols):
            # Agrupar bits
            bit_group = bits[i*bits_per_symbol:(i+1)*bits_per_symbol]
            # Convertir a índice decimal
            index = int(''.join(map(str, bit_group.astype(int))), 2)
            # Mapear a símbolo
            symbols[i] = self.constellation[index % len(self.constellation)]
        
        return symbols
    
    def symbols_to_bits(self, symbols):
        """
        Convierte símbolos complejos a bits (demodulación)
        
        Args:
            symbols: Array de símbolos complejos
            
        Returns:
            Array de bits demodulados
        """
        bits_per_symbol = int(np.log2(len(self.constellation)))
        bits = []
        
        for symbol in symbols:
            # Buscar el símbolo más cercano en la constelación
            distances = np.abs(self.constellation - symbol)
            nearest_idx = np.argmin(distances)
            
            # Convertir índice a bits
            bit_pattern = format(nearest_idx, f'0{bits_per_symbol}b')
            bits.extend([int(b) for b in bit_pattern])
        
        return np.array(bits)
    
    def get_constellation(self):
        """Retorna la constelación actual"""
        return self.constellation


class OFDMModulator:
    """Modulador OFDM que implementa IFFT y prefijo cíclico"""
    
    def __init__(self, config):
        """
        Inicializa el modulador OFDM
        
        Args:
            config: Objeto LTEConfig con parámetros de configuración
        """
        self.config = config
        self.qam_modulator = QAMModulator(config.modulation)
    
    def modulate(self, bits):
        """
        Modula bits a señal OFDM
        
        Proceso:
        1. Convertir bits a símbolos QAM
        2. Convertir serie a paralelo (mapear a subportadoras)
        3. Aplicar IFFT
        4. Agregar prefijo cíclico
        5. Convertir a serie
        
        Args:
            bits: Array de bits
            
        Returns:
            tuple: (signal_time_domain, symbols)
        """
        # Paso 1: Convertir bits a símbolos QAM
        qam_symbols = self.qam_modulator.bits_to_symbols(bits)
        
        # Asegurarse de que tenemos el número correcto de símbolos
        # Los símbolos restantes se rellenan con ceros
        symbols_parallel = np.zeros(self.config.N, dtype=complex)
        num_data_symbols = min(len(qam_symbols), self.config.Nc)
        symbols_parallel[:num_data_symbols] = qam_symbols[:num_data_symbols]
        
        # Paso 2: Aplicar IFFT (serie -> paralelo ya hecho)
        time_domain = np.fft.ifft(symbols_parallel) * np.sqrt(self.config.N)
        
        # Paso 3: Agregar prefijo cíclico
        ofdm_symbol_with_cp = np.concatenate([
            time_domain[-self.config.cp_length:],  # CP al inicio
            time_domain
        ])
        
        # Paso 4: Convertir a serie (ya está en serie)
        return ofdm_symbol_with_cp, qam_symbols[:num_data_symbols]
    
    def modulate_stream(self, bits, num_ofdm_symbols=None):
        """
        Modula un stream de bits a múltiples símbolos OFDM
        
        Args:
            bits: Array de bits
            num_ofdm_symbols: Número de símbolos OFDM a generar (opcional)
            
        Returns:
            tuple: (signal_concatenated, all_symbols)
        """
        bits_per_ofdm = self.config.Nc * self.config.bits_per_symbol
        
        # Calcular número de símbolos OFDM necesarios
        if num_ofdm_symbols is None:
            num_ofdm_symbols = int(np.ceil(len(bits) / bits_per_ofdm))
        
        # Rellenar bits si es necesario
        total_bits_needed = num_ofdm_symbols * bits_per_ofdm
        if len(bits) < total_bits_needed:
            bits = np.pad(bits, (0, total_bits_needed - len(bits)), 'constant')
        
        # Modular cada símbolo OFDM
        signal_stream = []
        all_symbols = []
        
        for i in range(num_ofdm_symbols):
            start_idx = i * bits_per_ofdm
            end_idx = start_idx + bits_per_ofdm
            bits_chunk = bits[start_idx:end_idx]
            
            ofdm_symbol, symbols = self.modulate(bits_chunk)
            signal_stream.append(ofdm_symbol)
            all_symbols.append(symbols)
        
        # Concatenar todos los símbolos OFDM
        signal_concatenated = np.concatenate(signal_stream)
        
        return signal_concatenated, all_symbols
    
    def get_qam_modulator(self):
        """Retorna el modulador QAM para acceso directo"""
        return self.qam_modulator
