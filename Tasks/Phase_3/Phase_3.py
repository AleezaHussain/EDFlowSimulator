import simpy
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from itertools import product

# Set random seed for reproducibility
np.random.seed(42)

# Updated parameters
SIM_DURATION = 1440  # 24 hours in minutes
WARM_UP = 120  # 2 hours warm-up
NUM_RUNS = 1000
PEAK_HOURS = [(18*60, 24*60, 15), (0*60, 6*60, 12), (6*60, 18*60, 10)]  # (start, end, lambda)
TRIAGE_TIME = (5, 1)  # Normal: mean, std
CONSULT_TIME = (10, 2)  # Lognormal: mean, std
DIAG_TIME = {'xray': 20, 'lab': 30}  # Exponential: mean
TREAT_TIME = (10, 2)  # Lognormal: mean, std - Reduced to free up beds faster
RESOURCES = {
    'day': {'doctors': 5, 'nurses': 9, 'beds': 15, 'xray': 2, 'ultrasound': 1},
    'night': {'doctors': 4, 'nurses': 7, 'beds': 15, 'xray': 2, 'ultrasound': 1}
}
PRIORITY_PROBS = {'critical': 0.2, 'urgent': 0.3, 'non-urgent': 0.5}
DIAG_PROB = 0.5
ADMIT_PROB = 0.1

# Sensitivity analysis parameters
ARRIVAL_RATES = [5, 10, 15, 20]
DOCTORS_DAY = [3, 4, 5]
DOCTORS_NIGHT = [2, 3, 4]
NURSES_DAY = [5, 7, 9]
NURSES_NIGHT = [3, 5, 7]
XRAY_UNITS = [1, 2, 3]
CRITICAL_PROBS = [0.1, 0.2, 0.3]

# Data storage
results = []
dropped_patients = []
completed_patients_log = []
sensitivity_results = []

def get_arrival_rate(time, peak_lambda):
    """Return arrival rate based on time of day, overriding peak hour lambda."""
    current_time = time % (24*60)
    if 18*60 <= current_time < 24*60:  # Peak: 6 PM - 12 AM
        return peak_lambda
    elif 0*60 <= current_time < 6*60:  # Night: 12 AM - 6 AM
        return 12
    else:  # Day: 6 AM - 6 PM
        return 10

def patient_process(env, patient_id, priority, resources, shift_schedule, doctor_usage, xray_usage):
    """Simulate patient flow through ED, logging completion."""
    arrival_time = env.now
    data = {'patient_id': patient_id, 'priority': priority, 'arrival_time': arrival_time}

    try:
        # Triage
        with resources['triage'].request(priority=priority) as triage_req:
            yield triage_req
            triage_duration = max(0, np.random.normal(*TRIAGE_TIME))
            yield env.timeout(triage_duration)
            data['triage_wait'] = env.now - arrival_time
            data['triage_end'] = env.now

        # Consultation
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

        # Diagnostics (if needed)
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
        else:
            data['diag_wait'] = 0
            data['diag_end'] = data['consult_end']

        # Treatment
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

        # Discharge or Admission
        data['los'] = env.now - arrival_time
        data['admitted'] = np.random.random() < ADMIT_PROB
        data['completion_time'] = env.now
        results.append(data)
        completed_patients_log.append({'patient_id': patient_id, 'completion_time': env.now})

    except simpy.Interrupt:
        dropped_patients.append({'patient_id': patient_id, 'stage': 'interrupted', 'time': env.now})
    except Exception as e:
        dropped_patients.append({'patient_id': patient_id, 'stage': str(e), 'time': env.now})

def patient_generator(env, resources, shift_schedule, peak_lambda, critical_prob, doctor_usage, xray_usage, total_arrivals):
    """Generate patients with specified parameters and track total arrivals."""
    patient_id = 0
    priority_probs = {'critical': critical_prob, 'urgent': (1-critical_prob)*0.375, 'non-urgent': (1-critical_prob)*0.625}
    while env.now < SIM_DURATION:
        lam = get_arrival_rate(env.now, peak_lambda)
        inter_arrival = np.random.exponential(60/lam)
        yield env.timeout(inter_arrival)
        priority = np.random.choice(['critical', 'urgent', 'non-urgent'], p=list(priority_probs.values()))
        priority_val = {'critical': 0, 'urgent': 1, 'non-urgent': 2}[priority]
        total_arrivals[0] += 1
        env.process(patient_process(env, patient_id, priority_val, resources, shift_schedule, doctor_usage, xray_usage))
        patient_id += 1

