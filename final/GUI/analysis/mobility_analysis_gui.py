"""
Mobility Analysis GUI - Análisis de Movilidad y Trayectorias UAV
Análisis de diferentes patrones de movimiento para optimización de throughput
"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.animation import FuncAnimation
import os
import json
from scipy.optimize import differential_evolution

class MobilityAnalysisGUI:
    """Análisis de movilidad y trayectorias UAV para GUI"""
    
    def __init__(self, output_dir="outputs"):
        """Inicializar análisis de movilidad GUI"""
        
        print("="*60)
        print("MOBILITY ANALYSIS GUI - Analisis Movilidad UAV")
        print("="*60)
        
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # Munich scenario configuration
        self.munich_config = {
            'simulation_time': 60,  # 60 segundos
            'time_steps': 120,      # 0.5s resolution
            'flight_area': 200,     # ±200m flight zone
            'min_height': 30,       # Minimum altitude
            'max_height': 80,       # Maximum altitude  
            'optimal_height': 40,   # From Phase 2
            'max_velocity': 15,     # m/s max velocity
            'frequency_ghz': 3.5,
            'bandwidth_mhz': 100,
            'gnb_position': [300, 200, 50],  # gNB sobre edificio más alto
            'gnb_power_dbm': 43,
            'gnb_antennas': 64,
            'uav_antennas': 4
        }
        
        # Trajectory patterns
        self.trajectory_patterns = {
            'circular': 'Trayectoria Circular',
            'linear': 'Trayectoria Lineal',
            'spiral': 'Trayectoria Espiral',
            'figure8': 'Trayectoria Figura-8',
            'random_walk': 'Caminata Aleatoria',
            'optimized': 'Trayectoria Optimizada'
        }
        
        # System configuration
        self.system_config = {
            'scenario': 'Munich Urban Mobility 3D',
            'simulation_time': f"{self.munich_config['simulation_time']}s",
            'time_resolution': f"{self.munich_config['simulation_time']/self.munich_config['time_steps']:.1f}s",
            'flight_area': f"±{self.munich_config['flight_area']}m",
            'height_range': f"{self.munich_config['min_height']}-{self.munich_config['max_height']}m",
            'patterns_analyzed': len(self.trajectory_patterns)
        }
        
        print("Mobility Analysis GUI inicializado")
        print(f"Directorio de salida: {output_dir}")
        print(f"Simulacion: {self.munich_config['simulation_time']}s con {self.munich_config['time_steps']} pasos")
        
    def generate_trajectory(self, pattern_type, progress_callback=None):
        """Generar trayectoria según patrón especificado"""
        
        if progress_callback:
            progress_callback(f"Generando trayectoria {pattern_type}...")
        
        time_steps = self.munich_config['time_steps']
        sim_time = self.munich_config['simulation_time']
        flight_area = self.munich_config['flight_area']
        
        # Time array
        t = np.linspace(0, sim_time, time_steps)
        
        # Initialize position arrays
        x_traj = np.zeros(time_steps)
        y_traj = np.zeros(time_steps)
        z_traj = np.zeros(time_steps)
        
        if pattern_type == 'circular':
            # Circular trajectory
            radius = flight_area * 0.6
            omega = 2 * np.pi / (sim_time * 0.8)  # Complete circle in 80% of time
            x_traj = radius * np.cos(omega * t)
            y_traj = radius * np.sin(omega * t)
            z_traj = np.full(time_steps, self.munich_config['optimal_height'])
            
        elif pattern_type == 'linear':
            # Back and forth linear trajectory
            period = sim_time / 4  # 4 segments
            for i, time_val in enumerate(t):
                phase = (time_val % period) / period
                if int(time_val / period) % 2 == 0:  # Forward
                    x_traj[i] = -flight_area + 2 * flight_area * phase
                else:  # Backward
                    x_traj[i] = flight_area - 2 * flight_area * phase
                y_traj[i] = 0
                z_traj[i] = self.munich_config['optimal_height']
                
        elif pattern_type == 'spiral':
            # Spiral trajectory with height variation
            max_radius = flight_area * 0.7
            omega = 4 * np.pi / sim_time  # 2 full rotations
            for i, time_val in enumerate(t):
                radius = max_radius * (1 - time_val / sim_time)  # Decreasing radius
                x_traj[i] = radius * np.cos(omega * time_val)
                y_traj[i] = radius * np.sin(omega * time_val)
                # Height variation
                height_var = 10 * np.sin(2 * np.pi * time_val / (sim_time / 3))
                z_traj[i] = self.munich_config['optimal_height'] + height_var
                
        elif pattern_type == 'figure8':
            # Figure-8 trajectory
            a = flight_area * 0.6
            omega = 2 * np.pi / sim_time
            x_traj = a * np.sin(omega * t)
            y_traj = a * np.sin(omega * t) * np.cos(omega * t)
            z_traj = np.full(time_steps, self.munich_config['optimal_height'])
            
        elif pattern_type == 'random_walk':
            # Constrained random walk
            np.random.seed(42)  # Reproducible
            max_step = 20  # meters per step
            x_traj[0] = 0
            y_traj[0] = 0
            z_traj[0] = self.munich_config['optimal_height']
            
            for i in range(1, time_steps):
                # Random step with boundary constraints
                dx = np.random.uniform(-max_step, max_step)
                dy = np.random.uniform(-max_step, max_step)
                dz = np.random.uniform(-5, 5)
                
                # Apply step with boundary checking
                x_new = np.clip(x_traj[i-1] + dx, -flight_area, flight_area)
                y_new = np.clip(y_traj[i-1] + dy, -flight_area, flight_area)
                z_new = np.clip(z_traj[i-1] + dz, 
                               self.munich_config['min_height'], 
                               self.munich_config['max_height'])
                
                x_traj[i] = x_new
                y_traj[i] = y_new
                z_traj[i] = z_new
                
        elif pattern_type == 'optimized':
            # Optimized trajectory (simplified - towards high throughput areas)
            # Move towards positions that historically had good coverage
            center_bias = 0.3
            x_traj = flight_area * center_bias * np.sin(3 * np.pi * t / sim_time)
            y_traj = flight_area * center_bias * np.cos(2 * np.pi * t / sim_time)
            z_traj = np.full(time_steps, self.munich_config['optimal_height'])
        
        # Calculate velocities
        dt = sim_time / time_steps
        vx = np.gradient(x_traj) / dt
        vy = np.gradient(y_traj) / dt
        vz = np.gradient(z_traj) / dt
        velocity_magnitude = np.sqrt(vx**2 + vy**2 + vz**2)
        
        # Limit maximum velocity
        max_vel = self.munich_config['max_velocity']
        velocity_magnitude = np.clip(velocity_magnitude, 0, max_vel)
        
        trajectory = {
            'pattern': pattern_type,
            'time': t,
            'positions': np.column_stack([x_traj, y_traj, z_traj]),
            'x': x_traj,
            'y': y_traj, 
            'z': z_traj,
            'velocities': np.column_stack([vx, vy, vz]),
            'velocity_magnitude': velocity_magnitude,
            'total_distance': np.sum(np.sqrt(np.diff(x_traj)**2 + np.diff(y_traj)**2 + np.diff(z_traj)**2)),
            'avg_velocity': np.mean(velocity_magnitude),
            'max_velocity': np.max(velocity_magnitude)
        }
        
        return trajectory
    
    def calculate_trajectory_performance(self, trajectory, progress_callback=None):
        """Calcular performance de throughput a lo largo de la trayectoria"""
        
        if progress_callback:
            progress_callback(f"Calculando performance trayectoria {trajectory['pattern']}...")
        
        positions = trajectory['positions']
        time_array = trajectory['time']
        gnb_pos = np.array(self.munich_config['gnb_position'])
        
        # Result arrays
        throughput_array = np.zeros(len(time_array))
        path_loss_array = np.zeros(len(time_array))
        distance_array = np.zeros(len(time_array))
        snr_array = np.zeros(len(time_array))
        los_array = np.zeros(len(time_array))
        
        # Munich buildings for LoS calculation
        buildings = [
            [100, 100, 20], [200, 150, 35], [300, 200, 45],
            [150, 300, 30], [350, 350, 25], [250, 50, 40]
        ]
        
        for i, (uav_pos, time_val) in enumerate(zip(positions, time_array)):
            if progress_callback and i % max(1, len(time_array) // 10) == 0:
                progress = (i + 1) / len(time_array) * 100
                progress_callback(f"Tiempo {time_val:.1f}s ({progress:.0f}%)...")
            
            # Distance to gNB
            distance_3d = np.linalg.norm(uav_pos - gnb_pos)
            distance_array[i] = distance_3d
            
            # LoS calculation
            los_probability = self._calculate_los_probability(uav_pos, gnb_pos, buildings)
            los_array[i] = los_probability
            
            # Path loss calculation
            fspl_db = 32.4 + 20 * np.log10(distance_3d) + 20 * np.log10(self.munich_config['frequency_ghz'])
            
            # Additional path loss for NLoS
            nlos_factor = 0 if los_probability > 0.5 else 20
            total_path_loss = fspl_db + nlos_factor
            path_loss_array[i] = total_path_loss
            
            # Received power
            rx_power_dbm = self.munich_config['gnb_power_dbm'] - total_path_loss
            
            # SNR calculation with mobility effects
            noise_floor_dbm = -104
            doppler_effect = self._calculate_doppler_effect(uav_pos, gnb_pos, 
                                                          trajectory['velocities'][i])
            snr_db = rx_power_dbm - noise_floor_dbm + doppler_effect
            
            # MIMO gain
            mimo_gain_db = 10 * np.log10(min(self.munich_config['gnb_antennas'], 
                                            self.munich_config['uav_antennas']))
            snr_db += mimo_gain_db
            snr_array[i] = snr_db
            
            # Shannon capacity with mobility penalty
            efficiency_factor = 0.7 * (1 - 0.1 * trajectory['velocity_magnitude'][i] / self.munich_config['max_velocity'])
            spectral_eff = efficiency_factor * np.log2(1 + max(0.1, 10**(snr_db/10)))
            throughput_mbps = spectral_eff * self.munich_config['bandwidth_mhz']
            
            throughput_array[i] = max(0, throughput_mbps)
        
        # Performance metrics
        performance = {
            'time': time_array,
            'throughput': throughput_array,
            'path_loss': path_loss_array,
            'distance': distance_array,
            'snr': snr_array,
            'los_probability': los_array,
            'avg_throughput': float(np.mean(throughput_array)),
            'min_throughput': float(np.min(throughput_array)),
            'max_throughput': float(np.max(throughput_array)),
            'throughput_variance': float(np.var(throughput_array)),
            'stability_score': float(1 / (1 + np.var(throughput_array) / np.mean(throughput_array))),
            'total_data_mb': float(np.sum(throughput_array) * (time_array[1] - time_array[0]) / 8)  # Convert to MB
        }
        
        return performance
    
    def _calculate_los_probability(self, uav_pos, gnb_pos, buildings):
        """Calcular probabilidad LoS considerando edificios"""
        
        height = uav_pos[2]
        los_prob_base = 1 / (1 + 9.61 * np.exp(-0.16 * (height - 1.5)))
        
        # Building blockage
        building_blockage = 0
        for bx, by, bh in buildings:
            dist_to_building = np.sqrt((uav_pos[0] - bx)**2 + (uav_pos[1] - by)**2)
            if dist_to_building < 60 and uav_pos[2] < bh + 15:
                building_blockage += 0.15
        
        return max(0.1, los_prob_base - min(0.8, building_blockage))
    
    def _calculate_doppler_effect(self, uav_pos, gnb_pos, velocity_vec):
        """Calcular efecto Doppler simplificado"""
        
        # Direction vector from gNB to UAV
        direction = uav_pos - gnb_pos
        distance = np.linalg.norm(direction)
        if distance == 0:
            return 0
        direction_unit = direction / distance
        
        # Radial velocity component
        radial_velocity = np.dot(velocity_vec, direction_unit)
        
        # Simplified Doppler effect (positive for approaching, negative for receding)
        c = 3e8  # Speed of light
        freq_hz = self.munich_config['frequency_ghz'] * 1e9
        doppler_shift = (radial_velocity / c) * freq_hz
        
        # Convert to dB gain/loss (simplified)
        doppler_effect_db = 0.1 * np.tanh(doppler_shift / 1000)  # Small effect
        
        return doppler_effect_db
    
    def analyze_mobility_patterns(self, progress_callback=None):
        """Analizar todos los patrones de movilidad"""
        
        if progress_callback:
            progress_callback("Analizando patrones de movilidad...")
        
        results = {}
        
        for pattern_key, pattern_name in self.trajectory_patterns.items():
            if progress_callback:
                progress_callback(f"Procesando {pattern_name}...")
            
            # Generate trajectory
            trajectory = self.generate_trajectory(pattern_key, progress_callback)
            
            # Calculate performance
            performance = self.calculate_trajectory_performance(trajectory, progress_callback)
            
            # Combine results
            results[pattern_key] = {
                'name': pattern_name,
                'trajectory': trajectory,
                'performance': performance
            }
        
        # Comparative analysis
        comparative_analysis = self._analyze_pattern_comparison(results)
        
        if progress_callback:
            progress_callback("Análisis de movilidad completado")
        
        return results, comparative_analysis
    
    def _analyze_pattern_comparison(self, results):
        """Análisis comparativo de patrones"""
        
        comparison = {
            'best_avg_throughput': {'pattern': None, 'value': 0},
            'most_stable': {'pattern': None, 'value': 0},
            'highest_peak': {'pattern': None, 'value': 0},
            'most_efficient': {'pattern': None, 'value': 0},
            'summary_stats': {}
        }
        
        for pattern_key, result in results.items():
            perf = result['performance']
            traj = result['trajectory']
            
            # Track best metrics
            if perf['avg_throughput'] > comparison['best_avg_throughput']['value']:
                comparison['best_avg_throughput'] = {'pattern': pattern_key, 'value': perf['avg_throughput']}
            
            if perf['stability_score'] > comparison['most_stable']['value']:
                comparison['most_stable'] = {'pattern': pattern_key, 'value': perf['stability_score']}
                
            if perf['max_throughput'] > comparison['highest_peak']['value']:
                comparison['highest_peak'] = {'pattern': pattern_key, 'value': perf['max_throughput']}
            
            # Efficiency = data per distance
            efficiency = perf['total_data_mb'] / max(traj['total_distance'], 1)
            if efficiency > comparison['most_efficient']['value']:
                comparison['most_efficient'] = {'pattern': pattern_key, 'value': efficiency}
            
            # Summary stats
            comparison['summary_stats'][pattern_key] = {
                'avg_throughput_mbps': perf['avg_throughput'],
                'stability_score': perf['stability_score'],
                'total_distance_m': traj['total_distance'],
                'avg_velocity_ms': traj['avg_velocity'],
                'total_data_mb': perf['total_data_mb']
            }
        
        return comparison
    
    def generate_mobility_plots(self, results, comparison, progress_callback=None):
        """Generar gráficos de análisis de movilidad"""
        
        if progress_callback:
            progress_callback("Generando gráficos de movilidad...")
        
        # Create comprehensive mobility analysis plot (2x2 layout)
        fig = plt.figure(figsize=(16, 12))
        
        # Define colors for patterns
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
        
        # 1. Trajectory Comparison (3D)
        ax1 = fig.add_subplot(2, 2, 1, projection='3d')
        for i, (pattern_key, result) in enumerate(results.items()):
            traj = result['trajectory']
            ax1.plot(traj['x'], traj['y'], traj['z'], 
                    color=colors[i % len(colors)], linewidth=3, 
                    label=f"{result['name']}", alpha=0.8)
        
        # Add gNB
        gnb_pos = self.munich_config['gnb_position']
        ax1.scatter(*gnb_pos, s=300, c='red', marker='^', 
                   label='gNB', alpha=1.0, edgecolors='darkred')
        
        ax1.set_xlabel('X [m]', fontweight='bold', fontsize=12)
        ax1.set_ylabel('Y [m]', fontweight='bold', fontsize=12)
        ax1.set_zlabel('Altura [m]', fontweight='bold', fontsize=12)
        ax1.set_title('Trayectorias 3D - Patrones de Movilidad\nComparación Visual', fontweight='bold')
        ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax1.grid(True, alpha=0.3)
        
        # 2. Throughput vs Time
        ax2 = fig.add_subplot(2, 2, 2)
        for i, (pattern_key, result) in enumerate(results.items()):
            perf = result['performance']
            ax2.plot(perf['time'], perf['throughput'], 
                    color=colors[i % len(colors)], linewidth=2, 
                    label=f"{result['name']}")
        
        ax2.set_xlabel('Tiempo [s]', fontweight='bold', fontsize=12)
        ax2.set_ylabel('Throughput [Mbps]', fontweight='bold', fontsize=12)
        ax2.set_title('Throughput vs Tiempo\nPerformance Temporal', fontweight='bold')
        ax2.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'{x:.3f}'))
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        # 3. Performance Comparison Bars - CORREGIDO
        ax3 = fig.add_subplot(2, 2, 3)
        
        # Get all patterns in order
        pattern_names = []
        avg_throughputs = []
        colors_bars = []
        
        for i, (pattern_key, result) in enumerate(results.items()):
            pattern_names.append(result['name'])
            avg_throughputs.append(result['performance']['avg_throughput'])
            colors_bars.append(colors[i % len(colors)])
        
        bars = ax3.bar(range(len(pattern_names)), avg_throughputs, color=colors_bars, alpha=0.8)
        ax3.set_ylabel('Throughput Promedio [Mbps]', fontweight='bold', fontsize=12)
        ax3.set_title('Comparación Performance\nThroughput Promedio por Patrón', fontweight='bold', fontsize=12)
        ax3.set_xticks(range(len(pattern_names)))
        ax3.set_xticklabels(pattern_names, rotation=45, ha='right')
        ax3.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'{x:.3f}'))
        ax3.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for bar, value in zip(bars, avg_throughputs):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height + 50,
                    f'{value:.0f}', ha='center', va='bottom', fontweight='bold', fontsize=10)
        
        # 4. Best Pattern Summary
        ax4 = fig.add_subplot(2, 2, 4)
        ax4.axis('off')
        
        # Summary text
        best_avg = comparison['best_avg_throughput']
        most_stable = comparison['most_stable'] 
        highest_peak = comparison['highest_peak']
        most_efficient = comparison['most_efficient']
        
        summary_text = f"""
