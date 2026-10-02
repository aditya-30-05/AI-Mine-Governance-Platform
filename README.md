# AI-Based Smart Governance & Compliance Monitoring System for Coal Mines

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?style=flat-square&logo=react)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.2-3178C6?style=flat-square&logo=typescript)](https://www.typescriptlang.org)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4-38B2AC?style=flat-square&logo=tailwind-css)](https://tailwindcss.com)
[![Vite PWA](https://img.shields.io/badge/PWA-Ready-10b981?style=flat-square)](https://vite-pwa-org.netlify.app)
[![Tests](https://img.shields.io/badge/pytest-23%2F23%20passed-brightgreen?style=flat-square)](https://docs.pytest.org)

An AI-powered smart governance, compliance monitoring, and audit verification platform built for coal mines and the Directorate General of Mines Safety (DGMS).

---

## 🌟 Key Features

1. **AI-Driven Risk & Violation Assessment**:
   - Provider-agnostic LLM integration with automatic rule-based fallback.
   - Coal Mines Regulations (CMR) 2017 compliance validation engine.
   - Deterministic risk severity scoring, mitigation recommendations, and recurring violation detection.

2. **Tamper-Evident SHA-256 Audit Trail**:
   - Cryptographic hash-chained audit ledger for all inspection and governance state transitions:
     $$H_i = \text{SHA-256}(\text{CanonicalJSON}(Payload_i) \parallel H_{i-1})$$
   - Real-time tampering detection, broken block localization, and audit state verification.

3. **Offline-First Field Inspections (PWA)**:
   - Built with Vite PWA and IndexedDB (`idb`) caching.
   - Field inspectors can capture observations, photos, and hazard notes offline with automatic background sync upon reconnection.

4. **Interactive GIS Spatial Mapping**:
   - Leaflet interactive map with custom severity markers, mine boundary polygons, and coordinate plotting.
   - Real-time hazard visualization across open-cast and underground mine sections.

5. **Live Governance & WebSocket Alerts**:
   - Real-time critical violation push alerts, task escalation broadcasts, and live compliance updates.
   - Interactive role-based dashboard for Executive Corporate Managers, Mine Managers, and Compliance Officers.

6. **OCR & Automated PDF Report Generator**:
   - Document repository with Tesseract / PaddleOCR pipeline for safety logbook digitisation.
   - Automated PDF compliance audit summary report generator.

---

## 🏗️ Architecture & Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.10+)
- **Database ORM**: SQLAlchemy 2.0 (AsyncIO) with Alembic migrations
- **Databases**: PostgreSQL + PostGIS (Production) / In-Memory Demo Store (Stand-alone local execution)
- **Security**: JWT OAuth2, Passlib (Bcrypt), Strict Role-Based Access Control (RBAC)
- **Real-Time**: WebSockets for push notifications and critical risk alerts

### Frontend
- **Framework**: React 18 with TypeScript
- **Tooling**: Vite 5 with `vite-plugin-pwa`
- **Styling**: TailwindCSS with modern dark-mode palette and glassmorphism styling
- **Charts & Maps**: Recharts, Leaflet, React-Leaflet
- **State Management**: Zustand & TanStack Query (React Query v5)

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10+
- Node.js 18+ & npm
- Git

---

### Option A: Local Standalone Mode (No Docker Required)

The platform includes an intelligent demo engine that runs out-of-the-box with pre-seeded synthetic data.

#### 1. Start the Backend API
```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Documentation (Swagger): [http://127.0.0.1:8000/api/docs](http://127.0.0.1:8000/api/docs)
- Health Check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

#### 2. Start the Frontend Application
```bash
cd frontend
npm install
npm run dev
```
- Web Application: [http://localhost:5173](http://localhost:5173)

---

### Option B: Full Infrastructure with Docker
```bash
docker compose up -d postgres redis
cd backend
alembic upgrade head
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🔑 Demo Login Credentials

Quick login buttons are available directly on the login screen for testing each persona:

| Role | Official Email | Password | Scope & Permissions |
|---|---|---|---|
| **System Admin** | `admin@coalmine.gov.in` | `Admin@1234` | Full platform administration, audit verification |
| **Mine Manager** | `manager.a@coalmine.gov.in` | `Manager@1234` | Operational KPIs, task delegation, risk mitigation |
| **Compliance Officer** | `compliance@coalmine.gov.in` | `Compliance@1234` | Regulation enforcement, inspection approvals |
| **Field Officer** | `field.officer@coalmine.gov.in` | `Field@1234` | On-site inspections, observation logging |
| **Corporate Manager**| `corporate@coalmine.gov.in` | `Corporate@1234` | Multi-mine aggregate analytics |

---

## 🧪 Testing

Run the automated test suite covering AI analysis, API routes, cryptographic audit chains, authentication, and the rules engine:

```bash
python -m pytest
```

---

## 🔒 Security & Compliance
- **Data Integrity**: SHA-256 cryptographic linkage ensures non-repudiation of inspection records.
- **Regulations**: Adheres to the Directorate General of Mines Safety (DGMS) guidelines and Coal Mines Regulations (CMR) 2017.
- **Environment**: Synthetic demo datasets are provided strictly for research, prototyping, and demonstration purposes.
