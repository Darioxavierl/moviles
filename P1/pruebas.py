import numpy as np
import matplotlib.pyplot as plt
from rayleighchannel import RayleighChannel
 

# ------------------------------
# Parámetros generales
# ------------------------------
fc = 0.9e9        # 2 GHz
v = 1.5/3.6      # 30 km/h -> m/s
#Fs = 1e4        # Hz
c = 3e8         # velocidad de la luz

# Doppler maximo según velocidad y frecuencia
fD = (v/c)*fc

Fs = 1/1e-4   # 10 kHz
delays = [0.0, 0.11, 0.19, 0.41, 0.71, 1.09]  # un solo camino sin retardo
gains = [0.0, -9.7, -19.2, -22.8, -27.7, -31.9]   # ganancia unitaria

#delays = [1e-5, 1.2e-4, 2.3e-4, 6.2e-4, 0.0011]
#gains =  [-0.2500, -2.7500, -5.2500, -7.7500, -10.2500]
chan = RayleighChannel(Fs, fD, delays, gains)

# Señal de entrada: constante (como 1i en MATLAB)
sig = 1j * np.ones(2000)

# Desvanecimiento de pequena escala
y_small = chan.filter(sig)
time = np.arange(len(y_small))/Fs
dist = v * time

# Desvanecimiento de gran escala
# Parametros factor de desvanecimiento
Pl0 = 30        # Perdidas a la distancia de referencia en dB
n = 3.5         # Exponente de perdidas
sigma = 4       # Ddesviacion estandar para modelar el shadowing

distancias = np.linspace(1, 100, 50)  # de 1m a 1km

potencias = [20*np.log10(chan.large_scale_fading(d, fc, PL0=30, n=3.5, sigma=4)) for d in distancias]


# ------------------------------
# Respuesta en frecuencia del canal multipath
# ------------------------------
N_freq = 1024
#freqs = np.linspace(-(fc-(fc/10)), fc+(fc/10), N_freq)
freqs = np.linspace(-Fs, Fs, N_freq)
H = chan.channel_response(N_freq, freqs)

freqs_fc = np.linspace(fc-(fc/10), fc+(fc/10), N_freq)
H_fc = chan.channel_response(N_freq, freqs_fc)
H_fc_dB = 20*np.log10(np.abs(H_fc))

# ------------------------------
# Respuesta al impulso del canal multipath
# ------------------------------
# Obtener respuesta al impulso
taps_delay,h_taps = chan.impulse_response()

# Eje de retardos en microsegundos
 


plt.figure(figsize=(8,4))
#plt.stem(taps_delay, 20*np.log10(np.abs(h_taps) + 1e-12), basefmt=" ")
plt.stem(taps_delay, np.abs(h_taps) + 1e-12, basefmt=" ")
plt.title("Respuesta al impulso del canal (taps multipath)")
plt.xlabel("Retardo [µs]")
plt.ylabel("Magnitud")
plt.grid(True)
plt.show()


# --- Graficar ---
plt.figure(figsize=(12,6))

plt.subplot(2,1,1)
plt.plot(time , 20*np.log10(np.abs(y_small)))
plt.title("Desvanecimiento de pequeña escala")
plt.xlabel("Tiempo (s)")
plt.ylabel("Potencia [dB]")
plt.grid(True)


plt.subplot(2,1,2)
plt.plot(distancias, potencias)
plt.title("Desvanecimiento de gran escala")
plt.xlabel("Distancia")
plt.ylabel("Potencia [dB]")
plt.grid(True)

plt.figure(figsize=(12,6))
plt.subplot(2,1,1)
plt.plot(freqs/1e3, 20*np.log10(np.abs(H)))
plt.title("Respuesta en frecuencia canal multipath")
plt.xlabel("Frecuencia [kHz]")
plt.ylabel("Magnitud [dB]")
plt.grid(True)

plt.subplot(2,1,2)
plt.plot(freqs_fc/1e9, H_fc_dB )
plt.vlines([fc/1e9],np.min(H_fc_dB),np.max(H_fc_dB),colors='red', label=f"fc = {fc/1e9} GHz")
plt.title("Respuesta en frecuencia canal multipath")
plt.xlabel("Frecuencia [GHz]")
plt.ylabel("Magnitud [dB]")
plt.legend()
plt.grid(True)



plt.tight_layout()
plt.show()
