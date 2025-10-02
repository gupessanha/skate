import requests
import time
import os
from dotenv import load_dotenv
import numpy as np
import pandas as pd
from collections import deque
import threading
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import queue
import json
from datetime import datetime


class PhyphoxSensorReader:
    """Class to handle sensor data collection from phyphox"""
    
    def __init__(self, url=None, max_buffer_size=1000):
        load_dotenv()
        self.url_phyphox = url or os.getenv('URL_PHYPHOX', 'http://localhost:8080')
        
        self.sensor_types = [
            "gyroX", "gyroY", "gyroZ", "gyro_time",  # gyroscope data
            "accX", "accY", "accZ", "acc_time",  # accelerometer data
            "graX", "graY", "graZ", "graT",  # gravity data
            "lin_accX", "lin_accY", "lin_accZ", "lin_acc_time"  # linear acceleration data
        ]
        
        self.url_get = f"{self.url_phyphox}/get?{'&'.join(self.sensor_types)}"
        
        # Data storage
        self.max_buffer_size = max_buffer_size
        self.data_buffer = deque(maxlen=max_buffer_size)
        self.data_queue = queue.Queue()
        
        # Control flags
        self.is_running = False
        self.collection_thread = None
        
    def parse_sensor_data(self, raw_data):
        """Parse raw JSON data from phyphox into structured format"""
        try:
            # Extract data with safety checks
            def safe_extract(buffer_name, index=0):
                buffer_data = raw_data.get('buffer', {}).get(buffer_name, {}).get('buffer', [])
                return buffer_data[index] if len(buffer_data) > index else 0.0
            
            # Extract all sensor data
            gravity = np.array([
                safe_extract('graX'),
                safe_extract('graY'), 
                safe_extract('graZ')
            ])
            gravity_time = safe_extract('graT')
            
            linear_acc = np.array([
                safe_extract('lin_accX'),
                safe_extract('lin_accY'),
                safe_extract('lin_accZ')
            ])
            linear_acc_time = safe_extract('lin_acc_time')
            
            acceleration = np.array([
                safe_extract('accX'),
                safe_extract('accY'),
                safe_extract('accZ')
            ])
            acc_time = safe_extract('acc_time')
            
            gyroscope = np.array([
                safe_extract('gyroX'),
                safe_extract('gyroY'),
                safe_extract('gyroZ')
            ])
            gyro_time = safe_extract('gyro_time')
            
            return {
                'timestamp': datetime.now(),
                'gravity': {'data': gravity, 'time': gravity_time},
                'linear_acceleration': {'data': linear_acc, 'time': linear_acc_time},
                'acceleration': {'data': acceleration, 'time': acc_time},
                'gyroscope': {'data': gyroscope, 'time': gyro_time}
            }
            
        except Exception as e:
            print(f"Error parsing sensor data: {e}")
            return None
    
    def collect_data(self):
        """Main data collection loop"""
        print("Starting sensor data collection...")
        
        while self.is_running:
            try:
                response = requests.get(self.url_get, timeout=2)
                response.raise_for_status()
                
                raw_data = response.json()
                parsed_data = self.parse_sensor_data(raw_data)
                
                if parsed_data:
                    # Add to buffer and queue
                    self.data_buffer.append(parsed_data)
                    self.data_queue.put(parsed_data)
                    
                    # Print current values
                    self.print_current_data(parsed_data)
                
                time.sleep(0.1)  # 10Hz sampling rate
                
            except requests.exceptions.RequestException as e:
                print(f"\nConnection error: {e}")
                print("Retrying in 2 seconds...")
                time.sleep(2)
            except Exception as e:
                print(f"\nUnexpected error: {e}")
                time.sleep(1)
    
    def print_current_data(self, data):
        """Print current sensor readings"""
        gravity = data['gravity']['data']
        lin_acc = data['linear_acceleration']['data']
        acc = data['acceleration']['data']
        gyro = data['gyroscope']['data']
        
        print(f"\rGrav: [{gravity[0]:6.2f}, {gravity[1]:6.2f}, {gravity[2]:6.2f}] | "
              f"LinAcc: [{lin_acc[0]:6.2f}, {lin_acc[1]:6.2f}, {lin_acc[2]:6.2f}] | "
              f"Acc: [{acc[0]:6.2f}, {acc[1]:6.2f}, {acc[2]:6.2f}] | "
              f"Gyro: [{gyro[0]:6.2f}, {gyro[1]:6.2f}, {gyro[2]:6.2f}]", end='')
    
    def start_collection(self):
        """Start data collection in a separate thread"""
        if not self.is_running:
            self.is_running = True
            self.collection_thread = threading.Thread(target=self.collect_data, daemon=True)
            self.collection_thread.start()
            print("Data collection started")
    
    def stop_collection(self):
        """Stop data collection"""
        self.is_running = False
        if self.collection_thread:
            self.collection_thread.join(timeout=1)
        print("\nData collection stopped")
    
    def get_latest_data(self):
        """Get the most recent sensor reading"""
        return self.data_buffer[-1] if self.data_buffer else None
    
    def get_data_history(self, count=None):
        """Get historical data"""
        if count is None:
            return list(self.data_buffer)
        else:
            return list(self.data_buffer)[-count:]
    
    def export_to_dataframe(self):
        """Export collected data to pandas DataFrame"""
        if not self.data_buffer:
            return pd.DataFrame()
        
        records = []
        for data in self.data_buffer:
            record = {
                'timestamp': data['timestamp'],
                'gravity_x': data['gravity']['data'][0],
                'gravity_y': data['gravity']['data'][1],
                'gravity_z': data['gravity']['data'][2],
                'gravity_time': data['gravity']['time'],
                'lin_acc_x': data['linear_acceleration']['data'][0],
                'lin_acc_y': data['linear_acceleration']['data'][1],
                'lin_acc_z': data['linear_acceleration']['data'][2],
                'lin_acc_time': data['linear_acceleration']['time'],
                'acc_x': data['acceleration']['data'][0],
                'acc_y': data['acceleration']['data'][1],
                'acc_z': data['acceleration']['data'][2],
                'acc_time': data['acceleration']['time'],
                'gyro_x': data['gyroscope']['data'][0],
                'gyro_y': data['gyroscope']['data'][1],
                'gyro_z': data['gyroscope']['data'][2],
                'gyro_time': data['gyroscope']['time']
            }
            records.append(record)
        
        return pd.DataFrame(records)


