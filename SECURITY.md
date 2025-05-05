# Security Policy

## Supported Versions

The **Emergency Department Flow Simulator** is currently maintained for the latest version of the project, running on **Python 3.9+** with the dependencies listed in `requirements.txt`. Security updates are applied to the `main` branch.

| Version | Supported          |
|---------|--------------------|
| Latest  | ✅                 |
| Older   | ❌                 |

## Reporting a Vulnerability

If you discover a security vulnerability in the **Emergency Department Flow Simulator**, please report it responsibly by following these steps:

1. **Do Not Open a Public Issue**: Avoid disclosing vulnerabilities publicly (e.g., via GitHub Issues) to prevent exploitation.
2. **Contact the Maintainers**:
   - Email the project maintainers at the contact provided in the [Support Resources](SUPPORT.md).
   - Include a detailed description of the vulnerability, steps to reproduce, and potential impact.
3. **Response Time**:
   - Expect an acknowledgment within 48 hours.
   - The team will investigate and provide updates on resolution progress.
4. **Resolution**:
   - Accepted vulnerabilities will be addressed promptly, with patches applied to the `main` branch.
   - You will be notified when the issue is resolved.
5. **Disclosure**:
   - After resolution, we may coordinate with you to publicly disclose the vulnerability, crediting you (if desired) for the discovery.

## Security Best Practices

To ensure the security of your local setup:
- Keep dependencies up to date (`pip install -r requirements.txt --upgrade`).
- Run the application in a virtual environment to isolate dependencies.
- Avoid exposing the application to public networks, as it is designed for local use.
- Regularly check for updates to the repository for security patches.

## Known Limitations

- The project does not currently implement authentication or encryption, as it is intended for local simulation use.
- External dependencies (e.g., SimPy, PyQt6) may have their own vulnerabilities; monitor their respective repositories for updates.

Thank you for helping keep the **Emergency Department Flow Simulator** secure!