#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# SPDX-License-Identifier: GPL-3.0
#
# GNU Radio Python Flow Graph
# Title: Modulacion GMSK vs MSK
# GNU Radio version: 3.10.9.2

from PyQt5 import Qt
from gnuradio import qtgui
from PyQt5 import QtCore
from gnuradio import blocks
import numpy
from gnuradio import channels
from gnuradio.filter import firdes
from gnuradio import digital
from gnuradio import gr
from gnuradio.fft import window
import sys
import signal
from PyQt5 import Qt
from argparse import ArgumentParser
from gnuradio.eng_arg import eng_float, intx
from gnuradio import eng_notation
from gnuradio import gr, digital, analog
import sip



class msk(gr.top_block, Qt.QWidget):

    def __init__(self):
        gr.top_block.__init__(self, "Modulacion GMSK vs MSK", catch_exceptions=True)
        Qt.QWidget.__init__(self)
        self.setWindowTitle("Modulacion GMSK vs MSK")
        qtgui.util.check_set_qss()
        try:
            self.setWindowIcon(Qt.QIcon.fromTheme('gnuradio-grc'))
        except BaseException as exc:
            print(f"Qt GUI: Could not set Icon: {str(exc)}", file=sys.stderr)
        self.top_scroll_layout = Qt.QVBoxLayout()
        self.setLayout(self.top_scroll_layout)
        self.top_scroll = Qt.QScrollArea()
        self.top_scroll.setFrameStyle(Qt.QFrame.NoFrame)
        self.top_scroll_layout.addWidget(self.top_scroll)
        self.top_scroll.setWidgetResizable(True)
        self.top_widget = Qt.QWidget()
        self.top_scroll.setWidget(self.top_widget)
        self.top_layout = Qt.QVBoxLayout(self.top_widget)
        self.top_grid_layout = Qt.QGridLayout()
        self.top_layout.addLayout(self.top_grid_layout)

        self.settings = Qt.QSettings("GNU Radio", "msk")

        try:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
        except BaseException as exc:
            print(f"Qt GUI: Could not restore geometry: {str(exc)}", file=sys.stderr)

        ##################################################
        # Variables
        ##################################################
        self.samp_rate = samp_rate = 32000
        self.Noise_Amplitude = Noise_Amplitude = 0.1

        ##################################################
        # Blocks
        ##################################################

        self.qtgui_tab_widget_0_1 = Qt.QTabWidget()
        self.qtgui_tab_widget_0_1_widget_0 = Qt.QWidget()
        self.qtgui_tab_widget_0_1_layout_0 = Qt.QBoxLayout(Qt.QBoxLayout.TopToBottom, self.qtgui_tab_widget_0_1_widget_0)
        self.qtgui_tab_widget_0_1_grid_layout_0 = Qt.QGridLayout()
        self.qtgui_tab_widget_0_1_layout_0.addLayout(self.qtgui_tab_widget_0_1_grid_layout_0)
        self.qtgui_tab_widget_0_1.addTab(self.qtgui_tab_widget_0_1_widget_0, 'Eye Sink')
        self.top_layout.addWidget(self.qtgui_tab_widget_0_1)
        self.qtgui_tab_widget_0_0 = Qt.QTabWidget()
        self.qtgui_tab_widget_0_0_widget_0 = Qt.QWidget()
        self.qtgui_tab_widget_0_0_layout_0 = Qt.QBoxLayout(Qt.QBoxLayout.TopToBottom, self.qtgui_tab_widget_0_0_widget_0)
        self.qtgui_tab_widget_0_0_grid_layout_0 = Qt.QGridLayout()
        self.qtgui_tab_widget_0_0_layout_0.addLayout(self.qtgui_tab_widget_0_0_grid_layout_0)
        self.qtgui_tab_widget_0_0.addTab(self.qtgui_tab_widget_0_0_widget_0, 'Eye Sink')
        self.top_layout.addWidget(self.qtgui_tab_widget_0_0)
        self.qtgui_tab_widget_0 = Qt.QTabWidget()
        self.qtgui_tab_widget_0_widget_0 = Qt.QWidget()
        self.qtgui_tab_widget_0_layout_0 = Qt.QBoxLayout(Qt.QBoxLayout.TopToBottom, self.qtgui_tab_widget_0_widget_0)
        self.qtgui_tab_widget_0_grid_layout_0 = Qt.QGridLayout()
        self.qtgui_tab_widget_0_layout_0.addLayout(self.qtgui_tab_widget_0_grid_layout_0)
        self.qtgui_tab_widget_0.addTab(self.qtgui_tab_widget_0_widget_0, 'Frecuencia')
        self.top_layout.addWidget(self.qtgui_tab_widget_0)
        self._Noise_Amplitude_range = qtgui.Range(0, 1, 0.01, 0.1, 10)
        self._Noise_Amplitude_win = qtgui.RangeWidget(self._Noise_Amplitude_range, self.set_Noise_Amplitude, "Amplitud del ruido", "counter_slider", float, QtCore.Qt.Horizontal)
        self.top_layout.addWidget(self._Noise_Amplitude_win)
        self.qtgui_freq_sink_x_0_0 = qtgui.freq_sink_c(
            8192, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            0, #fc
            samp_rate, #bw
            'Respuesta en frecuencia', #name
            1,
            None # parent
        )
        self.qtgui_freq_sink_x_0_0.set_update_time(0.10)
        self.qtgui_freq_sink_x_0_0.set_y_axis((-100), 10)
        self.qtgui_freq_sink_x_0_0.set_y_label('Relative Gain', 'dB')
        self.qtgui_freq_sink_x_0_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.qtgui_freq_sink_x_0_0.enable_autoscale(False)
        self.qtgui_freq_sink_x_0_0.enable_grid(True)
        self.qtgui_freq_sink_x_0_0.set_fft_average(1.0)
        self.qtgui_freq_sink_x_0_0.enable_axis_labels(True)
        self.qtgui_freq_sink_x_0_0.enable_control_panel(False)
        self.qtgui_freq_sink_x_0_0.set_fft_window_normalized(False)



        labels = ['MSK', 'MSK', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["red", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_freq_sink_x_0_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_freq_sink_x_0_0.set_line_label(i, labels[i])
            self.qtgui_freq_sink_x_0_0.set_line_width(i, widths[i])
            self.qtgui_freq_sink_x_0_0.set_line_color(i, colors[i])
            self.qtgui_freq_sink_x_0_0.set_line_alpha(i, alphas[i])

        self._qtgui_freq_sink_x_0_0_win = sip.wrapinstance(self.qtgui_freq_sink_x_0_0.qwidget(), Qt.QWidget)
        self.qtgui_tab_widget_0_layout_0.addWidget(self._qtgui_freq_sink_x_0_0_win)
        self.qtgui_freq_sink_x_0 = qtgui.freq_sink_c(
            8192, #size
            window.WIN_BLACKMAN_hARRIS, #wintype
            0, #fc
            samp_rate, #bw
            'Respuesta en frecuencia', #name
            1,
            None # parent
        )
        self.qtgui_freq_sink_x_0.set_update_time(0.10)
        self.qtgui_freq_sink_x_0.set_y_axis((-100), 10)
        self.qtgui_freq_sink_x_0.set_y_label('Relative Gain', 'dB')
        self.qtgui_freq_sink_x_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, 0.0, 0, "")
        self.qtgui_freq_sink_x_0.enable_autoscale(False)
        self.qtgui_freq_sink_x_0.enable_grid(True)
        self.qtgui_freq_sink_x_0.set_fft_average(1.0)
        self.qtgui_freq_sink_x_0.enable_axis_labels(True)
        self.qtgui_freq_sink_x_0.enable_control_panel(False)
        self.qtgui_freq_sink_x_0.set_fft_window_normalized(False)



        labels = ['GMSK', 'MSK', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_freq_sink_x_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_freq_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_freq_sink_x_0.set_line_width(i, widths[i])
            self.qtgui_freq_sink_x_0.set_line_color(i, colors[i])
            self.qtgui_freq_sink_x_0.set_line_alpha(i, alphas[i])

        self._qtgui_freq_sink_x_0_win = sip.wrapinstance(self.qtgui_freq_sink_x_0.qwidget(), Qt.QWidget)
        self.qtgui_tab_widget_0_layout_0.addWidget(self._qtgui_freq_sink_x_0_win)
        self.qtgui_eye_sink_x_0_0 = qtgui.eye_sink_f(
            1024, #size
            samp_rate, #samp_rate
            1, #number of inputs
            None
        )
        self.qtgui_eye_sink_x_0_0.set_update_time(0.10)
        self.qtgui_eye_sink_x_0_0.set_samp_per_symbol(8)
        self.qtgui_eye_sink_x_0_0.set_y_axis(-2.5, 2.5)

        self.qtgui_eye_sink_x_0_0.set_y_label('Amplitude', 'Eye sink MSK')

        self.qtgui_eye_sink_x_0_0.enable_tags(True)
        self.qtgui_eye_sink_x_0_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self.qtgui_eye_sink_x_0_0.enable_autoscale(False)
        self.qtgui_eye_sink_x_0_0.enable_grid(True)
        self.qtgui_eye_sink_x_0_0.enable_axis_labels(True)
        self.qtgui_eye_sink_x_0_0.enable_control_panel(False)


        labels = ['MSK', 'Parte Real', 'Signal 3', 'Signal 4', 'Signal 5',
            'Signal 6', 'Signal 7', 'Signal 8', 'Signal 9', 'Signal 10']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ['red', 'blue', 'blue', 'blue', 'blue',
            'blue', 'blue', 'blue', 'blue', 'blue']
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]
        styles = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1]


        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_eye_sink_x_0_0.set_line_label(i, "Eye[Data {0}]".format(i))
            else:
                self.qtgui_eye_sink_x_0_0.set_line_label(i, labels[i])
            self.qtgui_eye_sink_x_0_0.set_line_width(i, widths[i])
            self.qtgui_eye_sink_x_0_0.set_line_color(i, colors[i])
            self.qtgui_eye_sink_x_0_0.set_line_style(i, styles[i])
            self.qtgui_eye_sink_x_0_0.set_line_marker(i, markers[i])
            self.qtgui_eye_sink_x_0_0.set_line_alpha(i, alphas[i])

        self._qtgui_eye_sink_x_0_0_win = sip.wrapinstance(self.qtgui_eye_sink_x_0_0.qwidget(), Qt.QWidget)
        self.qtgui_tab_widget_0_0_layout_0.addWidget(self._qtgui_eye_sink_x_0_0_win)
        self.qtgui_eye_sink_x_0_0.set_block_alias("MSK - ISI")
        self.qtgui_eye_sink_x_0 = qtgui.eye_sink_f(
            1024, #size
            samp_rate, #samp_rate
            1, #number of inputs
            None
        )
        self.qtgui_eye_sink_x_0.set_update_time(0.10)
        self.qtgui_eye_sink_x_0.set_samp_per_symbol(8)
        self.qtgui_eye_sink_x_0.set_y_axis(-2.5, 2.5)

        self.qtgui_eye_sink_x_0.set_y_label('Amplitude', 'Eye sink GMSK')

        self.qtgui_eye_sink_x_0.enable_tags(True)
        self.qtgui_eye_sink_x_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, 0, "")
        self.qtgui_eye_sink_x_0.enable_autoscale(False)
        self.qtgui_eye_sink_x_0.enable_grid(True)
        self.qtgui_eye_sink_x_0.enable_axis_labels(True)
        self.qtgui_eye_sink_x_0.enable_control_panel(False)


        labels = ['GMSK', 'Parte Real', 'Signal 3', 'Signal 4', 'Signal 5',
            'Signal 6', 'Signal 7', 'Signal 8', 'Signal 9', 'Signal 10']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ['blue', 'blue', 'blue', 'blue', 'blue',
            'blue', 'blue', 'blue', 'blue', 'blue']
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]
        styles = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        markers = [-1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1]


        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_eye_sink_x_0.set_line_label(i, "Eye[Data {0}]".format(i))
            else:
                self.qtgui_eye_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_eye_sink_x_0.set_line_width(i, widths[i])
            self.qtgui_eye_sink_x_0.set_line_color(i, colors[i])
            self.qtgui_eye_sink_x_0.set_line_style(i, styles[i])
            self.qtgui_eye_sink_x_0.set_line_marker(i, markers[i])
            self.qtgui_eye_sink_x_0.set_line_alpha(i, alphas[i])

        self._qtgui_eye_sink_x_0_win = sip.wrapinstance(self.qtgui_eye_sink_x_0.qwidget(), Qt.QWidget)
        self.qtgui_tab_widget_0_0_layout_0.addWidget(self._qtgui_eye_sink_x_0_win)
        self.qtgui_eye_sink_x_0.set_block_alias("GMSK - ISI")
        self.qtgui_const_sink_x_1 = qtgui.const_sink_c(
            1024, #size
            'MSK - Constellation', #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_const_sink_x_1.set_update_time(0.10)
        self.qtgui_const_sink_x_1.set_y_axis((-2), 2)
        self.qtgui_const_sink_x_1.set_x_axis((-2), 2)
        self.qtgui_const_sink_x_1.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, "")
        self.qtgui_const_sink_x_1.enable_autoscale(False)
        self.qtgui_const_sink_x_1.enable_grid(False)
        self.qtgui_const_sink_x_1.enable_axis_labels(True)


        labels = ['MSK', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        styles = [0, 0, 0, 0, 0,
            0, 0, 0, 0, 0]
        markers = [0, 0, 0, 0, 0,
            0, 0, 0, 0, 0]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_const_sink_x_1.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_const_sink_x_1.set_line_label(i, labels[i])
            self.qtgui_const_sink_x_1.set_line_width(i, widths[i])
            self.qtgui_const_sink_x_1.set_line_color(i, colors[i])
            self.qtgui_const_sink_x_1.set_line_style(i, styles[i])
            self.qtgui_const_sink_x_1.set_line_marker(i, markers[i])
            self.qtgui_const_sink_x_1.set_line_alpha(i, alphas[i])

        self._qtgui_const_sink_x_1_win = sip.wrapinstance(self.qtgui_const_sink_x_1.qwidget(), Qt.QWidget)
        self.qtgui_tab_widget_0_1_layout_0.addWidget(self._qtgui_const_sink_x_1_win)
        self.qtgui_const_sink_x_0 = qtgui.const_sink_c(
            1024, #size
            'GMSK-Constellation', #name
            1, #number of inputs
            None # parent
        )
        self.qtgui_const_sink_x_0.set_update_time(0.10)
        self.qtgui_const_sink_x_0.set_y_axis((-2), 2)
        self.qtgui_const_sink_x_0.set_x_axis((-2), 2)
        self.qtgui_const_sink_x_0.set_trigger_mode(qtgui.TRIG_MODE_FREE, qtgui.TRIG_SLOPE_POS, 0.0, 0, "")
        self.qtgui_const_sink_x_0.enable_autoscale(False)
        self.qtgui_const_sink_x_0.enable_grid(False)
        self.qtgui_const_sink_x_0.enable_axis_labels(True)


        labels = ['GMSK', '', '', '', '',
            '', '', '', '', '']
        widths = [1, 1, 1, 1, 1,
            1, 1, 1, 1, 1]
        colors = ["blue", "red", "green", "black", "cyan",
            "magenta", "yellow", "dark red", "dark green", "dark blue"]
        styles = [0, 0, 0, 0, 0,
            0, 0, 0, 0, 0]
        markers = [0, 0, 0, 0, 0,
            0, 0, 0, 0, 0]
        alphas = [1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0]

        for i in range(1):
            if len(labels[i]) == 0:
                self.qtgui_const_sink_x_0.set_line_label(i, "Data {0}".format(i))
            else:
                self.qtgui_const_sink_x_0.set_line_label(i, labels[i])
            self.qtgui_const_sink_x_0.set_line_width(i, widths[i])
            self.qtgui_const_sink_x_0.set_line_color(i, colors[i])
            self.qtgui_const_sink_x_0.set_line_style(i, styles[i])
            self.qtgui_const_sink_x_0.set_line_marker(i, markers[i])
            self.qtgui_const_sink_x_0.set_line_alpha(i, alphas[i])

        self._qtgui_const_sink_x_0_win = sip.wrapinstance(self.qtgui_const_sink_x_0.qwidget(), Qt.QWidget)
        self.qtgui_tab_widget_0_1_layout_0.addWidget(self._qtgui_const_sink_x_0_win)
        self.digital_map_bb_0 = digital.map_bb([-1,1])
        self.digital_cpmmod_bc_0_0 = digital.cpmmod_bc(analog.cpm.GAUSSIAN, 0.5, 8, 4, 0.3)
        self.digital_cpmmod_bc_0 = digital.cpmmod_bc(analog.cpm.LREC, 0.5, 8, 1, 10000)
        self.channels_channel_model_0_0 = channels.channel_model(
            noise_voltage=Noise_Amplitude,
            frequency_offset=0.0,
            epsilon=1.0,
            taps=[1.0],
            noise_seed=0,
            block_tags=False)
        self.channels_channel_model_0_0.set_block_alias("AWGN Channel 2")
        self.channels_channel_model_0 = channels.channel_model(
            noise_voltage=Noise_Amplitude,
            frequency_offset=0.0,
            epsilon=1.0,
            taps=[1.0],
            noise_seed=0,
            block_tags=False)
        self.channels_channel_model_0.set_block_alias("AWGN Channel 1")
        self.blocks_complex_to_real_0_0 = blocks.complex_to_real(1)
        self.blocks_complex_to_real_0 = blocks.complex_to_real(1)
        self.analog_random_source_x_0 = blocks.vector_source_b(list(map(int, numpy.random.randint(0, 2, 1000))), True)


        ##################################################
        # Connections
        ##################################################
        self.connect((self.analog_random_source_x_0, 0), (self.digital_map_bb_0, 0))
        self.connect((self.blocks_complex_to_real_0, 0), (self.qtgui_eye_sink_x_0, 0))
        self.connect((self.blocks_complex_to_real_0_0, 0), (self.qtgui_eye_sink_x_0_0, 0))
        self.connect((self.channels_channel_model_0, 0), (self.blocks_complex_to_real_0, 0))
        self.connect((self.channels_channel_model_0, 0), (self.qtgui_const_sink_x_0, 0))
        self.connect((self.channels_channel_model_0, 0), (self.qtgui_freq_sink_x_0, 0))
        self.connect((self.channels_channel_model_0_0, 0), (self.blocks_complex_to_real_0_0, 0))
        self.connect((self.channels_channel_model_0_0, 0), (self.qtgui_const_sink_x_1, 0))
        self.connect((self.channels_channel_model_0_0, 0), (self.qtgui_freq_sink_x_0_0, 0))
        self.connect((self.digital_cpmmod_bc_0, 0), (self.channels_channel_model_0_0, 0))
        self.connect((self.digital_cpmmod_bc_0_0, 0), (self.channels_channel_model_0, 0))
        self.connect((self.digital_map_bb_0, 0), (self.digital_cpmmod_bc_0, 0))
        self.connect((self.digital_map_bb_0, 0), (self.digital_cpmmod_bc_0_0, 0))


    def closeEvent(self, event):
        self.settings = Qt.QSettings("GNU Radio", "msk")
        self.settings.setValue("geometry", self.saveGeometry())
        self.stop()
        self.wait()

        event.accept()

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.qtgui_eye_sink_x_0.set_samp_rate(self.samp_rate)
        self.qtgui_eye_sink_x_0_0.set_samp_rate(self.samp_rate)
        self.qtgui_freq_sink_x_0.set_frequency_range(0, self.samp_rate)
        self.qtgui_freq_sink_x_0_0.set_frequency_range(0, self.samp_rate)

    def get_Noise_Amplitude(self):
        return self.Noise_Amplitude

    def set_Noise_Amplitude(self, Noise_Amplitude):
        self.Noise_Amplitude = Noise_Amplitude
        self.channels_channel_model_0.set_noise_voltage(self.Noise_Amplitude)
        self.channels_channel_model_0_0.set_noise_voltage(self.Noise_Amplitude)




def main(top_block_cls=msk, options=None):

    qapp = Qt.QApplication(sys.argv)

    tb = top_block_cls()

    tb.start()

    tb.show()

    def sig_handler(sig=None, frame=None):
        tb.stop()
        tb.wait()

        Qt.QApplication.quit()

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    timer = Qt.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    qapp.exec_()

if __name__ == '__main__':
    main()
