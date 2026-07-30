# Hearth — return-to-work support platform

**Live demo: [reentry-app.onrender.com](https://reentry-app.onrender.com/)**
*(university project — demo data only; first load may take a moment on Render's free tier)*

Hearth is a multi-role web platform supporting women returning to work after
parental leave. Returning employees, their managers, and HR each get their own
view: guided onboarding flows, a progress diary that employees can choose to
share, and dashboards that help managers and HR support the transition instead
of just tracking it.

## Roles and features

- **Employee** — guided re-onboarding, progress diary (private by default,
  shareable by choice), personal dashboard
- **Manager** — team view, onboarding oversight, shared diary highlights
- **HR** — organisation-wide dashboards and administration

## Stack

Flask + SQLite, server-rendered templates with vanilla JS and CSS.
Deployed on Render (`Procfile` + `requirements.txt`).

Run locally:

```bash
pip install -r requirements.txt
python app.py
```

## Context

Group project for DECO7180 at The University of Queensland (2026), built by a
student team. My part: user research (surveys and interviews), qualitative
thematic analysis, and front-end development. UI design was AI-assisted.

## Author

Cristina Zhang — [hellocriss777.github.io](https://hellocriss777.github.io/)
