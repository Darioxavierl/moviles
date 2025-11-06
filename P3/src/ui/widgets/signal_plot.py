"""
Widget de visualización de señales CDMA usando matplotlib.
Muestra señales individuales y señal total combinada.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox
from PyQt5.QtCore import Qt
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from typing import Optional, List
import matplotlib.patches as mpatches


class SignalPlotWidget(QWidget):
    """
    Widget para visualizar señales CDMA codificadas.
    Muestra señales individuales de cada usuario y la señal total.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Datos
        self.individual_signals: Optional[np.ndarray] = None
        self.total_signal: Optional[np.ndarray] = None
        self.user_labels: Optional[List[str]] = None
        self.code_length: Optional[int] = None
        
        # Configuración de visualización
        self.show_grid = True
        self.show_legend = True
        self.show_markers = False
        
        # Colores para usuarios (paleta distintiva)
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
        controls_layout = QHBoxLayout()
        
        # Título
        self.title_label = QLabel("<b>Señales CDMA Codificadas</b>")
        controls_layout.addWidget(self.title_label)
        
        controls_layout.addStretch()
        
        # Checkbox: Mostrar grid
        self.check_grid = QCheckBox("Grid")
        self.check_grid.setChecked(True)
        self.check_grid.stateChanged.connect(self._on_grid_changed)
        controls_layout.addWidget(self.check_grid)
        
        # Checkbox: Mostrar leyenda
        self.check_legend = QCheckBox("Leyenda")
        self.check_legend.setChecked(True)
        self.check_legend.stateChanged.connect(self._on_legend_changed)
        controls_layout.addWidget(self.check_legend)
        
        # Checkbox: Mostrar marcadores
        self.check_markers = QCheckBox("Marcadores")
        self.check_markers.setChecked(False)
        self.check_markers.stateChanged.connect(self._on_markers_changed)
        controls_layout.addWidget(self.check_markers)
        
        # Botón: Limpiar
        btn_clear = QPushButton("Limpiar")
        btn_clear.clicked.connect(self.clear_plot)
        controls_layout.addWidget(btn_clear)
        
        layout.addLayout(controls_layout)
        
        # Crear figura de matplotlib
        self.figure = Figure(figsize=(10, 8))
        self.canvas = FigureCanvas(self.figure)
        
        # Toolbar de navegación
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        
        # Mensaje inicial
        self._show_empty_message()
    
    def plot_signals(self, 
                    individual_signals: np.ndarray,
                    total_signal: np.ndarray,
                    user_labels: Optional[List[str]] = None,
                    code_length: Optional[int] = None,
                    original_messages: Optional[np.ndarray] = None):
        """
        Grafica las señales CDMA con forma cuadrada.
        
        Args:
            individual_signals: Matriz (n_users, signal_length) con señales individuales
            total_signal: Array (signal_length,) con la señal total
            user_labels: Lista de etiquetas para usuarios
            code_length: Longitud del código de esparcimiento (para marcas)
            original_messages: Matriz (n_users, n_bits) con mensajes originales
        """
        self.individual_signals = individual_signals
        self.total_signal = total_signal
        self.code_length = code_length
        
        n_users = individual_signals.shape[0]
        
        # Generar etiquetas si no se proporcionan
        if user_labels is None:
            self.user_labels = [f"Usuario {i+1}" for i in range(n_users)]
        else:
            self.user_labels = user_labels
        
        # Limpiar figura
        self.figure.clear()
        
        # Crear subplots: uno para señal total, n para señales individuales
        n_plots = n_users + 1
        axes = self.figure.subplots(n_plots, 1, sharex=True)
        
        # Si solo hay un usuario, axes no es lista
        if n_users == 1:
            axes = [axes]
        
        # Ajustar espaciado
        self.figure.subplots_adjust(hspace=0.3, left=0.08, right=0.95, top=0.95, bottom=0.05)
        
        # Vector de tiempo/chips (para step plot necesitamos puntos extra)
        signal_length = len(total_signal)
        
        # Plot 1: Señal total (arriba)
        ax_total = axes[0]
        self._plot_square_wave(ax_total, total_signal, 'k', 2, 'Señal Total')
        ax_total.set_ylabel('Amplitud', fontweight='bold')
        ax_total.set_title('Señal Total (Canal CDMA)', fontweight='bold', fontsize=11)
        ax_total.grid(self.show_grid, alpha=0.3)
        
        if self.show_legend:
            ax_total.legend(loc='upper right')
        
        # Marcar límites de bits si se conoce code_length
        if code_length is not None:
            self._add_bit_boundaries(ax_total, signal_length, code_length)
        
        # Añadir línea en y=0
        ax_total.axhline(y=0, color='gray', linestyle='--', linewidth=0.5, alpha=0.5)
        
        # Plots 2 a N+1: Señales individuales
        for i in range(n_users):
            ax = axes[i + 1]
            color = self.colors[i % len(self.colors)]
            
            # Plotear señal con forma cuadrada
            self._plot_square_wave(ax, individual_signals[i], color, 1.5, 
                                  self.user_labels[i], self.show_markers)
            
            ax.set_ylabel('Amplitud', fontsize=9)
            ax.set_title(self.user_labels[i], fontweight='bold', fontsize=10, color=color)
            ax.grid(self.show_grid, alpha=0.3)
            
            if self.show_legend:
                ax.legend(loc='upper right', fontsize=8)
            
            # Marcar límites de bits
            if code_length is not None:
                self._add_bit_boundaries(ax, signal_length, code_length)
                
                # Añadir texto con bits originales
                if original_messages is not None:
                    self._add_bit_labels(ax, original_messages[i], code_length, 
                                        signal_length, color)
            
            # Línea en y=0
            ax.axhline(y=0, color='gray', linestyle='--', linewidth=0.5, alpha=0.5)
        
        # Label del eje X solo en el último plot
        axes[-1].set_xlabel('Tiempo (chips)', fontweight='bold')
        
        # Ajustar límites del eje Y para mejor visualización
        self._adjust_y_limits(axes)
        
        # Redibujar
        self.canvas.draw()
    
    def _plot_square_wave(self, ax, signal: np.ndarray, color: str, 
                         linewidth: float, label: str, show_markers: bool = False):
        """
        Plotea una señal con forma cuadrada (step plot).
        
        Args:
            ax: Eje de matplotlib
            signal: Señal a plotear
            color: Color de la línea
            linewidth: Grosor de línea
            label: Etiqueta
            show_markers: Mostrar marcadores en transiciones
        """
        # Crear vector de tiempo extendido para step plot
        n = len(signal)
        time_extended = np.arange(n + 1)
        signal_extended = np.append(signal, signal[-1])
        
        # Usar drawstyle='steps-post' para forma cuadrada
        ax.step(time_extended, signal_extended, where='post',
               color=color, linewidth=linewidth, label=label)
        
        # Opcional: marcar las transiciones
        if show_markers:
            # Encontrar índices donde cambia el valor
            transitions = np.where(np.diff(signal) != 0)[0] + 1
            if len(transitions) > 0:
                ax.plot(transitions, signal[transitions], 'o', 
                       color=color, markersize=4, markerfacecolor='white',
                       markeredgewidth=1.5)
    
    def _add_bit_labels(self, ax, message: np.ndarray, code_length: int,
                       signal_length: int, color: str):
        """
        Añade etiquetas de texto mostrando los bits originales.
        
        Args:
            ax: Eje de matplotlib
            message: Mensaje binario original
            code_length: Longitud del código (chips por bit)
            signal_length: Longitud total de la señal
            color: Color del texto
        """
        n_bits = len(message)
        ylim = ax.get_ylim()
        y_pos = ylim[1] * 0.80  # Posición del texto (80% de altura)
        
        # Añadir un rectángulo semi-transparente de fondo para destacar la zona de bits
        for i, bit in enumerate(message):
            # Posición del bit (desde inicio hasta fin del bit)
            start_chip = i * code_length
            end_chip = (i + 1) * code_length
            center_chip = (start_chip + end_chip) / 2
            
            # Rectángulo de fondo para el período del bit
            ax.axvspan(start_chip, end_chip, 
                      alpha=0.05, color=color, zorder=-1)
            
            # Añadir texto con el bit centrado
            ax.text(center_chip, y_pos, f'Bit: {bit}',
                   horizontalalignment='center',
                   verticalalignment='center',
                   fontsize=9,
                   fontweight='bold',
                   color='white',
                   bbox=dict(boxstyle='round,pad=0.4', 
                           facecolor=color, 
                           edgecolor='white',
                           linewidth=1.5,
                           alpha=0.9))
            
            # Añadir línea vertical al INICIO de cada bit (más clara que las de boundaries)
            ax.axvline(x=start_chip, color=color, linestyle='-', 
                      linewidth=2, alpha=0.6, zorder=1)
    
    def _add_chip_axis(self, ax, signal_length: int, code_length: int):
        """
        Añade un eje secundario mostrando el tiempo en bits.
        
        Args:
            ax: Eje principal
            signal_length: Longitud de la señal en chips
            code_length: Chips por bit
        """
        # Crear eje secundario en la parte superior
        ax2 = ax.twiny()
        
        # Posiciones de los bits
        n_bits = signal_length // code_length
        bit_positions = np.arange(0, n_bits + 1) * code_length
        bit_labels = [str(i) for i in range(n_bits + 1)]
        
        ax2.set_xlim(ax.get_xlim())
        ax2.set_xticks(bit_positions)
        ax2.set_xticklabels(bit_labels)
        ax2.set_xlabel('Tiempo (bits)', fontsize=9, fontweight='bold', color='blue')
        ax2.tick_params(axis='x', colors='blue', labelsize=8)
        
        return ax2
    
    def _add_bit_boundaries(self, ax, signal_length: int, code_length: int):
        """
        Añade líneas verticales para marcar límites de bits.
        
        Args:
            ax: Eje de matplotlib
            signal_length: Longitud total de la señal
            code_length: Longitud del código (chips por bit)
        """
        n_bits = signal_length // code_length
        
        for i in range(1, n_bits):
            boundary = i * code_length
            ax.axvline(x=boundary, color='red', linestyle=':', linewidth=1, alpha=0.4)
    
    def _adjust_y_limits(self, axes):
        """
        Ajusta los límites del eje Y para mejor visualización.
        
        Args:
            axes: Lista de ejes de matplotlib
        """
        for ax in axes:
            ylim = ax.get_ylim()
            margin = (ylim[1] - ylim[0]) * 0.1
            ax.set_ylim(ylim[0] - margin, ylim[1] + margin)
    
    def _show_empty_message(self):
        """Muestra un mensaje cuando no hay datos."""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, 
                'Ejecute la codificación para visualizar las señales',
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
        self.code_length = None
        self._show_empty_message()
    
    def _on_grid_changed(self, state):
        """Callback cuando cambia el estado del grid."""
        self.show_grid = (state == Qt.Checked)
        if self.individual_signals is not None:
            # Re-plotear manteniendo los mensajes originales si existen
            self.plot_signals(
                self.individual_signals, 
                self.total_signal, 
                self.user_labels,
                self.code_length,
                getattr(self, 'original_messages', None)
            )
    
    def _on_legend_changed(self, state):
        """Callback cuando cambia el estado de la leyenda."""
        self.show_legend = (state == Qt.Checked)
        if self.individual_signals is not None:
            self.plot_signals(
                self.individual_signals, 
                self.total_signal, 
                self.user_labels,
                self.code_length,
                getattr(self, 'original_messages', None)
            )
    
    def _on_markers_changed(self, state):
        """Callback cuando cambia el estado de los marcadores."""
        self.show_markers = (state == Qt.Checked)
        if self.individual_signals is not None:
            self.plot_signals(
                self.individual_signals, 
                self.total_signal, 
                self.user_labels,
                self.code_length,
                getattr(self, 'original_messages', None)
            )
    
    def export_figure(self, filename: str, dpi: int = 300):
        """
        Exporta la figura a un archivo.
        
        Args:
            filename: Nombre del archivo (con extensión)
            dpi: Resolución en DPI
        """
        self.figure.savefig(filename, dpi=dpi, bbox_inches='tight')


