"""
Mobility Analysis Tool - Two Routes Comparison
Compares throughput variation across two distinct 3D UAV trajectories
Using Sionna ray tracing for accurate channel modeling
"""

import tensorflow as tf
import numpy as np
import sionna
from sionna.rt import Transmitter, Receiver, PathSolver, PlanarArray, load_scene, Camera
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import os
import traceback

tf.get_logger().setLevel("INFO")

########################################
# CONFIGURATION CLASSES
########################################

class MIMO_Configuration:
    """Define standard 5G NR MIMO array configuration"""
    
    def __init__(self, name, tx_rows, tx_cols, rx_rows, rx_cols, 
                 description="", spacing=0.5, pattern="tr38901", polarization="VH"):
        self.name = name
        self.tx_rows = tx_rows
        self.tx_cols = tx_cols
        self.rx_rows = rx_rows
        self.rx_cols = rx_cols
        self.spacing = spacing
        self.pattern = pattern
        self.polarization = polarization
        self.description = description
        
        self.tx_antennas = tx_rows * tx_cols
        self.rx_antennas = rx_rows * rx_cols
        self.tx_antennas_sionna = self.tx_antennas * (2 if polarization == "VH" else 1)
        self.rx_antennas_sionna = self.rx_antennas * (2 if polarization == "VH" else 1)
        self.max_layers = min(self.tx_antennas, self.rx_antennas)

    def __repr__(self):
        return f"{self.name} ({self.tx_rows}x{self.tx_cols} Tx, {self.rx_rows}x{self.rx_cols} Rx)"

# Standard MIMO configuration
MIMO_CONFIG = MIMO_Configuration(
    name="MIMO_4x4",
    tx_rows=4, tx_cols=4, rx_rows=4, rx_cols=4,
    description="4x4 Massive MIMO for UAV"
)

class RFNR_Config:
    """5G NR RF configuration"""
    CARRIER_FREQUENCY = 3.5e9  # Band n78
    BANDWIDTH = 20e6           # 20 MHz
    SUBCARRIER_SPACING = 15e3  # 15 kHz
    NUM_SUBCARRIERS = int(BANDWIDTH / SUBCARRIER_SPACING)

class ScenarioConfig:
    """3D scenario configuration for Munich"""
    GNB_POSITION = [110, 70, 20]      # gNB base station
    ROUTE_A_START = [50, 150, 35]     # Route A: starting point
    ROUTE_A_END = [250, 100, 60]      # Route A: destination (higher altitude)
    ROUTE_B_START = [50, 150, 35]     # Route B: same start
    ROUTE_B_END = [100, 300, 50]      # Route B: different destination
    CAMERA_HEIGHT = 180
    Y_OFFSET = 350
    X_OFFSET = -100

class ScenarioConfig_BestRoute:
    """ALTERNATIVE: Same start/end, different paths (left vs right)
    
    Both routes go from same start point to same destination,
    but take different paths (around obstacles or terrain).
    
    Question: "Which is the best route to reach destination?"
    """
    GNB_POSITION = [110, 70, 20]      # gNB base station
    ROUTE_A_START = [80, 100, 35]     # Common start
    ROUTE_A_END = [280, 150, 55]      # Common destination
    ROUTE_B_START = [80, 100, 35]     # Same start
    ROUTE_B_END = [280, 150, 55]      # Same destination
    CAMERA_HEIGHT = 50
    
    # Note: Routes will curve in opposite directions due to perpendicular offset
    # Route A curves LEFT (north), Route B curves RIGHT (south) around destination
########################################
# ROUTE GENERATION
########################################

