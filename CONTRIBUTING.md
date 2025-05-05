# Contributing to Emergency Department Flow Simulator

Thank you for your interest in contributing to the **Emergency Department Flow Simulator**! This project aims to optimize patient flow in the Emergency Department of Sta. Cruz Provincial Hospital, and we welcome contributions from the community to enhance its functionality, usability, and impact.

## How to Contribute

### 1. Reporting Issues
- Check the [GitHub Issues](https://github.com/VoxDroid/EDFlowSimulator/issues) page to ensure the issue hasn't been reported.
- Open a new issue with a clear title, detailed description, steps to reproduce, and any relevant screenshots or logs.
- Use labels (e.g., `bug`, `enhancement`, `documentation`) to categorize your issue.

### 2. Suggesting Features
- Propose new features or improvements via the [GitHub Issues](https://github.com/VoxDroid/EDFlowSimulator/issues) page.
- Clearly explain the feature, its benefits, and potential implementation ideas.
- Tag the issue with the `enhancement` label.

### 3. Submitting Code
- **Fork the Repository**:
  ```
  git clone https://github.com/your-username/EDFlowSimulator.git
  cd EDFlowSimulator
  ```
- **Create a Branch**:
  ```
  git checkout -b feature/your-feature-name
  ```
- **Follow Coding Guidelines**:
  - Use PEP 8 for Python code.
  - Write clear, concise comments and docstrings.
  - Ensure compatibility with Python 3.9+ and project dependencies (SimPy, NumPy, Pandas, Matplotlib, PyQt6).
  - Maintain the project’s structure (e.g., place new scripts in appropriate directories).
- **Test Your Changes**:
  - Run the simulation (`briefcase dev`) to verify functionality.
  - Ensure no new errors or performance regressions.
- **Commit Changes**:
  - Use descriptive commit messages (e.g., `Add priority queue optimization for critical patients`).
  - Include related issue numbers (e.g., `Fixes #123`).
- **Submit a Pull Request**:
  - Push your branch to your fork:
    ```
    git push origin feature/your-feature-name
    ```
  - Open a pull request against the `main` branch of `VoxDroid/EDFlowSimulator`.
  - Follow the [Pull Request Template](PULL_REQUEST_TEMPLATE.md).
  - Ensure your PR passes any automated checks (if applicable).

### 4. Documentation
- Update relevant documentation (e.g., `README.md`, phase-specific Markdown files) for new features or changes.
- Ensure visualizations (`*.png`) and output files (`*.csv`, `*.txt`) are documented if modified.

## Development Setup

1. Clone the repository and set up the virtual environment:
   ```
   git clone https://github.com/VoxDroid/EDFlowSimulator.git
   cd EDFlowSimulator
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
2. Install dependencies:
   ```
   pip install -r requirements.txt
   python -m pip install briefcase
   ```
3. Run the application in development mode:
   ```
   briefcase dev
   ```

## Code Review Process

- Pull requests are reviewed by the core team (@VoxDroid members).
- Expect feedback within 3–5 days.
- Address reviewer comments promptly and update your PR as needed.
- PRs must align with project objectives (e.g., improving ED efficiency, enhancing GUI usability).

## Community Standards

Adhere to our [Code of Conduct](CODE_OF_CONDUCT.md) to maintain a respectful and collaborative environment.

## Questions?

Reach out via the [Support Resources](SUPPORT.md) or open a discussion on the [GitHub Discussions](https://github.com/VoxDroid/EDFlowSimulator/discussions) page.

Thank you for helping improve healthcare efficiency in the Philippines!