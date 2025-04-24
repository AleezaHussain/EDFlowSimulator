import sys
import simpy
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextBrowser, QPushButton, QScrollArea, QLabel, QLineEdit, QTextEdit, QSplitter, QComboBox, QDialog, QTabWidget, QFileDialog
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QPixmap, QImage
import matplotlib
matplotlib.use('QtAgg')
import io
from itertools import product
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Sensitivity Analysis Worker Thread
class SensitivityWorker(QThread):
    update_log_signal = pyqtSignal(str)
    update_progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(list, list, list, list)

    def __init__(self, params):
        super().__init__()
        self.params = params
        np.random.seed(42)

    def run_simulation(self, run, lam, doc_day, doc_night, xray, crit):
        SIM_DURATION = 1440
        WARM_UP = 120
        PEAK_HOURS = [(18*60, 24*60, lam), (0*60, 6*60, 12), (6*60, 18*60, 10)]
        TRIAGE_TIME = (5, 1)
        CONSULT_TIME = (10, 2)
        DIAG_TIME = {'xray': 20, 'lab': 30}
        TREAT_TIME = (10, 2)
        PRIORITY_PROBS = {'critical': crit, 'urgent': (1-crit)*0.375, 'non-urgent': (1-crit)*0.625}
        DIAG_PROB = 0.5
        ADMIT_PROB = 0.1

        def get_arrival_rate(time, peak_lambda):
            current_time = time % (24*60)
            if 18*60 <= current_time < 24*60:
                return peak_lambda
            elif 0*60 <= current_time < 6*60:
                return 12
            else:
                return 10

        def patient_process(env, patient_id, priority, resources, shift_schedule, doctor_usage, xray_usage, results, dropped_patients, completed_patients_log):
            arrival_time = env.now
            data = {'patient_id': patient_id, 'priority': priority, 'arrival_time': arrival_time}
            self.update_log_signal.emit(f"Patient {patient_id} (Priority: {priority}) arrived at {arrival_time:.2f} minutes")
            time.sleep(0.01)

            try:
                with resources['triage'].request(priority=priority) as triage_req:
                    yield triage_req
                    triage_duration = max(0, np.random.normal(*TRIAGE_TIME))
                    yield env.timeout(triage_duration)
                    data['triage_wait'] = env.now - arrival_time
                    data['triage_end'] = env.now
                    self.update_log_signal.emit(f"Patient {patient_id} completed triage at {env.now:.2f} minutes")
                    time.sleep(0.01)

                consult_start = env.now
                with resources['doctors'].request(priority=priority) as doctor_req:
                    yield doctor_req
                    yield shift_schedule['active_doctors'].get(1)
                    consult_duration = max(0, np.random.lognormal(np.log(CONSULT_TIME[0]), CONSULT_TIME[1]/CONSULT_TIME[0]))
                    yield env.timeout(consult_duration)
                    yield shift_schedule['active_doctors'].put(1)
                    data['consult_wait'] = env.now - data['triage_end']
                    data['consult_end'] = env.now
                    doctor_usage.append((consult_start, env.now, consult_duration))
                    self.update_log_signal.emit(f"Patient {patient_id} completed consultation at {env.now:.2f} minutes")
                    time.sleep(0.01)

                if np.random.random() < DIAG_PROB:
                    diag_type = np.random.choice(['xray', 'lab'], p=[0.6, 0.4])
                    diag_start = env.now
                    with resources[diag_type].request(priority=priority) as diag_req:
                        yield diag_req
                        diag_duration = max(0, np.random.exponential(DIAG_TIME[diag_type]))
                        yield env.timeout(diag_duration)
                        data['diag_wait'] = env.now - data['consult_end']
                        data['diag_end'] = env.now
                        if diag_type == 'xray':
                            xray_usage.append((diag_start, env.now, diag_duration))
                        self.update_log_signal.emit(f"Patient {patient_id} completed {diag_type} diagnostics at {env.now:.2f} minutes")
                        time.sleep(0.01)
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
                        time.sleep(0.01)

                data['los'] = env.now - arrival_time
                data['admitted'] = np.random.random() < ADMIT_PROB
                data['completion_time'] = env.now
                results.append(data)
                completed_patients_log.append({'patient_id': patient_id, 'completion_time': env.now})
                self.update_log_signal.emit(f"Patient {patient_id} completed process at {env.now:.2f} minutes (LOS: {data['los']:.2f} minutes)")
                time.sleep(0.01)

            except simpy.Interrupt:
                dropped_patients.append({'patient_id': patient_id, 'stage': 'interrupted', 'time': env.now})
                self.update_log_signal.emit(f"Patient {patient_id} dropped (interrupted) at {env.now:.2f} minutes")
                time.sleep(0.01)
            except Exception as e:
                dropped_patients.append({'patient_id': patient_id, 'stage': str(e), 'time': env.now})
                self.update_log_signal.emit(f"Patient {patient_id} dropped ({str(e)}) at {env.now:.2f} minutes")
                time.sleep(0.01)

        def patient_generator(env, resources, shift_schedule, peak_lambda, critical_prob, doctor_usage, xray_usage, results, dropped_patients, completed_patients_log, total_arrivals):
            patient_id = 0
            priority_probs = {'critical': critical_prob, 'urgent': (1-critical_prob)*0.375, 'non-urgent': (1-critical_prob)*0.625}
            while env.now < SIM_DURATION:
                lam = get_arrival_rate(env.now, peak_lambda)
                inter_arrival = np.random.exponential(60/lam)
                yield env.timeout(inter_arrival)
                priority = np.random.choice(['critical', 'urgent', 'non-urgent'], p=list(priority_probs.values()))
                priority_val = {'critical': 0, 'urgent': 1, 'non-urgent': 2}[priority]
                total_arrivals[0] += 1
                env.process(patient_process(env, patient_id, priority_val, resources, shift_schedule, doctor_usage, xray_usage, results, dropped_patients, completed_patients_log))
                patient_id += 1

        def manage_shifts(env, shift_schedule, doctors_day, doctors_night):
            while True:
                current_time = env.now % (24*60)
                if 0 <= current_time < 6*60:
                    target_doctors = max(1, doctors_night)
                    target_nurses = max(1, 7)
                else:
                    target_doctors = max(1, doctors_day)
                    target_nurses = max(1, 9)

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

        results = []
        dropped_patients = []
        completed_patients_log = []
        total_arrivals = [0]
        doctor_usage = []
        xray_usage = []

        env = simpy.Environment()
        resources = {
            'triage': simpy.PriorityResource(env, capacity=4),
            'doctors': simpy.PriorityResource(env, capacity=max(doc_day, doc_night)),
            'nurses': simpy.PriorityResource(env, capacity=max(9, 7)),
            'beds': simpy.PriorityResource(env, capacity=15),
            'xray': simpy.PriorityResource(env, capacity=xray),
            'lab': simpy.PriorityResource(env, capacity=1),
            'ultrasound': simpy.PriorityResource(env, capacity=1)
        }
        shift_schedule = {
            'active_doctors': simpy.Container(env, init=doc_day, capacity=max(doc_day, doc_night)),
            'active_nurses': simpy.Container(env, init=9, capacity=max(9, 7))
        }
        env.process(manage_shifts(env, shift_schedule, doc_day, doc_night))
        env.process(patient_generator(env, resources, shift_schedule, lam, crit, doctor_usage, xray_usage, results, dropped_patients, completed_patients_log, total_arrivals))
        env.run(until=SIM_DURATION)

        return results, dropped_patients, completed_patients_log, total_arrivals, doctor_usage, xray_usage

    def run(self):
        SIM_DURATION = 1440
        WARM_UP = 120
        NUM_RUNS = 10
        ARRIVAL_RATES = [5, 10, 15, 20] if self.params['vary_arrival'] else [float(self.params['peak_lambda'])]
        DOCTORS_DAY = [3, 4, 5] if self.params['vary_doctors'] else [int(self.params['doctors_day'])]
        DOCTORS_NIGHT = [2, 3, 4] if self.params['vary_doctors'] else [int(self.params['doctors_night'])]
        XRAY_UNITS = [1, 2, 3] if self.params['vary_xray'] else [int(self.params['xray_units'])]
        CRITICAL_PROBS = [0.1, 0.2, 0.3] if self.params['vary_critical'] else [float(self.params['critical_prob'])]

        def calculate_utilization(usage_list, total_time, shift_schedule, resource_type, xray_capacity=None):
            total_busy_time = 0
            for start, end, duration in usage_list:
                if start >= WARM_UP and end <= total_time:
                    total_busy_time += duration

            if resource_type in ['doctors', 'nurses']:
                resource_time = 0
                for t in range(int(WARM_UP), int(total_time), 1):
                    current_time = t % (24*60)
                    if 0 <= current_time < 6*60:
                        num_resources = max(1, shift_schedule[f'active_{resource_type}'].capacity if t == WARM_UP else shift_schedule[f'active_{resource_type}'].level)
                    else:
                        num_resources = max(1, shift_schedule[f'active_{resource_type}'].capacity if t == WARM_UP else shift_schedule[f'active_{resource_type}'].level)
                    resource_time += num_resources
            elif resource_type == 'xray':
                resource_time = xray_capacity * (total_time - WARM_UP)

            return (total_busy_time / resource_time) * 100 if resource_time > 0 else 0

        sensitivity_results = []
        combinations = list(product(ARRIVAL_RATES, DOCTORS_DAY, DOCTORS_NIGHT, XRAY_UNITS, CRITICAL_PROBS))
        total_combinations = len(combinations)
        total_runs = total_combinations * NUM_RUNS
        completed_runs = 0

        for idx, (lam, doc_day, doc_night, xray, crit) in enumerate(combinations):
            all_results = []
            all_dropped = []
            all_completed = []
            total_arrivals = [0]
            all_doctor_usage = []
            all_xray_usage = []

            # Run simulations concurrently with ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=20) as executor:
                futures = [executor.submit(self.run_simulation, run, lam, doc_day, doc_night, xray, crit) for run in range(NUM_RUNS)]
                for future in as_completed(futures):
                    results, dropped, completed, arrivals, doctor_usage, xray_usage = future.result()
                    all_results.extend(results)
                    all_dropped.extend(dropped)
                    all_completed.extend(completed)
                    total_arrivals[0] += arrivals[0]
                    all_doctor_usage.extend(doctor_usage)
                    all_xray_usage.extend(xray_usage)
                    completed_runs += 1
                    progress = int((completed_runs / total_runs) * 100)
                    self.update_progress_signal.emit(progress)
                    self.update_log_signal.emit(f"Run {len(all_completed)}/{NUM_RUNS} for lambda={lam}, doctors={doc_day}/{doc_night}, xray={xray}, critical={crit}")

            # Create shift_schedule for utilization calculation
            env = simpy.Environment()
            shift_schedule = {
                'active_doctors': simpy.Container(env, init=doc_day, capacity=max(doc_day, doc_night)),
                'active_nurses': simpy.Container(env, init=9, capacity=max(9, 7))
            }
            env.run(until=SIM_DURATION)

            df = pd.DataFrame(all_results)
            df_completed = df[df['completion_time'] >= WARM_UP]
            throughput = len(all_completed) / NUM_RUNS
            doctor_util = calculate_utilization(all_doctor_usage, SIM_DURATION, shift_schedule, 'doctors')
            xray_util = calculate_utilization(all_xray_usage, SIM_DURATION, shift_schedule, 'xray', xray_capacity=xray)

            sensitivity_results.append({
                'peak_lambda': lam,
                'doctors_day': doc_day,
                'doctors_night': doc_night,
                'xray_units': xray,
                'critical_prob': crit,
                'avg_los': df_completed['los'].mean() if not df_completed.empty else 0,
                'avg_consult_wait': df_completed['consult_wait'].mean() if not df_completed.empty else 0,
                'avg_diag_wait': df_completed['diag_wait'].mean() if not df_completed.empty else 0,
                'throughput': throughput,
                'doctor_util': doctor_util,
                'xray_util': xray_util
            })

        # Generate plots in the background
        sensitivity_df = pd.DataFrame(sensitivity_results)

        # Arrival Rate Sensitivity Plot
        arrival_sensitivity = sensitivity_df[sensitivity_df['peak_lambda'].isin(ARRIVAL_RATES)]
        arrival_sensitivity = arrival_sensitivity.groupby('peak_lambda').mean().reset_index()
        plt.figure(figsize=(8, 6))
        plt.plot(arrival_sensitivity['peak_lambda'], arrival_sensitivity['avg_los'], 'o-', label='Avg LOS')
        plt.plot(arrival_sensitivity['peak_lambda'], arrival_sensitivity['avg_consult_wait'], 's-', label='Avg Consult Wait')
        plt.plot(arrival_sensitivity['peak_lambda'], arrival_sensitivity['avg_diag_wait'], '^-', label='Avg Diag Wait')
        plt.plot(arrival_sensitivity['peak_lambda'], arrival_sensitivity['throughput'], 'd-', label='Throughput')
        plt.xlabel('Peak Arrival Rate')
        plt.ylabel('Time (min) / Throughput')
        plt.title('Arrival Rate Sensitivity')
        plt.legend()
        plt.grid(True)
        buf1 = io.BytesIO()
        plt.savefig(buf1, format='png', dpi=100)
        buf1.seek(0)
        plt.close()

        # LOS Heatmap
        heatmap_data = sensitivity_df[sensitivity_df['doctors_day'].isin(DOCTORS_DAY) & (sensitivity_df['peak_lambda'].isin(ARRIVAL_RATES))]
        heatmap_data = pd.pivot_table(heatmap_data, values='avg_los', index='peak_lambda', columns='doctors_day')
        plt.figure(figsize=(8, 6))
        plt.imshow(heatmap_data, cmap='viridis', interpolation='nearest')
        plt.colorbar(label='Avg LOS (min)')
        plt.xticks(range(len(DOCTORS_DAY)), DOCTORS_DAY)
        plt.yticks(range(len(ARRIVAL_RATES)), ARRIVAL_RATES)
        plt.xlabel('Doctors (Day)')
        plt.ylabel('Peak Arrival Rate')
        plt.title('LOS Heatmap')
        buf2 = io.BytesIO()
        plt.savefig(buf2, format='png', dpi=100)
        buf2.seek(0)
        plt.close()

        # Resource Utilization Plot
        plt.figure(figsize=(8, 6))
        plt.plot(arrival_sensitivity['peak_lambda'], arrival_sensitivity['doctor_util'], 'o-', label='Doctor Util')
        plt.plot(arrival_sensitivity['peak_lambda'], arrival_sensitivity['xray_util'], 's-', label='X-ray Util')
        plt.xlabel('Peak Arrival Rate')
        plt.ylabel('Utilization (%)')
        plt.title('Resource Utilization')
        plt.legend()
        plt.grid(True)
        buf3 = io.BytesIO()
        plt.savefig(buf3, format='png', dpi=100)
        buf3.seek(0)
        plt.close()

        self.finished_signal.emit(sensitivity_results, [buf1.getvalue()], [buf2.getvalue()], [buf3.getvalue()])