ANÁLISIS COMPARATIVO MOVILIDAD

Mejor Promedio:
   {self.trajectory_patterns[best_avg['pattern']]}
   {best_avg['value']:.0f} Mbps

Más Estable:
   {self.trajectory_patterns[most_stable['pattern']]}
   Score: {most_stable['value']:.2f}

Pico Máximo:
   {self.trajectory_patterns[highest_peak['pattern']]}
   {highest_peak['value']:.0f} Mbps

Más Eficiente:
   {self.trajectory_patterns[most_efficient['pattern']]}
   {most_efficient['value']:.1f} MB/m

Recomendación:
   Usar {self.trajectory_patterns[best_avg['pattern']]} para
   máximo throughput promedio
        """
        
        ax4.text(0.05, 0.95, summary_text, transform=ax4.transAxes, fontsize=11,
                verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle="round,pad=0.4", 
                facecolor='lightblue', alpha=0.8))
        ax4.set_title('Resumen de Resultados\n(Sionna Analysis)', fontweight='bold', fontsize=12)
        
        # Main title
        fig.suptitle('ANÁLISIS MOVILIDAD UAV - Sistema 5G NR Munich\nComparación Patrones de Trayectoria', 
                    fontsize=14, fontweight='bold', y=0.98)
        
        plt.tight_layout()
        plt.subplots_adjust(top=0.93, hspace=0.35, wspace=0.3)
        
        if progress_callback:
            progress_callback("Guardando análisis de movilidad...")
        
        plot_path = os.path.join(self.output_dir, "mobility_analysis.png")
        plt.savefig(plot_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return plot_path
    
    def generate_3d_mobility_scene(self, results, progress_callback=None):
        """Generar escena 3D con todas las trayectorias"""
        
        if progress_callback:
            progress_callback("Generando escena 3D de movilidad...")
        
        fig = plt.figure(figsize=(18, 14))
        ax = fig.add_subplot(111, projection='3d')
        
        # Munich terrain base
        area = 400
        x_ground = np.linspace(-area//2, area//2, 20)
        y_ground = np.linspace(-area//2, area//2, 20)
        X_ground, Y_ground = np.meshgrid(x_ground, y_ground)
        Z_ground = 2 * np.sin(X_ground/100) * np.cos(Y_ground/100) + 1
        ax.plot_surface(X_ground, Y_ground, Z_ground, alpha=0.1, color='lightgray')
        
        # Munich buildings
        buildings = [
            [100, 100, 20], [200, 150, 35], [300, 200, 45],
            [150, 300, 30], [350, 350, 25], [250, 50, 40]
        ]
        building_colors = ['#8B4513', '#696969', '#708090', '#2F4F4F', '#8FBC8F', '#CD853F']
        
        for i, (x, y, h) in enumerate(buildings):
            building_size = 35
            ax.bar3d(x-building_size/2, y-building_size/2, 0, building_size, building_size, h, 
                    alpha=0.6, color=building_colors[i], edgecolor='black')
        
        # gNB Tower
        gnb_x, gnb_y, gnb_z = self.munich_config['gnb_position']
        ax.scatter([gnb_x], [gnb_y], [gnb_z], c='red', s=600, marker='^', 
                  label='gNB Base Station', alpha=1.0, edgecolors='darkred', linewidth=3)
        ax.plot([gnb_x, gnb_x], [gnb_y, gnb_y], [0, gnb_z], 'darkred', linewidth=8)
        
        # Flight area boundary at different heights
        flight_area = self.munich_config['flight_area']
        theta = np.linspace(0, 2*np.pi, 50)
        
        # Ground level boundary
        boundary_x = flight_area * np.cos(theta)
        boundary_y = flight_area * np.sin(theta)
        boundary_z_ground = np.zeros_like(boundary_x)
        ax.plot(boundary_x, boundary_y, boundary_z_ground, 'gray', linewidth=2, alpha=0.5)
        
        # Flight ceiling boundary
        boundary_z_ceiling = np.full_like(boundary_x, self.munich_config['max_height'])
        ax.plot(boundary_x, boundary_y, boundary_z_ceiling, 'gray', linewidth=2, alpha=0.5)
        
        # Plot all trajectories
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
        
        for i, (pattern_key, result) in enumerate(results.items()):
            traj = result['trajectory']
            perf = result['performance']
            color = colors[i % len(colors)]
            
            # Main trajectory line
            ax.plot(traj['x'], traj['y'], traj['z'], 
                   color=color, linewidth=4, alpha=0.8, 
                   label=f"{result['name']} ({perf['avg_throughput']:.0f} Mbps avg)")
            
            # Start point
            ax.scatter(traj['x'][0], traj['y'][0], traj['z'][0], 
                      s=200, c=color, marker='o', edgecolors='black', 
                      linewidth=2, alpha=1.0)
            
            # End point
            ax.scatter(traj['x'][-1], traj['y'][-1], traj['z'][-1], 
                      s=200, c=color, marker='s', edgecolors='black', 
                      linewidth=2, alpha=1.0)
            
            # Performance visualization - color intensity based on throughput
            # Sample some points for performance visualization
            sample_indices = np.linspace(0, len(traj['x'])-1, 20, dtype=int)
            for idx in sample_indices:
                throughput_norm = perf['throughput'][idx] / max(perf['throughput'])
                size = 30 + 70 * throughput_norm
                alpha_val = 0.3 + 0.7 * throughput_norm
                ax.scatter(traj['x'][idx], traj['y'][idx], traj['z'][idx], 
                          s=size, c=color, alpha=alpha_val, edgecolors='none')
        
        # Communication links from gNB to best positions
        best_pattern_key = max(results.keys(), 
                              key=lambda k: results[k]['performance']['avg_throughput'])
        best_traj = results[best_pattern_key]['trajectory']
        best_perf = results[best_pattern_key]['performance']
        
        # Draw links to top 10 performance points
        top_indices = np.argsort(best_perf['throughput'])[-10:]
        for idx in top_indices:
            ax.plot([gnb_x, best_traj['x'][idx]], [gnb_y, best_traj['y'][idx]], 
                   [gnb_z, best_traj['z'][idx]], 
                   color='gold', linewidth=2, alpha=0.6)
        
        # Configuration and styling
        ax.set_xlabel('Coordenada X (metros)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Coordenada Y (metros)', fontsize=12, fontweight='bold')
        ax.set_zlabel('Altura Z (metros)', fontsize=12, fontweight='bold')
        ax.set_title('MUNICH 3D - Análisis Movilidad Multi-Patrón\nTrayectorias UAV con Performance Visualization', 
                    fontsize=16, fontweight='bold', pad=20)
        
        # Limits
        ax.set_xlim(-flight_area-50, flight_area+50)
        ax.set_ylim(-flight_area-50, flight_area+50) 
        ax.set_zlim(0, self.munich_config['max_height']+20)
        
        # Legend
        ax.legend(loc='upper left', bbox_to_anchor=(0.02, 0.98), fontsize=9)
        
        # Grid and view
        ax.grid(True, alpha=0.3)
        ax.view_init(elev=25, azim=45)
        
        plt.tight_layout()
        
        if progress_callback:
            progress_callback("Guardando escena 3D movilidad...")
        
        scene_path = os.path.join(self.output_dir, "mobility_scene_3d.png")
        plt.savefig(scene_path, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return scene_path
    
    def save_mobility_results_json(self, results, comparison):
        """Guardar resultados del análisis en JSON"""
        
        # Prepare serializable results
        json_results = {}
        for pattern_key, result in results.items():
            json_results[pattern_key] = {
                'name': result['name'],
                'trajectory_stats': {
                    'total_distance_m': result['trajectory']['total_distance'],
                    'avg_velocity_ms': result['trajectory']['avg_velocity'],
                    'max_velocity_ms': result['trajectory']['max_velocity']
                },
                'performance_stats': {
                    'avg_throughput_mbps': result['performance']['avg_throughput'],
                    'min_throughput_mbps': result['performance']['min_throughput'],
                    'max_throughput_mbps': result['performance']['max_throughput'],
                    'stability_score': result['performance']['stability_score'],
                    'total_data_mb': result['performance']['total_data_mb']
                }
            }
        
        complete_results = {
            'simulation_type': 'mobility_analysis',
            'timestamp': '2026-02-01',
            'system_config': self.system_config,
            'mobility_analysis': {
                'simulation_time_s': self.munich_config['simulation_time'],
                'patterns_analyzed': len(self.trajectory_patterns),
                'flight_area_m': self.munich_config['flight_area'] * 2,
                'height_range': f"{self.munich_config['min_height']}-{self.munich_config['max_height']}m"
            },
            'pattern_results': json_results,
            'comparative_analysis': {
                'best_avg_throughput': {
                    'pattern': self.trajectory_patterns[comparison['best_avg_throughput']['pattern']],
                    'value_mbps': comparison['best_avg_throughput']['value']
                },
                'most_stable': {
                    'pattern': self.trajectory_patterns[comparison['most_stable']['pattern']],
                    'stability_score': comparison['most_stable']['value']
                },
                'highest_peak': {
                    'pattern': self.trajectory_patterns[comparison['highest_peak']['pattern']],
                    'value_mbps': comparison['highest_peak']['value']
                },
                'most_efficient': {
                    'pattern': self.trajectory_patterns[comparison['most_efficient']['pattern']],
                    'efficiency_mb_per_m': comparison['most_efficient']['value']
                }
            },
            'summary': {
                'recommended_pattern': self.trajectory_patterns[comparison['best_avg_throughput']['pattern']],
                'best_avg_throughput': f"{comparison['best_avg_throughput']['value']:.1f} Mbps",
                'stability_range': f"{min(r['performance']['stability_score'] for r in results.values()):.2f} - {max(r['performance']['stability_score'] for r in results.values()):.2f}",
                'total_patterns_tested': len(self.trajectory_patterns)
            }
        }
        
        json_path = os.path.join(self.output_dir, "mobility_results.json")
        with open(json_path, 'w') as f:
            json.dump(complete_results, f, indent=2)
        
        return json_path
    
    def run_complete_analysis(self, progress_callback=None):
        """Ejecutar análisis completo de movilidad"""
        
        if progress_callback:
            progress_callback("Iniciando análisis de movilidad...")
        
        # 1. Analyze all mobility patterns
        results, comparison = self.analyze_mobility_patterns(progress_callback)
        
        if progress_callback:
            progress_callback("Generando visualizaciones movilidad...")
        
        # 2. Generate analysis plots
        plots_path = self.generate_mobility_plots(results, comparison, progress_callback)
        
        # 3. Generate 3D scene
        scene_path = self.generate_3d_mobility_scene(results, progress_callback)
        
        # 4. Save JSON results
        json_path = self.save_mobility_results_json(results, comparison)
        
        if progress_callback:
            progress_callback("Análisis de movilidad completado!")
        
        # Summary
        best_pattern = comparison['best_avg_throughput']['pattern']
        best_value = comparison['best_avg_throughput']['value']
        
        return {
            'type': 'mobility_analysis',
            'plots': [plots_path],
            'scene_3d': scene_path,
            'data': json_path,
            'summary': f'Movilidad: {self.trajectory_patterns[best_pattern]} mejor patrón ({best_value:.1f} Mbps)',
            'config': {
                'Mobility_Analysis': {
                    'Best_Pattern': self.trajectory_patterns[best_pattern],
                    'Avg_Throughput_Mbps': best_value,
                    'Simulation_Time': f"{self.munich_config['simulation_time']}s",
                    'Patterns_Tested': len(self.trajectory_patterns)
                },
                'Performance': {
                    'Most_Stable': self.trajectory_patterns[comparison['most_stable']['pattern']],
                    'Highest_Peak_Mbps': comparison['highest_peak']['value'],
                    'Most_Efficient': self.trajectory_patterns[comparison['most_efficient']['pattern']],
                    'Flight_Area': f"±{self.munich_config['flight_area']}m"
                }
            }
        }


def run_mobility_analysis_gui(output_dir="outputs", progress_callback=None):
    """Función para ejecutar desde GUI worker thread"""
    
    mobility_analyzer = MobilityAnalysisGUI(output_dir)
    results = mobility_analyzer.run_complete_analysis(progress_callback)
    
    return results


if __name__ == "__main__":
    # Test standalone
    print("Testing Mobility Analysis GUI...")
    results = run_mobility_analysis_gui("test_outputs")
    print(f"Test completado: {results['summary']}")