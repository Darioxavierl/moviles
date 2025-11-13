import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import uniform_filter1d
import random
from rayleighchannel import RayleighChannel
from ricianchannel import RicianChannel
from itu_r_m1225 import ITU_R_M1225
 
# Crear instancia de los modelos
itu = ITU_R_M1225()

chans = itu.get_models()

# ------------------------------
# Parámetros generales
# ------------------------------
Fs = 100e3   # 10 kHz
c = 3e8         # velocidad de la luz
KdB = random.randint(6,9)

# Señal de entrada: constante (como 1i en MATLAB)
sig = 1j * np.ones(int(Fs/2))

# Desvanecimiento de gran escala
# Parametros factor de desvanecimiento
d0 = 100
Pl0 = 30        # Perdidas a la distancia de referencia en dB
n = 3.5         # Exponente de perdidas
sigma = 4       # Desviacion estandar para modelar el shadowing

# ------------------------------------
# Simulacion
# ------------------------------------

for ch in chans[-2:]:
    dlys, gains = itu.get_delays_and_gains(ch)
    freqs = itu.get_recommended_frequencies(ch)
    vels = itu.get_example_velocities(ch)

    num_vels = len(vels)  # número de filas
    num_cols = 4          # 4 gráficos por frecuencia (o métrica)


    for i,fc in enumerate(freqs):
        # --- FIGURA TIEMPO ---
        # Rayleigh
        fig_time, axs_time = plt.subplots(num_vels, 3, figsize=(15, 4*num_vels))
        if num_vels == 1:
            axs_time = axs_time[np.newaxis, :]  # asegurar que sea 2D
        fig_time.suptitle(f"Canal {ch} - Frecuencia {fc/1e9:.2f} GHz - Dominio Tiempo\n Rayleigh", fontsize=16)
        # Rice
        fig_timeRi, axs_timeRi = plt.subplots(num_vels, 3, figsize=(15, 4*num_vels))
        if num_vels == 1:
            axs_timeRi = axs_timeRi[np.newaxis, :]  # asegurar que sea 2D
        fig_timeRi.suptitle(f"Canal {ch} - Frecuencia {fc/1e9:.2f} GHz - Dominio Tiempo\n Rice", fontsize=16)

        # --- FIGURA FRECUENCIA ---
        # Rayleigh
        fig_freq, axs_freq = plt.subplots(num_vels, 2, figsize=(12, 4*num_vels))
        if num_vels == 1:
            axs_freq = axs_freq[np.newaxis, :]
        fig_freq.suptitle(f"Canal {ch} - Frecuencia {fc/1e9:.2f} GHz - Dominio Frecuencia\n Rayleigh", fontsize=16)
        # Rice
        fig_freqRi, axs_freqRi = plt.subplots(num_vels, 2, figsize=(12, 4*num_vels))
        if num_vels == 1:
            axs_freqRi = axs_freqRi[np.newaxis, :]
        fig_freqRi.suptitle(f"Canal {ch} - Frecuencia {fc/1e9:.2f} GHz - Dominio Frecuencia\n Rice", fontsize=16)

        for j,v in enumerate(vels):
            print("-------------------------------------")
            print(f"Velocidad {v*3.6:.2f} Km/h")
            print(f"Frecuencia {fc/1e9:.2f} GHz")
            # Doppler maximo según velocidad y frecuencia
            fD = (v/c)*fc
            Tc = 0.423/fD
            print(f"Dopler Maximo {fD:.2f} Hz")
            print(f"Tiempo de coherencia {Tc:.5f}s")
            chan = RayleighChannel(Fs, fD, dlys, gains)
            chanRi = RicianChannel(Fs, fD, dlys, gains, KdB)

            # ------------------------------
            # Respuesta en tiempo del canal multipath
            # ------------------------------
            # Desvanecimiento de pequena escala
            # Rayleigh
            y_small = chan.filter(sig)
            time = np.arange(len(y_small))/Fs
            # Rice
            y_smallRi = chanRi.filter(sig)
            timeRi = np.arange(len(y_smallRi))/Fs

            # Desvanecimiento de gran escala
            distancias = np.linspace(100, 1000, 50)  # de 1m a 1km
            pot = [chan.large_scale_fading(d, fc, PL0=30, n=3.5, sigma=4, d0=d0) for d in distancias]
            potencias = 20*np.log10(pot)
            potRi = [chanRi.large_scale_fading(d, fc, PL0=30, n=3.5, sigma=4, d0=d0) for d in distancias]
            potenciasRi = 20*np.log10(potRi)

            # ------------------------------
            # Respuesta al impulso del canal multipath
            # ------------------------------
            # Obtener respuesta al impulso
            taps_delay, h_taps = chan.impulse_response()
            taps_delayRi, hRi_taps = chanRi.impulse_response()

            # ------------------------------
            # Respuesta en frecuencia del canal multipath
            # ------------------------------
            N_freq = 1024
            #freqs_fc = np.linspace(fc-(fc/10), fc+(fc/10), N_freq)
            freqs_fc = np.linspace(1, 3e9, N_freq)
            # Calcular respuesta en frecuencia
            H_fc = chan.channel_response(freqs_fc,h_taps)
            H_fcRi = chan.channel_response(freqs_fc,hRi_taps)

            # Rayleigh
            #H_fc = chan.channel_response(N_freq, freqs_fc)
            H_fc_dB = 20*np.log10(np.abs(H_fc))


            #H_fcRi = chanRi.channel_response(N_freq, freqs_fc)
            H_fcRi_dB = 20*np.log10(np.abs(H_fcRi))

            # Pequeña escala: efecto de fading rápido
            H_small_scale = H_fc
            H_small_scale_dB = H_fc_dB

            HRi_small_scale = H_fcRi
            HRi_small_scale_dB = H_fcRi_dB

            # Gran escala
            d = 200  # distancia que se analiza (metros)
            # calcular PL(f) (dB) y factor lineal L_freq
            PL0_fspl_dB = 20*np.log10(4*np.pi*freqs_fc / c)         # FSPL a d0 en función de f
            PL_dB_freq = PL0_fspl_dB + 10*n*np.log10(d / d0)        # PL(f,d) suave
            L_freq = 10**(-PL_dB_freq/20)

            H_gran_scale =  H_small_scale * L_freq
            H_gran_scale_dB = 20*np.log10(np.abs(H_gran_scale) + 1e-12)
            
            HRi_gran_scale =  HRi_small_scale * L_freq
            HRi_gran_scale_dB = 20*np.log10(np.abs(HRi_gran_scale) + 1e-12)

            

            

            # Normalizar magnitudes para peso
            power = np.abs(h_taps)**2
            power = power / np.sum(power)
            tau_mean = np.sum(taps_delay * power)
            sigma_tau = np.sqrt(np.sum(power * (taps_delay - tau_mean)**2))

            B_c = 1 / (5 * sigma_tau)  # en Hz
            print(f"Ancho de banda de coherencia Rayleigh: {B_c/1e6:.3f} MHz")

            power = np.abs(hRi_taps)**2
            power = power / np.sum(power)
            tau_mean = np.sum(taps_delay * power)
            sigma_tau = np.sqrt(np.sum(power * (taps_delay - tau_mean)**2))

            B_c = 1 / (5 * sigma_tau)  # en Hz
            print(f"Ancho de banda de coherencia Rician: {B_c/1e6:.3f} MHz")
            print("-------------------------------------")
            
            # Ajuste de pequena escala
            delta = 0.2  # ±10%
            mask = (freqs_fc >= (1-delta)*fc) & (freqs_fc <= (1+delta)*fc)

            freqs_focus = freqs_fc[mask]

            H_small_focus = H_small_scale[mask]
            H_small_focus_dB = 20*np.log10(np.abs(H_small_focus) + 1e-12)

            HRi_small_focus = HRi_small_scale[mask]
            HRi_small_focus_dB = 20*np.log10(np.abs(HRi_small_focus) + 1e-12)


            # Graficas
            axs_time[j, 0].plot(time, 20*np.log10(np.abs(y_small)), color="green")
            axs_time[j, 0].set_title(f"Pequeña escala - Vel {v*3.6:.1f} km/h")
            axs_time[j, 0].set_xlabel("Tiempo [s]")
            axs_time[j, 0].set_ylabel("dB")
            axs_time[j, 0].grid(True)


            axs_time[j, 1].plot(distancias, potencias, color="red")
            axs_time[j, 1].set_title(f"Gran escala - Vel {v*3.6:.1f} km/h")
            axs_time[j, 1].set_xlabel("Distancia [m]")
            axs_time[j, 1].set_ylabel("dB")
            axs_time[j, 1].grid(True)

            axs_time[j, 2].stem(taps_delay, np.abs(h_taps)+1e-12, basefmt=" ")
            axs_time[j, 2].set_title(f"Taps multipath - Vel {v*3.6:.1f} km/h")
            axs_time[j, 2].set_xlabel("Retardo [µs]")
            axs_time[j, 2].set_ylabel("Magnitud")
            axs_time[j, 2].grid(True)

            axs_timeRi[j, 0].plot(time, 20*np.log10(np.abs(y_smallRi)), color="green")
            axs_timeRi[j, 0].set_title(f"Pequeña escala - Vel {v*3.6:.1f} km/h")
            axs_timeRi[j, 0].set_xlabel("Tiempo [s]")
            axs_timeRi[j, 0].set_ylabel("dB")
            axs_timeRi[j, 0].grid(True)


            axs_timeRi[j, 1].plot(distancias, potenciasRi, color="red")
            axs_timeRi[j, 1].set_title(f"Gran escala - Vel {v*3.6:.1f} km/h")
            axs_timeRi[j, 1].set_xlabel("Distancia [m]")
            axs_timeRi[j, 1].set_ylabel("dB")
            axs_timeRi[j, 1].grid(True)

            axs_timeRi[j, 2].stem(taps_delayRi, np.abs(hRi_taps)+1e-12, basefmt=" ")
            axs_timeRi[j, 2].set_title(f"Taps multipath - Vel {v*3.6:.1f} km/h")
            axs_timeRi[j, 2].set_xlabel("Retardo [µs]")
            axs_timeRi[j, 2].set_ylabel("Magnitud")
            axs_timeRi[j, 2].grid(True)


            # Columna 1: Gran escala
            axs_freq[j, 0].plot(freqs_fc/1e9, H_gran_scale_dB, label="Gran escala", color="red", linewidth=2)
            axs_freq[j, 0].axvline(fc/1e9, color="black", linestyle="--", label=f"fc = {fc/1e9:.2f} GHz")
            axs_freq[j, 0].set_title(f"Gran escala - Vel {v*3.6:.1f} km/h")
            axs_freq[j, 0].set_xlabel("Frecuencia [GHz]")
            axs_freq[j, 0].set_ylabel("dB")
            axs_freq[j, 0].grid(True)
            axs_freq[j, 0].legend()

            # Columna 2: Pequeña escala
            axs_freq[j, 1].plot(freqs_focus/1e9, H_small_focus_dB, label="Pequeña escala", color="green")
            axs_freq[j, 1].axvline(fc/1e9, color="black", linestyle="--", label=f"fc = {fc/1e9:.2f} GHz")
            axs_freq[j, 1].set_title(f"Pequeña escala - Vel {v*3.6:.1f} km/h")
            axs_freq[j, 1].set_xlabel("Frecuencia [GHz]")
            axs_freq[j, 1].set_ylabel("dB")
            axs_freq[j, 1].grid(True)
            axs_freq[j, 1].legend()


            # Columna 1: Gran escala
            axs_freqRi[j, 0].plot(freqs_fc/1e9, HRi_gran_scale_dB, label="Gran escala", color="red", linewidth=2)
            axs_freqRi[j, 0].axvline(fc/1e9, color="black", linestyle="--", label=f"fc = {fc/1e9:.2f} GHz")
            axs_freqRi[j, 0].set_title(f"Gran escala - Vel {v*3.6:.1f} km/h")
            axs_freqRi[j, 0].set_xlabel("Frecuencia [GHz]")
            axs_freqRi[j, 0].set_ylabel("dB")
            axs_freqRi[j, 0].grid(True)
            axs_freqRi[j, 0].legend()

            # Columna 2: Pequeña escala
            axs_freqRi[j, 1].plot(freqs_focus/1e9, HRi_small_focus_dB, label="Pequeña escala", color="green")
            axs_freqRi[j, 1].axvline(fc/1e9, color="black", linestyle="--", label=f"fc = {fc/1e9:.2f} GHz")
            axs_freqRi[j, 1].set_title(f"Pequeña escala - Vel {v*3.6:.1f} km/h")
            axs_freqRi[j, 1].set_xlabel("Frecuencia [GHz]")
            axs_freqRi[j, 1].set_ylabel("dB")
            axs_freqRi[j, 1].grid(True)
            axs_freqRi[j, 1].legend()


        fig_time.tight_layout(rect=[0,0,1,0.96])
        fig_freq.tight_layout(rect=[0,0,1,0.96])
        fig_timeRi.tight_layout(rect=[0,0,1,0.96])
        fig_freqRi.tight_layout(rect=[0,0,1,0.96])
        plt.show()