# Optimization Worker Thread (unchanged for now, as the focus is on sensitivity analysis)
class OptimizationWorker(QThread):
    update_log_signal = pyqtSignal(str)
    update_progress_signal = pyqtSignal(int)
    finished_signal = pyqtSignal(list, list)

    def __init__(self, config):
        super().__init__()
        self.config = config
        np.random.seed(42)

    def run(self):
        SIM_DURATION = 1440
        WARM_UP = 120
        NUM_RUNS = 10
        PEAK_HOURS = [(18*60, 24*60, 15), (0*60, 6*60, 12), (6*60, 18*60, 10)]
        TRIAGE_TIME = (5, 1)
        CONSULT_TIME = (10, 2)
        DIAG_TIME = {'xray': 20, 'lab': 30}
        TREAT_TIME = (10, 2)
        PRIORITY_PROBS = {'critical': 0.2, 'urgent': 0.3, 'non-urgent': 0.5}
        DIAG_PROB = 0.5
        ADMIT_PROB = 0.1

        CONFIGS = [
            {'doctors_day': 5, 'doctors_night': 4, 'xray': 2, 'name': 'Baseline'},
            {'doctors_day': 4, 'doctors_night': 3, 'xray': 2, 'name': 'Config 1'},
            {'doctors_day': 5, 'doctors_night': 4, 'xray': 1, 'name': 'Config 2'},
            {'doctors_day': 5, 'doctors_night': 4, 'xray': 3, 'name': 'Config 3'}
        ]

        selected_config = CONFIGS[self.config]

        def get_arrival_rate(time, peak_lambda):
            current_time = time % (24*60)
            if 18*60 <= current_time < 24*60:
                return peak_lambda
            elif 0*60 <= current_time < 6*60:
                return 12
            else:
                return 10

        def patient_process(env, patient_id, priority, resources, shift_schedule, doctor_usage, xray_usage, results, dropped_patients, completed_patients_log):
            arrival_time = env.now
            data = {'patient_id': patient_id, 'priority': priority, 'arrival_time': arrival_time}
            self.update_log_signal.emit(f"Patient {patient_id} (Priority: {priority}) arrived at {arrival_time:.2f} minutes")
            time.sleep(0.01)

            try:
                with resources['triage'].request(priority=priority) as triage_req:
                    yield triage_req
                    triage_duration = max(0, np.random.normal(*TRIAGE_TIME))
                    yield env.timeout(triage_duration)
                    data['triage_wait'] = env.now - arrival_time
                    data['triage_end'] = env.now
                    self.update_log_signal.emit(f"Patient {patient_id} completed triage at {env.now:.2f} minutes")
                    time.sleep(0.01)

                consult_start = env.now
                with resources['doctors'].request(priority=priority) as doctor_req:
                    yield doctor_req
                    yield shift_schedule['active_doctors'].get(1)
                    consult_duration = max(0, np.random.lognormal(np.log(CONSULT_TIME[0]), CONSULT_TIME[1]/CONSULT_TIME[0]))
                    yield env.timeout(consult_duration)
                    yield shift_schedule['active_doctors'].put(1)
                    data['consult_wait'] = env.now - data['triage_end']
                    data['consult_end'] = env.now
                    doctor_usage.append((consult_start, env.now, consult_duration))
                    self.update_log_signal.emit(f"Patient {patient_id} completed consultation at {env.now:.2f} minutes")
                    time.sleep(0.01)

                if np.random.random() < DIAG_PROB:
                    diag_type = np.random.choice(['xray', 'lab'], p=[0.6, 0.4])
                    diag_start = env.now
                    with resources[diag_type].request(priority=priority) as diag_req:
                        yield diag_req
                        diag_duration = max(0, np.random.exponential(DIAG_TIME[diag_type]))
                        yield env.timeout(diag_duration)
                        data['diag_wait'] = env.now - data['consult_end']
                        data['diag_end'] = env.now
                        if diag_type == 'xray':
                            xray_usage.append((diag_start, env.now, diag_duration))
                        self.update_log_signal.emit(f"Patient {patient_id} completed {diag_type} diagnostics at {env.now:.2f} minutes")
                        time.sleep(0.01)
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
                        time.sleep(0.01)

                data['los'] = env.now - arrival_time
                data['admitted'] = np.random.random() < ADMIT_PROB
                data['completion_time'] = env.now
                results.append(data)
                completed_patients_log.append({'patient_id': patient_id, 'completion_time': env.now})
                self.update_log_signal.emit(f"Patient {patient_id} completed process at {env.now:.2f} minutes (LOS: {data['los']:.2f} minutes)")
                time.sleep(0.01)

            except simpy.Interrupt:
                dropped_patients.append({'patient_id': patient_id, 'stage': 'interrupted', 'time': env.now})
                self.update_log_signal.emit(f"Patient {patient_id} dropped (interrupted) at {env.now:.2f} minutes")
                time.sleep(0.01)
            except Exception as e:
                dropped_patients.append({'patient_id': patient_id, 'stage': str(e), 'time': env.now})
                self.update_log_signal.emit(f"Patient {patient_id} dropped ({str(e)}) at {env.now:.2f} minutes")
                time.sleep(0.01)

        def patient_generator(env, resources, shift_schedule, peak_lambda, critical_prob, doctor_usage, xray_usage, results, dropped_patients, completed_patients_log, total_arrivals):
            patient_id = 0
            priority_probs = {'critical': critical_prob, 'urgent': (1-critical_prob)*0.375, 'non-urgent': (1-critical_prob)*0.625}
            while env.now < SIM_DURATION:
                lam = get_arrival_rate(env.now, peak_lambda)
                inter_arrival = np.random.exponential(60/lam)
                yield env.timeout(inter_arrival)
                priority = np.random.choice(['critical', 'urgent', 'non-urgent'], p=list(priority_probs.values()))
                priority_val = {'critical': 0, 'urgent': 1, 'non-urgent': 2}[priority]
                total_arrivals[0] += 1
                env.process(patient_process(env, patient_id, priority_val, resources, shift_schedule, doctor_usage, xray_usage, results, dropped_patients, completed_patients_log))
                patient_id += 1

        def manage_shifts(env, shift_schedule, doctors_day, doctors_night):
            while True:
                current_time = env.now % (24*60)
                if 0 <= current_time < 6*60:
                    target_doctors = max(1, doctors_night)
                    target_nurses = max(1, 7)
                else:
                    target_doctors = max(1, doctors_day)
                    target_nurses = max(1, 9)

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

        def calculate_utilization(usage_list, total_time, shift_schedule, resource_type, xray_capacity=None):
            total_busy_time = 0
            for start, end, duration in usage_list:
                if start >= WARM_UP and end <= total_time:
                    total_busy_time += duration

            if resource_type in ['doctors', 'nurses']:
                resource_time = 0
                for t in range(int(WARM_UP), int(total_time), 1):
                    current_time = t % (24*60)
                    if 0 <= current_time < 6*60:
                        num_resources = max(1, shift_schedule[f'active_{resource_type}'].capacity if t == WARM_UP else shift_schedule[f'active_{resource_type}'].level)
                    else:
                        num_resources = max(1, shift_schedule[f'active_{resource_type}'].capacity if t == WARM_UP else shift_schedule[f'active_{resource_type}'].level)
                    resource_time += num_resources
            elif resource_type == 'xray':
                resource_time = xray_capacity * (total_time - WARM_UP)

            return (total_busy_time / resource_time) * 100 if resource_time > 0 else 0

        optimization_results = []
        for idx, config in enumerate([selected_config]):
            results = []
            dropped_patients = []
            completed_patients_log = []
            total_arrivals = [0]
            total_completed = 0

            for run in range(NUM_RUNS):
                doctor_usage = []
                xray_usage = []
                env = simpy.Environment()
                resources = {
                    'triage': simpy.PriorityResource(env, capacity=4),
                    'doctors': simpy.PriorityResource(env, capacity=max(config['doctors_day'], config['doctors_night'])),
                    'nurses': simpy.PriorityResource(env, capacity=max(9, 7)),
                    'beds': simpy.PriorityResource(env, capacity=15),
                    'xray': simpy.PriorityResource(env, capacity=config['xray']),
                    'lab': simpy.PriorityResource(env, capacity=1),
                    'ultrasound': simpy.PriorityResource(env, capacity=1)
                }
                shift_schedule = {
                    'active_doctors': simpy.Container(env, init=config['doctors_day'], capacity=max(config['doctors_day'], config['doctors_night'])),
                    'active_nurses': simpy.Container(env, init=9, capacity=max(9, 7))
                }
                env.process(manage_shifts(env, shift_schedule, config['doctors_day'], config['doctors_night']))
                env.process(patient_generator(env, resources, shift_schedule, 15, 0.2, doctor_usage, xray_usage, results, dropped_patients, completed_patients_log, total_arrivals))
                env.run(until=SIM_DURATION)
                total_completed += len(completed_patients_log)
                self.update_log_signal.emit(f"Run {run + 1}/{NUM_RUNS} for {config['name']}")
                progress = int(((run + 1) / NUM_RUNS) * 100)
                self.update_progress_signal.emit(progress)

            df = pd.DataFrame(results)
            df_completed = df[df['completion_time'] >= WARM_UP]
            throughput = total_completed / NUM_RUNS
            doctor_util = calculate_utilization(doctor_usage, SIM_DURATION, shift_schedule, 'doctors')
            xray_util = calculate_utilization(xray_usage, SIM_DURATION, shift_schedule, 'xray', xray_capacity=config['xray'])

            critical_df = df_completed[df_completed['priority'] == 0]
            critical_los = critical_df['los'].mean() if not critical_df.empty else 0

            optimization_results.append({
                'config': config['name'],
                'avg_los': df_completed['los'].mean() if not df_completed.empty else 0,
                'avg_consult_wait': df_completed['consult_wait'].mean() if not df_completed.empty else 0,
                'avg_diag_wait': df_completed['diag_wait'].mean() if not df_completed.empty else 0,
                'throughput': throughput,
                'doctor_util': doctor_util,
                'xray_util': xray_util,
                'critical_los': critical_los
            })

        # Generate bar plot
        optimization_df = pd.DataFrame(optimization_results)
        plt.figure(figsize=(8, 6))
        plt.bar(optimization_df['config'], optimization_df['avg_los'], alpha=0.5, label='Avg LOS')
        plt.bar(optimization_df['config'], optimization_df['throughput'], alpha=0.5, label='Throughput', bottom=optimization_df['avg_los'])
        plt.ylabel('Time (min) / Throughput')
        plt.title('LOS and Throughput')
        plt.legend()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100)
        buf.seek(0)
        plt.close()

        self.finished_signal.emit(optimization_results, [buf.getvalue()])