class ComparisonSignalPlotWidget(QWidget):
    """
    Widget para comparar señales antes y después del procesamiento.
    Por ejemplo: señal limpia vs señal con ruido.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
        self._init_ui()
    
    def _init_ui(self):
        """Inicializa la interfaz del widget."""
        layout = QVBoxLayout(self)
        
        # Título
        title = QLabel("<b>Comparación de Señales</b>")
        layout.addWidget(title)
        
        # Figura
        self.figure = Figure(figsize=(10, 6))
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        
        self._show_empty_message()
    
    def plot_comparison(self,
                       signal1: np.ndarray,
                       signal2: np.ndarray,
                       label1: str = "Señal 1",
                       label2: str = "Señal 2",
                       title: str = "Comparación de Señales"):
        """
        Grafica comparación entre dos señales.
        
        Args:
            signal1: Primera señal
            signal2: Segunda señal
            label1: Etiqueta para señal 1
            label2: Etiqueta para señal 2
            title: Título del gráfico
        """
        self.figure.clear()
        
        # Crear 3 subplots: señal1, señal2, diferencia
        ax1 = self.figure.add_subplot(3, 1, 1)
        ax2 = self.figure.add_subplot(3, 1, 2)
        ax3 = self.figure.add_subplot(3, 1, 3)
        
        time = np.arange(len(signal1))
        
        # Señal 1
        ax1.plot(time, signal1, color=self.colors[0], linewidth=1.5, label=label1)
        ax1.set_ylabel('Amplitud')
        ax1.set_title(label1, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc='upper right')
        
        # Señal 2
        ax2.plot(time, signal2, color=self.colors[1], linewidth=1.5, label=label2)
        ax2.set_ylabel('Amplitud')
        ax2.set_title(label2, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.legend(loc='upper right')
        
        # Diferencia
        diff = signal2 - signal1
        ax3.plot(time, diff, color=self.colors[2], linewidth=1.5, label='Diferencia')
        ax3.set_ylabel('Amplitud')
        ax3.set_xlabel('Tiempo (chips)')
        ax3.set_title('Diferencia (Ruido)', fontweight='bold')
        ax3.grid(True, alpha=0.3)
        ax3.legend(loc='upper right')
        ax3.axhline(y=0, color='black', linestyle='--', linewidth=0.8)
        
        self.figure.suptitle(title, fontweight='bold', fontsize=12)
        self.figure.tight_layout()
        
        self.canvas.draw()
    
    def plot_overlay_comparison(self,
                               signal1: np.ndarray,
                               signal2: np.ndarray,
                               label1: str = "Señal Original",
                               label2: str = "Señal Procesada"):
        """
        Grafica dos señales superpuestas para comparación directa.
        
        Args:
            signal1: Primera señal
            signal2: Segunda señal
            label1: Etiqueta para señal 1
            label2: Etiqueta para señal 2
        """
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        time = np.arange(len(signal1))
        
        ax.plot(time, signal1, color=self.colors[0], linewidth=2, 
               alpha=0.7, label=label1)
        ax.plot(time, signal2, color=self.colors[1], linewidth=1.5, 
               linestyle='--', alpha=0.7, label=label2)
        
        ax.set_xlabel('Tiempo (chips)', fontweight='bold')
        ax.set_ylabel('Amplitud', fontweight='bold')
        ax.set_title('Comparación de Señales', fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best')
        ax.axhline(y=0, color='gray', linestyle=':', linewidth=0.5)
        
        self.figure.tight_layout()
        self.canvas.draw()
    
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
    widget = SignalPlotWidget()
    widget.setWindowTitle("CDMA Signal Plotter - Demo")
    widget.resize(1000, 800)
    
    # Generar datos de prueba
    n_users = 3
    n_bits = 4
    code_length = 4
    signal_length = n_bits * code_length
    
    # Códigos Walsh
    codes = np.array([
        [ 1,  1,  1,  1],
        [ 1, -1,  1, -1],
        [ 1,  1, -1, -1]
    ])
    
    # Mensajes
    messages = np.array([
        [1, 0, 1, 0],
        [0, 1, 1, 0],
        [1, 1, 0, 1]
    ])
    
    # Codificar (simple)
    def simple_encode(msg, code):
        msg_bipolar = 2 * msg - 1
        return np.repeat(msg_bipolar, len(code)) * np.tile(code, len(msg))
    
    signals = np.array([simple_encode(messages[i], codes[i]) for i in range(n_users)])
    total_signal = np.sum(signals, axis=0)
    
    # Graficar
    widget.plot_signals(
        signals, 
        total_signal,
        user_labels=[f"Usuario {i+1}" for i in range(n_users)],
        code_length=code_length,
        original_messages=messages  # ← Añadir mensajes originales
    )
    
    widget.show()
    
    sys.exit(app.exec_())