# Progress Report: Phase 4 - Report Writing and Presentation  
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
**Phase Duration**: Weeks 6–7  

## Executive Summary  
In Phase 4, the team finalized the simulation model and HCI prototype for optimizing patient flow in the Emergency Department (ED) of Sta. Cruz Provincial Hospital. Final testing validated Config 3 (5 doctors day, 4 night, 3 X-rays), achieving a throughput of 195.376 patients/day and an average length of stay (LOS) of 48.081 minutes, surpassing targets of ~180 patients/day and ~60 minutes. The HCI prototype was completed with interactive dashboards and a user guide. A comprehensive final report and presentation were prepared, consolidating all phases. Critical patient LOS (31.0 minutes vs. <30 minutes) and low resource utilization (11.218% doctors, 11.231% X-rays) remain areas for refinement, but the project offers actionable recommendations for hospital efficiency, meeting CSEL 303 and CMSC 313 objectives.

## Objectives  
- Conduct final testing to validate the optimized simulation model (Config 3).  
- Finalize the HCI prototype with a user guide for hospital staff.  
- Prepare a comprehensive final report and presentation summarizing all phases.  
- Address anticipated feedback to refine critical patient LOS and documentation.  

## Activities and Accomplishments  
1. **Final Testing and Validation**  
   - **Mhar Andrei Macapallag** conducted stress tests on Config 3, simulating demand surges (λ=20 patients/hour peak).  
   - Validated KPIs:  
     - Throughput: 195.376 patients/day (target: ~180).  
     - Average LOS: 48.081 minutes (target: ~60 minutes).  
     - Consultation wait: 10.352 minutes (target: ~12.3 minutes).  
     - Diagnostics wait: 13.586 minutes (target: ~18.5 minutes).  
     - Critical patient LOS: 31.0 minutes (target: <30 minutes).  
     - Resource utilization: 11.218% doctors, 11.231% X-rays (target: 70–90%).  
   - Confirmed robustness, with no significant performance degradation under high demand.  

2. **HCI Prototype Finalization**  
   - **Seanrei Ethan Valdeabella** finalized the Figma prototype, adding a help section with tooltips for KPIs and an exportable report feature.  
   - Conducted usability testing, ensuring intuitive navigation and accessibility (e.g., high-contrast colors, large fonts).  
   - Integrated real-time simulation outputs, displaying KPIs like waiting times and throughput dynamically.  

3. **Final Report and Documentation**  
   - **Eldi Nill Driz** compiled a comprehensive final report (`Phase_4.md`), detailing the system, modeling approach, simulation results, sensitivity analysis, optimization, and recommendations.  
   - Created a user guide explaining how to run the simulation, interpret KPIs, and use the HCI dashboard, aligning with anticipated usability requirements.  
   - Organized the Git repository with code, visualizations (`los_distribution.png`, `arrival_rate_sensitivity.png`, `los_heatmap.png`, `resource_utilization.png`, `optimization_los.png`), and documentation.  

4. **Presentation Preparation**  
   - **Jeron Simon Javier** led the development of a 10–15-minute presentation summarizing the project’s objectives, methodology, results, and recommendations.  
   - Included visualizations (e.g., optimization bar plot, LOS heatmap) to illustrate Config 3’s impact (32% LOS reduction, 51% diagnostics wait reduction).  
   - Rehearsed the presentation to ensure clarity and alignment with assessment criteria (e.g., effective communication, visual support).  

## Challenges Encountered  
- Critical patient LOS (31.0 minutes) slightly exceeded the target, requiring trade-offs with overall throughput.  
- Low resource utilization (11.218% doctors, 11.231% X-rays) indicated overcapacity, challenging the 70–90% target.  
- Condensing complex simulation results into a concise presentation required careful selection of key insights.  

## Results and Impact  
- Config 3 reduced LOS by 32% (from 71.090 to 48.081 minutes) and increased throughput by 13% (from 172.50 to 195.376 patients/day) compared to Phase 2.  
- Consultation and diagnostics wait times dropped by 43% and 51%, respectively, addressing Phase 2 bottlenecks.  
- The HCI prototype provides hospital staff with an intuitive tool to monitor ED performance, enhancing decision-making.  
- The project meets CSEL 303 objectives (computational modeling) and CMSC 313 goals (user-centered design), offering a scalable solution for Philippine hospitals.  

## Instructor Feedback  
Reflecting Ms. Roxanne Garbo’s emphasis on actionable outcomes and usability in CSEL 303 and CMSC 313, the team expects guidance to fine-tune priority queuing to achieve critical patient LOS <30 minutes and to include a limitations section (e.g., low utilization, generalized data). The user guide and comprehensive visualizations are anticipated to align with expectations for clear communication and practical application in healthcare settings.  

## Conclusion  
Phase 4 delivered a validated simulation model and HCI prototype, achieving significant improvements in ED efficiency (195.376 patients/day, 48.081-minute LOS). The final report and presentation consolidate findings, providing actionable recommendations for Sta. Cruz Provincial Hospital. While critical patient LOS and resource utilization require further refinement, the project demonstrates the power of computational science and HCI, with potential for broader impact in the Philippines.