# Visualization Modal Dialog
class VisualizationDialog(QDialog):
    def __init__(self, visualizations, titles, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Visualizations")
        self.setModal(True)
        self.setMinimumSize(800, 600)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowMaximizeButtonHint)  # Enable maximize/resize
        self.visualizations = visualizations
        self.titles = titles
        self.image_labels = []  # Store labels for resizing

        # Main layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Tab widget for different visualizations
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Add each visualization to a tab with a scroll area
        for viz_data, title in zip(visualizations, titles):
            tab = QWidget()
            tab_layout = QVBoxLayout()
            tab.setLayout(tab_layout)

            # Scroll area for each tab
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_widget = QWidget()
            scroll_layout = QVBoxLayout()
            scroll_widget.setLayout(scroll_layout)

            # Title label
            title_label = QLabel(title)
            title_label.setStyleSheet("font-size: 16px; color: #FFFFFF; font-weight: bold;")
            scroll_layout.addWidget(title_label)

            # Image label
            image = QImage.fromData(viz_data)
            pixmap = QPixmap.fromImage(image)
            label = QLabel()
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setPixmap(pixmap)
            label.original_pixmap = pixmap  # Store the original pixmap for resizing
            self.image_labels.append(label)
            scroll_layout.addWidget(label)

            scroll_area.setWidget(scroll_widget)
            tab_layout.addWidget(scroll_area)
            self.tab_widget.addTab(tab, title)

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
        # Resize images in all tabs to fit the window while maintaining aspect ratio
        for label in self.image_labels:
            if not label.original_pixmap.isNull():
                # Get the available width and height (accounting for padding/margins)
                available_width = self.width() - 60  # Adjust for scroll area and tab margins
                available_height = self.height() - 150  # Adjust for title, tabs, buttons, and margins
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

        # Get the currently selected tab's index
        current_tab_index = self.tab_widget.currentIndex()
        if current_tab_index < 0:
            return

        # Default file name based on the tab title
        default_filename = self.titles[current_tab_index].lower().replace(' ', '_') + '.png'

        # Open a file dialog to choose the save location
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Export Image",
            default_filename,
            "PNG Files (*.png);;All Files (*)"
        )
        if file_name:
            # Save the image data from the current tab
            with open(file_name, 'wb') as f:
                f.write(self.visualizations[current_tab_index])