def manage_shifts(env, shift_schedule, doctors_day, doctors_night, nurses_day, nurses_night):
    """Simulate shift changes, ensuring at least 1 active doctor and nurse."""
    while True:
        current_time = env.now % (24*60)
        if 0 <= current_time < 6*60:  # Night shift: 12 AM - 6 AM
            target_doctors = max(1, doctors_night)
            target_nurses = max(1, nurses_night)
        else:  # Day shift: 6 AM - 12 AM
            target_doctors = max(1, doctors_day)
            target_nurses = max(1, nurses_day)

        # Adjust doctors
        current_doctors = shift_schedule['active_doctors'].level
        if current_doctors > target_doctors:
            yield shift_schedule['active_doctors'].get(current_doctors - target_doctors)
        elif current_doctors < target_doctors:
            yield shift_schedule['active_doctors'].put(target_doctors - current_doctors)

        # Adjust nurses
        current_nurses = shift_schedule['active_nurses'].level
        if current_nurses > target_nurses:
            yield shift_schedule['active_nurses'].get(current_nurses - target_nurses)
        elif current_nurses < target_nurses:
            yield shift_schedule['active_nurses'].put(target_nurses - current_nurses)

        yield env.timeout(60)  # Check every hour

def calculate_utilization(usage_list, total_time, shift_schedule, resource_type, xray_capacity=None):
    """Calculate resource utilization considering shift changes."""
    total_busy_time = 0
    for start, end, duration in usage_list:
        if start >= WARM_UP and end <= total_time:
            total_busy_time += duration
    
    if resource_type in ['doctors', 'nurses']:
        resource_time = 0
        for t in range(int(WARM_UP), int(total_time), 1):  # Check every minute
            current_time = t % (24*60)
            if 0 <= current_time < 6*60:
                num_resources = max(1, shift_schedule[f'active_{resource_type}'].capacity if t == WARM_UP else shift_schedule[f'active_{resource_type}'].level)
            else:
                num_resources = max(1, shift_schedule[f'active_{resource_type}'].capacity if t == WARM_UP else shift_schedule[f'active_{resource_type}'].level)
            resource_time += num_resources
    elif resource_type == 'xray':
        resource_time = xray_capacity * (total_time - WARM_UP)
    
    return (total_busy_time / resource_time) * 100 if resource_time > 0 else 0

