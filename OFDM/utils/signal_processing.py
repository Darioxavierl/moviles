"""
Utilidades para procesamiento y visualización de señales
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure


class SignalAnalyzer:
    """Herramientas para análisis de señales OFDM"""
    
    @staticmethod
    def plot_constellation(symbols, title="Constelación", ax=None):
        """
        Grafica la constelación de símbolos
        
        Args:
            symbols: Array de símbolos complejos
            title: Título del gráfico
            ax: Axes de matplotlib (opcional)
            
        Returns:
            Figure de matplotlib
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(8, 8))
        else:
            fig = ax.figure
        
        ax.scatter(symbols.real, symbols.imag, alpha=0.5, s=20)
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='k', linewidth=0.5)
        ax.axvline(x=0, color='k', linewidth=0.5)
        ax.set_xlabel('In-Phase (I)')
        ax.set_ylabel('Quadrature (Q)')
        ax.set_title(title)
        ax.set_aspect('equal')
        
        return fig
    
    @staticmethod
    def plot_spectrum(signal, fs, title="Espectro de Frecuencia", ax=None):
        """
        Grafica el espectro de frecuencia de una señal
        
        Args:
            signal: Señal en el tiempo
            fs: Frecuencia de muestreo
            title: Título del gráfico
            ax: Axes de matplotlib (opcional)
            
        Returns:
            Figure de matplotlib
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 6))
        else:
            fig = ax.figure
        
        # FFT
        N = len(signal)
        fft_signal = np.fft.fft(signal)
        fft_freq = np.fft.fftfreq(N, 1/fs)
        
        # Magnitud en dB
        magnitude_db = 20 * np.log10(np.abs(fft_signal) + 1e-10)
        
        # Graficar solo frecuencias positivas
        positive_freq_idx = fft_freq >= 0
        
        ax.plot(fft_freq[positive_freq_idx] / 1e6, 
               magnitude_db[positive_freq_idx])
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('Frecuencia (MHz)')
        ax.set_ylabel('Magnitud (dB)')
        ax.set_title(title)
        
        return fig
    
    @staticmethod
    def plot_time_signal(signal, fs, max_samples=1000, title="Señal en el Tiempo", ax=None):
        """
        Grafica la señal en el dominio del tiempo
        
        Args:
            signal: Señal compleja
            fs: Frecuencia de muestreo
            max_samples: Número máximo de muestras a graficar
            title: Título del gráfico
            ax: Axes de matplotlib (opcional)
            
        Returns:
            Figure de matplotlib
        """
        if ax is None:
            fig, ax = plt.subplots(2, 1, figsize=(12, 8))
        else:
            fig = ax[0].figure
        
        # Limitar número de muestras
        signal = signal[:max_samples]
        time = np.arange(len(signal)) / fs * 1e6  # En microsegundos
        
        # Parte real
        ax[0].plot(time, signal.real, linewidth=0.5)
        ax[0].grid(True, alpha=0.3)
        ax[0].set_xlabel('Tiempo (μs)')
        ax[0].set_ylabel('Amplitud (I)')
        ax[0].set_title(f'{title} - Componente I')
        
        # Parte imaginaria
        ax[1].plot(time, signal.imag, linewidth=0.5, color='orange')
        ax[1].grid(True, alpha=0.3)
        ax[1].set_xlabel('Tiempo (μs)')
        ax[1].set_ylabel('Amplitud (Q)')
        ax[1].set_title(f'{title} - Componente Q')
        
        plt.tight_layout()
        
        return fig
    
    @staticmethod
    def plot_ber_curve(snr_db, ber_mean, ber_std=None, theoretical_ber=None, 
                       title="BER vs SNR", ax=None):
        """
        Grafica curva BER vs SNR
        
        Args:
            snr_db: Array de valores SNR
            ber_mean: BER promedio
            ber_std: Desviación estándar del BER (opcional)
            theoretical_ber: BER teórico (opcional)
            title: Título del gráfico
            ax: Axes de matplotlib (opcional)
            
        Returns:
            Figure de matplotlib
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 7))
        else:
            fig = ax.figure
        
        # BER simulado
        ax.semilogy(snr_db, ber_mean, 'o-', label='BER Simulado', linewidth=2)
        
        # Barras de error si hay desviación estándar
        if ber_std is not None:
            confidence = 1.96 * np.array(ber_std) / np.sqrt(10)  # 95% CI
            ax.fill_between(snr_db, 
                           np.maximum(np.array(ber_mean) - confidence, 1e-6),
                           np.array(ber_mean) + confidence,
                           alpha=0.3, label='Intervalo de confianza 95%')
        
        # BER teórico si está disponible
        if theoretical_ber is not None:
            theoretical_ber = np.array(theoretical_ber)
            valid_idx = ~np.isnan(theoretical_ber)
            if np.any(valid_idx):
                ax.semilogy(np.array(snr_db)[valid_idx], 
                           theoretical_ber[valid_idx], 
                           's--', label='BER Teórico', linewidth=2, markersize=8)
        
        ax.grid(True, alpha=0.3, which='both')
        ax.set_xlabel('SNR (dB)', fontsize=12)
        ax.set_ylabel('BER', fontsize=12)
        ax.set_title(title, fontsize=14)
        ax.legend(fontsize=10)
        
        return fig
    
    @staticmethod
    def plot_ofdm_symbol_structure(ofdm_signal, cp_length, fft_size, 
                                   n_symbols=2, ax=None):
        """
        Visualiza la estructura de símbolos OFDM con CP
        
        Args:
            ofdm_signal: Señal OFDM
            cp_length: Longitud del prefijo cíclico
            fft_size: Tamaño de la FFT
            n_symbols: Número de símbolos a visualizar
            ax: Axes de matplotlib (opcional)
            
        Returns:
            Figure de matplotlib
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(14, 6))
        else:
            fig = ax.figure
        
        symbol_length = fft_size + cp_length
        samples_to_plot = min(n_symbols * symbol_length, len(ofdm_signal))
        
        time_axis = np.arange(samples_to_plot)
        
        # Graficar magnitud
        ax.plot(time_axis, np.abs(ofdm_signal[:samples_to_plot]), linewidth=0.5)
        
        # Marcar límites de símbolos OFDM y CP
        for i in range(n_symbols):
            start = i * symbol_length
            cp_end = start + cp_length
            
            # Región del CP
            ax.axvspan(start, cp_end, alpha=0.2, color='red', label='CP' if i == 0 else '')
            # Región del símbolo útil
            ax.axvspan(cp_end, start + symbol_length, alpha=0.1, color='blue', 
                      label='Símbolo útil' if i == 0 else '')
        
        ax.grid(True, alpha=0.3)
        ax.set_xlabel('Muestra')
        ax.set_ylabel('Magnitud')
        ax.set_title('Estructura de Símbolos OFDM')
        ax.legend()
        
        return fig


class PlotGenerator:
    """Generador de gráficos para la interfaz"""
    
    @staticmethod
    def create_figure_from_array(plot_func, *args, **kwargs):
        """
        Crea una figura matplotlib que puede ser usada en PyQt
        
        Args:
            plot_func: Función de plotting
            *args, **kwargs: Argumentos para la función
            
        Returns:
            matplotlib Figure
        """
        fig = Figure(figsize=(10, 6), dpi=100)
        ax = fig.add_subplot(111)
        
        plot_func(*args, ax=ax, **kwargs)
        
        return fig