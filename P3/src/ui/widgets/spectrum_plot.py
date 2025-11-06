"""
Widget de visualización de espectros de frecuencia para señales CDMA.
Muestra análisis espectral (FFT) de señales individuales y total.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QCheckBox, QComboBox, QGroupBox
)
from PyQt5.QtCore import Qt
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from typing import Optional, List, Tuple
from scipy.fft import fft, fftfreq


class SpectrumPlotWidget(QWidget):
    """
    Widget para visualizar espectros de frecuencia de señales CDMA.
    Muestra el ensanchamiento espectral característico del CDMA.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Datos
        self.individual_signals: Optional[np.ndarray] = None
        self.total_signal: Optional[np.ndarray] = None
        self.user_labels: Optional[List[str]] = None
        self.sampling_rate: float = 1.0
        
        # Datos procesados (espectros)
        self.individual_spectra: Optional[List[Tuple[np.ndarray, np.ndarray]]] = None
        self.total_spectrum: Optional[Tuple[np.ndarray, np.ndarray]] = None
        
        # Configuración de visualización
        self.show_grid = True
        self.show_legend = True
        self.plot_mode = 'magnitude'  # 'magnitude', 'magnitude_db', 'power'
        self.frequency_range = 'positive'  # 'positive', 'full'
        
        # Colores
        self.colors = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728',
            '#9467bd', '#8c564b', '#e377c2', '#7f7f7f',
            '#bcbd22', '#17becf', '#aec7e8', '#ffbb78'
        ]
        
        self._init_ui()
    
    def _init_ui(self):
        """Inicializa la interfaz del widget."""
        layout = QVBoxLayout(self)
        
        # Controles superiores
        controls_layout = self._create_controls()
        layout.addLayout(controls_layout)
        
        # Figura de matplotlib
        self.figure = Figure(figsize=(10, 8))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        
        # Mensaje inicial
        self._show_empty_message()
    
    def _create_controls(self) -> QHBoxLayout:
        """Crea los controles superiores."""
        controls_layout = QHBoxLayout()
        
        # Título
        self.title_label = QLabel("<b>Análisis Espectral (FFT)</b>")
        controls_layout.addWidget(self.title_label)
        
        controls_layout.addStretch()
        
        # Modo de visualización
        controls_layout.addWidget(QLabel("Modo:"))
        self.combo_plot_mode = QComboBox()
        self.combo_plot_mode.addItems([
            "Magnitud",
            "Magnitud (dB)",
            "Potencia (PSD)"
        ])
        self.combo_plot_mode.currentIndexChanged.connect(self._on_mode_changed)
        controls_layout.addWidget(self.combo_plot_mode)
        
        # Rango de frecuencias
        controls_layout.addWidget(QLabel("Rango:"))
        self.combo_freq_range = QComboBox()
        self.combo_freq_range.addItems([
            "Frecuencias Positivas",
            "Espectro Completo"
        ])
        self.combo_freq_range.currentIndexChanged.connect(self._on_range_changed)
        controls_layout.addWidget(self.combo_freq_range)
        
        # Checkbox: Grid
        self.check_grid = QCheckBox("Grid")
        self.check_grid.setChecked(True)
        self.check_grid.stateChanged.connect(self._on_grid_changed)
        controls_layout.addWidget(self.check_grid)
        
        # Checkbox: Leyenda
        self.check_legend = QCheckBox("Leyenda")
        self.check_legend.setChecked(True)
        self.check_legend.stateChanged.connect(self._on_legend_changed)
        controls_layout.addWidget(self.check_legend)
        
        # Botón: Limpiar
        btn_clear = QPushButton("Limpiar")
        btn_clear.clicked.connect(self.clear_plot)
        controls_layout.addWidget(btn_clear)
        
        return controls_layout
    
    def plot_spectra(self,
                    individual_signals: np.ndarray,
                    total_signal: np.ndarray,
                    user_labels: Optional[List[str]] = None,
                    sampling_rate: float = 1.0):
        """
        Calcula y grafica los espectros de frecuencia.
        
        Args:
            individual_signals: Matriz (n_users, signal_length)
            total_signal: Array (signal_length,)
            user_labels: Lista de etiquetas
            sampling_rate: Tasa de muestreo (Hz o chips/segundo)
        """
        self.individual_signals = individual_signals
        self.total_signal = total_signal
        self.sampling_rate = sampling_rate
        
        n_users = individual_signals.shape[0]
        
        # Generar etiquetas
        if user_labels is None:
            self.user_labels = [f"Usuario {i+1}" for i in range(n_users)]
        else:
            self.user_labels = user_labels
        
        # Calcular espectros
        self._compute_spectra()
        
        # Graficar
        self._plot_all_spectra()
    
    def _compute_spectra(self):
        """Calcula los espectros de todas las señales."""
        n_users = self.individual_signals.shape[0]
        
        # Espectros individuales
        self.individual_spectra = []
        for i in range(n_users):
            freqs, mags = self._compute_spectrum(self.individual_signals[i])
            self.individual_spectra.append((freqs, mags))
        
        # Espectro total
        self.total_spectrum = self._compute_spectrum(self.total_signal)
    
    def _compute_spectrum(self, signal: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calcula el espectro de una señal.
        
        Args:
            signal: Señal en el tiempo
        
        Returns:
            Tuple[np.ndarray, np.ndarray]: Frecuencias y magnitudes
        """
        n = len(signal)
        
        # FFT
        spectrum = fft(signal)
        
        # Frecuencias
        frequencies = fftfreq(n, d=1/self.sampling_rate)
        
        if self.frequency_range == 'positive':
            # Solo frecuencias positivas
            positive_mask = frequencies >= 0
            frequencies = frequencies[positive_mask]
            spectrum = spectrum[positive_mask]
        
        # Calcular magnitud según el modo
        if self.plot_mode == 'magnitude':
            magnitudes = np.abs(spectrum)
        elif self.plot_mode == 'magnitude_db':
            magnitudes = 20 * np.log10(np.abs(spectrum) + 1e-10)
        elif self.plot_mode == 'power':
            # PSD (Power Spectral Density)
            magnitudes = (np.abs(spectrum) ** 2) / n
        else:
            magnitudes = np.abs(spectrum)
        
        return frequencies, magnitudes
    
    def _plot_all_spectra(self):
        """Grafica todos los espectros."""
        self.figure.clear()
        
        n_users = len(self.individual_spectra)
        n_plots = n_users + 1
        
        # Crear subplots
        axes = self.figure.subplots(n_plots, 1, sharex=True)
        
        if n_users == 1:
            axes = [axes]
        
        # Ajustar espaciado
        self.figure.subplots_adjust(hspace=0.3, left=0.08, right=0.95, top=0.95, bottom=0.05)
        
        # Plot 1: Espectro total (arriba)
        ax_total = axes[0]
        freqs_total, mags_total = self.total_spectrum
        
        ax_total.plot(freqs_total, mags_total, 'k-', linewidth=2, label='Espectro Total')
        ax_total.set_ylabel(self._get_ylabel(), fontweight='bold')
        ax_total.set_title('Espectro Total (Canal CDMA)', fontweight='bold', fontsize=11)
        ax_total.grid(self.show_grid, alpha=0.3)
        
        if self.show_legend:
            ax_total.legend(loc='upper right')
        
        # Línea en y=0 para dB
        if self.plot_mode == 'magnitude_db':
            ax_total.axhline(y=0, color='gray', linestyle='--', linewidth=0.5, alpha=0.5)
        
        # Plots individuales
        for i in range(n_users):
            ax = axes[i + 1]
            color = self.colors[i % len(self.colors)]
            
            freqs, mags = self.individual_spectra[i]
            
            ax.plot(freqs, mags, color=color, linewidth=1.5, label=self.user_labels[i])
            ax.set_ylabel(self._get_ylabel(), fontsize=9)
            ax.set_title(self.user_labels[i], fontweight='bold', fontsize=10, color=color)
            ax.grid(self.show_grid, alpha=0.3)
            
            if self.show_legend:
                ax.legend(loc='upper right', fontsize=8)
            
            if self.plot_mode == 'magnitude_db':
                ax.axhline(y=0, color='gray', linestyle='--', linewidth=0.5, alpha=0.5)
        
        # Label del eje X
        axes[-1].set_xlabel('Frecuencia (Hz)', fontweight='bold')
        
        # Ajustar límites Y
        self._adjust_y_limits(axes)
        
        self.canvas.draw()
    
    def _get_ylabel(self) -> str:
        """Retorna la etiqueta del eje Y según el modo."""
        if self.plot_mode == 'magnitude':
            return 'Magnitud'
        elif self.plot_mode == 'magnitude_db':
            return 'Magnitud (dB)'
        elif self.plot_mode == 'power':
            return 'PSD'
        return 'Magnitud'
    
    def _adjust_y_limits(self, axes):
        """Ajusta los límites del eje Y."""
        for ax in axes:
            ylim = ax.get_ylim()
            
            if self.plot_mode == 'magnitude_db':
                # Para dB, usar límites más razonables
                max_val = np.max([line.get_ydata().max() for line in ax.get_lines()])
                ax.set_ylim(-80, max_val + 10)
            else:
                # Añadir margen
                margin = (ylim[1] - ylim[0]) * 0.1
                ax.set_ylim(max(0, ylim[0] - margin), ylim[1] + margin)
    
    def _on_mode_changed(self, index):
        """Callback cuando cambia el modo de visualización."""
        modes = ['magnitude', 'magnitude_db', 'power']
        self.plot_mode = modes[index]
        
        if self.individual_signals is not None:
            self._compute_spectra()
            self._plot_all_spectra()
    
    def _on_range_changed(self, index):
        """Callback cuando cambia el rango de frecuencias."""
        ranges = ['positive', 'full']
        self.frequency_range = ranges[index]
        
        if self.individual_signals is not None:
            self._compute_spectra()
            self._plot_all_spectra()
    
    def _on_grid_changed(self, state):
        """Callback cuando cambia el estado del grid."""
        self.show_grid = (state == Qt.Checked)
        if self.individual_signals is not None:
            self._plot_all_spectra()
    
    def _on_legend_changed(self, state):
        """Callback cuando cambia el estado de la leyenda."""
        self.show_legend = (state == Qt.Checked)
        if self.individual_signals is not None:
            self._plot_all_spectra()
    
    def _show_empty_message(self):
        """Muestra un mensaje cuando no hay datos."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5,
                'Ejecute la codificación para visualizar los espectros',
                horizontalalignment='center',
                verticalalignment='center',
                transform=ax.transAxes,
                fontsize=12,
                color='gray')
        ax.axis('off')
        self.canvas.draw()
    
    def clear_plot(self):
        """Limpia el gráfico."""
        self.individual_signals = None
        self.total_signal = None
        self.user_labels = None
        self.individual_spectra = None
        self.total_spectrum = None
        self._show_empty_message()
    
    def export_figure(self, filename: str, dpi: int = 300):
        """
        Exporta la figura a un archivo.
        
        Args:
            filename: Nombre del archivo
            dpi: Resolución en DPI
        """
        self.figure.savefig(filename, dpi=dpi, bbox_inches='tight')