class SensorPlotter:
    """Class to handle real-time plotting of sensor data"""
    
    def __init__(self, sensor_reader, max_points=100):
        self.sensor_reader = sensor_reader
        self.max_points = max_points
        
        # Initialize data buffers for plotting
        self.gravity_data = {'x': deque(maxlen=max_points), 'y': deque(maxlen=max_points), 'z': deque(maxlen=max_points)}
        self.lin_acc_data = {'x': deque(maxlen=max_points), 'y': deque(maxlen=max_points), 'z': deque(maxlen=max_points)}
        self.acc_data = {'x': deque(maxlen=max_points), 'y': deque(maxlen=max_points), 'z': deque(maxlen=max_points)}
        self.gyro_data = {'x': deque(maxlen=max_points), 'y': deque(maxlen=max_points), 'z': deque(maxlen=max_points)}
        
        # Set up the figure
        self.fig, self.axes = plt.subplots(2, 2, figsize=(14, 10))
        self.fig.suptitle('Real-time Sensor Data from Phyphox', fontsize=16)
        
        # Configure subplots
        self.axes[0,0].set_title('Gravity (m/s²)')
        self.axes[0,1].set_title('Linear Acceleration (m/s²)')
        self.axes[1,0].set_title('Total Acceleration (m/s²)')
        self.axes[1,1].set_title('Gyroscope (rad/s)')
        
        # Set up lines for each axis
        self.lines = {}
        colors = ['red', 'green', 'blue']
        labels = ['X', 'Y', 'Z']
        
        ax_positions = [(0,0), (0,1), (1,0), (1,1)]
        for i, ax_pos in enumerate(ax_positions):
            self.lines[i] = []
            current_ax = self.axes[ax_pos[0], ax_pos[1]]
            for j, (color, label) in enumerate(zip(colors, labels)):
                line, = current_ax.plot([], [], color=color, label=label, linewidth=2)
                self.lines[i].append(line)
            current_ax.legend()
            current_ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
    
    def update_plot_data(self):
        """Update plot data from sensor reader"""
        try:
            # Get new data from queue (non-blocking)
            while not self.sensor_reader.data_queue.empty():
                data = self.sensor_reader.data_queue.get_nowait()
                
                # Add to plot buffers
                gravity = data['gravity']['data']
                self.gravity_data['x'].append(gravity[0])
                self.gravity_data['y'].append(gravity[1])
                self.gravity_data['z'].append(gravity[2])
                
                lin_acc = data['linear_acceleration']['data']
                self.lin_acc_data['x'].append(lin_acc[0])
                self.lin_acc_data['y'].append(lin_acc[1])
                self.lin_acc_data['z'].append(lin_acc[2])
                
                acc = data['acceleration']['data']
                self.acc_data['x'].append(acc[0])
                self.acc_data['y'].append(acc[1])
                self.acc_data['z'].append(acc[2])
                
                gyro = data['gyroscope']['data']
                self.gyro_data['x'].append(gyro[0])
                self.gyro_data['y'].append(gyro[1])
                self.gyro_data['z'].append(gyro[2])
        
        except queue.Empty:
            pass
    
    def animate(self, frame):
        """Animation function for matplotlib"""
        self.update_plot_data()
        
        # Update plots
        datasets = [self.gravity_data, self.lin_acc_data, self.acc_data, self.gyro_data]
        
        for i, data_dict in enumerate(datasets):
            if len(data_dict['x']) > 0:
                x_range = range(len(data_dict['x']))
                
                self.lines[i][0].set_data(x_range, list(data_dict['x']))
                self.lines[i][1].set_data(x_range, list(data_dict['y']))
                self.lines[i][2].set_data(x_range, list(data_dict['z']))
                
                # Auto-scale axes
                ax = self.axes.flat[i]
                ax.relim()
                ax.autoscale_view()
        
        return [line for line_group in self.lines.values() for line in line_group]
    
    def start_plotting(self, interval=50):
        """Start the real-time plotting"""
        self.animation = FuncAnimation(self.fig, self.animate, interval=interval, blit=False)
        plt.show()
    
    def save_plot(self, filename):
        """Save the current plot"""
        self.fig.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"Plot saved as {filename}")


def main():
    """Main function to run the sensor data collection and plotting"""
    print("Phyphox Sensor Data Collector and Plotter")
    print("==========================================")
    print("Make sure phyphox is running with remote access enabled.")
    print("Press Ctrl+C to stop.\n")
    
    # Create sensor reader and plotter
    sensor_reader = PhyphoxSensorReader()
    plotter = SensorPlotter(sensor_reader)
    
    try:
        # Start data collection
        sensor_reader.start_collection()
        
        # Start plotting (this will block until window is closed)
        plotter.start_plotting()
        
    except KeyboardInterrupt:
        print("\nStopping data collection...")
    
    finally:
        # Clean up
        sensor_reader.stop_collection()
        
        # Export data to CSV
        df = sensor_reader.export_to_dataframe()
        if not df.empty:
            filename = f"sensor_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(filename, index=False)
            print(f"Data exported to {filename}")
            print(f"Total samples collected: {len(df)}")


if __name__ == "__main__":
    main()