class RouteGenerator:
    """Generate 3D trajectories for UAV routes"""
    
    @staticmethod
    def generate_route(start_point, end_point, num_points=20, route_style="curved", curve_direction="left"):
        """
        Generate smooth 3D route from start to end point
        
        Args:
            start_point: [x, y, z] starting position
            end_point: [x, y, z] destination position
            num_points: Number of waypoints
            route_style: "curved" (with arc), "spiral", or "direct"
            curve_direction: "left" or "right" for curve direction (only for same start/end comparison)
        
        Returns:
            route: Array of shape (num_points, 3) with waypoint positions
        """
        from scipy.interpolate import CubicSpline
        
        start = np.array(start_point, dtype=np.float32)
        end = np.array(end_point, dtype=np.float32)
        
        # Parameter t from 0 to 1
        t = np.linspace(0, 1, num_points)
        
        if route_style == "curved":
            # Create curved path with arc (like real drone delivery)
            direction = end[:2] - start[:2]
            distance_2d = np.linalg.norm(direction)
            
            if distance_2d > 0:
                direction_unit = direction / distance_2d
                perpendicular = np.array([-direction_unit[1], direction_unit[0]])
            else:
                perpendicular = np.array([0, 1])
            
            # Arc offset from direct path (25% of distance)
            offset_distance = distance_2d * 0.25
            
            # Apply curve direction (left = positive, right = negative)
            if curve_direction.lower() == "right":
                offset_distance = -offset_distance
            
            mid_point = (start[:2] + end[:2]) / 2
            curve_offset = mid_point + perpendicular * offset_distance
            
            # Cubic spline for smooth arc
            control_t = [0, 0.5, 1]
            control_x = [start[0], curve_offset[0], end[0]]
            control_y = [start[1], curve_offset[1], end[1]]
            
            cs_x = CubicSpline(control_t, control_x, bc_type="natural")
            cs_y = CubicSpline(control_t, control_y, bc_type="natural")
            
            x_interp = cs_x(t)
            y_interp = cs_y(t)
            
        elif route_style == "spiral":
            # Spiral descent towards destination
            angle = np.arctan2(end[1] - start[1], end[0] - start[0])
            
            # Create spiral effect with decreasing amplitude
            spiral_amplitude = 20 * (1 - t)  # Reduces as approaches destination
            x_interp = start[0] + t * (end[0] - start[0]) + spiral_amplitude * np.sin(6 * np.pi * t) * np.cos(angle)
            y_interp = start[1] + t * (end[1] - start[1]) + spiral_amplitude * np.sin(6 * np.pi * t) * np.sin(angle)
            
        else:  # "direct"
            # Direct linear path
            x_interp = start[0] + t * (end[0] - start[0])
            y_interp = start[1] + t * (end[1] - start[1])
        
        # Z interpolation: rise quickly, cruise, then descend
        z_start = start[2]
        z_end = end[2]
        
        # Bell curve height profile for more realistic altitude variation
        height_variation = 15 * np.sin(np.pi * t) * (1 - (t - 0.5)**2 * 4)
        z_interp = z_start + (z_end - z_start) * t + height_variation
        
        # Combine into route
        route = np.column_stack([x_interp, y_interp, z_interp])
        
        print(f"✓ Generated {route_style} route: {num_points} points")
        print(f"  Start: {route[0]}")
        print(f"  End: {route[-1]}")
        print(f"  Height range: {route[:, 2].min():.1f} - {route[:, 2].max():.1f} m")
        print(f"  Path length: {np.sum(np.linalg.norm(np.diff(route, axis=0), axis=1)):.1f} m")
        
        return route

########################################
# CHANNEL ANALYSIS FUNCTIONS (from height.py)
########################################

def svd_multistream_beamforming(H, num_streams_max=None, beamforming_rank=None):
    """SVD-based multi-stream beamforming (same as height.py)"""
    try:
        H_np = H.numpy() if hasattr(H, 'numpy') else H
        U, S, Vh = np.linalg.svd(H_np, full_matrices=False)
        
        S_threshold = np.max(S) * 1e-5
        S_clamped = np.maximum(S, S_threshold)
        
        max_rank = min(U.shape[1], Vh.shape[0])
        if num_streams_max is not None:
            max_rank = min(max_rank, num_streams_max)
        
        if beamforming_rank == 1:
            active_rank = 1
        else:
            active_rank = max_rank
        
        valid_streams = np.sum(S_clamped > S_threshold)
        
        return Vh.T, S_clamped, U, valid_streams, S_clamped[:active_rank]
        
    except Exception as e:
        print(f"SVD error: {e}")
        traceback.print_exc()
        return None, None, None, 0, np.array([-50.0])

def get_physical_metrics(paths, bandwidth):
    """Extract path loss from Sionna CIR (same as height.py)"""
    try:
        cir_result = paths.cir()
        if isinstance(cir_result, (list, tuple)):
            a = cir_result[0]
        else:
            a = cir_result
        
        if hasattr(a, 'numpy'):
            a_np = a.numpy()
        else:
            a_np = np.array(a)
        
        power_rx_lin = np.sum(np.abs(a_np) ** 2)
        
        tx_power_dbm = 35.0
        power_rx_dbm = 10 * np.log10(power_rx_lin + 1e-12)
        path_loss_db = tx_power_dbm - power_rx_dbm
        path_loss_db = np.clip(path_loss_db, 0, 150)
        
        return path_loss_db, power_rx_lin
        
    except Exception as e:
        print(f"Path loss calc error: {e}")
        return 100.0, 1e-6