class ComparisonSpectrumWidget(QWidget):
    """
    Widget para comparar espectros (ej: antes vs después de esparcimiento).
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
        self.sampling_rate = 1.0
        
        self._init_ui()
    
    def _init_ui(self):
        """Inicializa la interfaz."""
        layout = QVBoxLayout(self)
        
        # Controles
        controls_layout = QHBoxLayout()
        
        title = QLabel("<b>Comparación Espectral</b>")
        controls_layout.addWidget(title)
        controls_layout.addStretch()
        
        # Modo de visualización
        controls_layout.addWidget(QLabel("Modo:"))
        self.combo_mode = QComboBox()
        self.combo_mode.addItems(["Magnitud", "Magnitud (dB)", "Potencia"])
        self.combo_mode.currentIndexChanged.connect(self._refresh_plot)
        controls_layout.addWidget(self.combo_mode)
        
        layout.addLayout(controls_layout)
        
        # Figura
        self.figure = Figure(figsize=(10, 6))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        
        # Datos
        self.signal1 = None
        self.signal2 = None
        self.label1 = None
        self.label2 = None
        
        self._show_empty_message()
    
    def plot_comparison(self,
                       signal1: np.ndarray,
                       signal2: np.ndarray,
                       label1: str = "Señal Original",
                       label2: str = "Señal Esparcida",
                       sampling_rate: float = 1.0):
        """
        Compara dos espectros.
        
        Args:
            signal1: Primera señal
            signal2: Segunda señal
            label1: Etiqueta señal 1
            label2: Etiqueta señal 2
            sampling_rate: Tasa de muestreo
        """
        self.signal1 = signal1
        self.signal2 = signal2
        self.label1 = label1
        self.label2 = label2
        self.sampling_rate = sampling_rate
        
        self._refresh_plot()
    
    def _refresh_plot(self):
        """Actualiza el gráfico."""
        if self.signal1 is None or self.signal2 is None:
            return
        
        self.figure.clear()
        
        # Crear subplot
        ax = self.figure.add_subplot(111)
        
        # Modo de visualización
        mode_idx = self.combo_mode.currentIndex()
        
        # Calcular espectros
        freqs1, mags1 = self._compute_spectrum(self.signal1, mode_idx)
        freqs2, mags2 = self._compute_spectrum(self.signal2, mode_idx)
        
        # Graficar
        ax.plot(freqs1, mags1, color=self.colors[0], linewidth=2, 
               alpha=0.7, label=self.label1)
        ax.plot(freqs2, mags2, color=self.colors[1], linewidth=2, 
               linestyle='--', alpha=0.7, label=self.label2)
        
        # Etiquetas
        ax.set_xlabel('Frecuencia (Hz)', fontweight='bold')
        
        if mode_idx == 0:
            ax.set_ylabel('Magnitud', fontweight='bold')
        elif mode_idx == 1:
            ax.set_ylabel('Magnitud (dB)', fontweight='bold')
        else:
            ax.set_ylabel('PSD', fontweight='bold')
        
        ax.set_title('Comparación de Espectros', fontweight='bold', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best', fontsize=10)
        
        if mode_idx == 1:
            ax.axhline(y=0, color='gray', linestyle=':', linewidth=0.5)
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def _compute_spectrum(self, signal: np.ndarray, mode: int) -> Tuple[np.ndarray, np.ndarray]:
        """Calcula el espectro según el modo."""
        n = len(signal)
        spectrum = fft(signal)
        frequencies = fftfreq(n, d=1/self.sampling_rate)
        
        # Solo frecuencias positivas
        positive_mask = frequencies >= 0
        frequencies = frequencies[positive_mask]
        spectrum = spectrum[positive_mask]
        
        if mode == 0:  # Magnitud
            magnitudes = np.abs(spectrum)
        elif mode == 1:  # Magnitud dB
            magnitudes = 20 * np.log10(np.abs(spectrum) + 1e-10)
        else:  # Potencia
            magnitudes = (np.abs(spectrum) ** 2) / n
        
        return frequencies, magnitudes
    
    def _show_empty_message(self):
        """Muestra un mensaje cuando no hay datos."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5,
                'No hay datos para comparar',
                horizontalalignment='center',
                verticalalignment='center',
                transform=ax.transAxes,
                fontsize=12,
                color='gray')
        ax.axis('off')
        self.canvas.draw()


