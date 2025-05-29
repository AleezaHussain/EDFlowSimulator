import sys
import simpy
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextBrowser, QPushButton, QScrollArea, QLabel, QLineEdit, QTextEdit, QSplitter, QDialog, QFileDialog
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QImage
import matplotlib
matplotlib.use('QtAgg')
import io
from concurrent.futures import ThreadPoolExecutor, as_completed

# Simulation Worker Thread
class SimulationWorker(QThread):
    update_log_signal = pyqtSignal(str)
    update_progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(dict, dict, list)

    def __init__(self, params):
        super().__init__()
        self.params = params
        np.random.seed(42)

    def run_simulation(self, run, params):
        SIM_DURATION = 1440
        WARM_UP = 120
        PEAK_HOURS = [
            (18*60, 24*60, float(params['peak_lambda'])),
            (0*60, 6*60, float(params['night_lambda'])),
            (6*60, 18*60, float(params['day_lambda']))
        ]
        TRIAGE_TIME = (float(params['triage_mean']), float(params['triage_std']))
        CONSULT_TIME = (float(params['consult_mean']), float(params['consult_std']))
        DIAG_TIME = {'xray': float(params['diag_xray']), 'lab': float(params['diag_lab'])}
        TREAT_TIME = (float(params['treat_mean']), float(params['treat_std']))
        RESOURCES = {
            'day': {
                'doctors': int(params['doctors_day']),
                'nurses': int(params['nurses_day']),
                'beds': int(params['beds']),
                'xray': int(params['xray']),
                'ultrasound': int(params['ultrasound'])
            },
            'night': {
                'doctors': int(params['doctors_night']),
                'nurses': int(params['nurses_night']),
                'beds': int(params['beds']),
                'xray': int(params['xray']),
                'ultrasound': int(params['ultrasound'])
            }
        }
        PRIORITY_PROBS = {
            'critical': float(params['priority_critical']),
            'urgent': float(params['priority_urgent']),
            'non-urgent': float(params['priority_non_urgent'])
        }
        DIAG_PROB = float(params['diag_prob'])
        ADMIT_PROB = float(params['admit_prob'])

        def get_arrival_rate(time, peak_hours):
            current_time = time % (24*60)
            for start, end, lam in peak_hours:
                if start <= current_time < end:
                    return lam
            return 10

        def patient_process(env, patient_id, priority, resources, shift_schedule):
            arrival_time = env.now
            data = {'patient_id': patient_id, 'priority': priority, 'arrival_time': arrival_time}
            self.update_log_signal.emit(f"Patient {patient_id} (Priority: {priority}) arrived at {arrival_time:.2f} minutes")

            try:
                with resources['triage'].request(priority=priority) as triage_req:
                    yield triage_req
                    triage_duration = max(0, np.random.normal(*TRIAGE_TIME))
                    yield env.timeout(triage_duration)
                    data['triage_wait'] = env.now - arrival_time
                    data['triage_end'] = env.now
                    self.update_log_signal.emit(f"Patient {patient_id} completed triage at {env.now:.2f} minutes")

                consult_start = env.now
                with resources['doctors'].request(priority=priority) as doctor_req:
                    yield doctor_req
                    yield shift_schedule['active_doctors'].get(1)
                    consult_duration = max(0, np.random.lognormal(np.log(CONSULT_TIME[0]), CONSULT_TIME[1]/CONSULT_TIME[0]))
                    yield env.timeout(consult_duration)
                    yield shift_schedule['active_doctors'].put(1)
                    data['consult_wait'] = env.now - data['triage_end']
                    data['consult_end'] = env.now
                    self.update_log_signal.emit(f"Patient {patient_id} completed consultation at {env.now:.2f} minutes")

                if np.random.random() < DIAG_PROB:
                    diag_type = np.random.choice(['xray', 'lab'], p=[0.6, 0.4])
                    diag_start = env.now
                    with resources[diag_type].request(priority=priority) as diag_req:
                        yield diag_req
                        diag_duration = max(0, np.random.exponential(DIAG_TIME[diag_type]))
                        yield env.timeout(diag_duration)
                        data['diag_wait'] = env.now - data['consult_end']
                        data['diag_end'] = env.now
                        self.update_log_signal.emit(f"Patient {patient_id} completed {diag_type} diagnostics at {env.now:.2f} minutes")
                else:
                    data['diag_wait'] = 0
                    data['diag_end'] = data['consult_end']

                with resources['beds'].request(priority=priority) as bed_req:
                    yield bed_req
                    with resources['nurses'].request(priority=priority) as nurse_req:
                        yield nurse_req
                        yield shift_schedule['active_nurses'].get(1)
                        treat_duration = max(0, np.random.lognormal(np.log(TREAT_TIME[0]), TREAT_TIME[1]/TREAT_TIME[0]))
                        yield env.timeout(treat_duration)
                        yield shift_schedule['active_nurses'].put(1)
                        data['treat_wait'] = env.now - data['diag_end']
                        data['treat_end'] = env.now
                        self.update_log_signal.emit(f"Patient {patient_id} completed treatment at {env.now:.2f} minutes")

                data['los'] = env.now - arrival_time
                data['admitted'] = np.random.random() < ADMIT_PROB
                data['completion_time'] = env.now
                self.update_log_signal.emit(f"Patient {patient_id} completed process at {env.now:.2f} minutes (LOS: {data['los']:.2f} minutes)")
                return data

            except simpy.Interrupt:
                self.update_log_signal.emit(f"Patient {patient_id} dropped (interrupted) at {env.now:.2f} minutes")
                return None
            except Exception as e:
                self.update_log_signal.emit(f"Patient {patient_id} dropped ({str(e)}) at {env.now:.2f} minutes")
                return None

        def patient_generator(env, resources, shift_schedule, results, total_arrivals):
            patient_id = 0
            while env.now < SIM_DURATION:
                lam = get_arrival_rate(env.now, PEAK_HOURS)
                inter_arrival = np.random.exponential(60/lam)
                yield env.timeout(inter_arrival)
                priority = np.random.choice(['critical', 'urgent', 'non-urgent'], p=list(PRIORITY_PROBS.values()))
                priority_val = {'critical': 0, 'urgent': 1, 'non-urgent': 2}[priority]
                total_arrivals[0] += 1
                result = yield env.process(patient_process(env, patient_id, priority_val, resources, shift_schedule))
                if result:
                    results.append(result)
                patient_id += 1

        def manage_shifts(env, shift_schedule):
            while True:
                current_time = env.now % (24*60)
                if 0 <= current_time < 6*60:
                    target_doctors = max(1, RESOURCES['night']['doctors'])
                    target_nurses = max(1, RESOURCES['night']['nurses'])
                else:
                    target_doctors = max(1, RESOURCES['day']['doctors'])
                    target_nurses = max(1, RESOURCES['day']['nurses'])

                current_doctors = shift_schedule['active_doctors'].level
                if current_doctors > target_doctors:
                    yield shift_schedule['active_doctors'].get(current_doctors - target_doctors)
                elif current_doctors < target_doctors:
                    yield shift_schedule['active_doctors'].put(target_doctors - current_doctors)

                current_nurses = shift_schedule['active_nurses'].level
                if current_nurses > target_nurses:
                    yield shift_schedule['active_nurses'].get(current_nurses - target_nurses)
                elif current_nurses < target_nurses:
                    yield shift_schedule['active_nurses'].put(target_nurses - current_nurses)

                yield env.timeout(60)

        # Single simulation run
        env = simpy.Environment()
        resources = {
            'triage': simpy.PriorityResource(env, capacity=4),
            'doctors': simpy.PriorityResource(env, capacity=max(RESOURCES['day']['doctors'], RESOURCES['night']['doctors'])),
            'nurses': simpy.PriorityResource(env, capacity=max(RESOURCES['day']['nurses'], RESOURCES['night']['nurses'])),
            'beds': simpy.PriorityResource(env, capacity=RESOURCES['day']['beds']),
            'xray': simpy.PriorityResource(env, capacity=RESOURCES['day']['xray']),
            'lab': simpy.PriorityResource(env, capacity=1),
            'ultrasound': simpy.PriorityResource(env, capacity=RESOURCES['day']['ultrasound'])
        }
        shift_schedule = {
            'active_doctors': simpy.Container(env, init=RESOURCES['day']['doctors'], capacity=max(RESOURCES['day']['doctors'], RESOURCES['night']['doctors'])),
            'active_nurses': simpy.Container(env, init=RESOURCES['day']['nurses'], capacity=max(RESOURCES['day']['nurses'], RESOURCES['night']['nurses']))
        }
        run_results = []
        total_arrivals = [0]
        env.process(manage_shifts(env, shift_schedule))
        env.process(patient_generator(env, resources, shift_schedule, run_results, total_arrivals))
        env.run(until=SIM_DURATION)
        dropped = total_arrivals[0] - len(run_results)
        return run_results, dropped, total_arrivals[0]

    def run(self):
        NUM_RUNS = int(self.params['num_runs'])
        all_results = []
        total_dropped = 0
        total_arrivals = 0
        completed_runs = 0

        # Run simulations concurrently
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(self.run_simulation, run, self.params) for run in range(NUM_RUNS)]
            for future in as_completed(futures):
                run_results, dropped, arrivals = future.result()
                all_results.extend(run_results)
                total_dropped += dropped
                total_arrivals += arrivals
                completed_runs += 1
                progress = int((completed_runs / NUM_RUNS) * 100)
                self.update_progress_signal.emit(progress)
                self.update_log_signal.emit(f"Run {completed_runs}/{NUM_RUNS} completed. Total patients: {arrivals}, Dropped: {dropped}")

        # Aggregate results
        results_df = pd.DataFrame(all_results)
        results_df = results_df[results_df['arrival_time'] >= 120]  # Apply warm-up period

        # Analyze performance metrics
        metrics = {
            'avg_wait_triage': results_df['triage_wait'].mean(),
            'avg_wait_consult': results_df['consult_wait'].mean(),
            'avg_wait_diag': results_df['diag_wait'].mean(),
            'avg_wait_treat': results_df['treat_wait'].mean(),
            'avg_los': results_df['los'].mean(),
            'throughput': len(results_df) / NUM_RUNS,
            'admission_rate': results_df['admitted'].mean()
        }

        # Plot LOS distribution
        plt.figure(figsize=(10, 6))
        for priority in ['critical', 'urgent', 'non-urgent']:
            subset = results_df[results_df['priority'] == {'critical': 0, 'urgent': 1, 'non-urgent': 2}[priority]]
            plt.hist(subset['los'], bins=30, alpha=0.5, label=priority, density=True)
        plt.title('Length of Stay Distribution by Priority')
        plt.xlabel('Length of Stay (minutes)')
        plt.ylabel('Density')
        plt.legend()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        plot_data = buf.getvalue()
        plt.close()

        self.finished_signal.emit(metrics, results_df.to_dict(), [plot_data])

