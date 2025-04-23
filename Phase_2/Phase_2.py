import simpy
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

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
TREAT_TIME = (10, 2)  # Lognormal: mean, std
RESOURCES = {
    'day': {'doctors': 5, 'nurses': 9, 'beds': 15, 'xray': 2, 'ultrasound': 1},
    'night': {'doctors': 4, 'nurses': 7, 'beds': 15, 'xray': 2, 'ultrasound': 1}
}
PRIORITY_PROBS = {'critical': 0.2, 'urgent': 0.3, 'non-urgent': 0.5}
DIAG_PROB = 0.5
ADMIT_PROB = 0.1

# Data storage
results = []
dropped_patients = []
completed_patients_log = []

def get_arrival_rate(time, peak_lambda=15):
    """Return arrival rate based on time of day, using the specified peak lambda."""
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

def patient_generator(env, resources, shift_schedule, total_arrivals):
    """Generate patients with specified parameters and track total arrivals."""
    patient_id = 0
    priority_probs = {'critical': PRIORITY_PROBS['critical'], 'urgent': PRIORITY_PROBS['urgent'], 'non-urgent': PRIORITY_PROBS['non-urgent']}
    while env.now < SIM_DURATION:
        lam = get_arrival_rate(env.now)
        inter_arrival = np.random.exponential(60/lam)
        yield env.timeout(inter_arrival)
        priority = np.random.choice(['critical', 'urgent', 'non-urgent'], p=list(priority_probs.values()))
        priority_val = {'critical': 0, 'urgent': 1, 'non-urgent': 2}[priority]
        total_arrivals[0] += 1
        env.process(patient_process(env, patient_id, priority_val, resources, shift_schedule, [], []))
        patient_id += 1

def manage_shifts(env, shift_schedule):
    """Simulate shift changes, ensuring at least 1 active doctor and nurse."""
    while True:
        current_time = env.now % (24*60)
        if 0 <= current_time < 6*60:  # Night shift: 12 AM - 6 AM
            target_doctors = max(1, RESOURCES['night']['doctors'])
            target_nurses = max(1, RESOURCES['night']['nurses'])
        else:  # Day shift: 6 AM - 12 AM
            target_doctors = max(1, RESOURCES['day']['doctors'])
            target_nurses = max(1, RESOURCES['day']['nurses'])

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

def run_simulation():
    """Run a single simulation replication."""
    global results, dropped_patients, completed_patients_log
    results = []
    dropped_patients = []
    completed_patients_log = []
    total_arrivals = [0]
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
    env.process(manage_shifts(env, shift_schedule))
    env.process(patient_generator(env, resources, shift_schedule, total_arrivals))
    env.run(until=SIM_DURATION)
    return pd.DataFrame(results), len(dropped_patients)

# Run multiple simulations
all_results = []
total_dropped = 0
for _ in range(NUM_RUNS):
    df, dropped = run_simulation()
    all_results.append(df)
    total_dropped += dropped

# Aggregate results
results_df = pd.concat(all_results, ignore_index=True)
results_df = results_df[results_df['arrival_time'] >= WARM_UP]  # Exclude warm-up period

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

# Plot waiting times by priority
plt.figure(figsize=(10, 6))
for priority in ['critical', 'urgent', 'non-urgent']:
    subset = results_df[results_df['priority'] == {'critical': 0, 'urgent': 1, 'non-urgent': 2}[priority]]
    plt.hist(subset['los'], bins=30, alpha=0.5, label=priority, density=True)
plt.title('Length of Stay Distribution by Priority')
plt.xlabel('Length of Stay (minutes)')
plt.ylabel('Density')
plt.legend()
plt.savefig('los_distribution.png')

# Save metrics
with open('metrics.txt', 'w') as f:
    for k, v in metrics.items():
        f.write(f'{k}: {v:.2f}\n')