class Phase3Tab(QWidget):
    def __init__(self):
        super().__init__()
        self.is_running = False
        self.init_ui()
        self.log_timer = QTimer()
        self.log_timer.setInterval(100)
        self.log_timer.timeout.connect(self.flush_log)

    def init_ui(self):
        # Main layout
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        # Stack for main content, sensitivity analysis, and optimization pages
        self.stack = QSplitter(Qt.Orientation.Vertical)
        self.main_layout.addWidget(self.stack)

        # Main content widget
        self.main_content = QWidget()
        self.main_content_layout = QVBoxLayout()
        self.main_content.setLayout(self.main_content_layout)

        # Text browser for Phase 3 content
        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(True)
        self.main_content_layout.addWidget(self.text_browser)

        # Buttons to show sensitivity analysis and optimization pages
        self.button_layout = QHBoxLayout()
        self.show_sensitivity_btn = QPushButton("Show Sensitivity Analysis")
        self.show_sensitivity_btn.clicked.connect(self.show_sensitivity_page)
        self.button_layout.addWidget(self.show_sensitivity_btn)

        self.show_optimization_btn = QPushButton("Show Optimization")
        self.show_optimization_btn.clicked.connect(self.show_optimization_page)
        self.button_layout.addWidget(self.show_optimization_btn)

        self.main_content_layout.addLayout(self.button_layout)

        # Sensitivity Analysis Page
        self.sensitivity_page = QWidget()
        self.sensitivity_layout = QHBoxLayout()
        self.sensitivity_page.setLayout(self.sensitivity_layout)

        # Left side: Parameter container
        self.sensitivity_left_container = QVBoxLayout()

        self.sensitivity_param_container = QScrollArea()
        self.sensitivity_param_widget = QWidget()
        self.sensitivity_param_layout = QVBoxLayout()
        self.sensitivity_param_widget.setLayout(self.sensitivity_param_layout)

        self.sensitivity_params = {
            'peak_lambda': '15',
            'doctors_day': '5',
            'doctors_night': '4',
            'xray_units': '2',
            'critical_prob': '0.2',
            'vary_arrival': True,
            'vary_doctors': False,
            'vary_xray': False,
            'vary_critical': False
        }
        self.sensitivity_inputs = {}

        param_groups = [
            ("Parameters", ['peak_lambda', 'doctors_day', 'doctors_night', 'xray_units', 'critical_prob']),
            ("Vary Parameters", ['vary_arrival', 'vary_doctors', 'vary_xray', 'vary_critical'])
        ]

        for group_name, params in param_groups:
            group_label = QLabel(group_name)
            group_label.setStyleSheet("font-size: 16px; color: #FFFFFF; font-weight: bold;")
            self.sensitivity_param_layout.addWidget(group_label)
            for param in params:
                label = QLabel(param.replace('_', ' ').title())
                label.setStyleSheet("color: #E6D5F5;")
                self.sensitivity_param_layout.addWidget(label)
                if param.startswith('vary_'):
                    input_field = QComboBox()
                    input_field.addItems(['False', 'True'])
                    input_field.setCurrentText('True' if self.sensitivity_params[param] else 'False')
                else:
                    input_field = QLineEdit(self.sensitivity_params[param])
                input_field.setStyleSheet("background-color: #4A3B6A; color: #E6D5F5; border: 1px solid #6B5A8D;")
                self.sensitivity_inputs[param] = input_field
                self.sensitivity_param_layout.addWidget(input_field)

        self.sensitivity_param_container.setWidget(self.sensitivity_param_widget)
        self.sensitivity_param_container.setWidgetResizable(True)
        self.sensitivity_param_container.setFixedWidth(300)
        self.sensitivity_left_container.addWidget(self.sensitivity_param_container)

        # Sensitivity buttons
        self.sensitivity_button_layout = QHBoxLayout()
        self.sensitivity_run_btn = QPushButton("Run Sensitivity Analysis")
        self.sensitivity_run_btn.clicked.connect(self.run_sensitivity_analysis)
        self.sensitivity_button_layout.addWidget(self.sensitivity_run_btn)

        self.sensitivity_defaults_btn = QPushButton("Defaults")
        self.sensitivity_defaults_btn.clicked.connect(self.reset_sensitivity_defaults)
        self.sensitivity_button_layout.addWidget(self.sensitivity_defaults_btn)

        self.sensitivity_back_btn = QPushButton("Go Back")
        self.sensitivity_back_btn.clicked.connect(self.show_main_content)
        self.sensitivity_button_layout.addWidget(self.sensitivity_back_btn)

        self.sensitivity_left_container.addLayout(self.sensitivity_button_layout)
        self.sensitivity_layout.addLayout(self.sensitivity_left_container)

        # Right side: Output
        self.sensitivity_output_container = QWidget()
        self.sensitivity_output_layout = QVBoxLayout()
        self.sensitivity_output_container.setLayout(self.sensitivity_output_layout)

        self.sensitivity_progress_label = QLabel("Progress: 0%")
        self.sensitivity_progress_label.setStyleSheet("color: #E6D5F5; font-size: 14px;")
        self.sensitivity_output_layout.addWidget(self.sensitivity_progress_label)

        self.sensitivity_sim_log = QTextEdit()
        self.sensitivity_sim_log.setReadOnly(True)
        self.sensitivity_output_layout.addWidget(self.sensitivity_sim_log)

        self.sensitivity_metrics_display = QTextBrowser()
        self.sensitivity_output_layout.addWidget(self.sensitivity_metrics_display)

        self.sensitivity_viz_btn = QPushButton("Show Visualizations")
        self.sensitivity_viz_btn.setEnabled(False)
        self.sensitivity_viz_btn.clicked.connect(self.show_sensitivity_visualizations)
        self.sensitivity_output_layout.addWidget(self.sensitivity_viz_btn)

        self.sensitivity_layout.addWidget(self.sensitivity_output_container)

        # Optimization Page
        self.optimization_page = QWidget()
        self.optimization_layout = QHBoxLayout()
        self.optimization_page.setLayout(self.optimization_layout)

        # Left side: Config selection
        self.optimization_left_container = QVBoxLayout()

        self.config_container = QWidget()
        self.config_layout = QVBoxLayout()
        self.config_container.setLayout(self.config_layout)

        self.config_label = QLabel("Select Configuration")
        self.config_label.setStyleSheet("font-size: 16px; color: #FFFFFF; font-weight: bold;")
        self.config_layout.addWidget(self.config_label)

        self.config_dropdown = QComboBox()
        self.config_dropdown.addItems(['Baseline', 'Config 1', 'Config 2', 'Config 3'])
        self.config_dropdown.setStyleSheet("background-color: #4A3B6A; color: #E6D5F5; border: 1px solid #6B5A8D;")
        self.config_layout.addWidget(self.config_dropdown)

        self.optimization_left_container.addWidget(self.config_container)

        # Optimization buttons
        self.optimization_button_layout = QHBoxLayout()
        self.optimization_run_btn = QPushButton("Run Optimization")
        self.optimization_run_btn.clicked.connect(self.run_optimization)
        self.optimization_button_layout.addWidget(self.optimization_run_btn)

        self.optimization_back_btn = QPushButton("Go Back")
        self.optimization_back_btn.clicked.connect(self.show_main_content)
        self.optimization_button_layout.addWidget(self.optimization_back_btn)

        self.optimization_left_container.addLayout(self.optimization_button_layout)
        self.optimization_layout.addLayout(self.optimization_left_container)

        # Right side: Output
        self.optimization_output_container = QWidget()
        self.optimization_output_layout = QVBoxLayout()
        self.optimization_output_container.setLayout(self.optimization_output_layout)

        self.optimization_progress_label = QLabel("Progress: 0%")
        self.optimization_progress_label.setStyleSheet("color: #E6D5F5; font-size: 14px;")
        self.optimization_output_layout.addWidget(self.optimization_progress_label)

        self.optimization_sim_log = QTextEdit()
        self.optimization_sim_log.setReadOnly(True)
        self.optimization_output_layout.addWidget(self.optimization_sim_log)

        self.optimization_metrics_display = QTextBrowser()
        self.optimization_output_layout.addWidget(self.optimization_metrics_display)

        self.optimization_viz_btn = QPushButton("Show Visualizations")
        self.optimization_viz_btn.setEnabled(False)
        self.optimization_viz_btn.clicked.connect(self.show_optimization_visualizations)
        self.optimization_output_layout.addWidget(self.optimization_viz_btn)

        self.optimization_layout.addWidget(self.optimization_output_container)

        # Add widgets to stack
        self.stack.addWidget(self.main_content)
        self.stack.addWidget(self.sensitivity_page)
        self.stack.addWidget(self.optimization_page)

        # Set initial page
        self.show_main_content()

        # Set Phase 3 content
        self.set_phase3_content()

        # Apply styles
        self.apply_styles()

    def set_phase3_content(self):
        html_content = """
        <html>
        <body style="background-color: #34294F; color: #E6D5F5; font-family: 'Poppins', Arial, sans-serif;">
            <h1 style="color: #FFFFFF;">Phase 3: Experimentation and Sensitivity Analysis</h1>

            <h2 style="color: #D1C4E9;">Introduction</h2>
            <p>In Phase 3, we conduct <b>sensitivity analysis</b> and <b>optimization</b> for the Emergency Department (ED) simulation model of Sta. Cruz Provincial Hospital, Sta. Cruz, Laguna, Philippines, developed in Phase 2. The objectives are to analyze how changes in key input parameters (e.g., patient arrival rates, resource capacities) affect performance metrics (e.g., waiting times, throughput, resource utilization) and to optimize the system for improved patient flow, targeting a throughput of ~180 patients/day at <code>peak_lambda=15</code>. We use the Python-based discrete-event simulation from Phase 2, leveraging <b>SimPy</b>, <b>NumPy</b>, <b>Pandas</b>, and <b>Matplotlib</b> for analysis and visualization. The previous throughput in Phase 2 was 172.50 patients/day with an average LOS of 73.55 minutes, slightly below the target. This phase aims to refine the model, improve throughput, reduce LOS, and ensure critical patients have an LOS < 30 minutes.</p>

            <h2 style="color: #D1C4E9;">Sensitivity Analysis</h2>
            <h3 style="color: #B39DDB;">Objectives</h3>
            <ul>
                <li>Identify parameters with the greatest impact on ED performance (e.g., average length of stay, queue lengths, throughput).</li>
                <li>Quantify how variations in patient arrival rates, resource capacities, and priority distributions affect metrics.</li>
                <li>Generate visualizations (e.g., line plots, heatmaps, utilization plots) to illustrate parameter effects.</li>
            </ul>

            <h3 style="color: #B39DDB;">Parameters Tested</h3>
            <p>Based on Phase 2 findings, which identified bottlenecks in consultation, diagnostics, and treatment, we selected the following parameters for sensitivity analysis:</p>
            <ul>
                <li><b>Patient Arrival Rate (λ)</b>: Varied from 5 to 20 patients/hour during peak hours (6 PM–12 AM) to simulate low, medium, and high demand (baseline: 15 patients/hour). Non-peak rates are 10 (day) and 12 (night).</li>
                <li><b>Number of Doctors</b>: Varied from 3 to 5 (day) and 2 to 4 (night) (baseline: 5 day, 4 night).</li>
                <li><b>Number of Nurses</b>: Varied from 5 to 9 (day) and 3 to 7 (night) (baseline: 9 day, 7 night).</li>
                <li><b>Diagnostic Equipment (X-ray Machines)</b>: Varied from 1 to 3 (baseline: 2).</li>
                <li><b>Patient Priority Distribution</b>: Varied critical patient proportion from 10% to 30% (baseline: 20%).</li>
            </ul>

            <h3 style="color: #B39DDB;">Methodology</h3>
            <ul>
                <li><b>Simulation Setup</b>: Each parameter was tested independently, holding others at baseline values. For each parameter value, 1000 simulation runs (24-hour cycles, 2-hour warm-up) were executed to ensure statistical reliability.</li>
                <li><b>Metrics Analyzed</b>:
                    <ul>
                        <li>Average Length of Stay (LOS): Total time from arrival to discharge/admission.</li>
                        <li>Average Consultation Waiting Time: Time waiting for a doctor.</li>
                        <li>Average Diagnostics Waiting Time: Time waiting for X-ray or lab tests.</li>
                        <li>Throughput: Average number of patients processed per day.</li>
                        <li>Queue Length: Average number of patients waiting at consultation and diagnostics.</li>
                        <li>Resource Utilization: Percentage of time doctors and X-ray machines are in use.</li>
                    </ul>
                </li>
                <li><b>Analysis Tools</b>: Pandas for data aggregation, Matplotlib for plotting, and NumPy for statistical computations.</li>
                <li><b>Visualization</b>: Line plots for single-parameter effects, heatmaps for two-parameter interactions, and utilization plots for resource analysis.</li>
            </ul>

            <h2 style="color: #D1C4E9;">Optimization</h2>
            <h3 style="color: #B39DDB;">Objectives</h3>
            <ul>
                <li>Minimize average LOS and consultation waiting time.</li>
                <li>Achieve throughput close to 180 patients/day, as expected.</li>
                <li>Maintain resource utilization between 70–90% to balance efficiency and availability.</li>
                <li>Ensure critical patients have LOS < 30 minutes.</li>
            </ul>

            <h3 style="color: #B39DDB;">Methodology</h3>
            <p>We used a <b>grid search</b> approach to test resource configurations, focusing on doctors and X-ray machines, as these were identified as key factors. The following configurations were tested:</p>
            <ol>
                <li><b>Baseline</b>: 5 doctors (day), 4 (night), 2 X-rays.</li>
                <li><b>Config 1</b>: 4 doctors (day), 3 (night), 2 X-rays.</li>
                <li><b>Config 2</b>: 5 doctors (day), 4 (night), 1 X-ray.</li>
                <li><b>Config 3</b>: 5 doctors (day), 4 (night), 3 X-rays.</li>
            </ol>

            <h2 style="color: #D1C4E9;">Conclusion</h2>
            <p>Sensitivity analysis confirmed that patient arrival rates, doctor availability, and X-ray machines are the most critical factors affecting ED performance. The simulation now achieves a throughput of 195.376 patients/day with Config 3, surpassing the target of ~180 patients/day, and reduces LOS to 48.081 minutes from Phase 2’s 73.55 minutes. Consultation wait time (10.352 minutes) and diagnostics wait time (13.586 minutes) are significantly improved, addressing previous bottlenecks. However, critical patients’ LOS at 31.0 minutes slightly exceeds the target of < 30 minutes, and resource utilization remains low (11.218% for doctors, 11.231% for X-rays), suggesting overcapacity. Future work should focus on fine-tuning priority queuing to further reduce critical patient LOS and optimizing resource scheduling to improve utilization while maintaining performance. Config 3 provides actionable recommendations for Sta. Cruz Provincial Hospital to enhance patient flow and care quality, with potential applicability to similar healthcare systems in the Philippines.</p>
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
        self.sensitivity_param_container.setStyleSheet("""
            QScrollArea {
                background-color: #34294F;
                border: 1px solid #4A3B6A;
            }
        """)
        self.sensitivity_sim_log.setStyleSheet("""
            QTextEdit {
                background-color: #4A3B6A;
                color: #E6D5F5;
                border: 1px solid #6B5A8D;
                padding: 5px;
            }
        """)
        self.sensitivity_metrics_display.setStyleSheet("""
            QTextBrowser {
                background-color: #4A3B6A;
                color: #E6D5F5;
                border: 1px solid #6B5A8D;
                padding: 5px;
            }
        """)
        self.optimization_sim_log.setStyleSheet("""
            QTextEdit {
                background-color: #4A3B6A;
                color: #E6D5F5;
                border: 1px solid #6B5A8D;
                padding: 5px;
            }
        """)
        self.optimization_metrics_display.setStyleSheet("""
            QTextBrowser {
                background-color: #4A3B6A;
                color: #E6D5F5;
                border: 1px solid #6B5A8D;
                padding: 5px;
            }
        """)
        for btn in [self.show_sensitivity_btn, self.show_optimization_btn, self.sensitivity_run_btn, self.sensitivity_defaults_btn, self.sensitivity_back_btn, self.optimization_run_btn, self.optimization_back_btn, self.sensitivity_viz_btn, self.optimization_viz_btn]:
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
        self.stack.setSizes([self.stack.height(), 0, 0])
        self.main_content.setVisible(True)
        self.sensitivity_page.setVisible(False)
        self.optimization_page.setVisible(False)

    def show_sensitivity_page(self):
        self.stack.setSizes([0, self.stack.height(), 0])
        self.main_content.setVisible(False)
        self.sensitivity_page.setVisible(True)
        self.optimization_page.setVisible(False)

    def show_optimization_page(self):
        self.stack.setSizes([0, 0, self.stack.height()])
        self.main_content.setVisible(False)
        self.sensitivity_page.setVisible(False)
        self.optimization_page.setVisible(True)

    def reset_sensitivity_defaults(self):
        default_params = {
            'peak_lambda': '15',
            'doctors_day': '5',
            'doctors_night': '4',
            'xray_units': '2',
            'critical_prob': '0.2',
            'vary_arrival': True,
            'vary_doctors': False,
            'vary_xray': False,
            'vary_critical': False
        }
        for param, value in default_params.items():
            if param.startswith('vary_'):
                self.sensitivity_inputs[param].setCurrentText('True' if value else 'False')
            else:
                self.sensitivity_inputs[param].setText(value)

    def run_sensitivity_analysis(self):
        if self.is_running:
            return
        self.is_running = True
        self.sensitivity_run_btn.setEnabled(False)
        self.sensitivity_defaults_btn.setEnabled(False)
        self.sensitivity_back_btn.setEnabled(False)

        params = {key: input_field.currentText() == 'True' if key.startswith('vary_') else input_field.text() for key, input_field in self.sensitivity_inputs.items()}
        self.sensitivity_sim_log.clear()
        self.sensitivity_metrics_display.clear()
        self.sensitivity_viz_btn.setEnabled(False)
        self.sensitivity_progress_label.setText("Progress: 0%")

        self.log_buffer = []
        self.log_timer.start()

        self.sensitivity_worker = SensitivityWorker(params)
        self.sensitivity_worker.update_log_signal.connect(self.buffer_log)
        self.sensitivity_worker.update_progress_signal.connect(self.update_sensitivity_progress)
        self.sensitivity_worker.finished_signal.connect(self.display_sensitivity_results)
        self.sensitivity_worker.finished.connect(self.on_simulation_finished)
        self.sensitivity_worker.start()

    def update_sensitivity_progress(self, progress):
        self.sensitivity_progress_label.setText(f"Progress: {progress}%")

    def buffer_log(self, message):
        self.log_buffer.append(message)

    def flush_log(self):
        if not self.log_buffer:
            return
        active_log = self.sensitivity_sim_log if self.sensitivity_page.isVisible() else self.optimization_sim_log
        for message in self.log_buffer:
            active_log.append(message)
            active_log.verticalScrollBar().setValue(active_log.verticalScrollBar().maximum())
        self.log_buffer.clear()

    def display_sensitivity_results(self, results, arrival_plot, heatmap_plot, util_plot):
        self.flush_log()
        self.log_timer.stop()

        # Display metrics
        metrics_html = """
        <html>
        <body style="background-color: #4A3B6A; color: #E6D5F5; font-family: 'Poppins', Arial, sans-serif;">
            <h3 style="color: #FFFFFF;">Sensitivity Analysis Results</h3>
            <ul>
        """
        for result in results:
            metrics_html += f"<li><b>Lambda: {result['peak_lambda']}, Doctors: {result['doctors_day']}/{result['doctors_night']}, X-ray: {result['xray_units']}, Critical Prob: {result['critical_prob']}</b></li>"
            metrics_html += f"<ul>"
            metrics_html += f"<li>Avg LOS: {result['avg_los']:.2f} minutes</li>"
            metrics_html += f"<li>Avg Consult Wait: {result['avg_consult_wait']:.2f} minutes</li>"
            metrics_html += f"<li>Avg Diag Wait: {result['avg_diag_wait']:.2f} minutes</li>"
            metrics_html += f"<li>Throughput: {result['throughput']:.2f} patients/day</li>"
            metrics_html += f"<li>Doctor Util: {result['doctor_util']:.2f}%</li>"
            metrics_html += f"<li>X-ray Util: {result['xray_util']:.2f}%</li>"
            metrics_html += f"</ul>"
        metrics_html += """
            </ul>
        </body>
        </html>
        """
        self.sensitivity_metrics_display.setHtml(metrics_html)

        # Store visualizations and enable the button
        self.sensitivity_visualizations = [arrival_plot[0], heatmap_plot[0], util_plot[0]]
        self.sensitivity_viz_titles = ["Arrival Rate Sensitivity", "LOS Heatmap", "Resource Utilization"]
        self.sensitivity_viz_btn.setEnabled(True)

    def show_sensitivity_visualizations(self):
        dialog = VisualizationDialog(self.sensitivity_visualizations, self.sensitivity_viz_titles, self)
        dialog.exec()

    def run_optimization(self):
        if self.is_running:
            return
        self.is_running = True
        self.optimization_run_btn.setEnabled(False)
        self.optimization_back_btn.setEnabled(False)

        config = self.config_dropdown.currentIndex()
        self.optimization_sim_log.clear()
        self.optimization_metrics_display.clear()
        self.optimization_viz_btn.setEnabled(False)
        self.optimization_progress_label.setText("Progress: 0%")

        self.log_buffer = []
        self.log_timer.start()

        self.optimization_worker = OptimizationWorker(config)
        self.optimization_worker.update_log_signal.connect(self.buffer_log)
        self.optimization_worker.update_progress_signal.connect(self.update_optimization_progress)
        self.optimization_worker.finished_signal.connect(self.display_optimization_results)
        self.optimization_worker.finished.connect(self.on_simulation_finished)
        self.optimization_worker.start()

    def update_optimization_progress(self, progress):
        self.optimization_progress_label.setText(f"Progress: {progress}%")

    def display_optimization_results(self, results, bar_plot):
        self.flush_log()
        self.log_timer.stop()

        # Display metrics
        metrics_html = """
        <html>
        <body style="background-color: #4A3B6A; color: #E6D5F5; font-family: 'Poppins', Arial, sans-serif;">
            <h3 style="color: #FFFFFF;">Optimization Results</h3>
            <ul>
        """
        for result in results:
            metrics_html += f"<li><b>{result['config']}</b></li>"
            metrics_html += f"<ul>"
            metrics_html += f"<li>Avg LOS: {result['avg_los']:.2f} minutes</li>"
            metrics_html += f"<li>Avg Consult Wait: {result['avg_consult_wait']:.2f} minutes</li>"
            metrics_html += f"<li>Avg Diag Wait: {result['avg_diag_wait']:.2f} minutes</li>"
            metrics_html += f"<li>Throughput: {result['throughput']:.2f} patients/day</li>"
            metrics_html += f"<li>Doctor Util: {result['doctor_util']:.2f}%</li>"
            metrics_html += f"<li>X-ray Util: {result['xray_util']:.2f}%</li>"
            metrics_html += f"<li>Critical LOS: {result['critical_los']:.2f} minutes</li>"
            metrics_html += f"</ul>"
        metrics_html += """
            </ul>
        </body>
        </html>
        """
        self.optimization_metrics_display.setHtml(metrics_html)

        # Store visualizations and enable the button
        self.optimization_visualizations = [bar_plot[0]]
        self.optimization_viz_titles = ["LOS and Throughput"]
        self.optimization_viz_btn.setEnabled(True)

    def show_optimization_visualizations(self):
        dialog = VisualizationDialog(self.optimization_visualizations, self.optimization_viz_titles, self)
        dialog.exec()

    def on_simulation_finished(self):
        self.is_running = False
        self.sensitivity_run_btn.setEnabled(True)
        self.sensitivity_defaults_btn.setEnabled(True)
        self.sensitivity_back_btn.setEnabled(True)
        self.optimization_run_btn.setEnabled(True)
        self.optimization_back_btn.setEnabled(True)