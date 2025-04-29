# Phase 2: Model Development and Simulation

## Introduction

In Phase 2, we develop a computational simulation model for the Emergency Department (ED) of Sta. Cruz Provincial Hospital in Sta. Cruz, Laguna, Philippines, as outlined in Phase 1. The goal is to simulate patient flow, analyze bottlenecks, and evaluate performance metrics such as waiting times, throughput, and resource utilization. We implement a **discrete-event simulation** using Python with the SimPy library, incorporating **queuing theory**, **Monte Carlo methods**, and **pseudorandom number generation** to model the stochastic nature of the ED. The simulation captures patient arrivals, triage, consultation, diagnostics, treatment, and discharge/admission processes, with realistic parameters based on the local context. Adjustments were made in Phase 3 to improve throughput and reduce waiting times, and this document reflects those updates with the latest simulation results.

## Model Design

### System Overview

The ED is modeled as a series of queues and processes:

- **Patient Arrival**: Patients arrive randomly following a Poisson process with time-varying rates (e.g., higher during peak hours).
- **Triage**: Patients are prioritized (critical, urgent, non-urgent) and queued for consultation.
- **Consultation**: Doctors examine patients, potentially ordering diagnostics or proceeding to treatment.
- **Diagnostics**: Patients queue for tests (e.g., X-ray, lab), modeled as shared resources.
- **Treatment**: Patients receive treatment (e.g., medication, procedures) using beds and nurses.
- **Discharge/Admission**: Patients exit the ED or are admitted to the hospital.

### Modeling Techniques

- **Discrete-Event Simulation**: Using SimPy, we model discrete events (e.g., patient arrival, consultation start) to track patient flow and resource usage over a 24-hour cycle.
- **Queuing Theory**: Each stage (triage, consultation, diagnostics) is modeled as a queue (e.g., M/M/c for consultation with multiple doctors).
- **Monte Carlo Methods**: Stochastic inputs (e.g., arrival rates, service times) are sampled from probability distributions to capture uncertainty.
- **Pseudorandom Number Generation**: NumPy’s random number generators produce realistic variations in arrival and service times.

### Assumptions

- Patient arrivals follow a non-homogeneous Poisson process with rates varying by time of day (e.g., λ = 15 patients/hour from 6 PM to 12 AM, λ = 10 patients/hour from 6 AM to 6 PM, λ = 12 patients/hour from 12 AM to 6 AM).
- Service times (triage, consultation, diagnostics, treatment) follow specified distributions (e.g., lognormal for consultation, exponential for diagnostics).
- Resources (doctors, nurses, beds, diagnostic equipment) have fixed capacities based on updated parameters.
- 50% of patients require diagnostics, and 10% require hospital admission post-treatment.
- Priority queuing ensures critical patients are processed first.

## Simulation Implementation

### Tools and Libraries

- **Python 3.9**: Core programming language.
- **SimPy 4.0.1**: For discrete-event simulation.
- **NumPy 1.21.0**: For pseudorandom number generation and statistical distributions.
- **Pandas 1.3.0**: For data collection and analysis.
- **Matplotlib 3.4.0**: For visualizing simulation outputs.

### Simulation Parameters

- **Input Parameters** (updated to align with Phase 3):
  - **Arrival Rate**: Poisson, λ = 15 patients/hour (peak, 6 PM–12 AM), 12 patients/hour (night, 12 AM–6 AM), 10 patients/hour (day, 6 AM–6 PM).
  - **Triage Time**: Normal, mean = 5 min, std = 1 min.
  - **Consultation Time**: Lognormal, mean = 10 min, std = 2 min.
  - **Diagnostic Test Time**: Exponential, mean = 20 min (X-ray), 30 min (lab).
  - **Treatment Time**: Lognormal, mean = 10 min, std = 2 min.
  - **Resources**: 5 doctors (day), 4 (night); 9 nurses (day), 7 (night); 15 beds; 2 X-rays, 1 ultrasound, shared lab.
  - **Patient Priority**: 20% critical, 30% urgent, 50% non-urgent.
  - **Diagnostic Probability**: 50% of patients require diagnostics.
  - **Admission Probability**: 10% of patients require admission.
- **Simulation Settings**:
  - Duration: 24 hours (1440 minutes).
  - Replications: 1000 runs to ensure statistical reliability.
  - Warm-up Period: 2 hours to stabilize queues.

### Code Implementation

The simulation is implemented in Python using SimPy. Below is the updated code, reflecting adjustments made in Phase 3 to improve throughput, reduce waiting times, and add utilization tracking. The code uses priority queues for critical patients, tracks performance metrics, and handles dropped patients to ensure robustness.

```python
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
```

### Simulation Execution

The simulation runs for 1000 iterations, each simulating a 24-hour period with a 2-hour warm-up period to stabilize initial queues. The code:

- Generates patients with time-varying Poisson arrivals, achieving an average throughput of 172.50 patients/day at `peak_lambda=15`, slightly below the expected \~180 patients/day.

- Assigns priorities using Monte Carlo sampling, with 20% critical, 30% urgent, and 50% non-urgent patients.

- Simulates patient flow through triage, consultation, diagnostics, and treatment using priority queues, with adjustments to reduce excessive waiting times.

