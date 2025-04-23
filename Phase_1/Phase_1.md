# Phase 1: Problem Selection and Proposal

## Project Title: Optimizing Patient Flow in a Local Hospital Emergency Department in Sta. Cruz, Laguna, Philippines

### 1. Introduction

The Emergency Department (ED) of a hospital is a critical component of healthcare systems, providing immediate care to patients with urgent medical needs. In Sta. Cruz, Laguna, Philippines, the Sta. Cruz Provincial Hospital serves as a primary healthcare facility for a diverse population, handling a high volume of emergency cases daily. However, like many public hospitals in the Philippines, it faces challenges such as long patient waiting times, overcrowded facilities, and strained resources, which can compromise patient outcomes and staff efficiency.

This project aims to develop a computational simulation model to optimize patient flow in the ED of Sta. Cruz Provincial Hospital. By modeling the ED as a complex system, we will analyze bottlenecks, resource utilization, and patient throughput to propose data-driven solutions for improving operational efficiency and patient care quality. The simulation will incorporate discrete-event modeling, Monte Carlo methods, and queuing theory to capture the stochastic nature of patient arrivals, triage processes, and treatment times.

### 2. System Selection

We have selected the Emergency Department of Sta. Cruz Provincial Hospital as the real-world system for this project. The ED is a suitable choice for computational modeling due to its complex, dynamic nature, characterized by:

- **Stochastic Processes**: Random patient arrival patterns and varying treatment times.
- **Queuing Systems**: Patients waiting for triage, consultation, diagnostics, and treatment.
- **Resource Constraints**: Limited doctors, nurses, beds, and diagnostic equipment (e.g., X-ray machines).
- **Multiple Stages**: Patient flow through registration, triage, consultation, diagnostics, treatment, and discharge or admission.

This system is ideal for applying computational science techniques, as it involves discrete events (e.g., patient arrivals), uncertainty (e.g., emergency case severity), and measurable performance metrics (e.g., waiting times, throughput).

### 3. Problem Definition

#### 3.1 Objectives

The primary objective is to optimize patient flow in the ED to:

- Minimize average patient waiting times (from arrival to discharge or admission).
- Maximize patient throughput (number of patients treated per day).
- Improve resource utilization (e.g., doctors, nurses, beds) to reduce idle times and overcrowding.
- Enhance patient satisfaction and care quality by reducing delays and bottlenecks.

#### 3.2 Scope

The simulation will focus on the ED’s core processes, including:

- **Patient Arrival**: Random arrivals based on historical data (e.g., peak hours, seasonal trends).
- **Triage**: Categorization of patients into priority levels (e.g., critical, urgent, non-urgent).
- **Consultation**: Examination by doctors, potentially leading to diagnostics or treatment.
- **Diagnostics**: Tests such as X-rays, laboratory exams, or ultrasounds.
- **Treatment**: Procedures, medication administration, or observation.
- **Discharge/Admission**: Patients leaving the ED or being admitted to the hospital.

The model will exclude non-emergency outpatient services and focus on a 24-hour operational cycle to capture daily variations.

#### 3.3 Input Parameters

Based on preliminary discussions with hospital staff and publicly available healthcare data for similar facilities in the Philippines, the following input parameters will be modeled:

- **Patient Arrival Rate**: Modeled as a Poisson process with varying rates (e.g., λ = 5 patients/hour during off-peak, λ = 15 patients/hour during peak hours from 6 PM to 12 AM).
- **Triage Time**: Normally distributed, mean = 5 minutes, standard deviation = 1 minute.
- **Consultation Time**: Lognormal distribution, mean = 15 minutes, standard deviation = 5 minutes.
- **Diagnostic Test Time**: Exponential distribution, mean = 30 minutes for X-rays, 45 minutes for lab tests.
- **Treatment Time**: Lognormal distribution, mean = 20 minutes, standard deviation = 10 minutes.
- **Resource Capacities**:
  - Doctors: 3 available during day shift, 2 during night shift.
  - Nurses: 5 available during day shift, 3 during night shift.
  - Beds: 10 emergency beds.
  - Diagnostic Equipment: 1 X-ray machine, 1 ultrasound machine, shared lab resources.
