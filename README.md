# Life Less

Life Less is an AI-powered life and productivity platform built as a full-stack app with a modern web frontend, intelligent backend services, documentation blog, and end-to-end test coverage. The project combines a Wasp-based SaaS application with a Python FastAPI AI assistant layer that supports multi-agent reasoning, memory, and proactive conversations.

At a high level, this repository is designed to be a practical starter for building a personalized assistant or digital life operating system: a user-facing app for product experiences, plus an AI backend capable of contextual chat, persona-aware responses, and future agent-based workflows.

## Overview

This repository contains four primary areas:

1. `app` — the main web application built with Wasp, React, Prisma, and Tailwind.
2. `ai_services` — the AI backend built with FastAPI, PostgreSQL, vector memory, and multi-agent orchestration.
3. `blog` — an Astro + Starlight documentation/blog site.
4. `e2e-tests` — Playwright end-to-end tests for the web app.

The app is based on the Open SaaS starter and includes many production-oriented features such as authentication, billing, analytics, admin dashboards, file upload support, and UI components.

## What is included

### Application (`app`)

The main app is a Wasp application using React on the client side and a Prisma-backed backend. It includes:

- Landing page and marketing UI
- User authentication and signup flows
- Admin dashboards
- Payment and Stripe integration
- Analytics and event tracking
- File upload utilities
- AI assistant interface
- Tailwind-based design system with shadcn/ui-inspired components

This layer is the user-facing experience for the product and acts as the app shell for the AI assistant and broader product features.

### AI Services (`ai_services`)

The Python backend is a FastAPI service focused on AI-driven conversations and orchestration. It includes:

- FastAPI API for chat and persona endpoints
- Multi-agent coordination using a crew-based architecture
- Emotional / persona-aware response logic
- Proactive conversation features
- Vector memory / semantic retrieval support
- PostgreSQL + pgvector storage
- Ollama / local model integration support
- Health and system-info endpoints

The backend is designed to support more advanced workflows later, including long-term memory, agent supervision, and contextual assistance connected to the app layer.

### Blog / Docs (`blog`)

The blog is built with Astro and the Starlight template. It is intended to host product documentation, feature notes, tutorials, and general product content.

### E2E Tests (`e2e-tests`)

This section contains Playwright tests for validating the Wasp app flows and critical user journeys.

## Tech stack

Frontend / App:
- Wasp
- React
- TypeScript
- Prisma
- Tailwind CSS
- Stripe
- Playwright

AI services:
- Python
- FastAPI
- PostgreSQL
- pgvector
- Ollama
- Crew-style multi-agent orchestration

Documentation:
- Astro
- Starlight

## Repository structure

```text
life_less/
├── app/                  # Main SaaS app (Wasp + React)
├── ai_services/          # FastAPI AI backend and agent orchestration
├── blog/                 # Astro docs/blog site
├── e2e-tests/            # End-to-end browser tests
├── README.md             # Project overview
├── ollama.tar.gz         # Local model bundle / dependency artifact
└── .gitignore            # Root ignore rules
```

## Getting started

### 1) Run the web app

From the repository root:

```bash
cd app
npm install
wasp start db
wasp start
```

If you are setting up the app for the first time and the database schema has changed, you may also need:

```bash
wasp db migrate-dev
```

### 2) Run the AI backend

```bash
cd ai_services
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The AI service exposes chat and health endpoints and is designed to work with the app’s assistant UI.

### 3) Run the blog

```bash
cd blog
npm install
npm run dev
```

### 4) Run end-to-end tests

```bash
cd e2e-tests
npm install
npx playwright test
```

## Notes

- This project is intentionally structured as a product + AI hybrid app and is suitable as a foundation for a personal productivity or life-assistant application.
- Some generated/project-template content still contains default Open SaaS placeholders and should be customized as the product evolves.
- Environment variables, secrets, and deployment-specific configuration should be managed outside the source tree and configured per environment.

## Why this project matters

Life Less is meant to combine the workflow of a polished web app with the capabilities of an intelligent assistant. The goal is not just a landing page or template, but a functional product architecture where a user-facing application and a reasoning-capable AI backend work together.

The repo is a strong foundation for:

- AI-powered personal assistant experiences
- productivity and habit tracking workflows
- custom onboarding and user support agents
- memory-driven conversation systems
- productized SaaS experiences with AI features

## Next steps

As the project evolves, the most valuable next steps are usually:

- replace template marketing text with real product branding and positioning
- connect the AI backend more deeply to app data and user context
- define a clear user persona and assistant behavior model
- add persistence for conversations, memory, and user preferences
- clean up the default starter content and tailor the product experience to the actual use case

This repository has the bones of a real product: an app, AI service, docs site, and test layer. The remaining work is mainly product definition and customization.
