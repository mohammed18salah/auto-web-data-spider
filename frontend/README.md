# Auto Web Data Spider Frontend

React 19 + TypeScript + Electron desktop user interface for the Auto Web Data Spider autonomous crawling and knowledge discovery system.

---

## Features

- **React 19 Architecture** — Built with modern React 19, TypeScript, and Vite for instant HMR and high-performance rendering.
- **Glassmorphic Design System** — Tailored obsidian dark mode (`#030305`) and clean light mode with smooth transitions.
- **Interactive Knowledge Graph Viewer** — Hardware-accelerated 60 FPS HTML5 Canvas engine rendering interconnected entities in cosmic deep-space view:
  - Concentric planetary orbits for balanced topology.
  - Coulomb repulsion and Hooke's spring physics.
  - Multi-category entity tagging (People, Organizations, Concepts, Publications).
  - Search filter, category pills, smooth zoom/pan camera controls, and detailed side-inspector card.
  - One-click recursive entity crawling (`onExpandTopic`).
- **Full Bilingual Support** — Real-time switching between Arabic (RTL) and English (LTR).
- **Session Explorer & Analytics** — View analyzed sources, quality ratings, word counts, extracted summaries, and full JSON payloads.
- **Strict Accessibility & Clean Aesthetics** — Zero emojis across the entire UI for a professional, high-signal experience.
- **Electron Desktop Bridge** — Context-isolated preload script with secure IPC communication.

---

## Getting Started

### Development Mode

```bash
# Install dependencies
npm install

# Run Vite dev server in web browser mode
npm run dev

# Run inside Electron desktop window
npm run electron:dev
```

### Production Build

```bash
# Build production bundle with TypeScript checks
npm run build

# Package Electron executable
npm run electron:build
```