def run_simulation(peak_lambda, doctors_day, doctors_night, nurses_day, nurses_night, xray_units, critical_prob):
    """Run simulation with specified parameters."""
    global results, dropped_patients, completed_patients_log
    total_arrivals_list = []
    completed_patients_list = []
    for run in range(NUM_RUNS):
        results = []
        dropped_patients = []
        completed_patients_log = []
        doctor_usage = []
        xray_usage = []
        total_arrivals = [0]
        env = simpy.Environment()
        resources = {
            'triage': simpy.PriorityResource(env, capacity=4),  # Increased to handle higher arrivals
            'doctors': simpy.PriorityResource(env, capacity=max(doctors_day, doctors_night)),
            'nurses': simpy.PriorityResource(env, capacity=max(nurses_day, nurses_night)),
            'beds': simpy.PriorityResource(env, capacity=RESOURCES['day']['beds']),
            'xray': simpy.PriorityResource(env, capacity=xray_units),
            'lab': simpy.PriorityResource(env, capacity=1),
            'ultrasound': simpy.PriorityResource(env, capacity=RESOURCES['day']['ultrasound'])
        }
        shift_schedule = {
            'active_doctors': simpy.Container(env, init=max(1, doctors_day), capacity=max(doctors_day, doctors_night)),
            'active_nurses': simpy.Container(env, init=max(1, nurses_day), capacity=max(nurses_day, nurses_night))
        }
        env.process(manage_shifts(env, shift_schedule, doctors_day, doctors_night, nurses_day, nurses_night))
        env.process(patient_generator(env, resources, shift_schedule, peak_lambda, critical_prob, doctor_usage, xray_usage, total_arrivals))
        env.run(until=SIM_DURATION)
        total_arrivals_list.append(total_arrivals[0])
        completed_patients_list.append(len(completed_patients_log))
        print(f"Run {run + 1}/{NUM_RUNS}: Generated {total_arrivals[0]} patients, Completed {len(completed_patients_log)} patients, Dropped {len(dropped_patients)} patients")
    
    avg_total_arrivals = sum(total_arrivals_list) / NUM_RUNS
    avg_completed = sum(completed_patients_list) / NUM_RUNS
    
    df = pd.DataFrame(results)
    if df.empty:
        return {
            'peak_lambda': peak_lambda,
            'doctors_day': doctors_day,
            'doctors_night': doctors_night,
            'nurses_day': nurses_day,
            'nurses_night': nurses_night,
            'xray_units': xray_units,
            'critical_prob': critical_prob,
            'avg_los': 0,
            'avg_consult_wait': 0,
            'avg_diag_wait': 0,
            'throughput': 0,
            'consult_queue': 0,
            'diag_queue': 0,
            'doctor_util': 0,
            'xray_util': 0,
            'total_arrivals': avg_total_arrivals,
            'dropped_patients': len(dropped_patients)
        }
    
    df_completed = df[df['completion_time'] >= WARM_UP]
    throughput = avg_completed
    
    doctor_util = calculate_utilization(doctor_usage, SIM_DURATION, shift_schedule, 'doctors')
    xray_util = calculate_utilization(xray_usage, SIM_DURATION, shift_schedule, 'xray', xray_capacity=xray_units)
    
    return {
        'peak_lambda': peak_lambda,
        'doctors_day': doctors_day,
        'doctors_night': doctors_night,
        'nurses_day': nurses_day,
        'nurses_night': nurses_night,
        'xray_units': xray_units,
        'critical_prob': critical_prob,
        'avg_los': df_completed['los'].mean() if not df_completed.empty else 0,
        'avg_consult_wait': df_completed['consult_wait'].mean() if not df_completed.empty else 0,
        'avg_diag_wait': df_completed['diag_wait'].mean() if not df_completed.empty else 0,
        'throughput': throughput,
        'consult_queue': df_completed['consult_wait'].apply(lambda x: 1 if x > 0 else 0).mean() * len(df_completed) / NUM_RUNS if not df_completed.empty else 0,
        'diag_queue': df_completed['diag_wait'].apply(lambda x: 1 if x > 0 else 0).mean() * len(df_completed) / NUM_RUNS if not df_completed.empty else 0,
        'doctor_util': doctor_util,
        'xray_util': xray_util,
        'total_arrivals': avg_total_arrivals,
        'dropped_patients': len(dropped_patients)
    }

# Perform sensitivity analysis
for lam in ARRIVAL_RATES:
    sensitivity_results.append(run_simulation(lam, RESOURCES['day']['doctors'], RESOURCES['night']['doctors'], RESOURCES['day']['nurses'], RESOURCES['night']['nurses'], RESOURCES['day']['xray'], PRIORITY_PROBS['critical']))
for doc_day, doc_night in zip(DOCTORS_DAY, DOCTORS_NIGHT):
    sensitivity_results.append(run_simulation(PEAK_HOURS[0][2], doc_day, doc_night, RESOURCES['day']['nurses'], RESOURCES['night']['nurses'], RESOURCES['day']['xray'], PRIORITY_PROBS['critical']))
for nurse_day, nurse_night in zip(NURSES_DAY, NURSES_NIGHT):
    sensitivity_results.append(run_simulation(PEAK_HOURS[0][2], RESOURCES['day']['doctors'], RESOURCES['night']['doctors'], nurse_day, nurse_night, RESOURCES['day']['xray'], PRIORITY_PROBS['critical']))
for xray in XRAY_UNITS:
    sensitivity_results.append(run_simulation(PEAK_HOURS[0][2], RESOURCES['day']['doctors'], RESOURCES['night']['doctors'], RESOURCES['day']['nurses'], RESOURCES['night']['nurses'], xray, PRIORITY_PROBS['critical']))
for crit in CRITICAL_PROBS:
    sensitivity_results.append(run_simulation(PEAK_HOURS[0][2], RESOURCES['day']['doctors'], RESOURCES['night']['doctors'], RESOURCES['day']['nurses'], RESOURCES['night']['nurses'], RESOURCES['day']['xray'], crit))

