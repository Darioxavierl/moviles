import numpy as np

class RicianChannel:
    def __init__(self, Fs, fD, delays, gains, K_dB=6):
        """
        Canal Rician con línea de vista (LOS).
        
        Parámetros:
        ------------
        Fs:     Frecuencia de muestreo [Hz]
        fD:     Doppler máximo [Hz]
        delays: Lista de retardos de cada trayectoria [s]
        gains:  Lista de ganancias de cada trayectoria [dB]
        K_dB:   Factor K en dB (relación entre potencia LOS y NLOS)
        """
        self.Fs = Fs
        self.fD = fD
        self.delays = np.array(delays)
        self.gains = 10**(np.array(gains)/20)   # amplitud lineal
        self.K = 10**(K_dB/10)                  # factor K lineal
        assert len(self.delays) == len(self.gains), "delays y gains deben tener la misma longitud"
        self.num_paths = len(delays)

    def jakes_fading(self, N, N_s=16):
        """
        Genera el componente difuso (Rayleigh) mediante el modelo de Jakes.
        """
        t = np.arange(N) / self.Fs
        fD = self.fD
        phi_n = 2 * np.pi * np.random.rand(N_s)
        alpha_n = 2 * np.pi * np.arange(1, N_s+1) / N_s
        h = np.zeros(N, dtype=complex)

        for n in range(N_s):
            h += np.exp(1j * (2*np.pi*fD*np.cos(alpha_n[n])*t + phi_n[n]))

        h = h * np.sqrt(2 / N_s)
        return h

    def rician_fading(self, N):
        """
        Genera un proceso Rician combinando un componente LOS y otro difuso.
        """
        rayleigh = self.jakes_fading(N)
        # Componente LOS con fase aleatoria
        theta = 2 * np.pi * np.random.rand()
        los = np.exp(1j * theta) * np.ones(N)
        
        # Combinación según el factor K
        rician = (np.sqrt(self.K/(self.K+1)) * los) + (np.sqrt(1/(self.K+1)) * rayleigh)
        return rician

    def filter(self, x):
        """
        Aplica el canal Rician a una señal de entrada x.
        """
        N = len(x)
        y = np.zeros(N, dtype=complex)

        for i in range(self.num_paths):
            delay_samples = int(np.round(self.delays[i] * self.Fs))
            fading = self.rician_fading(N)
            x_delayed = np.concatenate([np.zeros(delay_samples), x])[:N]
            y += self.gains[i] * fading * x_delayed

        return y

    def large_scale_fading(self, d, fc, PL0=30, n=3.5, sigma=4,d0=100):
        """
        Modelo log-distance + shadowing (igual al del canal Rayleigh).
        """
        PL_dB = PL0 + 10 * n * np.log10(d / d0)
        shadowing = np.random.normal(0, sigma)
        total_loss_dB = PL_dB + shadowing
        return 10**(-total_loss_dB/20)

    def channel_response(self, freqs, h_taps, N_freq=None):
        """
        Respuesta en frecuencia del canal multipath con Rician fading.
        """
        Hf = np.zeros_like(freqs, dtype=complex)
        for i in range(self.num_paths):
            Hf += h_taps[i] * np.exp(-1j * 2 * np.pi * freqs * self.delays[i])
        return Hf
    
    def impulse_response(self, N=1):
        """
        Devuelve la respuesta al impulso compleja del canal Rician (taps).
        Cada camino se representa con su ganancia y retardo correspondiente.
        """
        taps = []
        delays = []
        
        for i in range(self.num_paths):
            fading = self.rician_fading(N)[0]  # una muestra instantánea
            tap_value = self.gains[i] * fading
            taps.append(tap_value)
            delays.append(self.delays[i])

        # Retornos de retardos y taps
        return np.array(delays), np.array(taps)

