from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextBrowser
from PyQt6.QtCore import Qt

class Phase1Tab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Create a QTextBrowser to display HTML content
        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(True)
        layout.addWidget(self.text_browser)

        # Set HTML content for Phase 1
        self.set_phase1_content()

        # Apply styles
        self.apply_styles()

    def set_phase1_content(self):
        """Set the HTML content for Phase 1 based on Phase_1.md."""
        html_content = """
        <html>
        <body style="background-color: #34294F; color: #E6D5F5; font-family: 'Poppins', Arial, sans-serif;">
            <h1 style="color: #FFFFFF;">Phase 1: Problem Selection and Proposal</h1>

            <h2 style="color: #D1C4E9;">Project Title: Optimizing Patient Flow in a Local Hospital Emergency Department in Sta. Cruz, Laguna, Philippines</h2>

            <h3 style="color: #B39DDB;">1. Introduction</h3>
            <p>The Emergency Department (ED) of a hospital is a critical component of healthcare systems, providing immediate care to patients with urgent medical needs. In Sta. Cruz, Laguna, Philippines, the Sta. Cruz Provincial Hospital serves as a primary healthcare facility for a diverse population, handling a high volume of emergency cases daily. However, like many public hospitals in the Philippines, it faces challenges such as long patient waiting times, overcrowded facilities, and strained resources, which can compromise patient outcomes and staff efficiency.</p>
            <p>This project aims to develop a computational simulation model to optimize patient flow in the ED of Sta. Cruz Provincial Hospital. By modeling the ED as a complex system, we will analyze bottlenecks, resource utilization, and patient throughput to propose data-driven solutions for improving operational efficiency and patient care quality. The simulation will incorporate discrete-event modeling, Monte Carlo methods, and queuing theory to capture the stochastic nature of patient arrivals, triage processes, and treatment times.</p>

            <h3 style="color: #B39DDB;">2. System Selection</h3>
            <p>We have selected the Emergency Department of Sta. Cruz Provincial Hospital as the real-world system for this project. The ED is a suitable choice for computational modeling due to its complex, dynamic nature, characterized by:</p>
            <ul>
                <li><b>Stochastic Processes</b>: Random patient arrival patterns and varying treatment times.</li>
                <li><b>Queuing Systems</b>: Patients waiting for triage, consultation, diagnostics, and treatment.</li>
                <li><b>Resource Constraints</b>: Limited doctors, nurses, beds, and diagnostic equipment (e.g., X-ray machines).</li>
                <li><b>Multiple Stages</b>: Patient flow through registration, triage, consultation, diagnostics, treatment, and discharge or admission.</li>
            </ul>
            <p>This system is ideal for applying computational science techniques, as it involves discrete events (e.g., patient arrivals), uncertainty (e.g., emergency case severity), and measurable performance metrics (e.g., waiting times, throughput).</p>

            <h3 style="color: #B39DDB;">3. Problem Definition</h3>
            <h4 style="color: #9575CD;">3.1 Objectives</h4>
            <p>The primary objective is to optimize patient flow in the ED to:</p>
            <ul>
                <li>Minimize average patient waiting times (from arrival to discharge or admission).</li>
                <li>Maximize patient throughput (number of patients treated per day).</li>
                <li>Improve resource utilization (e.g., doctors, nurses, beds) to reduce idle times and overcrowding.</li>
                <li>Enhance patient satisfaction and care quality by reducing delays and bottlenecks.</li>
            </ul>

            <h4 style="color: #9575CD;">3.2 Scope</h4>
            <p>The simulation will focus on the ED’s core processes, including:</p>
            <ul>
                <li><b>Patient Arrival</b>: Random arrivals based on historical data (e.g., peak hours, seasonal trends).</li>
                <li><b>Triage</b>: Categorization of patients into priority levels (e.g., critical, urgent, non-urgent).</li>
                <li><b>Consultation</b>: Examination by doctors, potentially leading to diagnostics or treatment.</li>
                <li><b>Diagnostics</b>: Tests such as X-rays, laboratory exams, or ultrasounds.</li>
                <li><b>Treatment</b>: Procedures, medication administration, or observation.</li>
                <li><b>Discharge/Admission</b>: Patients leaving the ED or being admitted to the hospital.</li>
            </ul>
            <p>The model will exclude non-emergency outpatient services and focus on a 24-hour operational cycle to capture daily variations.</p>

            <h4 style="color: #9575CD;">3.3 Input Parameters</h4>
            <p>Based on preliminary discussions with hospital staff and publicly available healthcare data for similar facilities in the Philippines, the following input parameters will be modeled:</p>
            <ul>
                <li><b>Patient Arrival Rate</b>: Modeled as a Poisson process with varying rates (e.g., λ = 5 patients/hour during off-peak, λ = 15 patients/hour during peak hours from 6 PM to 12 AM).</li>
                <li><b>Triage Time</b>: Normally distributed, mean = 5 minutes, standard deviation = 1 minute.</li>
                <li><b>Consultation Time</b>: Lognormal distribution, mean = 15 minutes, standard deviation = 5 minutes.</li>
                <li><b>Diagnostic Test Time</b>: Exponential distribution, mean = 30 minutes for X-rays, 45 minutes for lab tests.</li>
                <li><b>Treatment Time</b>: Lognormal distribution, mean = 20 minutes, standard deviation = 10 minutes.</li>
                <li><b>Resource Capacities</b>:
                    <ul>
                        <li>Doctors: 3 available during day shift, 2 during night shift.</li>
                        <li>Nurses: 5 available during day shift, 3 during night shift.</li>
                        <li>Beds: 10 emergency beds.</li>
                        <li>Diagnostic Equipment: 1 X-ray machine, 1 ultrasound machine, shared lab resources.</li>
                    </ul>
                </li>
                <li><b>Patient Priority Levels</b>: 20% critical, 30% urgent, 50% non-urgent, affecting triage and treatment order.</li>
            </ul>
            <p>These parameters will be validated with hospital data during Phase 2, and pseudorandom number generation will be used to simulate stochastic variations.</p>

            <h4 style="color: #9575CD;">3.4 Performance Metrics</h4>
            <p>The simulation will evaluate the system based on the following metrics:</p>
            <ul>
                <li><b>Average Waiting Time</b>: Time from patient arrival to first consultation (target: &lt;30 minutes for critical cases, &lt;60 minutes for non-urgent cases).</li>
                <li><b>Total Length of Stay (LOS)</b>: Time from arrival to discharge/admission (target: &lt;4 hours for non-admitted patients).</li>
                <li><b>Patient Throughput</b>: Number of patients processed per 24-hour cycle (target: maximize without compromising care quality).</li>
                <li><b>Resource Utilization Rate</b>: Percentage of time doctors, nurses, beds, and diagnostic equipment are in use (target: 70-90% to balance efficiency and availability).</li>
                <li><b>Queue Length</b>: Average number of patients waiting at each stage (triage, consultation, diagnostics) (target: &lt;5 patients per queue).</li>
                <li><b>Bottleneck Identification</b>: Stages with the longest delays or highest resource contention.</li>
            </ul>

            <h3 style="color: #B39DDB;">4. Expected Outcomes</h3>
            <p>The simulation is expected to:</p>
            <ul>
                <li>Identify key bottlenecks in the ED, such as insufficient diagnostic equipment or doctor availability during peak hours.</li>
                <li>Quantify the impact of resource constraints on patient waiting times and throughput.</li>
                <li>Propose optimal resource allocations (e.g., additional nurses during peak hours, prioritized diagnostic access for critical patients).</li>
                <li>Provide sensitivity analysis showing how changes in arrival rates or staffing levels affect performance.</li>
                <li>Recommend data-driven strategies to improve patient flow, such as adjusting shift schedules, prioritizing critical cases, or investing in additional equipment.</li>
            </ul>

            <h3 style="color: #B39DDB;">5. Computational Methods</h3>
            <p>The project will leverage the following computational science techniques:</p>
            <ul>
                <li><b>Discrete-Event Simulation</b>: To model patient flow through ED stages (e.g., using Python with SimPy library).</li>
                <li><b>Queuing Theory</b>: To analyze waiting times and queue lengths at each stage (e.g., M/M/c queue models for consultation).</li>
                <li><b>Monte Carlo Methods</b>: To simulate uncertainty in arrival rates, treatment times, and patient priority levels.</li>
                <li><b>Pseudorandom Number Generation</b>: To generate realistic stochastic inputs (e.g., using NumPy’s random number generators).</li>
                <li><b>Statistical Analysis</b>: To analyze simulation outputs and perform sensitivity analysis (e.g., using Pandas and Matplotlib for data visualization).</li>
            </ul>

            <h3 style="color: #B39DDB;">6. Relevance to Sta. Cruz, Laguna</h3>
            <p>The project is tailored to the local context of Sta. Cruz, a bustling capital town with a growing population and increasing healthcare demands. The Sta. Cruz Provincial Hospital serves not only local residents but also patients from nearby municipalities, making ED efficiency critical. By focusing on a local system, the project aligns with community needs and has the potential to inform hospital policy, improve patient care, and contribute to regional healthcare planning.</p>

            <h3 style="color: #B39DDB;">7. Team Roles</h3>
            <p>The project will be conducted by a group of four students with the following roles:</p>
            <ul>
                <li><b>Project Manager</b>: Oversees timeline, coordinates tasks, and ensures deliverables meet requirements.</li>
                <li><b>Model Developer</b>: Designs and implements the simulation model in Python.</li>
                <li><b>Data Analyst</b>: Conducts statistical analysis, sensitivity analysis, and visualization of results.</li>
                <li><b>Report/Presentation Lead</b>: Prepares the final report and presentation, ensuring clarity and professionalism.</li>
            </ul>

            <h3 style="color: #B39DDB;">8. Timeline</h3>
            <ul>
                <li><b>Week 1</b>: Research ED operations, gather preliminary data, and finalize system parameters.</li>
                <li><b>Week 2</b>: Develop and submit the project proposal (this document).</li>
                <li><b>Week 3-4</b>: Begin Phase 2 (Model Development), including data validation and simulation coding.</li>
            </ul>

            <h3 style="color: #B39DDB;">9. Conclusion</h3>
            <p>This project proposes a comprehensive simulation model to optimize patient flow in the Emergency Department of Sta. Cruz Provincial Hospital. By applying computational science techniques, we aim to address real-world challenges in healthcare delivery, providing actionable insights to enhance efficiency and patient care. The proposal outlines a clear problem definition, measurable objectives, and a robust methodology, setting the foundation for a successful final project.</p>
        </body>
        </html>
        """
        self.text_browser.setHtml(html_content)

    def apply_styles(self):
        """Apply styles specific to the Phase 1 tab."""
        self.text_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #34294F;
                color: #E6D5F5;
                border: 1px solid #4A3B6A;
                padding: 10px;
            }
        """)