# Ejemplo de uso
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # Crear widget
    widget = SpectrumPlotWidget()
    widget.setWindowTitle("CDMA Spectrum Analyzer - Demo")
    widget.resize(1000, 800)
    
    # Generar datos de prueba
    n_users = 3
    n_bits = 8
    code_length = 4
    signal_length = n_bits * code_length
    sampling_rate = 100  # 100 Hz
    
    # Códigos Walsh
    codes = np.array([
        [ 1,  1,  1,  1],
        [ 1, -1,  1, -1],
        [ 1,  1, -1, -1]
    ])
    
    # Mensajes
    messages = np.array([
        [1, 0, 1, 0, 1, 0, 1, 0],
        [0, 1, 1, 0, 0, 1, 1, 0],
        [1, 1, 0, 1, 1, 0, 0, 1]
    ])
    
    # Codificar
    def simple_encode(msg, code):
        msg_bipolar = 2 * msg - 1
        return np.repeat(msg_bipolar, len(code)) * np.tile(code, len(msg))
    
    signals = np.array([simple_encode(messages[i], codes[i]) for i in range(n_users)])
    total_signal = np.sum(signals, axis=0)
    
    # Graficar espectros
    widget.plot_spectra(
        signals,
        total_signal,
        user_labels=[f"Usuario {i+1}" for i in range(n_users)],
        sampling_rate=sampling_rate
    )
    
    widget.show()
    
    sys.exit(app.exec_())