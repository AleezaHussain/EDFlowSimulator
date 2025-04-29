# Progress Report: Phase 1 - Problem Selection and Proposal  
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
**Phase Duration**: Week 1  

## Executive Summary  
In Phase 1, the team initiated the project to optimize patient flow in the Emergency Department (ED) of Sta. Cruz Provincial Hospital, Sta. Cruz, Laguna, Philippines. The ED was selected as a complex system suitable for computational modeling, and a project proposal was developed to define the problem and objectives. The goals include minimizing patient waiting times, maximizing throughput, and improving resource utilization using discrete-event simulation, queuing theory, and Monte Carlo methods, with a Human Computer Interaction (HCI) component for visualizing outputs. Team roles were assigned, a timeline was established, and initial parameters were defined, laying a robust foundation for Phase 2.

## Objectives  
- Select a real-world system (ED) for computational simulation.  
- Define the problem, including objectives, input parameters, and performance metrics.  
- Develop a project proposal outlining the system, methodology, and expected outcomes.  
- Assign team roles and establish a project timeline.  
- Plan the integration of HCI principles for visualizing simulation results.  

## Activities and Accomplishments  
1. **System Selection**  
   - Chose the ED of Sta. Cruz Provincial Hospital due to its stochastic processes, queuing dynamics, and resource constraints, making it ideal for computational modeling.  
   - Identified key processes: patient arrival, triage, consultation, diagnostics, treatment, and discharge/admission.  
   - Confirmed the system’s relevance to local healthcare challenges in Sta. Cruz, Laguna, serving a diverse population.  

2. **Problem Definition**  
   - Defined objectives: minimize average waiting times (target: <30 minutes for critical cases, <60 minutes for non-urgent), maximize throughput (~180 patients/day), and optimize resource utilization (70–90%).  
   - Specified input parameters:  
     - Patient arrival rate: Poisson process (λ=15 patients/hour peak, 10 day, 12 night).  
     - Service times: Triage (normal, mean=5 min), consultation (lognormal, mean=15 min), diagnostics (exponential, mean=30 min), treatment (lognormal, mean=20 min).  
     - Resources: 3 doctors (day)/2 (night), 5 nurses (day)/3 (night), 10 beds, 1 X-ray, 1 ultrasound.  
     - Patient priority: 20% critical, 30% urgent, 50% non-urgent.  
   - Established performance metrics: average waiting time, length of stay (LOS), throughput, queue length, resource utilization, and bottleneck identification.  

3. **Project Proposal Development**  
   - Drafted a comprehensive proposal (`Phase_1.md`) detailing the system, problem, computational methods (discrete-event simulation, queuing theory, Monte Carlo methods), expected outcomes, and local relevance.  
   - Proposed an HCI component to visualize simulation outputs (e.g., dashboards for waiting times and throughput) for hospital staff.  

4. **Team Roles and Timeline**  
   - Assigned roles:  
     - **Mhar Andrei Macapallag**: Project Manager and Model Developer, overseeing timeline and simulation coding.  
     - **Jeron Simon Javier**: Data Analyst, responsible for statistical analysis and performance metrics.  
     - **Seanrei Ethan Valdeabella**: HCI Designer, focusing on visualization and interface development.  
     - **Eldi Nill Driz**: Report/Presentation Lead, managing documentation and final deliverables.  
   - Established a timeline:  
     - Phase 1: Problem selection and proposal (Week 1)  
     - Phase 2: Model development and simulation (Weeks 2–3)  
     - Phase 3: Experimentation and sensitivity analysis (Weeks 4–5)  
     - Phase 4: Report writing and presentation (Weeks 6–7)  

5. **Computational and HCI Planning**  
   - Selected Python with SimPy for discrete-event simulation, NumPy for pseudorandom number generation, Pandas for data analysis, and Matplotlib for visualization.  
   - Planned to use Figma for HCI prototype design, focusing on intuitive dashboards for hospital staff to monitor KPIs (e.g., waiting times, bed occupancy).  
   - Discussed integrating Monte Carlo methods for stochastic inputs and queuing theory for analyzing wait times.  

## Challenges Encountered  
- Limited access to specific ED data required reliance on generalized parameters from Philippine hospital contexts, necessitating validation in Phase 2.  
- Balancing simulation complexity with computational efficiency posed initial planning challenges.  
- Defining a clear scope for the HCI component required iterative discussions to align with hospital staff needs.  

## Next Steps  
- Develop the discrete-event simulation model in Python using SimPy.  
- Validate input parameters with typical Philippine hospital data.  
- Begin designing the HCI prototype in Figma for visualizing simulation outputs.  
- Ensure alignment with course requirements for computational modeling and HCI design.  

## Instructor Feedback  
To align with Ms. Roxanne Garbo’s expectations for CSEL 303 and CMSC 313, the team anticipates guidance to refine the problem definition by incorporating more specific performance metrics and ensuring the HCI component is user-centered. The proposal’s focus on discrete-event simulation and local relevance is expected to meet course standards, but further emphasis on validating parameters and planning sensitivity analysis in Phase 2 will enhance rigor.  

## Conclusion  
Phase 1 established a solid foundation by selecting the ED, defining the problem, and developing a detailed proposal. The integration of HCI principles enhances the project’s practicality, aligning with the goals of CSEL 303 and CMSC 313. The team’s collaborative efforts ensured clear objectives and a feasible timeline, positioning the project for successful model development in Phase 2.