def calculate_thermal_noise(bandwidth, nf_db=7.0, temp_k=290):
    """Thermal noise calculation (same as height.py)"""
    k_boltzmann = 1.38064852e-23
    nf_linear = 10 ** (nf_db / 10)
    noise_power = k_boltzmann * temp_k * bandwidth * nf_linear
    return noise_power

def calculate_throughput(sinr_db_array, bandwidth=20e6):
    """Shannon capacity from SINR (same as height.py)"""
    sinr_linear = tf.pow(10.0, sinr_db_array / 10.0)
    capacity_per_stream = tf.math.log(1.0 + sinr_linear) / tf.math.log(2.0)
    total_capacity = tf.reduce_sum(capacity_per_stream)
    throughput = total_capacity * bandwidth
    return throughput

########################################
# MOBILITY ANALYSIS CLASS
########################################

class MobilityAnalysis:
    """Analyze two UAV routes with Sionna ray tracing"""
    
    def __init__(self):
        """Initialize mobility analysis"""
        print("\n" + "="*70)
        print("MOBILITY ANALYSIS - Two Routes Comparison")
        print("="*70)
        
        # Setup Sionna scene
        self.scene = None
        self.tx = None
        self.setup_scene()
        
        # Route storage
        self.route_a = None
        self.route_b = None
        
        # Results storage
        self.results_a = None
        self.results_b = None
        
        # Accumulated RX objects
        self.rx_objects_a = []
        self.rx_objects_b = []
    
    def setup_scene(self):
        """Load and configure Sionna Munich scene"""
        print("\nLoading Sionna Munich scene...")
        try:
            self.scene = load_scene(sionna.rt.scene.munich)
            self.scene.frequency = RFNR_Config.CARRIER_FREQUENCY
            
            # Configure TX array
            self.scene.tx_array = PlanarArray(
                num_rows=MIMO_CONFIG.tx_rows, num_cols=MIMO_CONFIG.tx_cols,
                vertical_spacing=MIMO_CONFIG.spacing,
                horizontal_spacing=MIMO_CONFIG.spacing,
                pattern=MIMO_CONFIG.pattern,
                polarization=MIMO_CONFIG.polarization
            )
            
            # Configure RX array
            self.scene.rx_array = PlanarArray(
                num_rows=MIMO_CONFIG.rx_rows, num_cols=MIMO_CONFIG.rx_cols,
                vertical_spacing=MIMO_CONFIG.spacing,
                horizontal_spacing=MIMO_CONFIG.spacing,
                pattern=MIMO_CONFIG.pattern,
                polarization=MIMO_CONFIG.polarization
            )
            
            # Create transmitter
            gnb_pos = np.array(ScenarioConfig.GNB_POSITION, dtype=np.float32)
            self.tx = Transmitter(name="GNB", position=gnb_pos)
            self.scene.add(self.tx)
            
            print("✓ Scene configured successfully")
            
        except Exception as e:
            print(f"✗ Error loading scene: {e}")
            traceback.print_exc()
            return False
        
        return True
    
    def generate_routes(self, num_points=20, route_style="curved", scenario="default"):
        """
        Generate both routes
        
        Args:
            num_points: Number of waypoints per route
            route_style: "curved", "spiral", or "direct"
            scenario: "default" (different destinations) or "best_route" (same destination, different paths)
        """
        # Select scenario configuration
        if scenario.lower() == "best_route":
            config = ScenarioConfig_BestRoute
            scenario_name = "BEST ROUTE COMPARISON (same dest, different paths)"
        else:
            config = ScenarioConfig
            scenario_name = "ROUTE COMPARISON (different destinations)"
        
        print(f"\n[Scenario: {scenario_name}]")
        print(f"Generating routes ({num_points} points each, style: {route_style})...")
        
        # Route A
        print("\nRoute A:")
        self.route_a = RouteGenerator.generate_route(
            config.ROUTE_A_START,
            config.ROUTE_A_END,
            num_points,
            route_style=route_style,
            curve_direction="left"  # Curve to the left
        )
        
        # Route B
        print("\nRoute B:")
        self.route_b = RouteGenerator.generate_route(
            config.ROUTE_B_START,
            config.ROUTE_B_END,
            num_points,
            route_style=route_style,
            curve_direction="right"  # Curve to the right
        )
    
    def analyze_point(self, position, point_index, route_name=""):
        """
        Analyze channel at a single UAV position
        
        Returns:
            dict with throughput, SNR, path_loss
        """
        try:
            # Create temporary receiver
            rx_name = f"{route_name}_{point_index}"
            rx = Receiver(name=rx_name, position=position)
            self.scene.add(rx)
            
            # Make TX look at RX
            self.tx.look_at(rx)
            
            # Compute paths
            paths = PathSolver()(self.scene)
            
            if paths is None:
                print(f"  ✗ No paths at {route_name}[{point_index}]")
                self.scene.remove(rx_name)
                return None
            
            # Extract channel
            carrier_frequency = RFNR_Config.CARRIER_FREQUENCY
            bandwidth = RFNR_Config.BANDWIDTH
            num_subcarriers = min(RFNR_Config.NUM_SUBCARRIERS, 256)  # Limit for memory
            subcarrier_spacing = RFNR_Config.SUBCARRIER_SPACING
            
            frequencies = tf.linspace(
                carrier_frequency - (num_subcarriers//2) * subcarrier_spacing,
                carrier_frequency + (num_subcarriers//2 - 1) * subcarrier_spacing,
                num_subcarriers
            )
            
            cfr = paths.cfr(frequencies=frequencies, normalize=False, out_type="tf")
            H = tf.reduce_mean(cfr[:, :, :, 0], axis=0)
            H = tf.cast(H, tf.complex64)
            
            # Physical metrics
            path_loss_db, power_rx_lin = get_physical_metrics(paths, bandwidth)
            noise_power = calculate_thermal_noise(bandwidth, nf_db=7.0)
            
            # TX power
            tx_power_dbm = 35.0
            tx_power_w = 10 ** ((tx_power_dbm - 30) / 10)
            
            # SVD beamforming
            V, S_all, U, valid_streams, S_active = svd_multistream_beamforming(
                H, MIMO_CONFIG.max_layers, beamforming_rank=None
            )
            
            # Physical SNR from CIR
            snr_linear_global = power_rx_lin / (noise_power + 1e-15)
            snr_db_global = 10 * np.log10(snr_linear_global + 1e-12)
            
            # Normalize and redistribute via singular values
            sigma_norm = S_active / (np.max(S_active) + 1e-12)
            sigma2_norm = (sigma_norm ** 2) / (np.sum(sigma_norm ** 2) + 1e-12)
            
            sinr_db_svd = snr_db_global + 10 * np.log10(sigma2_norm + 1e-12)
            sinr_db = np.mean(sinr_db_svd)
            
            # Throughput
            throughput = calculate_throughput(
                tf.constant(sinr_db_svd, dtype=tf.float32),
                bandwidth=bandwidth
            ).numpy() / 1e6
            
            # Prepare to keep RX for final render
            result = {
                'position': position,
                'throughput': throughput,
                'snr_db': sinr_db,
                'path_loss': path_loss_db,
                'power_rx_lin': power_rx_lin,
                'rx_object': rx  # Save reference for later render
            }
            
            # Remove from scene temporarily (will add back for final render)
            self.scene.remove(rx_name)
            
            return result
        
        except Exception as e:
            print(f"  ✗ Error analyzing point: {e}")
            try:
                self.scene.remove(rx_name)
            except:
                pass
            return None
    
    def analyze_route(self, route, route_name="A"):
        """
        Analyze entire route (without rendering)
        Accumulates RX objects for final render
        
        Args:
            route: Array of (num_points, 3) waypoints
            route_name: "A" or "B"
        
        Returns:
            results dict with metrics across route
        """
        print(f"\nAnalyzing Route {route_name} ({len(route)} points)...")
        
        throughputs = []
        snrs = []
        path_losses = []
        positions = []
        rx_objects = []
        
        for i, position in enumerate(route):
            print(f"  [{i+1}/{len(route)}] Position: {position}", end=" ... ")
            
            result = self.analyze_point(position, i, f"Route{route_name}")
            
            if result is not None:
                throughputs.append(result['throughput'])
                snrs.append(result['snr_db'])
                path_losses.append(result['path_loss'])
                positions.append(position)
                rx_objects.append(result['rx_object'])
                print(f"✓ TP={result['throughput']:.0f}Mbps SNR={result['snr_db']:.1f}dB")
            else:
                throughputs.append(0)
                snrs.append(-100)
                path_losses.append(150)
                positions.append(position)
                print(f"✗ Failed")
        
        results = {
            'route_name': route_name,
            'positions': np.array(positions),
            'throughputs': np.array(throughputs),
            'snrs': np.array(snrs),
            'path_losses': np.array(path_losses),
            'rx_objects': rx_objects,
            'avg_throughput': np.mean(throughputs),
            'max_throughput': np.max(throughputs),
            'min_throughput': np.min(throughputs),
            'avg_snr': np.mean(snrs),
        }
        
        return results


# ========== PHASE 1 TEST: Route Generation ==========
# ========== PHASE 2 TEST: Single Point Analysis ==========

if __name__ == "__main__":
    import sys
    
    phase = sys.argv[1] if len(sys.argv) > 1 else "full"
    
    if phase == "1":
        print("\n" + "#"*70)
        print("# PHASE 1: ROUTE GENERATION TEST")
        print("#"*70)
        
        # Test route generation
        route_gen = RouteGenerator()
        
        test_route_a = route_gen.generate_route(
            ScenarioConfig.ROUTE_A_START,
            ScenarioConfig.ROUTE_A_END,
            20
        )
        
        test_route_b = route_gen.generate_route(
            ScenarioConfig.ROUTE_B_START,
            ScenarioConfig.ROUTE_B_END,
            20
        )
        
        # Plot routes for verification
        fig = plt.figure(figsize=(14, 6))
        
        # 3D plot
        ax1 = fig.add_subplot(121, projection='3d')
        ax1.plot(test_route_a[:, 0], test_route_a[:, 1], test_route_a[:, 2], 
                 'b-o', linewidth=2, markersize=5, label='Route A')
        ax1.plot(test_route_b[:, 0], test_route_b[:, 1], test_route_b[:, 2],
                 'r-s', linewidth=2, markersize=5, label='Route B')
        
        # Add TX
        gnb_pos = ScenarioConfig.GNB_POSITION
        ax1.scatter(*gnb_pos, s=300, c='green', marker='^', label='gNB', edgecolors='darkgreen', linewidth=2)
        
        ax1.set_xlabel('X [m]')
        ax1.set_ylabel('Y [m]')
        ax1.set_zlabel('Z [m]')
        ax1.set_title('3D Routes')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Height profile
        ax2 = fig.add_subplot(122)
        ax2.plot(range(len(test_route_a)), test_route_a[:, 2], 'b-o', linewidth=2, markersize=5, label='Route A')
        ax2.plot(range(len(test_route_b)), test_route_b[:, 2], 'r-s', linewidth=2, markersize=5, label='Route B')
        ax2.set_xlabel('Waypoint Index')
        ax2.set_ylabel('Height [m]')
        ax2.set_title('Height Profile')
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        
        plt.tight_layout()
        plt.savefig('mobility_routes_test.png', dpi=150, bbox_inches='tight')
        print("\n✓ Saved: mobility_routes_test.png")
        plt.close(fig)
        
        print("\n" + "#"*70)
        print("# PHASE 1 COMPLETE - Routes generated successfully")
        print("#"*70)
    
    elif phase == "2":
        print("\n" + "#"*70)
        print("# PHASE 2: SINGLE POINT ANALYSIS TEST")
        print("#"*70)
        
        mobility = MobilityAnalysis()
        
        # Test with first 3 points of route A
        route_gen = RouteGenerator()
        test_route = route_gen.generate_route(
            ScenarioConfig.ROUTE_A_START,
            ScenarioConfig.ROUTE_A_END,
            20
        )
        
        print("\nTesting first 3 points of Route A:")
        for i in range(3):
            print(f"\nPoint {i}: {test_route[i]}")
            result = mobility.analyze_point(test_route[i], i, "TestRoute")
            if result:
                print(f"  ✓ TP={result['throughput']:.0f}Mbps SNR={result['snr_db']:.1f}dB PL={result['path_loss']:.1f}dB")
            else:
                print(f"  ✗ Failed")
        
        print("\n" + "#"*70)
        print("# PHASE 2 COMPLETE - Single point analysis works")
        print("#"*70)
    
    elif phase == "3":
        print("\n" + "#"*70)
        print("# PHASE 3: COMPLETE ROUTE ANALYSIS (NO RENDER)")
        print("#"*70)
        
        mobility = MobilityAnalysis()
        mobility.generate_routes(num_points=20)
        
        # Analyze Route A
        results_a = mobility.analyze_route(mobility.route_a, route_name="A")
        
        # Print summary
        print(f"\n{'='*70}")
        print(f"ROUTE A SUMMARY")
        print(f"{'='*70}")
        print(f"Points analyzed: {len(results_a['positions'])}")
        print(f"Avg Throughput: {results_a['avg_throughput']:.1f} Mbps")
        print(f"Max Throughput: {results_a['max_throughput']:.1f} Mbps")
        print(f"Min Throughput: {results_a['min_throughput']:.1f} Mbps")
        print(f"Avg SNR: {results_a['avg_snr']:.1f} dB")
        print(f"{'='*70}")
        
        # Plot results
        fig, axes = plt.subplots(2, 1, figsize=(14, 8))
        
        x_axis = range(len(results_a['throughputs']))
        
        # Throughput
        axes[0].plot(x_axis, results_a['throughputs'], 'b-o', linewidth=2, markersize=6, label='Route A')
        axes[0].set_ylabel('Throughput [Mbps]', fontsize=12, fontweight='bold')
        axes[0].set_title('Route A: Throughput vs Waypoint', fontsize=13, fontweight='bold')
        axes[0].grid(True, alpha=0.3)
        axes[0].legend()
        
        # SNR
        axes[1].plot(x_axis, results_a['snrs'], 'r-s', linewidth=2, markersize=6, label='Route A')
        axes[1].set_xlabel('Waypoint Index', fontsize=12, fontweight='bold')
        axes[1].set_ylabel('SNR [dB]', fontsize=12, fontweight='bold')
        axes[1].set_title('Route A: SNR vs Waypoint', fontsize=13, fontweight='bold')
        axes[1].grid(True, alpha=0.3)
        axes[1].legend()
        
        plt.tight_layout()
        plt.savefig('mobility_route_a_analysis.png', dpi=150, bbox_inches='tight')
        print("\n✓ Saved: mobility_route_a_analysis.png")
        plt.close(fig)
        
        print("\n" + "#"*70)
        print("# PHASE 3 COMPLETE - Route analysis works")
        print("#"*70)
    
    elif phase == "4":
        print("\n" + "#"*70)
        print("# PHASE 4: FINAL RENDER TEST (NO RAYS)")
        print("#"*70)
        
        mobility = MobilityAnalysis()
        mobility.generate_routes(num_points=20)
        
        # Analyze Route A and accumulate RX objects
        results_a = mobility.analyze_route(mobility.route_a, route_name="A")
        
        print(f"\nAccumulated {len(results_a['rx_objects'])} RX objects from Route A")
        
        # Now add ALL RX objects back to scene for final render
        print("\nAdding all RX objects to scene for final render...")
        for i, rx_obj in enumerate(results_a['rx_objects']):
            try:
                mobility.scene.add(rx_obj)
                if i % 5 == 0:
                    print(f"  Added RX {i}/{len(results_a['rx_objects'])}")
            except Exception as e:
                print(f"  ✗ Error adding RX {i}: {e}")
        
        print("\nRendering scene with all RX positions...")
        try:
            # Position camera
            cam_pos = [ScenarioConfig.GNB_POSITION[0]+ScenarioConfig.X_OFFSET, ScenarioConfig.GNB_POSITION[1]+ScenarioConfig.Y_OFFSET, ScenarioConfig.CAMERA_HEIGHT]  # Center of route with height
            cam = Camera(position=cam_pos)
            cam.look_at(mobility.tx)
            
            # Render WITHOUT paths (just the scene and RX objects)
            bitmap = mobility.scene.render(camera=cam, paths=None, return_bitmap=True, num_samples=32)
            
            img = np.array(bitmap)
            
            # Convert to uint8
            if img.dtype != np.uint8:
                if np.issubdtype(img.dtype, np.floating):
                    img = (np.clip(img, 0, 1) * 255).astype(np.uint8)
                else:
                    img = img.astype(np.uint8)
            
            # Drop alpha if present
            if len(img.shape) == 3 and img.shape[2] == 4:
                img = img[:, :, :3]
            
            # Save
            fig = plt.figure(figsize=(12, 8))
            plt.imshow(img)
            plt.title('Route A: 3D Render with All RX Positions (No Rays)', fontsize=13, fontweight='bold')
            plt.axis('off')
            plt.tight_layout()
            plt.savefig('mobility_route_a_render.png', dpi=150, bbox_inches='tight')
            print(f"✓ Render saved: {img.shape}")
            plt.close(fig)
            
        except Exception as e:
            print(f"✗ Render error: {e}")
            traceback.print_exc()
        
        print("\n" + "#"*70)
        print("# PHASE 4 COMPLETE - Final render works")
        print("#"*70 + "\n")
    
    if phase == "full" or phase not in ["1", "2", "3", "4"]:
        print("\n" + "#"*70)
        print("# FULL ANALYSIS: Both Routes with Renders and Comparison")
        print("#"*70)
        
        mobility = MobilityAnalysis()
        # ========================================================================
        # CAMBIAR ESCENARIO AQUÍ:
        # - scenario="default"    → Rutas con destinos DIFERENTES
        # - scenario="best_route" → Rutas al MISMO destino, caminos opuestos
        # ========================================================================
        mobility.generate_routes(num_points=20, scenario="best_route")
        
        # Analyze both routes
        print("\n" + "="*70)
        print("ANALYZING BOTH ROUTES")
        print("="*70)
        
        results_a = mobility.analyze_route(mobility.route_a, route_name="A")
        results_b = mobility.analyze_route(mobility.route_b, route_name="B")
        
        # Print summaries
        print(f"\n{'='*70}")
        print(f"ROUTE SUMMARIES")
        print(f"{'='*70}")
        print(f"\nRoute A:")
        print(f"  Avg Throughput: {results_a['avg_throughput']:.1f} Mbps")
        print(f"  Max/Min: {results_a['max_throughput']:.1f} / {results_a['min_throughput']:.1f} Mbps")
        print(f"  Avg SNR: {results_a['avg_snr']:.1f} dB")
        print(f"\nRoute B:")
        print(f"  Avg Throughput: {results_b['avg_throughput']:.1f} Mbps")
        print(f"  Max/Min: {results_b['max_throughput']:.1f} / {results_b['min_throughput']:.1f} Mbps")
        print(f"  Avg SNR: {results_b['avg_snr']:.1f} dB")
        print(f"\nBetter Route: {'A' if results_a['avg_throughput'] > results_b['avg_throughput'] else 'B'}")
        print(f"{'='*70}")
        
        # Generate comparative plots (FIGURE 1)
        print("\nGenerating comparative analysis figure...")
        fig, axes = plt.subplots(2, 2, figsize=(16, 10))
        
        x_axis = range(20)
        
        # Throughput comparison
        axes[0, 0].plot(x_axis, results_a['throughputs'], 'b-o', linewidth=2, markersize=6, label='Route A')
        axes[0, 0].plot(x_axis, results_b['throughputs'], 'r-s', linewidth=2, markersize=6, label='Route B')
        axes[0, 0].set_ylabel('Throughput [Mbps]', fontsize=11, fontweight='bold')
        axes[0, 0].set_title('Throughput vs Waypoint', fontsize=12, fontweight='bold')
        axes[0, 0].grid(True, alpha=0.3)
        axes[0, 0].legend()
        
        # SNR comparison
        axes[0, 1].plot(x_axis, results_a['snrs'], 'b-o', linewidth=2, markersize=6, label='Route A')
        axes[0, 1].plot(x_axis, results_b['snrs'], 'r-s', linewidth=2, markersize=6, label='Route B')
        axes[0, 1].set_ylabel('SNR [dB]', fontsize=11, fontweight='bold')
        axes[0, 1].set_title('SNR vs Waypoint', fontsize=12, fontweight='bold')
        axes[0, 1].grid(True, alpha=0.3)
        axes[0, 1].legend()
        
        # Path Loss comparison
        axes[1, 0].plot(x_axis, results_a['path_losses'], 'b-o', linewidth=2, markersize=6, label='Route A')
        axes[1, 0].plot(x_axis, results_b['path_losses'], 'r-s', linewidth=2, markersize=6, label='Route B')
        axes[1, 0].set_xlabel('Waypoint Index', fontsize=11, fontweight='bold')
        axes[1, 0].set_ylabel('Path Loss [dB]', fontsize=11, fontweight='bold')
        axes[1, 0].set_title('Path Loss vs Waypoint', fontsize=12, fontweight='bold')
        axes[1, 0].grid(True, alpha=0.3)
        axes[1, 0].legend()
        
        # Summary table
        axes[1, 1].axis('off')
        summary_text = f"""
COMPARISON SUMMARY

Route A:
  • Avg TP: {results_a['avg_throughput']:.1f} Mbps
  • Max TP: {results_a['max_throughput']:.1f} Mbps
  • Min TP: {results_a['min_throughput']:.1f} Mbps
  • Avg SNR: {results_a['avg_snr']:.1f} dB
  • Stability: {(results_a['min_throughput']/results_a['max_throughput']*100):.1f}%

Route B:
  • Avg TP: {results_b['avg_throughput']:.1f} Mbps
  • Max TP: {results_b['max_throughput']:.1f} Mbps
  • Min TP: {results_b['min_throughput']:.1f} Mbps
  • Avg SNR: {results_b['avg_snr']:.1f} dB
  • Stability: {(results_b['min_throughput']/results_b['max_throughput']*100):.1f}%

Winner: {'Route A' if results_a['avg_throughput'] > results_b['avg_throughput'] else 'Route B'}
Difference: {abs(results_a['avg_throughput']-results_b['avg_throughput']):.1f} Mbps
        """
        axes[1, 1].text(0.05, 0.95, summary_text, transform=axes[1, 1].transAxes,
                       fontsize=11, verticalalignment='top', fontfamily='monospace',
                       bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
        
        fig.suptitle('Route Comparison: Throughput, SNR, and Path Loss Analysis',
                    fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig('mobility_comparison_analysis.png', dpi=150, bbox_inches='tight')
        print("✓ Saved: mobility_comparison_analysis.png")
        plt.close(fig)
        
        # Generate renders for both routes (FIGURE 2)
        print("\nGenerating 3D renders for both routes...")
        
        renders_created = []
        
        for route_results, route_name, route_color in [(results_a, "A", 'b'), (results_b, "B", 'r')]:
            print(f"\nRendering Route {route_name}...")
            
            # Clear scene and add all RX for this route
            for obj in route_results['rx_objects']:
                try:
                    mobility.scene.add(obj)
                except:
                    pass
            
            try:
                # Position camera: High above, center of route, looking down
                # Calculate center of route positions
                route_positions = np.array(route_results['positions'])
                route_center_xy = np.mean(route_positions[:, :2], axis=0)
                route_center_z = np.mean(route_positions[:, 2])
                
                # Camera positioned high above center, looking down
                cam_height = route_center_z + ScenarioConfig.CAMERA_HEIGHT  # 500m above route center
                #cam_pos = (float(route_center_xy[0]), float(route_center_xy[1]), float(cam_height))
                cam_pos = [ScenarioConfig.GNB_POSITION[0]+ScenarioConfig.X_OFFSET, ScenarioConfig.GNB_POSITION[1]+ScenarioConfig.Y_OFFSET, ScenarioConfig.CAMERA_HEIGHT]

                cam = Camera(position=cam_pos)
                # Look at center of route (from above looking down)
                look_at_point = (float(route_center_xy[0]), float(route_center_xy[1]), float(route_center_z))
                cam.look_at(look_at_point)
                
                # Render without paths
                bitmap = mobility.scene.render(camera=cam, paths=None, return_bitmap=True, num_samples=32)
                img = np.array(bitmap)
                
                # Convert to uint8
                if img.dtype != np.uint8:
                    if np.issubdtype(img.dtype, np.floating):
                        img = (np.clip(img, 0, 1) * 255).astype(np.uint8)
                    else:
                        img = img.astype(np.uint8)
                
                if len(img.shape) == 3 and img.shape[2] == 4:
                    img = img[:, :, :3]
                
                renders_created.append(img)
                print(f"  ✓ Route {route_name} render: {img.shape}")
                
            except Exception as e:
                print(f"  ✗ Render error: {e}")
                renders_created.append(None)
            
            # Remove RX objects for next route
            for obj in route_results['rx_objects']:
                try:
                    mobility.scene.remove(obj.name)
                except:
                    pass
        
        # Create figure with both renders
        if len(renders_created) == 2 and renders_created[0] is not None and renders_created[1] is not None:
            fig = plt.figure(figsize=(16, 6))
            
            ax1 = plt.subplot(121)
            ax1.imshow(renders_created[0])
            ax1.set_title(f'Route A: 3D Scene with All Positions\nAvg TP: {results_a["avg_throughput"]:.0f} Mbps',
                         fontsize=12, fontweight='bold', color='darkblue')
            ax1.axis('off')
            
            ax2 = plt.subplot(122)
            ax2.imshow(renders_created[1])
            ax2.set_title(f'Route B: 3D Scene with All Positions\nAvg TP: {results_b["avg_throughput"]:.0f} Mbps',
                         fontsize=12, fontweight='bold', color='darkred')
            ax2.axis('off')
            
            fig.suptitle('3D Ray Tracing Renders: UAV Routes in Munich Scene',
                        fontsize=14, fontweight='bold', y=0.98)
            plt.tight_layout()
            plt.savefig('mobility_3d_renders.png', dpi=150, bbox_inches='tight')
            print("\n✓ Saved: mobility_3d_renders.png")
            plt.close(fig)
        
        print("\n" + "="*70)
        print("MOBILITY ANALYSIS COMPLETE")
        print("="*70)
        print("Generated files:")
        print("  1. mobility_comparison_analysis.png  (Data comparison)")
        print("  2. mobility_3d_renders.png            (3D scene renders)")
        print("="*70)