- **Patient Priority Levels**: 20% critical, 30% urgent, 50% non-urgent, affecting triage and treatment order.

These parameters will be validated with hospital data during Phase 2, and pseudorandom number generation will be used to simulate stochastic variations.

#### 3.4 Performance Metrics

The simulation will evaluate the system based on the following metrics:

- **Average Waiting Time**: Time from patient arrival to first consultation (target: &lt;30 minutes for critical cases, &lt;60 minutes for non-urgent cases).
- **Total Length of Stay (LOS)**: Time from arrival to discharge/admission (target: &lt;4 hours for non-admitted patients).
- **Patient Throughput**: Number of patients processed per 24-hour cycle (target: maximize without compromising care quality).
- **Resource Utilization Rate**: Percentage of time doctors, nurses, beds, and diagnostic equipment are in use (target: 70-90% to balance efficiency and availability).
- **Queue Length**: Average number of patients waiting at each stage (triage, consultation, diagnostics) (target: &lt;5 patients per queue).
- **Bottleneck Identification**: Stages with the longest delays or highest resource contention.

### 4. Expected Outcomes

The simulation is expected to:

- Identify key bottlenecks in the ED, such as insufficient diagnostic equipment or doctor availability during peak hours.
- Quantify the impact of resource constraints on patient waiting times and throughput.
- Propose optimal resource allocations (e.g., additional nurses during peak hours, prioritized diagnostic access for critical patients).
- Provide sensitivity analysis showing how changes in arrival rates or staffing levels affect performance.
- Recommend data-driven strategies to improve patient flow, such as adjusting shift schedules, prioritizing critical cases, or investing in additional equipment.

### 5. Computational Methods

The project will leverage the following computational science techniques:

- **Discrete-Event Simulation**: To model patient flow through ED stages (e.g., using Python with SimPy library).
- **Queuing Theory**: To analyze waiting times and queue lengths at each stage (e.g., M/M/c queue models for consultation).
- **Monte Carlo Methods**: To simulate uncertainty in arrival rates, treatment times, and patient priority levels.
- **Pseudorandom Number Generation**: To generate realistic stochastic inputs (e.g., using NumPy’s random number generators).
- **Statistical Analysis**: To analyze simulation outputs and perform sensitivity analysis (e.g., using Pandas and Matplotlib for data visualization).

### 6. Relevance to Sta. Cruz, Laguna

The project is tailored to the local context of Sta. Cruz, a bustling capital town with a growing population and increasing healthcare demands. The Sta. Cruz Provincial Hospital serves not only local residents but also patients from nearby municipalities, making ED efficiency critical. By focusing on a local system, the project aligns with community needs and has the potential to inform hospital policy, improve patient care, and contribute to regional healthcare planning.

### 7. Team Roles

The project will be conducted by a group of four students with the following roles:

- **Project Manager**: Oversees timeline, coordinates tasks, and ensures deliverables meet requirements.
- **Model Developer**: Designs and implements the simulation model in Python.
- **Data Analyst**: Conducts statistical analysis, sensitivity analysis, and visualization of results.
- **Report/Presentation Lead**: Prepares the final report and presentation, ensuring clarity and professionalism.

### 8. Timeline

- **Week 1**: Research ED operations, gather preliminary data, and finalize system parameters.
- **Week 2**: Develop and submit the project proposal (this document).
- **Week 3-4**: Begin Phase 2 (Model Development), including data validation and simulation coding.

### 9. Conclusion

This project proposes a comprehensive simulation model to optimize patient flow in the Emergency Department of Sta. Cruz Provincial Hospital. By applying computational science techniques, we aim to address real-world challenges in healthcare delivery, providing actionable insights to enhance efficiency and patient care. The proposal outlines a clear problem definition, measurable objectives, and a robust methodology, setting the foundation for a successful final project.