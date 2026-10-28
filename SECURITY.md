# Security Policy

Security is taken seriously for Auto Web Data Spider and its users.

---

## Supported Versions

Only the latest release version on the `main` branch receives active security updates and vulnerability patches.

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

---

## Reporting a Vulnerability

If you discover a security vulnerability within **Auto Web Data Spider**, please do **not** disclose it in a public GitHub issue.

Instead, please report security vulnerabilities responsibly by:

1. Opening a **Draft Security Advisory** on GitHub under the [Security tab](https://github.com/mohammed18salah/auto-web-data-spider/security/advisories).
2. Or contacting the repository maintainer directly through GitHub.

Please provide:
- A clear description of the vulnerability and its potential impact.
- Step-by-step reproduction instructions or a minimal Proof of Concept (PoC).
- The operating system, Python version, and dependency versions used during reproduction.

You will receive an acknowledgment within **48 hours**, followed by ongoing status updates until a patch is developed and published.

---

## Security Practices in Auto Web Data Spider

- **Electron Isolation**: Electron desktop application enforces `contextIsolation: true`, `nodeIntegration: false`, and `sandbox: true` with strict Preload bridge communication.
- **Backend Origin Controls**: FastAPI enforces origin whitelisting to eliminate wildcard (`*`) CORS exploitation.
- **SQL Injection Prevention**: All persistent queries utilize **SQLModel** with parameterized statements.
- **Polite Crawling Compliance**: Built-in adherence to target domains' `robots.txt` specifications and configurable request delays to prevent denial-of-service impacts on crawled servers.