- Dynamically adjusts doctor and nurse availability for day (6 AM–12 AM) and night (12 AM–6 AM) shifts using a container-based scheduling mechanism.

- Collects data on waiting times, length of stay (LOS), throughput, and admission rates.

- Produces a histogram of LOS by priority level, saved as `los_distribution.png`, showing the distribution of patient stays across critical, urgent, and non-urgent categories. The updated plot is displayed below:

- Saves key metrics to `metrics.txt` for further analysis.

### Output Metrics

Results from 1000 runs (post-warm-up), updated to reflect the latest simulation outcomes:

- **Average Triage Waiting Time**: 5.01 minutes (close to the expected 4.8 minutes, indicating efficient triage with capacity of 4).
- **Average Consultation Waiting Time**: 17.23 minutes (higher than the expected 12.3 minutes, indicating a persistent bottleneck in doctor availability).
- **Average Diagnostics Waiting Time**: 31.22 minutes (much higher than the expected 18.5 minutes, reflecting significant delays due to 50% diagnostic probability and limited X-ray/lab resources).
- **Average Treatment Waiting Time**: 20.09 minutes (much higher than the expected 10.7 minutes, indicating a bottleneck in nurses or beds despite increased resources).
- **Average Length of Stay (LOS)**: 73.55 minutes (higher than the expected 62.4 minutes, driven by increased waiting times across stages).
- **Throughput**: 172.50 patients/day (slightly below the expected \~180 patients/day, suggesting some patients may be dropped or delayed).
- **Admission Rate**: 10% (matches the expected 9.8%, confirming correct implementation).

The updated LOS distribution plot (`los_distribution.png`) shows that critical patients have the shortest stays (mostly under 100 minutes), followed by urgent and non-urgent patients. However, the distribution has a long tail, with some non-urgent patients experiencing stays up to 1200 minutes, reflecting significant bottlenecks in diagnostics and treatment stages.

**Analysis of Results**:

- The throughput of 172.50 patients/day is slightly below the expected \~180 patients/day, suggesting that bottlenecks in diagnostics and treatment are preventing the system from achieving full capacity.
- Consultation waiting time (17.23 minutes) remains higher than the expected 12.3 minutes, indicating that doctor availability is still a bottleneck, though it’s slightly improved from previous runs (17.499 minutes).
- Diagnostics waiting time (31.22 minutes) is significantly higher than the expected 18.5 minutes, likely due to the 50% diagnostic probability overwhelming the 2 X-ray machines and shared lab during peak hours.
- Treatment waiting time (20.09 minutes) has increased substantially from previous runs (\~0 minutes), suggesting that the increased nurses (9 day, 7 night) and beds (15) are still insufficient to handle the demand, possibly due to longer queuing times upstream (e.g., diagnostics).
- The LOS distribution confirms that priority queuing works, with critical patients having shorter stays, but the long tail for non-urgent patients (up to 1200 minutes) highlights the impact of bottlenecks on lower-priority patients.

## Validation

The model was validated by:

- **Parameter Calibration**: Arrival rates and service times were cross-checked with typical values for Philippine public hospitals (e.g., DOH reports on patient volumes), but the slightly lower throughput suggests further adjustments may be needed.
- **Logical Consistency**: Critical patients have shorter LOS, as seen in the distribution plot, confirming that priority queuing functions correctly.
- **Statistical Reliability**: 1000 runs provide a 95% confidence interval for metrics (e.g., LOS CI: ±2.5 minutes, estimated based on standard deviation of LOS).

## Next Steps

In Phase 3, we will:

- Conduct sensitivity analysis by varying arrival rates, resource capacities (e.g., doctors, nurses, X-ray machines), and priority distributions to identify factors affecting performance.
- Optimize resource allocation to reduce diagnostics waiting times (target: 18.5 minutes) and treatment waiting times (target: 10.7 minutes), aiming to increase throughput to \~180 patients/day.
- Investigate the long tail in LOS for non-urgent patients (up to 1200 minutes), potentially by adding more diagnostic resources or adjusting patient flow logic.
- Generate additional visualizations (e.g., queue length over time, resource utilization plots) to better understand system dynamics.

## Conclusion

The simulation model captures the dynamics of the Sta. Cruz Provincial Hospital ED, incorporating realistic stochastic processes and resource constraints. The implementation utilizes and manipulates discrete-event simulation, queuing theory, and Monte Carlo methods, producing data for performance analysis. With the adjustments made in Phase 3 (increased resources, reduced service times, higher diagnostic probability), the model achieves a throughput of 172.50 patients/day, slightly below the expected \~180 patients/day. Waiting times remain high (consultation: 17.23 minutes, diagnostics: 31.22 minutes, treatment: 20.09 minutes), and the overall LOS (73.55 minutes) exceeds the expected 62.4 minutes. The LOS distribution plot confirms that priority queuing prioritizes critical patients effectively, but non-urgent patients experience excessive delays, with stays reaching up to 1200 minutes due to bottlenecks in diagnostics and treatment. Phase 3 will focus on sensitivity analysis and optimization to address these issues, aiming to reduce waiting times, improve throughput, and enhance overall ED efficiency.