# Save results
sensitivity_df = pd.DataFrame(sensitivity_results)
sensitivity_df.to_csv('sensitivity_results.csv', index=False)

# Plot sensitivity analysis
arrival_sensitivity = sensitivity_df[sensitivity_df['peak_lambda'].isin(ARRIVAL_RATES)]
arrival_sensitivity = arrival_sensitivity.groupby('peak_lambda').mean().reset_index()

plt.figure(figsize=(12, 8))
plt.plot(arrival_sensitivity['peak_lambda'], arrival_sensitivity['avg_los'], 'o-', label='Avg LOS')
plt.plot(arrival_sensitivity['peak_lambda'], arrival_sensitivity['avg_consult_wait'], 's-', label='Avg Consult Wait')
plt.plot(arrival_sensitivity['peak_lambda'], arrival_sensitivity['avg_diag_wait'], '^-', label='Avg Diag Wait')
plt.plot(arrival_sensitivity['peak_lambda'], arrival_sensitivity['throughput'], 'd-', label='Throughput')
plt.xlabel('Peak Arrival Rate (patients/hour)')
plt.ylabel('Time (minutes) / Throughput (patients/day)')
plt.title('Sensitivity of Metrics to Arrival Rate')
plt.legend()
plt.grid(True)
plt.savefig('arrival_rate_sensitivity.png')

# Heatmap for arrival rate vs. doctors
heatmap_data = sensitivity_df[sensitivity_df['doctors_day'].isin(DOCTORS_DAY) & (sensitivity_df['peak_lambda'].isin(ARRIVAL_RATES))]
heatmap_data = pd.pivot_table(heatmap_data, values='avg_los', index='peak_lambda', columns='doctors_day')
plt.figure(figsize=(10, 8))
plt.imshow(heatmap_data, cmap='viridis', interpolation='nearest')
plt.colorbar(label='Average LOS (minutes)')
plt.xticks(range(len(DOCTORS_DAY)), DOCTORS_DAY)
plt.yticks(range(len(ARRIVAL_RATES)), ARRIVAL_RATES)
plt.xlabel('Number of Doctors (Day Shift)')
plt.ylabel('Peak Arrival Rate (patients/hour)')
plt.title('LOS Heatmap: Arrival Rate vs. Doctors')
plt.savefig('los_heatmap.png')

# Resource utilization plot
plt.figure(figsize=(12, 8))
plt.plot(arrival_sensitivity['peak_lambda'], arrival_sensitivity['doctor_util'], 'o-', label='Doctor Utilization')
plt.plot(arrival_sensitivity['peak_lambda'], arrival_sensitivity['xray_util'], 's-', label='X-ray Utilization')
plt.xlabel('Peak Arrival Rate (patients/hour)')
plt.ylabel('Utilization (%)')
plt.title('Resource Utilization vs. Arrival Rate')
plt.legend()
plt.grid(True)
plt.savefig('resource_utilization.png')

# Optimization configurations
CONFIGS = [
    {'doctors_day': 5, 'doctors_night': 4, 'xray': 2, 'name': 'Baseline'},
    {'doctors_day': 4, 'doctors_night': 3, 'xray': 2, 'name': 'Config 1'},
    {'doctors_day': 5, 'doctors_night': 4, 'xray': 1, 'name': 'Config 2'},
    {'doctors_day': 5, 'doctors_night': 4, 'xray': 3, 'name': 'Config 3'}
]

optimization_results = []

for config in CONFIGS:
    result = run_simulation(PEAK_HOURS[0][2], config['doctors_day'], config['doctors_night'], RESOURCES['day']['nurses'], RESOURCES['night']['nurses'], config['xray'], PRIORITY_PROBS['critical'])
    result['config'] = config['name']
    optimization_results.append(result)

# Save results
optimization_df = pd.DataFrame(optimization_results)
optimization_df.to_csv('optimization_results.csv', index=False)

# Plot optimization results
plt.figure(figsize=(12, 8))
plt.bar(optimization_df['config'], optimization_df['avg_los'], alpha=0.5, label='Avg LOS')
plt.bar(optimization_df['config'], optimization_df['throughput'], alpha=0.5, label='Throughput', bottom=optimization_df['avg_los'])
plt.ylabel('Time (minutes) / Throughput (patients/day)')
plt.title('LOS and Throughput by Configuration')
plt.legend()
plt.savefig('optimization_los.png')