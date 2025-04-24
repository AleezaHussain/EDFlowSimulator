from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextBrowser
from PyQt6.QtCore import Qt

class Phase4Tab(QWidget):
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

        # Set HTML content for Phase 4
        self.set_phase4_content()

        # Apply styles
        self.apply_styles()

    def set_phase4_content(self):
        """Set the HTML content for Phase 4 based on Phase_4.md."""
        html_content = """
        <html>
        <body style="background-color: #34294F; color: #E6D5F5; font-family: 'Poppins', Arial, sans-serif;">
            <h1 style="color: #FFFFFF;">Phase 4: Report Writing and Presentation</h1>

            <h2 style="color: #D1C4E9;">Final Report</h2>

            <h3 style="color: #B39DDB;">Introduction</h3>
            <p>The Emergency Department (ED) of Sta. Cruz Provincial Hospital in Sta. Cruz, Laguna, Philippines, faces significant challenges including long patient waiting times, resource constraints, and operational inefficiencies, which are prevalent in public healthcare facilities across the Philippines. This project aimed to develop a computational simulation model to optimize patient flow in the ED, with the goals of reducing waiting times, increasing throughput, and improving resource utilization. Using <b>discrete-event simulation</b>, <b>queuing theory</b>, <b>Monte Carlo methods</b>, and <b>pseudorandom number generation</b>, we modeled patient arrivals, triage, consultation, diagnostics, treatment, and discharge/admission processes. This report consolidates findings from Phases 1 through 3, detailing the modeling approach, simulation results, sensitivity analysis, optimization outcomes, and actionable recommendations to enhance ED efficiency.</p>

            <h3 style="color: #B39DDB;">System and Problem Definition</h3>
            <p>The ED was chosen as a complex system due to its stochastic nature (random patient arrivals, variable service times), queuing dynamics, and resource constraints (doctors, nurses, beds, diagnostic equipment). The problem was defined in Phase 1 with the following objectives:</p>
            <ul>
                <li>Minimize average length of stay (LOS) and waiting times, particularly for critical patients (target: LOS &lt; 30 minutes).</li>
                <li>Maximize patient throughput (target: ~180 patients/day at <code>peak_lambda=15</code>).</li>
                <li>Optimize resource utilization (target: 70–90% for doctors, nurses, and equipment).</li>
                <li>Identify and mitigate bottlenecks in consultation and diagnostics.</li>
            </ul>

            <h4 style="color: #9575CD;">Key Parameters</h4>
            <p>(updated from Phase 3 for consistency):</p>
            <ul>
                <li><b>Patient Arrival Rate</b>: Poisson process, varying by time of day: 15 patients/hour (peak: 6 PM–12 AM), 12 patients/hour (night: 12 AM–6 AM), 10 patients/hour (day: 6 AM–6 PM).</li>
                <li><b>Service Times</b>:
                    <ul>
                        <li>Triage: Normal, mean=5 minutes, std=1 minute.</li>
                        <li>Consultation: Lognormal, mean=10 minutes, std=2 minutes.</li>
                        <li>Diagnostics: Exponential, mean=20 minutes (X-ray), 30 minutes (lab).</li>
                        <li>Treatment: Lognormal, mean=10 minutes, std=2 minutes.</li>
                    </ul>
                </li>
                <li><b>Resources</b> (baseline from Phase 3):
                    <ul>
                        <li>Doctors: 5 (day), 4 (night).</li>
                        <li>Nurses: 9 (day), 7 (night).</li>
                        <li>Beds: 15.</li>
                        <li>Diagnostic Equipment: 2 X-ray machines, 1 ultrasound, shared lab.</li>
                    </ul>
                </li>
                <li><b>Patient Priority</b>: 20% critical, 30% urgent, 50% non-urgent.</li>
                <li><b>Diagnostics Probability</b>: 50% of patients require diagnostics.</li>
                <li><b>Admission Probability</b>: 10% of patients are admitted.</li>
            </ul>

            <h4 style="color: #9575CD;">Performance Metrics</h4>
            <ul>
                <li>Average LOS: Total time from arrival to discharge/admission.</li>
                <li>Waiting Times: At triage, consultation, diagnostics, and treatment stages.</li>
                <li>Throughput: Number of patients processed per day.</li>
                <li>Queue Lengths: Average number of patients waiting at consultation and diagnostics.</li>
                <li>Resource Utilization: Percentage of time doctors and X-ray machines are in use.</li>
            </ul>

            <h3 style="color: #B39DDB;">Modeling Approach</h3>
            <p>The simulation was implemented in <b>Python</b> using <b>SimPy</b> for discrete-event modeling, <b>NumPy</b> for pseudorandom number generation, <b>Pandas</b> for data analysis, and <b>Matplotlib</b> for visualization. The model structure, developed in Phase 2 and refined in Phase 3, included:</p>
            <ul>
                <li><b>Discrete-Event Simulation</b>: Modeled patient flow as a series of events (e.g., arrival, triage start) with priority queues to ensure critical patients are processed first.</li>
                <li><b>Queuing Theory</b>: Represented stages as M/M/c queues (e.g., consultation with multiple doctors).</li>
                <li><b>Monte Carlo Methods</b>: Sampled stochastic inputs (e.g., arrival rates, service times) from probability distributions to capture variability.</li>
                <li><b>Pseudorandom Number Generation</b>: Used NumPy’s random generators for realistic variations, with a fixed seed (42) for reproducibility.</li>
            </ul>
            <p>The simulation ran for 1000 iterations, each simulating a 24-hour cycle with a 2-hour warm-up period to stabilize queues. The model was validated against typical Philippine hospital data, with arrival rates and service times calibrated to reflect local conditions (e.g., higher patient volumes during peak hours).</p>

            <h3 style="color: #B39DDB;">Simulation Results</h3>
            <p>The baseline simulation results from Phase 3, using 5 doctors (day), 4 (night), and 2 X-ray machines, are as follows (1000 runs, post-warm-up):</p>
            <ul>
                <li><b>Average LOS</b>: 71.090 minutes (critical: 29.5 minutes, slightly below the target of &lt; 30 minutes).</li>
                <li><b>Waiting Times</b>:
                    <ul>
                        <li>Triage: 5.01 minutes (from Phase 2, consistent with normal distribution mean=5 minutes).</li>
                        <li>Consultation: 18.025 minutes.</li>
                        <li>Diagnostics: 27.643 minutes.</li>
                        <li>Treatment: 20.09 minutes (from Phase 2, reflecting bottlenecks).</li>
                    </ul>
                </li>
                <li><b>Throughput</b>: 193.408 patients/day (exceeding the target of ~180 patients/day).</li>
                <li><b>Queue Lengths</b> (from Phase 3, at <code>peak_lambda=15</code>):
                    <ul>
                        <li>Consultation: Not explicitly reported but inferred as moderate based on wait times.</li>
                        <li>Diagnostics: Not explicitly reported but significant based on 27.643-minute wait.</li>
                    </ul>
                </li>
                <li><b>Resource Utilization</b>:
                    <ul>
                        <li>Doctors: 41.814%.</li>
                        <li>X-ray: 60.542%.</li>
                    </ul>
                </li>
            </ul>
            <p>These results highlight persistent bottlenecks in consultation and diagnostics, with utilization rates below the target range (70–90%), indicating potential overcapacity after resource adjustments in Phase 3.</p>

            <h3 style="color: #B39DDB;">Sensitivity Analysis</h3>
            <p>Sensitivity analysis, conducted in Phase 3, tested the impact of varying key parameters on ED performance. The parameters tested included patient arrival rate, number of doctors, number of nurses, X-ray machines, and critical patient proportion. Key findings are summarized below:</p>
            <ul>
                <li><b>Patient Arrival Rate</b> (at baseline: 5 doctors day, 4 night, 9 nurses day, 7 night, 2 X-rays, 20% critical):
                    <ul>
                        <li><code>peak_lambda=5</code>: Throughput: 177.9 patients/day, Avg LOS: 67.548 minutes, Doctor Util: 31.487%, X-ray Util: 43.705%.</li>
                        <li><code>peak_lambda=10</code>: Throughput: 189.654 patients/day, Avg LOS: 55.981 minutes, Doctor Util: 32.627%, X-ray Util: 45.411%.</li>
                        <li><code>peak_lambda=15</code>: Throughput: 191.472 patients/day, Avg LOS: 56.349 minutes, Doctor Util: 24.681%, X-ray Util: 38.623%.</li>
                        <li><code>peak_lambda=20</code>: Throughput: 187.357 patients/day, Avg LOS: 68.188 minutes, Doctor Util: 26.850%, X-ray Util: 27.240%.</li>
                    </ul>
                </li>
                <li><b>Number of Doctors</b> (at <code>peak_lambda=15</code>, 9 nurses day, 7 night, 2 X-rays, 20% critical):
                    <ul>
                        <li>3 doctors (day)/2 (night): Throughput: 83.053 patients/day, Avg LOS: 72.459 minutes.</li>
                        <li>4 doctors (day)/3 (night): Throughput: 127.09 patients/day, Avg LOS: 104.213 minutes.</li>
                        <li>5 doctors (day)/4 (night): Throughput: 192.318 patients/day, Avg LOS: 58.020 minutes.</li>
                    </ul>
                </li>
                <li><b>Number of Nurses</b> (at <code>peak_lambda=15</code>, 5 doctors day, 4 night, 2 X-rays, 20% critical):
                    <ul>
                        <li>5 nurses (day)/3 (night): Throughput: 164.087 patients/day, Avg LOS: 69.961 minutes.</li>
                        <li>7 nurses (day)/5 (night): Throughput: 189.285 patients/day, Avg LOS: 95.700 minutes.</li>
                        <li>9 nurses (day)/7 (night): Throughput: 193.736 patients/day, Avg LOS: 81.255 minutes.</li>
                    </ul>
                </li>
                <li><b>X-ray Machines</b> (at <code>peak_lambda=15</code>, 5 doctors day, 4 night, 9 nurses day, 7 night, 20% critical):
                    <ul>
                        <li>1 X-ray: Throughput: 186.63 patients/day, Avg LOS: 102.721 minutes, Avg Diag Wait: 57.609 minutes.</li>
                        <li>2 X-rays: Throughput: 191.249 patients/day, Avg LOS: 84.261 minutes, Avg Diag Wait: 39.371 minutes.</li>
                        <li>3 X-rays: Throughput: 195.279 patients/day, Avg LOS: 63.101 minutes, Avg Diag Wait: 20.468 minutes.</li>
                    </ul>
                </li>
                <li><b>Critical Patient Proportion</b> (at <code>peak_lambda=15</code>, 5 doctors day, 4 night, 9 nurses day, 7 night, 2 X-rays):
                    <ul>
                        <li>10% critical: Throughput: 195.259 patients/day, Avg LOS: 68.375 minutes.</li>
                        <li>20% critical: Throughput: 189.155 patients/day, Avg LOS: 59.639 minutes.</li>
                        <li>30% critical: Throughput: 192.995 patients/day, Avg LOS: 64.285 minutes.</li>
                    </ul>
                </li>
            </ul>
            <p><b>Key Finding</b>: Arrival rate and doctor availability significantly impact throughput and LOS, with throughput peaking at <code>peak_lambda=15</code> (191.472 patients/day). Diagnostics wait times are highly sensitive to X-ray availability, dropping from 57.609 minutes (1 X-ray) to 20.468 minutes (3 X-rays). Resource utilization remains below the target range (e.g., doctor utilization peaks at 45.467% with 10% critical patients), indicating inefficiencies.</p>

            <h4 style="color: #9575CD;">Visualization</h4>
            <ul>
                <li><b>Arrival Rate Sensitivity Plot</b> (<code>arrival_rate_sensitivity.png</code>): Demonstrates non-linear trends in LOS, wait times, and throughput with increasing arrival rates, peaking at <code>peak_lambda=15</code>.</li>
                <p><img src="resources/arrival_rate_sensitivity.png" alt="Sensitivity of Metrics to Arrival Rate"></p>
                <li><b>LOS Heatmap</b> (<code>los_heatmap.png</code>): Shows that LOS decreases with more doctors, especially at higher arrival rates (e.g., 58.020 minutes with 5 doctors at <code>peak_lambda=15</code>).</li>
                <p><img src="resources/los_heatmap.png" alt="LOS Heatmap: Arrival Rate vs. Doctors"></p>
                <li><b>Resource Utilization Plot</b> (<code>resource_utilization.png</code>): Indicates underutilization of doctors and X-ray machines, with maximums of 32.627% and 45.411% at <code>peak_lambda=10</code>.</li>
                <p><img src="resources/resource_utilization.png" alt="Resource Utilization vs. Arrival Rate"></p>
            </ul>

            <h3 style="color: #B39DDB;">Optimization Results</h3>
            <p>Optimization in Phase 3 used a grid search approach to test resource configurations, focusing on doctors and X-ray machines. The configurations tested were:</p>
            <ul>
                <li><b>Baseline</b>: 5 doctors (day), 4 (night), 2 X-rays.</li>
                <li><b>Config 1</b>: 4 doctors (day), 3 (night), 2 X-rays.</li>
                <li><b>Config 2</b>: 5 doctors (day), 4 (night), 1 X-ray.</li>
                <li><b>Config 3</b>: 5 doctors (day), 4 (night), 3 X-rays.</li>
            </ul>
            <h4 style="color: #9575CD;">Results</h4>
            <table border="1" style="border-collapse: collapse; color: #E6D5F5;">
                <tr style="background-color: #4A3B6A;">
                    <th>Configuration</th>
                    <th>Avg LOS (min)</th>
                    <th>Avg Consult Wait (min)</th>
                    <th>Avg Diag Wait (min)</th>
                    <th>Throughput (patients/day)</th>
                    <th>Doctor Util (%)</th>
                    <th>X-ray Util (%)</th>
                    <th>Critical LOS (min)</th>
                </tr>
                <tr>
                    <td>Baseline</td>
                    <td>71.090</td>
                    <td>18.025</td>
                    <td>27.643</td>
                    <td>193.408</td>
                    <td>41.814</td>
                    <td>60.542</td>
                    <td>29.5</td>
                </tr>
                <tr>
                    <td>Config 1</td>
                    <td>62.306</td>
                    <td>12.590</td>
                    <td>22.931</td>
                    <td>130.544</td>
                    <td>14.408</td>
                    <td>16.655</td>
                    <td>45.0</td>
                </tr>
                <tr>
                    <td>Config 2</td>
                    <td>91.760</td>
                    <td>18.690</td>
                    <td>52.059</td>
                    <td>191.362</td>
                    <td>31.645</td>
                    <td>70.512</td>
                    <td>42.0</td>
                </tr>
                <tr>
                    <td>Config 3</td>
                    <td>48.081</td>
                    <td>10.352</td>
                    <td>13.586</td>
                    <td>195.376</td>
                    <td>11.218</td>
                    <td>11.231</td>
                    <td>31.0</td>
                </tr>
            </table>
            <p><b>Config 3</b> was optimal, reducing LOS by 32% (from 71.090 to 48.081 minutes), consultation wait by 43% (from 18.025 to 10.352 minutes), and diagnostics wait by 51% (from 27.643 to 13.586 minutes) compared to the baseline. Throughput increased to 195.376 patients/day, exceeding the target, but critical patient LOS (31.0 minutes) slightly missed the target of &lt; 30 minutes. Resource utilization dropped significantly (doctors: 11.218%, X-ray: 11.231%), indicating overcapacity.</p>

            <h4 style="color: #9575CD;">Visualization</h4>
            <ul>
                <li><b>Optimization Bar Plot</b> (<code>optimization_los.png</code>): Highlights Config 3’s superior performance in reducing LOS and increasing throughput.</li>
                <p><img src="resources/optimization_los.png" alt="LOS and Throughput by Configuration"></p>
                <li><b>LOS Distribution by Priority</b> (<code>los_distribution.png</code>, from Phase 2): Shows critical patients with shorter stays (mostly under 100 minutes), but non-urgent patients experience delays up to 1200 minutes due to bottlenecks.</li>
                <p><img src="resources/los_distribution.png" alt="Length of Stay Distribution by Priority"></p>
            </ul>

            <h3 style="color: #B39DDB;">Conclusions</h3>
            <p>The simulation effectively modeled the ED’s complex dynamics, identifying consultation and diagnostics as primary bottlenecks in Phase 2 (LOS: 73.55 minutes, throughput: 172.50 patients/day). Sensitivity analysis in Phase 3 confirmed that patient arrival rates, doctor availability, and X-ray machines are critical factors, with LOS dropping significantly with additional resources (e.g., from 102.721 minutes with 1 X-ray to 63.101 minutes with 3 X-rays). Optimization results demonstrated that Config 3 (5 doctors day, 4 night, 3 X-rays) achieves the best performance, reducing LOS to 48.081 minutes and increasing throughput to 195.376 patients/day. However, critical patient LOS (31.0 minutes) slightly exceeds the target, and resource utilization (11.218% for doctors, 11.231% for X-rays) is well below the 70–90% target, suggesting overcapacity.</p>
            <p>The model’s stochastic inputs, priority queuing, and validation against Philippine healthcare data ensure a realistic representation of the ED. The long tail in LOS for non-urgent patients (up to 1200 minutes, from Phase 2) highlights the need for further optimization in resource scheduling and priority queuing to balance care across all patient types.</p>

            <h3 style="color: #B39DDB;">Recommendations</h3>
            <ol>
                <li><b>Implement Config 3</b>: Allocate 5 doctors (day), 4 (night), and 3 X-ray machines to achieve an LOS of 48.081 minutes and throughput of 195.376 patients/day, significantly improving from Phase 2’s 73.55 minutes and 172.50 patients/day.</li>
                <li><b>Enhance Priority Queuing</b>: Adjust triage protocols to further reduce critical patient LOS to meet the &lt; 30-minute target, possibly by reserving specific resources (e.g., an X-ray machine) for critical cases.</li>
                <li><b>Optimize Resource Scheduling</b>: Introduce dynamic scheduling to reallocate doctors and X-ray machines during off-peak hours, increasing utilization closer to the 70–90% target while maintaining capacity for demand surges.</li>
                <li><b>Monitor Arrival Patterns</b>: Use real-time data to predict peak loads (e.g., 6 PM–12 AM) and adjust staffing proactively.</li>
                <li><b>Future Investments</b>: If budget allows, invest in additional diagnostic equipment (e.g., lab resources) to further reduce diagnostics wait times, which remain a secondary bottleneck (13.586 minutes in Config 3).</li>
            </ol>

            <h3 style="color: #B39DDB;">Implications</h3>
            <p>The findings provide Sta. Cruz Provincial Hospital with a data-driven strategy to enhance patient care and operational efficiency, directly addressing local healthcare challenges in Sta. Cruz, Laguna. The model’s adaptability makes it applicable to other public hospitals in the Philippines with similar constraints, supporting broader healthcare improvements. This project demonstrates the value of computational science in solving real-world problems, offering a scalable framework for hospital management and policy planning.</p>

            <h3 style="color: #B39DDB;">Visuals</h3>
            <ul>
                <li><b>Table 1</b>: Optimization results comparing configurations (see above).</li>
                <li><b>Figure 1</b>: Arrival rate sensitivity plot (<code>arrival_rate_sensitivity.png</code>).</li>
                <li><b>Figure 2</b>: LOS heatmap (<code>los_heatmap.png</code>).</li>
                <li><b>Figure 3</b>: Resource utilization plot (<code>resource_utilization.png</code>).</li>
                <li><b>Figure 4</b>: Optimization bar plot (<code>optimization_los.png</code>).</li>
                <li><b>Figure 5</b>: LOS distribution by priority (<code>los_distribution.png</code>).</li>
            </ul>
            <p>These visuals, generated using Matplotlib, are referenced throughout the report to support findings and will be included in the presentation to illustrate key insights.</p>
        </body>
        </html>
        """
        self.text_browser.setHtml(html_content)

    def apply_styles(self):
        """Apply styles specific to the Phase 4 tab."""
        self.text_browser.setStyleSheet("""
            QTextBrowser {
                background-color: #34294F;
                color: #E6D5F5;
                border: 1px solid #4A3B6A;
                padding: 10px;
            }
            QTextBrowser QTable {
                border: 1px solid #4A3B6A;
                background-color: #4A3B6A;
                color: #E6D5F5;
            }
        """)