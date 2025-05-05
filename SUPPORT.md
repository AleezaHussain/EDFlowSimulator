# Support Resources

Welcome to the **Emergency Department Flow Simulator** support page! Here, you’ll find resources to help you use, troubleshoot, and contribute to the project.

## Frequently Asked Questions (FAQs)

**Q: How do I run the simulator?**  
A: Follow the [Setup Instructions](README.md#setup-instructions) in the README. Ensure Python 3.9+ and dependencies are installed, then run `briefcase dev`.

**Q: Why is the GUI not displaying correctly?**  
A: Verify that PyQt6 and qtawesome are installed (`pip install pyqt6 qtawesome`). Check for errors in the terminal and ensure your system supports Qt6 rendering.

**Q: How can I interpret the simulation outputs?**  
A: Refer to the phase-specific documentation (`Phase_1.md` to `Phase_4.md`) for KPI explanations. Visualizations (e.g., `los_distribution.png`) are described in the README.

**Q: What should I do if the simulation crashes?**  
A: Check the console for error messages. Common issues include missing dependencies or incompatible Python versions. Ensure all requirements are met (`pip install -r requirements.txt`).

## Troubleshooting

- **Dependency Issues**: Run `pip install -r requirements.txt` and `python -m pip install briefcase` in a virtual environment.
- **Performance Issues**: Reduce the number of iterations (e.g., from 1000 to 100) for testing, as high iterations may strain system resources.
- **Visualization Errors**: Ensure Matplotlib is installed (`pip install matplotlib`). Verify that output files (e.g., `*.png`) are generated in the correct directory.

## Getting Help

- **GitHub Issues**: For bugs or feature requests, open an issue on the [GitHub Issues](https://github.com/VoxDroid/EDFlowSimulator/issues) page. Follow the [Contributing Guidelines](CONTRIBUTING.md#reporting-issues).
- **GitHub Discussions**: For general questions or ideas, use the [GitHub Discussions](https://github.com/VoxDroid/EDFlowSimulator/discussions) page.
- **Contact Maintainers**: Reach out to the team via email (contact details available in the repository’s main page or through GitHub).

## Contributing

Want to improve the simulator? Check the [Contributing Guidelines](CONTRIBUTING.md) for how to report issues, propose features, or submit code.

## Community Standards

Please adhere to our [Code of Conduct](CODE_OF_CONDUCT.md) when interacting with the project community.

Thank you for using the **Emergency Department Flow Simulator**!