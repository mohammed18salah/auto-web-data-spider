# Contributing to Auto Web Data Spider

Thank you for your interest in contributing to **Auto Web Data Spider**! We welcome contributions from developers, researchers, and data enthusiasts of all experience levels.

This guide outlines our development workflow, standards, and how to get your changes merged quickly and smoothly.

---

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please treat all community members with respect and professionalism.

---

## How Can You Contribute?

You can contribute to Auto Web Data Spider in several ways:

1. **Reporting Bugs**: Found an unexpected behavior or crash? Open a bug report.
2. **Suggesting Enhancements**: Have ideas for new data extractors, export formats, or graph features? Open a feature request.
3. **Submitting Code**: Fix an open issue or implement a requested capability.
4. **Improving Documentation**: Fix typos, add examples, or clarify complex concepts in the documentation.
5. **Writing Tests**: Enhance test coverage across crawler components, NLP parsers, or UI modules.

---

## Development Setup

### Prerequisites

- **Python**: `3.11` or higher
- **Node.js**: `18.0.0` or higher
- **Git**: Installed and configured

### 1. Fork and Clone

```bash
git clone https://github.com/<your-username>/auto-web-data-spider.git
cd auto-web-data-spider
```

### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate       # Linux/macOS
# or .venv\Scripts\Activate.ps1 # Windows PowerShell

# Install dependencies in editable mode
pip install -r requirements.txt
python -m spacy download en_core_web_sm
pip install -e .
```

### 3. Frontend Setup

In a separate terminal:

```bash
cd frontend
npm install
```

---

## Development Workflow

### Creating a Branch

Always create a dedicated feature or bugfix branch from `main`:

```bash
git checkout -b feat/my-new-feature
# or
git checkout -b fix/issue-description
```

### Running Tests

Before submitting your changes, verify that all tests pass:

#### Backend Verification:
```bash
cd backend
python tests/test_new_fixes.py
python tests/test_step0.py
python tests/test_step1.py
python tests/test_step2.py
python tests/test_step3.py
```

#### Frontend Type Checking & Build:
```bash
cd frontend
npm run build
```

---

## Coding Standards

### Python (Backend)
- Follow **PEP 8** style guidelines.
- Always use explicit type annotations for function signatures.
- Prefer `datetime.now(timezone.utc)` over deprecated `datetime.utcnow()`.
- Keep database operations parameterized through **SQLModel** to prevent SQL injection.
- Ensure all public functions and classes have descriptive docstrings.

### TypeScript / React (Frontend)
- Adhere to strict TypeScript typing; avoid using `any`.
- Keep components modular and reusable under `frontend/src/`.
- Ensure bilingual support is maintained for all UI strings (Arabic RTL and English LTR).
- Maintain security isolation in Electron: never enable `nodeIntegration` without `contextIsolation`.

### Commit Conventions
We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` A new feature or capability
- `fix:` A bug fix
- `docs:` Documentation updates
- `refactor:` Code restructuring without changing external behavior
- `test:` Adding or updating tests
- `chore:` Dependency bumps, CI workflow adjustments, or build script updates

---

## Submitting a Pull Request

1. Push your branch to your GitHub fork:
   ```bash
   git push origin feat/my-new-feature
   ```
2. Open a Pull Request against the `main` branch of `mohammed18salah/auto-web-data-spider`.
3. Fill out the Pull Request template completely.
4. Ensure CI automated checks pass.
5. Address any code review feedback promptly.

Once approved, your PR will be squash-merged into `main`. Thank you for helping make Auto Web Data Spider better!