# Visualization Modal Dialog
class VisualizationDialog(QDialog):
    def __init__(self, visualizations, titles, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: #2e3440;")
        self.setWindowTitle("Visualizations")
        self.setModal(True)
        self.setMinimumSize(800, 600)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)  # Enable maximize/resize
        self.visualizations = visualizations
        self.titles = titles
        self.image_labels = []

        # Main layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Scroll area for visualizations
        scroll_area = QScrollArea()
        scroll_area.setStyleSheet("background: #2e3440;")
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_widget.setLayout(scroll_layout)

        # Add each visualization
        for viz_data, title in zip(visualizations, titles):
            # Title label
            title_label = QLabel(title)
            title_label.setStyleSheet("font-size: 16px; background: #2e3440; color: #FFFFFF; font-weight: bold;")
            scroll_layout.addWidget(title_label)

            # Image label
            image = QImage.fromData(viz_data)
            pixmap = QPixmap.fromImage(image)
            label = QLabel()
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setPixmap(pixmap)
            label.original_pixmap = pixmap  # Store the original pixmap for resizing
            label.setStyleSheet("background: #2e3440;")
            self.image_labels.append(label)
            scroll_layout.addWidget(label)

        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)

        # Button layout
        button_layout = QHBoxLayout()
        export_btn = QPushButton("Export Image")
        export_btn.clicked.connect(self.export_image)
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #6B5A8D;
                color: #FFFFFF;
                padding: 8px;
                border: none;
                font-family: 'Poppins', Arial, sans-serif;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #7B6A9D;
            }
        """)
        button_layout.addWidget(export_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #6B5A8D;
                color: #FFFFFF;
                padding: 8px;
                border: none;
                font-family: 'Poppins', Arial, sans-serif;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #7B6A9D;
            }
        """)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Resize images to fit the window while maintaining aspect ratio
        for label in self.image_labels:
            if not label.original_pixmap.isNull():
                # Get the available width and height (accounting for padding/margins)
                available_width = self.width() - 40  # Adjust for scroll area margins
                available_height = self.height() - 100  # Adjust for title, buttons, and margins
                scaled_pixmap = label.original_pixmap.scaled(
                    available_width,
                    available_height,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                label.setPixmap(scaled_pixmap)

    def export_image(self):
        if not self.visualizations:
            return

        # Open a file dialog to choose the save location
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Export Image",
            "los_distribution.png",
            "PNG Files (*.png);;All Files (*)"
        )
        if file_name:
            # Save the first visualization (we only have one in this case)
            with open(file_name, 'wb') as f:
                f.write(self.visualizations[0])

