# Progress Report: Phase 3 - Experimentation and Sensitivity Analysis  
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
**Phase Duration**: Weeks 4–5  

## Executive Summary  
In Phase 3, the team conducted sensitivity analysis and optimization for the Emergency Department (ED) simulation model, achieving a throughput of 195.376 patients/day and an average length of stay (LOS) of 48.081 minutes with Config 3 (5 doctors day, 4 night, 3 X-rays). Sensitivity analysis identified patient arrival rates, doctors, and X-ray machines as critical factors, reducing diagnostics wait times from 57.609 minutes (1 X-ray) to 20.468 minutes (3 X-rays). The HCI prototype was enhanced with interactive dashboards and exportable reports. Critical patient LOS (31.0 minutes) slightly exceeded the target (<30 minutes), and resource utilization remained low (11.218% doctors, 11.231% X-rays). Anticipated feedback will guide further refinements in Phase 4, ensuring alignment with course objectives.

## Objectives  
- Perform sensitivity analysis to identify key parameters affecting ED performance.  
- Optimize resource configurations to achieve ~180 patients/day throughput and reduce LOS.  
- Enhance the HCI prototype with interactive features for hospital staff.  
- Address Phase 2 bottlenecks (consultation and diagnostics) and improve critical patient LOS.  

## Activities and Accomplishments  
1. **Sensitivity Analysis**  
   - **Jeron Simon Javier** tested key parameters:  
     - Arrival rate (5–20 patients/hour peak).  
     - Doctors (3–5 day, 2–4 night).  
     - Nurses (5–9 day, 3–7 night).  
     - X-ray machines (1–3).  
     - Critical patient proportion (10–30%).  
   - Ran 1000 iterations per configuration, analyzing LOS, consultation wait, diagnostics wait, throughput, queue length, and resource utilization.  
   - Key findings:  
     - Throughput peaked at λ=15 (191.472 patients/day), dropping at λ=20 (187.357 patients/day).  
     - Diagnostics wait fell from 57.609 minutes (1 X-ray) to 20.468 minutes (3 X-rays).  
     - Doctors significantly impacted LOS (e.g., 104.213 minutes with 4 doctors day vs. 58.020 minutes with 5).  
   - Generated visualizations: arrival rate sensitivity plot, LOS heatmap, and resource utilization plot (`arrival_rate_sensitivity.png`, `los_heatmap.png`, `resource_utilization.png`).  

2. **Optimization**  
   - **Mhar Andrei Macapallag** tested four configurations:  
     - Baseline: 5 doctors (day), 4 (night), 2 X-rays (LOS: 71.090 minutes, throughput: 193.408 patients/day).  
     - Config 1: 4 doctors (day), 3 (night), 2 X-rays (throughput: 130.544 patients/day).  
     - Config 2: 5 doctors (day), 4 (night), 1 X-ray (LOS: 91.760 minutes).  
     - Config 3: 5 doctors (day), 4 (night), 3 X-rays (LOS: 48.081 minutes, throughput: 195.376 patients/day).  
   - Selected Config 3 as optimal, reducing LOS by 32%, consultation wait by 43%, and diagnostics wait by 51% compared to baseline.  
   - Critical patient LOS (31.0 minutes) slightly missed the target, and utilization was low (11.218% doctors, 11.231% X-rays).  
   - Produced an optimization bar plot (`optimization_los.png`).  

3. **HCI Prototype Enhancement**  
   - **Seanrei Ethan Valdeabella** upgraded the Figma prototype with interactive KPI filters (e.g., by time or patient type) and exportable CSV reports.  
   - Improved accessibility with high-contrast colors and larger fonts to meet hospital staff needs.  
   - Tested usability with team members simulating hospital staff, confirming intuitive navigation.  

4. **Documentation and Integration**  
   - **Eldi Nill Driz** documented sensitivity analysis and optimization results (`Phase_3.md`), including visualizations and recommendations.  
   - Integrated simulation outputs with the HCI prototype, enabling real-time KPI updates.  
   - Updated the Git repository with code, results, and documentation for traceability.  

## Challenges Encountered  
- Long LOS tails for non-urgent patients (up to 1200 minutes, from Phase 2) persisted, requiring further resource optimization.  
- Low resource utilization (11.218% doctors, 11.231% X-rays in Config 3) indicated overcapacity, challenging the 70–90% target.  
- Achieving critical patient LOS <30 minutes was difficult without compromising overall throughput.  

## Next Steps  
- Finalize testing to validate Config 3’s performance under varied conditions (e.g., demand surges).  
- Develop a comprehensive final report and presentation summarizing all phases.  
- Create a user guide for the simulation and HCI prototype.  
- Refine priority queuing to reduce critical patient LOS to <30 minutes.  

## Instructor Feedback  
Aligned with Ms. Roxanne Garbo’s focus on thorough experimentation and user-centered design, the team anticipates guidance to further reduce critical patient LOS by refining priority queuing in Phase 4. The sensitivity analysis and optimization results meet CSEL 303’s rigor, but adding a user guide for the HCI prototype is expected to enhance CMSC 313’s emphasis on usability and practical application for hospital staff.  

## Conclusion  
Phase 3 advanced the project by optimizing the simulation model to achieve a throughput of 195.376 patients/day and an LOS of 48.081 minutes, surpassing Phase 2’s results. The HCI prototype’s interactivity and accessibility were enhanced, aligning with CMSC 313 goals. While critical patient LOS and resource utilization require refinement, the team is well-positioned to finalize the project in Phase 4, delivering a robust solution for Sta. Cruz Provincial Hospital.