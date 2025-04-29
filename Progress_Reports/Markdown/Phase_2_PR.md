# Progress Report: Phase 2 - Model Development and Simulation  
**Project Title**: Optimizing Patient Flow in the Emergency Department of Sta. Cruz Provincial Hospital  
**Github Repository Link**: [**`github.com/VoxDroid/EDFlowSimulator`**](https://github.com/VoxDroid/EDFlowSimulator)

**Courses**: CSEL 303 (Computational Science) and CMSC 313 (Human Computer Interaction)  
**Instructor**: Ms. Roxanne Garbo  

**Team Members**:  
- Mhar Andrei Macapallag  
- Jeron Simon Javier  
- Seanrei Ethan Valdeabella  
- Eldi Nill Driz  


**Date**: April 2025  
**Phase Duration**: Weeks 2–3  

## Executive Summary  
In Phase 2, the team developed a discrete-event simulation model for the Emergency Department (ED) of Sta. Cruz Provincial Hospital using Python and SimPy. The model simulates patient flow through arrival, triage, consultation, diagnostics, treatment, and discharge/admission, incorporating Monte Carlo methods and queuing theory for stochastic processes. Initial results showed a throughput of 172.50 patients/day and an average length of stay (LOS) of 73.55 minutes, slightly below the target of ~180 patients/day and above the expected 62.4 minutes. Bottlenecks were identified in consultation (17.23 minutes wait) and diagnostics (31.22 minutes wait). An HCI prototype was initiated in Figma to visualize key performance indicators (KPIs), enhancing the project’s usability. The team anticipates feedback to guide resource adjustments and interface improvements for Phase 3.

## Objectives  
- Develop a discrete-event simulation model for ED patient flow.  
- Implement Monte Carlo methods and queuing theory to model stochastic processes.  
- Run simulations to collect performance metrics and identify bottlenecks.  
- Begin designing an HCI prototype to visualize simulation outputs.  
- Validate the model against typical Philippine hospital data.  

## Activities and Accomplishments  
1. **Simulation Model Development**  
   - **Mhar Andrei Macapallag** implemented the simulation in Python using SimPy, modeling patient arrivals (Poisson, λ=15 peak, 10 day, 12 night), triage (normal, mean=5 min), consultation (lognormal, mean=10 min), diagnostics (exponential, mean=20–30 min), and treatment (lognormal, mean=10 min).  
   - Incorporated resources: 5 doctors (day)/4 (night), 9 nurses (day)/7 (night), 15 beds, 2 X-rays, 1 ultrasound, shared lab.  
   - Used priority queues to prioritize critical patients (20% critical, 30% urgent, 50% non-urgent).  

2. **Simulation Execution and Analysis**  
   - **Jeron Simon Javier** ran 1000 iterations (24-hour cycles, 2-hour warm-up) to ensure statistical reliability.  
   - Collected KPIs:  
     - Average triage wait: 5.01 minutes (target: ~5 minutes).  
     - Average consultation wait: 17.23 minutes (target: ~12.3 minutes).  
     - Average diagnostics wait: 31.22 minutes (target: ~18.5 minutes).  
     - Average treatment wait: 20.09 minutes (target: ~10.7 minutes).  
     - Average LOS: 73.55 minutes (target: ~62.4 minutes).  
     - Throughput: 172.50 patients/day (target: ~180 patients/day).  
     - Admission rate: 10% (target: ~9.8%).  
   - Identified bottlenecks in consultation (limited doctors) and diagnostics (high diagnostic probability, limited X-rays).  
   - Generated a LOS distribution plot (`los_distribution.png`) showing shorter stays for critical patients but long tails for non-urgent patients (up to 1200 minutes).  

3. **HCI Prototype Development**  
   - **Seanrei Ethan Valdeabella** designed an initial Figma prototype with dashboards displaying KPIs (e.g., waiting times, throughput, bed occupancy) and a patient flow flowchart.  
   - Ensured intuitive design with color-coded indicators (e.g., red for high wait times) and clear labels for hospital staff.  
   - Incorporated team feedback for larger fonts and simplified visualizations.  

4. **Documentation and Validation**  
   - **Eldi Nill Driz** documented the model implementation, simulation results, and HCI design in the project repository (`Phase_2.md`).  
   - Validated parameters against typical Philippine hospital data (e.g., DOH reports), confirming realistic arrival rates and service times.  
   - Set up a Git repository for version control, ensuring collaborative code management.  

## Challenges Encountered  
- High diagnostics wait times (31.22 minutes) due to 50% diagnostic probability overwhelmed limited X-ray resources.  
- Long LOS tails for non-urgent patients (up to 1200 minutes) indicated inefficiencies in resource allocation.  
- Integrating real-time KPI updates into the static Figma prototype posed design challenges.  

## Next Steps  
- Conduct sensitivity analysis to evaluate the impact of arrival rates, doctors, nurses, and X-ray machines on performance.  
- Optimize resource configurations to achieve ~180 patients/day throughput and reduce LOS to ~60 minutes.  
- Enhance the HCI prototype with interactive elements (e.g., KPI filters, exportable reports).  
- Investigate long LOS tails for non-urgent patients through resource adjustments.  

## Instructor Feedback  
Based on Ms. Roxanne Garbo’s emphasis on rigorous computational modeling and user-centered design in CSEL 303 and CMSC 313, the team expects guidance to address consultation and diagnostics bottlenecks by increasing resources (e.g., doctors, X-rays) in Phase 3. The HCI prototype’s initial design aligns with course goals, but adding accessibility features (e.g., high-contrast colors) and interactive elements is anticipated to enhance usability for hospital staff.  

## Conclusion  
Phase 2 delivered a functional simulation model, achieving a throughput of 172.50 patients/day and identifying bottlenecks in consultation and diagnostics. The HCI prototype lays the groundwork for visualizing KPIs, enhancing practical value. Anticipated feedback will guide resource optimization and interface improvements in Phase 3, targeting improved throughput, reduced LOS, and enhanced usability.