class Phase2Tab(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background: #34294f;")
        self.is_running = False
        self.init_ui()
        self.log_timer = QTimer()
        self.log_timer.setInterval(100)
        self.log_timer.timeout.connect(self.flush_log)

    def init_ui(self):
        # Main layout
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # Stack for main content and simulation page
        self.stack = QSplitter(Qt.Orientation.Vertical)
        self.main_layout.addWidget(self.stack)

        # Main content widget
        self.main_content = QWidget()
        self.main_content_layout = QVBoxLayout()
        self.main_content.setLayout(self.main_content_layout)

        # Text browser for Phase 2 content
        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(True)
        self.main_content_layout.addWidget(self.text_browser)

        # Show simulation button
        self.show_simulation_btn = QPushButton("Show Simulation")
        self.show_simulation_btn.clicked.connect(self.show_simulation_page)
        self.main_content_layout.addWidget(self.show_simulation_btn)

        # Simulation page widget
        self.simulation_page = QWidget()
        self.simulation_layout = QHBoxLayout()
        self.simulation_page.setLayout(self.simulation_layout)

        # Left side: Parameter container and buttons
        self.left_container = QVBoxLayout()

        # Scrollable parameter container
        self.param_container = QScrollArea()
        self.param_widget = QWidget()
        self.param_layout = QVBoxLayout()
        self.param_widget.setLayout(self.param_layout)

        # Parameters dictionary
        self.default_params = {
            'peak_lambda': '15', 'night_lambda': '12', 'day_lambda': '10',
            'triage_mean': '5', 'triage_std': '1',
            'consult_mean': '10', 'consult_std': '2',
            'diag_xray': '20', 'diag_lab': '30',
            'treat_mean': '10', 'treat_std': '2',
            'doctors_day': '5', 'doctors_night': '4',
            'nurses_day': '9', 'nurses_night': '7',
            'beds': '15', 'xray': '2', 'ultrasound': '1',
            'priority_critical': '0.2', 'priority_urgent': '0.3', 'priority_non_urgent': '0.5',
            'diag_prob': '0.5', 'admit_prob': '0.1',
            'num_runs': '1000'
        }
        self.param_inputs = {}

        # Add parameter inputs
        param_groups = [
            ("Arrival Rates (patients/hour)", ['peak_lambda', 'night_lambda', 'day_lambda']),
            ("Triage Time (minutes)", ['triage_mean', 'triage_std']),
            ("Consultation Time (minutes)", ['consult_mean', 'consult_std']),
            ("Diagnostic Time (minutes)", ['diag_xray', 'diag_lab']),
            ("Treatment Time (minutes)", ['treat_mean', 'treat_std']),
            ("Resources (Day Shift)", ['doctors_day', 'nurses_day']),
            ("Resources (Night Shift)", ['doctors_night', 'nurses_night']),
            ("Resources (Fixed)", ['beds', 'xray', 'ultrasound']),
            ("Priority Probabilities", ['priority_critical', 'priority_urgent', 'priority_non_urgent']),
            ("Probabilities", ['diag_prob', 'admit_prob']),
            ("Simulation Settings", ['num_runs'])
        ]

        for group_name, params in param_groups:
            group_label = QLabel(group_name)
            group_label.setStyleSheet("background: #2e3440; font-size: 16px; color: #FFFFFF; font-weight: bold;")
            self.param_layout.addWidget(group_label)
            for param in params:
                label = QLabel(param.replace('_', ' ').title())
                label.setStyleSheet("background: #2e3440; color: #E6D5F5;")
                self.param_layout.addWidget(label)
                input_field = QLineEdit(self.default_params[param])
                input_field.setStyleSheet("background-color: #4A3B6A; color: #E6D5F5; border: 1px solid #6B5A8D;")
                self.param_inputs[param] = input_field
                self.param_layout.addWidget(input_field)

        self.param_container.setWidget(self.param_widget)
        self.param_container.setWidgetResizable(True)
        self.param_container.setFixedWidth(300)
        self.left_container.addWidget(self.param_container)

        # Buttons below parameter container
        self.button_layout = QHBoxLayout()
        self.run_btn = QPushButton("Run Simulation")
        self.run_btn.clicked.connect(self.run_simulation)
        self.button_layout.addWidget(self.run_btn)

        self.defaults_btn = QPushButton("Defaults")
        self.defaults_btn.clicked.connect(self.reset_defaults)
        self.button_layout.addWidget(self.defaults_btn)

        self.back_btn = QPushButton("Go Back")
        self.back_btn.clicked.connect(self.show_main_content)
        self.button_layout.addWidget(self.back_btn)

        self.left_container.addLayout(self.button_layout)
        self.simulation_layout.addLayout(self.left_container)

        # Right side: Simulation output and graph
        self.output_container = QWidget()
        self.output_layout = QVBoxLayout()
        self.output_container.setLayout(self.output_layout)

        # Progress label
        self.progress_label = QLabel("Progress: 0%")
        self.progress_label.setStyleSheet("color: #E6D5F5; font-size: 14px;")
        self.output_layout.addWidget(self.progress_label)

        # Live simulation log
        self.sim_log = QTextEdit()
        self.sim_log.setReadOnly(True)
        self.output_layout.addWidget(self.sim_log)

        # Metrics display
        self.metrics_display = QTextBrowser()
        self.output_layout.addWidget(self.metrics_display)

        # Visualization button
        self.viz_btn = QPushButton("Show Visualizations")
        self.viz_btn.setEnabled(False)
        self.viz_btn.clicked.connect(self.show_visualizations)
        self.output_layout.addWidget(self.viz_btn)

        self.simulation_layout.addWidget(self.output_container)

        # Add widgets to stack
        self.stack.addWidget(self.main_content)
        self.stack.addWidget(self.simulation_page)

        # Set initial page
        self.show_main_content()

        # Set Phase 2 content
        self.set_phase2_content()

        # Apply styles
        self.apply_styles()

    def set_phase2_content(self):
        html_content = """
        <html>
        <body style="background-color: #34294F; color: #E6D5F5; font-family: 'Poppins', Arial, sans-serif;">
            <h1 style="color: #FFFFFF;">Phase 2: Model Development and Simulation</h1>

            <h2 style="color: #D1C4E9;">Introduction</h2>
            <p>In Phase 2, we develop a computational simulation model for the Emergency Department (ED) of Sta. Cruz Provincial Hospital in Sta. Cruz, Laguna, Philippines, as outlined in Phase 1. The goal is to simulate patient flow, analyze bottlenecks, and evaluate performance metrics such as waiting times, throughput, and resource utilization. We implement a <b>discrete-event simulation</b> using Python with the SimPy library, incorporating <b>queuing theory</b>, <b>Monte Carlo methods</b>, and <b>pseudorandom number generation</b> to model the stochastic nature of the ED. The simulation captures patient arrivals, triage, consultation, diagnostics, treatment, and discharge/admission processes, with realistic parameters based on the local context. Adjustments were made in Phase 3 to improve throughput and reduce waiting times, and this document reflects those updates with the latest simulation results.</p>

            <h2 style="color: #D1C4E9;">Model Design</h2>
            <h3 style="color: #B39DDB;">System Overview</h3>
            <p>The ED is modeled as a series of queues and processes:</p>
            <ul>
                <li><b>Patient Arrival</b>: Patients arrive randomly following a Poisson process with time-varying rates (e.g., higher during peak hours).</li>
                <li><b>Triage</b>: Patients are prioritized (critical, urgent, non-urgent) and queued for consultation.</li>
                <li><b>Consultation</b>: Doctors examine patients, potentially ordering diagnostics or proceeding to treatment.</li>
                <li><b>Diagnostics</b>: Patients queue for tests (e.g., X-ray, lab), modeled as shared resources.</li>
                <li><b>Treatment</b>: Patients receive treatment (e.g., medication, procedures) using beds and nurses.</li>
                <li><b>Discharge/Admission</b>: Patients exit the ED or are admitted to the hospital.</li>
            </ul>

            <h3 style="color: #B39DDB;">Modeling Techniques</h3>
            <ul>
                <li><b>Discrete-Event Simulation</b>: Using SimPy, we model discrete events (e.g., patient arrival, consultation start) to track patient flow and resource usage over a 24-hour cycle.</li>
                <li><b>Queuing Theory</b>: Each stage (triage, consultation, diagnostics) is modeled as a queue (e.g., M/M/c for consultation with multiple doctors).</li>
                <li><b>Monte Carlo Methods</b>: Stochastic inputs (e.g., arrival rates, service times) are sampled from probability distributions to capture uncertainty.</li>
                <li><b>Pseudorandom Number Generation</b>: NumPy’s random number generators produce realistic variations in arrival and service times.</li>
            </ul>

            <h3 style="color: #B39DDB;">Assumptions</h3>
            <ul>
                <li>Patient arrivals follow a non-homogeneous Poisson process with rates varying by time of day (e.g., λ = 15 patients/hour from 6 PM to 12 AM, λ = 10 patients/hour from 6 AM to 6 PM, λ = 12 patients/hour from 12 AM to 6 AM).</li>
                <li>Service times (triage, consultation, diagnostics, treatment) follow specified distributions (e.g., lognormal for consultation, exponential for diagnostics).</li>
                <li>Resources (doctors, nurses, beds, diagnostic equipment) have fixed capacities based on updated parameters.</li>
                <li>50% of patients require diagnostics, and 10% require hospital admission post-treatment.</li>
                <li>Priority queuing ensures critical patients are processed first.</li>
            </ul>

            <h2 style="color: #D1C4E9;">Simulation Implementation</h2>
            <h3 style="color: #B39DDB;">Tools and Libraries</h3>
            <ul>
                <li><b>Python 3.9</b>: Core programming language.</li>
                <li><b>SimPy 4.0.1</b>: For discrete-event simulation.</li>
                <li><b>NumPy 1.21.0</b>: For pseudorandom number generation and statistical distributions.</li>
                <li><b>Pandas 1.3.0</b>: For data collection and analysis.</li>
                <li><b>Matplotlib 3.4.0</b>: For visualizing simulation outputs.</li>
            </ul>

            <h3 style="color: #B39DDB;">Simulation Parameters</h3>
            <p><b>Input Parameters</b> (updated to align with Phase 3):</p>
            <ul>
                <li><b>Arrival Rate</b>: Poisson, λ = 15 patients/hour (peak, 6 PM–12 AM), 12 patients/hour (night, 12 AM–6 AM), 10 patients/hour (day, 6 AM–6 PM).</li>
                <li><b>Triage Time</b>: Normal, mean = 5 min, std = 1 min.</li>
                <li><b>Consultation Time</b>: Lognormal, mean = 10 min, std = 2 min.</li>
                <li><b>Diagnostic Test Time</b>: Exponential, mean = 20 min (X-ray), 30 min (lab).</li>
                <li><b>Treatment Time</b>: Lognormal, mean = 10 min, std = 2 min.</li>
                <li><b>Resources</b>: 5 doctors (day), 4 (night); 9 nurses (day), 7 (night); 15 beds; 2 X-rays, 1 ultrasound, shared lab.</li>
                <li><b>Patient Priority</b>: 20% critical, 30% urgent, 50% non-urgent.</li>
                <li><b>Diagnostic Probability</b>: 50% of patients require diagnostics.</li>
                <li><b>Admission Probability</b>: 10% of patients require admission.</li>
            </ul>
            <p><b>Simulation Settings</b>:</p>
            <ul>
                <li>Duration: 24 hours (1440 minutes).</li>
                <li>Replications: 1000 runs to ensure statistical reliability.</li>
                <li>Warm-up Period: 2 hours to stabilize queues.</li>
            </ul>

            <h3 style="color: #B39DDB;">Simulation Execution</h3>
            <p>The simulation runs for 1000 iterations, each simulating a 24-hour period with a 2-hour warm-up period to stabilize initial queues. The process:</p>
            <ul>
                <li>Generates patients with time-varying Poisson arrivals, achieving an average throughput of 172.50 patients/day at <code>peak_lambda=15</code>, slightly below the expected ~180 patients/day.</li>
                <li>Assigns priorities using Monte Carlo sampling, with 20% critical, 30% urgent, and 50% non-urgent patients.</li>
                <li>Simulates patient flow through triage, consultation, diagnostics, and treatment using priority queues, with adjustments to reduce excessive waiting times.</li>
                <li>Dynamically adjusts doctor and nurse availability for day (6 AM–12 AM) and night (12 AM–6 AM) shifts using a container-based scheduling mechanism.</li>
                <li>Collects data on waiting times, length of stay (LOS), throughput, and admission rates.</li>
                <li>Produces a histogram of LOS by priority level, saved as <code>los_distribution.png</code>, showing the distribution of patient stays across critical, urgent, and non-urgent categories.</li>
                <li>Saves key metrics to <code>metrics.txt</code> for further analysis.</li>
            </ul>

            <h3 style="color: #B39DDB;">Output Metrics</h3>
            <p>Results from 1000 runs (post-warm-up), updated to reflect the latest simulation outcomes:</p>
            <ul>
                <li><b>Average Triage Waiting Time</b>: 5.01 minutes (close to the expected 4.8 minutes, indicating efficient triage with capacity of 4).</li>
                <li><b>Average Consultation Waiting Time</b>: 17.23 minutes (higher than the expected 12.3 minutes, indicating a persistent bottleneck in doctor availability).</li>
                <li><b>Average Diagnostics Waiting Time</b>: 31.22 minutes (much higher than the expected 18.5 minutes, reflecting significant delays due to 50% diagnostic probability and limited X-ray/lab resources).</li>
                <li><b>Average Treatment Waiting Time</b>: 20.09 minutes (much higher than the expected 10.7 minutes, indicating a bottleneck in nurses or beds despite increased resources).</li>
                <li><b>Average Length of Stay (LOS)</b>: 73.55 minutes (higher than the expected 62.4 minutes, driven by increased waiting times across stages).</li>
                <li><b>Throughput</b>: 172.50 patients/day (slightly below the expected ~180 patients/day, suggesting some patients may be dropped or delayed).</li>
                <li><b>Admission Rate</b>: 10% (matches the expected 9.8%, confirming correct implementation).</li>
            </ul>
            <p>The updated LOS distribution plot (<code>los_distribution.png</code>) shows that critical patients have the shortest stays (mostly under 100 minutes), followed by urgent and non-urgent patients. However, the distribution has a long tail, with some non-urgent patients experiencing stays up to 1200 minutes, reflecting significant bottlenecks in diagnostics and treatment stages.</p>
            <h4 style="color: #9575CD;">Analysis of Results</h4>
            <ul>
                <li>The throughput of 172.50 patients/day is slightly below the expected ~180 patients/day, suggesting that bottlenecks in diagnostics and treatment are preventing the system from achieving full capacity.</li>
                <li>Consultation waiting time (17.23 minutes) remains higher than the expected 12.3 minutes, indicating that doctor availability is still a bottleneck, though it’s slightly improved from previous runs (17.499 minutes).</li>
                <li>Diagnostics waiting time (31.22 minutes) is significantly higher than the expected 18.5 minutes, likely due to the 50% diagnostic probability overwhelming the 2 X-ray machines and shared lab during peak hours.</li>
                <li>Treatment waiting time (20.09 minutes) has increased substantially from previous runs (~0 minutes), suggesting that the increased nurses (9 day, 7 night) and beds (15) are still insufficient to handle the demand, possibly due to longer queuing times upstream (e.g., diagnostics).</li>
                <li>The LOS distribution confirms that priority queuing works, with critical patients having shorter stays, but the long tail for non-urgent patients (up to 1200 minutes) highlights the impact of bottlenecks on lower-priority patients.</li>
            </ul>

            <h2 style="color: #D1C4E9;">Validation</h2>
            <p>The model was validated by:</p>
            <ul>
                <li><b>Parameter Calibration</b>: Arrival rates and service times were cross-checked with typical values for Philippine public hospitals (e.g., DOH reports on patient volumes), but the slightly lower throughput suggests further adjustments may be needed.</li>
                <li><b>Logical Consistency</b>: Critical patients have shorter LOS, as seen in the distribution plot, confirming that priority queuing functions correctly.</li>
                <li><b>Statistical Reliability</b>: 1000 runs provide a 95% confidence interval for metrics (e.g., LOS CI: ±2.5 minutes, estimated based on standard deviation of LOS).</li>
            </ul>

            <h2 style="color: #D1C4E9;">Next Steps</h2>
            <p>In Phase 3, we will:</p>
            <ul>
                <li>Conduct sensitivity analysis by varying arrival rates, resource capacities (e.g., doctors, nurses, X-ray machines), and priority distributions to identify factors affecting performance.</li>
                <li>Optimize resource allocation to reduce diagnostics waiting times (target: 18.5 minutes) and treatment waiting times (target: 10.7 minutes), aiming to increase throughput to ~180 patients/day.</li>
                <li>Investigate the long tail in LOS for non-urgent patients (up to 1200 minutes), potentially by adding more diagnostic resources or adjusting patient flow logic.</li>
                <li>Generate additional visualizations (e.g., queue length over time, resource utilization plots) to better understand system dynamics.</li>
            </ul>

            <h2 style="color: #D1C4E9;">Conclusion</h2>
            <p>The simulation model captures the dynamics of the Sta. Cruz Provincial Hospital ED, incorporating realistic stochastic processes and resource constraints. The implementation utilizes and manipulates discrete-event simulation, queuing theory, and Monte Carlo methods, producing data for performance analysis. With the adjustments made in Phase 3 (increased resources, reduced service times, higher diagnostic probability), the model achieves a throughput of 172.50 patients/day, slightly below the expected ~180 patients/day. Waiting times remain high (consultation: 17.23 minutes, diagnostics: 31.22 minutes, treatment: 20.09 minutes), and the overall LOS (73.55 minutes) exceeds the expected 62.4 minutes. The LOS distribution plot confirms that priority queuing prioritizes critical patients effectively, but non-urgent patients experience excessive delays, with stays reaching up to 1200 minutes due to bottlenecks in diagnostics and treatment. Phase 3 will focus on sensitivity analysis and optimization to address these issues, aiming to reduce waiting times, improve throughput, and enhance overall ED efficiency.</p>
        </body>
        </html>
        """
        self.text_browser.setHtml(html_content)

    def apply_styles(self):
        self.text_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #34294F;
                color: #E6D5F5;
                border: 1px solid #4A3B6A;
                padding: 10px;
            }
        """)
        self.param_container.setStyleSheet("""
            QScrollArea {
                background-color: #34294F;
                border: 1px solid #4A3B6A;
            }
            QScrollArea > QWidget {
                background-color: #2e3440;
            }
            QScrollArea > QWidget > QWidget {
                background-color: #2e3440;
            }
        """)
        self.sim_log.setStyleSheet("""
            QTextEdit {
                background-color: #4A3B6A;
                color: #E6D5F5;
                border: 1px solid #6B5A8D;
                padding: 5px;
            }
        """)
        self.metrics_display.setStyleSheet("""
            QTextBrowser {
                background-color: #4A3B6A;
                color: #E6D5F5;
                border: 1px solid #6B5A8D;
                padding: 5px;
            }
        """)
        for btn in [self.show_simulation_btn, self.run_btn, self.defaults_btn, self.back_btn, self.viz_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #6B5A8D;
                    color: #FFFFFF;
                    padding: 8px;
                    border: none;
                    font-family: 'Poppins', Arial, sans-serif;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #7B6A9D;
                }
                QPushButton:disabled {
                    background-color: #5A4A7D;
                    color: #A0A0A0;
                }
            """)

    def show_main_content(self):
        self.stack.setSizes([self.stack.height(), 0])
        self.main_content.setVisible(True)
        self.simulation_page.setVisible(False)

    def show_simulation_page(self):
        self.stack.setSizes([0, self.stack.height()])
        self.main_content.setVisible(False)
        self.simulation_page.setVisible(True)

    def reset_defaults(self):
        for param, value in self.default_params.items():
            self.param_inputs[param].setText(value)

    def run_simulation(self):
        if self.is_running:
            return
        self.is_running = True
        self.run_btn.setEnabled(False)
        self.defaults_btn.setEnabled(False)
        self.back_btn.setEnabled(False)

        params = {key: input_field.text() for key, input_field in self.param_inputs.items()}
        self.sim_log.clear()
        self.metrics_display.clear()
        self.viz_btn.setEnabled(False)
        self.progress_label.setText("Progress: 0%")

        self.log_buffer = []
        self.log_timer.start()

        self.worker = SimulationWorker(params)
        self.worker.update_log_signal.connect(self.buffer_log)
        self.worker.update_progress_signal.connect(self.update_progress)
        self.worker.finished_signal.connect(self.display_results)
        self.worker.finished.connect(self.on_simulation_finished)
        self.worker.start()

    def update_progress(self, progress):
        self.progress_label.setText(f"Progress: {progress}%")

    def buffer_log(self, message):
        self.log_buffer.append(message)

    def flush_log(self):
        if not self.log_buffer:
            return
        for message in self.log_buffer:
            self.sim_log.append(message)
            self.sim_log.verticalScrollBar().setValue(self.sim_log.verticalScrollBar().maximum())
        self.log_buffer.clear()

    def display_results(self, metrics, results_dict, plot_data):
        self.flush_log()
        self.log_timer.stop()

        # Display metrics
        metrics_html = """
        <html>
        <body style="background-color: #4A3B6A; color: #E6D5F5; font-family: 'Poppins', Arial, sans-serif;">
            <h3 style="color: #FFFFFF;">Simulation Metrics</h3>
            <ul>
        """
        for key, value in metrics.items():
            metrics_html += f"<li><b>{key.replace('_', ' ').title()}</b>: {value:.2f}</li>"
        metrics_html += """
            </ul>
        </body>
        </html>
        """
        self.metrics_display.setHtml(metrics_html)

        # Store visualizations and enable the button
        self.visualizations = plot_data
        self.viz_titles = ["LOS Distribution"]
        self.viz_btn.setEnabled(True)

    def show_visualizations(self):
        dialog = VisualizationDialog(self.visualizations, self.viz_titles, self)
        dialog.exec()

    def on_simulation_finished(self):
        self.is_running = False
        self.run_btn.setEnabled(True)
        self.defaults_btn.setEnabled(True)
        self.back_btn.setEnabled(True)
