# Emergency Department Flow Simulator - Sta. Cruz Provincial Hospital

<p align="center">
   <img src="https://raw.githubusercontent.com/VoxDroid/EDFlowSimulator/refs/heads/main/assets/img/EDFlowSimulator.png" width="250" height="250" alt="Emergency Department Flow Simulator Logo">
</p>

Welcome to the **Emergency Department Flow Simulator**, a computational tool designed to optimize patient flow in the Emergency Department (ED) of Sta. Cruz Provincial Hospital, Sta. Cruz, Laguna, Philippines. This project, developed for **CSEL 303 (Computational Science)** and **CMSC 313 (Human Computer Interaction)**, leverages discrete-event simulation to reduce waiting times, increase throughput, and enhance resource utilization. Built with Python and PyQt6, it provides actionable insights for hospital administrators through an intuitive GUI and data visualizations.

## Project Overview

The simulator models ED operations, including patient arrival, triage, consultation, diagnostics, treatment, and discharge/admission. By employing **discrete-event simulation (SimPy)**, **queuing theory**, **Monte Carlo methods**, and **optimization techniques**, the project addresses real-world healthcare challenges in the Philippines. Key achievements include:

- **Throughput**: 195.376 patients/day (target: ~180).
- **Average Length of Stay (LOS)**: 48.081 minutes (32% reduction from baseline).
- **Critical Patient LOS**: 31.0 minutes (target: <30 minutes).
- **Resource Utilization**: Identified overcapacity at 11.218% (doctors) and 11.231% (X-rays), with recommendations for optimization.

The project is structured in four phases, with findings documented in `Phase_1.md` to `Phase_4.md`. Visualizations and a user-friendly GUI enhance accessibility for hospital staff.

## Objectives

- **Minimize Waiting Times**: Target <30 minutes for critical patients and ~60 minutes overall.
- **Maximize Throughput**: Achieve ~180 patients/day at a peak arrival rate of 15 patients/hour.
- **Optimize Resources**: Target 70–90% utilization for doctors, nurses, and diagnostic equipment.
- **Identify Bottlenecks**: Mitigate delays in consultation and diagnostics.

## Methodology

The simulation uses:
- **Discrete-Event Simulation**: SimPy models patient flow through ED stages.
- **Queuing Theory**: M/M/c queues represent stages like consultation with multiple doctors.
- **Monte Carlo Methods**: Stochastic inputs (e.g., arrival rates, service times) sampled from probability distributions.
- **Pseudorandom Number Generation**: NumPy ensures realistic variability.
- **Sensitivity Analysis & Optimization**: Tests parameter impacts and optimizes resource allocation.

**Simulation Parameters**:
- **Patient Arrival**: Poisson process (15 patients/hour peak, 12 night, 10 day).
- **Resources**: 5 doctors (day), 4 (night); 9 nurses (day), 7 (night); 15 beds; 2 X-ray machines (baseline).
- **Patient Priority**: 20% critical, 30% urgent, 50% non-urgent.
- **Simulation Setup**: 1000 iterations, 24-hour cycle, 2-hour warm-up period.

## Key Findings

- **Baseline (Phase 2)**: Throughput of 172.50 patients/day, LOS of 73.55 minutes, with bottlenecks in consultation (17.23 minutes wait) and diagnostics (31.22 minutes wait).
- **Sensitivity Analysis (Phase 3)**: Throughput peaks at 191.472 patients/day at λ=15. Adding X-ray machines reduces diagnostics wait from 57.609 minutes (1 X-ray) to 20.468 minutes (3 X-rays).
- **Optimization (Phase 3)**: Config 3 (5 doctors day, 4 night, 3 X-rays) achieves:
  - Throughput: 195.376 patients/day.
  - LOS: 48.081 minutes.
  - Critical Patient LOS: 31.0 minutes.
  - Resource Utilization: 11.218% (doctors), 11.231% (X-rays).
- **Recommendations (Phase 4)**: Adopt Config 3, enhance priority queuing for critical patients, and optimize scheduling to improve utilization.

## Repository Structure

- `app.py`: Main PyQt6-based GUI application.
- `Phase_1.py`, `Phase_2.py`, `Phase_3.py`, `Phase_4.py`: Simulation logic for each phase.
- `Phase_1.md`, `Phase_2.md`, `Phase_3.md`, `Phase_4.md`: Phase-specific documentation.
- `los_distribution.png`, `arrival_rate_sensitivity.png`, `los_heatmap.png`, `resource_utilization.png`, `optimization_los.png`: Visualizations.
- `metrics.txt`, `sensitivity_results.csv`, `optimization_results.csv`: Simulation outputs.
- `resources/EDFlowSimulator.png`: Application icon.
- `CONTRIBUTING.md`: Guidelines for contributing.
- `CODE_OF_CONDUCT.md`: Community standards.
- `SECURITY.md`: Security policies.
- `SUPPORT.md`: Support resources.
- `PULL_REQUEST_TEMPLATE.md`: Pull request guidelines.

## Setup Instructions

1. **Clone the Repository**:
   ```
   git clone https://github.com/VoxDroid/EDFlowSimulator.git
   cd EDFlowSimulator
   ```
2. **Create a Virtual Environment**:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. **Install Dependencies**:
   ```
   pip install -r requirements.txt
   python -m pip install briefcase
   ```
4. **Run the Application**:
   ```
   briefcase dev
   ```

## Dependencies

- Python 3.9+
- SimPy 4.0.1
- NumPy 1.21.0
- Pandas 1.3.0
- Matplotlib 3.4.0
- PyQt6
- qtawesome
- briefcase

Install via:
```
pip install simpy numpy pandas matplotlib pyqt6 qtawesome
python -m pip install briefcase
```

## Visualizations

Key outputs displayed in the GUI:
- **LOS Distribution** (`los_distribution.png`): Critical patients have shorter stays; non-urgent patients face delays up to 1200 minutes.
- **Arrival Rate Sensitivity** (`arrival_rate_sensitivity.png`): Throughput peaks at 191.472 patients/day at λ=15.
- **LOS Heatmap** (`los_heatmap.png`): LOS decreases with more doctors at higher arrival rates.
- **Resource Utilization** (`resource_utilization.png`): Peaks at 32.627% (doctors) and 45.411% (X-rays) at λ=10.
- **Optimization Results** (`optimization_los.png`): Config 3 achieves the lowest LOS (48.081 minutes).

## Contributing

We welcome contributions! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details on how to submit issues, propose features, or contribute code.

## Code of Conduct

Our community adheres to the [Code of Conduct](CODE_OF_CONDUCT.md) to ensure a respectful and inclusive environment.

## Security

For security-related concerns, please refer to our [Security Policy](SECURITY.md).

## Support

Need help? Check our [Support Resources](SUPPORT.md) for FAQs, troubleshooting, and contact information.

## Pull Requests

To submit changes, follow our [Pull Request Guidelines](https://github.com/VoxDroid/EDFlowSimulator/blob/main/.github/PULL_REQUEST_TEMPLATE.md) for a smooth review process.

## Attribution

Developed by **@VoxDroid** (Mhar Andrei Macapallag, Jeron Simon Javier, Seanrei Ethan Valdeabella, Eldi Nill Driz) for **CSEL 303 & CMSC 313 Final Project**. Licensed under [MIT License](LICENSE).