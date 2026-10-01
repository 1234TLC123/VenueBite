# VenueBite — Codex Project Instructions

## Project Goal

VenueBite is a full-stack restaurant location intelligence web application.

The goal is to help restaurant owners and entrepreneurs find, analyze, compare, and evaluate potential restaurant locations.

Users should eventually be able to search by:

- City
- Neighborhood
- ZIP code
- Intersection
- Exact address

VenueBite should analyze real-world location factors such as:

- Population
- Population growth
- Household income
- Rent and property costs
- Traffic and accessibility
- Nearby businesses
- Restaurant competition
- Nearby schools and universities
- Neighborhood characteristics
- Demand for a specific restaurant concept

VenueBite should generate a Location Opportunity Score from 0–100 and explain the strengths, weaknesses, opportunities, and risks associated with the location.

The long-term product should support two major workflows:

### Analyze a Location

The user already has a location in mind.

Example:

123 Main St, Aurora, CO

VenueBite analyzes that location and produces a detailed location intelligence report.

### Find an Area

The user knows what type of restaurant they want to open and the general city or region but does not know the best location.

Example:

Restaurant concept: Congolese restaurant
Target market: Aurora, CO

VenueBite should eventually evaluate multiple areas and help identify promising candidate locations.

---

# Development Workflow

VenueBite is being developed as a real software product.

Work as a software engineering collaborator and implementation agent, not as a step-by-step programming tutor.

When given a development task:

1. Inspect the existing repository and relevant files first.
2. Understand the current architecture before modifying it.
3. Implement complete features when requested.
4. Create new files and refactor existing code when technically appropriate.
5. Fix bugs discovered during implementation.
6. Preserve working functionality unless replacing it is necessary.
7. Run appropriate tests after significant changes.
8. Keep the application runnable after major changes.
9. Explain major architectural decisions after implementation.
10. Report errors and technical debt clearly.

Do NOT:

- Turn development tasks into programming exercises.
- Ask the user to implement every small piece.
- Stop after every small change for a lesson.
- Require the user to understand every line before continuing.
- Introduce unnecessary complexity or frameworks.

If the user specifically asks for an explanation or lesson, then explain the requested concept.

Otherwise, prioritize implementation and shipping working software.

---

# Current Technology

Current core stack:

- Python 3.13
- Flask
- Jinja
- HTML
- CSS
- JavaScript
- Git
- GitHub
- Python virtual environment

Continue using Flask + Jinja for the current MVP.

Do not introduce React, Vue, or another frontend framework unless a future requirement provides a strong reason.

---

# Application-First Product Design

VenueBite is NOT primarily a marketing website.

The actual analysis application should be the primary user experience.

Avoid spending large amounts of screen space on:

- Marketing copy
- Promotional sections
- Generic "How it works" sections
- Decorative landing-page content

The application should quickly allow the user to:

1. Enter a location.
2. Select a restaurant concept.
3. Analyze the location.
4. View the location/map.
5. Receive a VenueBite Opportunity Score.
6. Inspect individual scoring factors.
7. See area insights.
8. Review nearby competition.
9. Understand strengths and risks.
10. Search another location.

The interface should eventually resemble professional location-intelligence software rather than a restaurant marketing website.

---

# Application Architecture

Maintain clear separation of concerns.

Flask routes should primarily handle:

- HTTP requests
- Input validation
- Calling application services
- Rendering responses

Business logic should NOT live directly inside route handlers.

Scoring logic should live in a dedicated scoring module.

Location and external-data retrieval should use service/provider abstractions.

Templates should handle presentation rather than business logic.

Frontend assets should live under `static/`.

Automated tests should live under `tests/`.

Prefer maintainable architecture without unnecessary enterprise complexity.

---

# Current Development Phase

The current phase is the full-stack VenueBite MVP.

Mock/sample location data may still be used while application architecture is developed.

Mock data must:

- Be clearly separated from real data providers.
- Never be represented as verified real-world information.
- Be labeled as demo/sample data in the UI.
- Be replaceable by real providers later.

Do NOT scatter mock numbers throughout routes or templates.

Use a dedicated mock-data provider/service.

---

# VenueBite Scoring Engine

VenueBite should have a dedicated scoring system.

Current/future factors may include:

- Population
- Income
- Rent
- Competition
- Population growth
- Traffic
- Accessibility
- Business density
- Restaurant demand
- Nearby schools/universities

Scoring requirements:

- Overall score should normally remain between 0 and 100.
- Higher scores should consistently mean better opportunity.
- Scoring weights should be centralized.
- Weights should be documented.
- Scoring should be deterministic and testable.
- Routes should not contain scoring formulas directly.
- Individual factor results should be available to the frontend.
- Score labels must not be represented as guarantees of business success.

As real data is integrated, scoring assumptions should be reviewed and documented.

---

# Location Analysis Workspace

The main application should eventually contain:

## Search Controls

- Location
- Restaurant concept/type
- Analyze button

## Map / Location View

Eventually display:

- Selected location
- Nearby restaurants
- Nearby businesses
- Geographic context

Until a real map provider is integrated, use an intentional placeholder.

Never fake an interactive map.

## Analysis Panel

Display:

- VenueBite Opportunity Score
- Opportunity classification
- Population score
- Income score
- Rent score
- Competition score
- Future additional factors

## Area Insights

Eventually display real metrics such as:

- Population
- Median household income
- Population growth
- Restaurant/business counts
- Rent/property indicators
- Schools/universities
- Accessibility indicators

## Nearby Competition

Eventually display real nearby restaurants with relevant information.

During the mock-data phase, demo records may be used but must be identified as demo data.

## Strengths and Risks

Generate strengths and risks from the structured analysis.

Do not simply hardcode generic marketing statements.

---

# Data Provider Architecture

Design the application so data sources can be replaced without rewriting the entire application.

The architecture should eventually support providers/services such as:

- GeocodingService
- GooglePlacesService
- CensusDataService
- TrafficDataService
- CommercialRealEstateService
- MockLocationDataService

Routes and templates should not care which provider produced the underlying data.

---

# Real Data Roadmap

Future development should progressively replace mock data.

Potential sources include:

## Maps and Places

Google Maps / Google Places may provide:

- Address search
- Geocoding
- Maps
- Nearby restaurants
- Nearby businesses
- Place information
- Competition analysis

## Demographic Data

Government or other reliable datasets may provide:

- Population
- Household income
- Population growth
- Demographics

## Property / Rent Data

Appropriate data sources may eventually provide:

- Commercial rent indicators
- Property costs
- Real-estate availability

Do not invent real-world statistics when data is unavailable.

---

# Database

A database will eventually support:

- User accounts
- Saved analyses
- Favorite locations
- Analysis history
- Comparison results

Do not add a database simply because it is on the roadmap.

Introduce persistence when required by the active development phase.

---

# Authentication

Future users may create accounts and save analyses.

When authentication is implemented:

- Hash passwords securely.
- Never store plaintext passwords.
- Protect sessions.
- Validate input.
- Use secure environment configuration.
- Follow standard authentication security practices.

---

# Security

Security is required throughout development.

Never:

- Hardcode API keys.
- Hardcode passwords.
- Commit secrets.
- Expose private API credentials in frontend JavaScript.
- Commit `.env`.

Use environment variables for secrets.

Maintain `.env.example` with placeholder values only.

Validate untrusted user input server-side.

Use Jinja escaping appropriately.

Handle errors without exposing sensitive internal information in production.

---

# AI

VenueBite may eventually use AI to explain location-analysis results.

AI should operate on structured VenueBite data.

AI may:

- Summarize analysis.
- Explain strengths.
- Explain risks.
- Answer questions about collected location data.
- Compare analyzed locations.

AI must NOT invent:

- Population statistics
- Income statistics
- Restaurant counts
- Rent prices
- Traffic statistics
- Demographic statistics
- Nearby businesses
- Other factual location information

Factual location information must come from appropriate data providers.

---

# Testing

For substantial changes:

- Run automated tests.
- Check Python syntax.
- Verify affected Flask routes.
- Verify templates render.
- Test input validation.
- Test scoring logic.
- Test important failure paths.
- Add regression tests for important bugs.

Do not hide failing tests.

---

# Git Rules

Before major work:

- Inspect `git status`.
- Understand existing uncommitted changes.
- Protect user work.

After significant implementation:

- Inspect `git diff`.
- Inspect `git status`.

NEVER commit unless the user explicitly asks you to commit.

NEVER push unless the user explicitly asks you to push.

Do not:

- Rewrite Git history without permission.
- Delete branches without permission.
- Discard uncommitted user work.
- Force push without explicit permission.

---

# Dependency Rules

Only introduce dependencies that are actually needed.

Avoid installing libraries simply because they may be useful later.

Keep dependency files accurate.

Do not introduce major frameworks without a clear architectural reason.

---

# Development Roadmap

Current:

Phase 1 — Full-stack VenueBite MVP using mock data

Future:

Phase 2 — Geocoding and interactive map

Phase 3 — Real nearby businesses and restaurant competition

Phase 4 — Real demographic and economic data

Phase 5 — Improved scoring model

Phase 6 — Database and saved analyses

Phase 7 — User authentication

Phase 8 — Location comparison and Find an Area

Phase 9 — AI-generated explanations based on real data

Phase 10 — Docker, deployment, CI/CD, monitoring, and production hardening

Do not implement future phases merely because they are listed.

Follow the active sprint prompt in `prompts/`.

---

# Before Finishing a Development Task

When appropriate:

1. Run tests.
2. Verify the application starts.
3. Verify affected routes.
4. Inspect Git diff.
5. Inspect Git status.
6. Check for accidentally introduced secrets.
7. Summarize files created.
8. Summarize files modified.
9. Report test results.
10. Report unresolved issues or technical debt.
11. Recommend the next logical development phase.

---

# Engineering Priorities

Prioritize:

Working software > tutorials

Correctness > rushing broken features

Maintainability > shortcuts

Real data > invented production data

Security > convenience

Testing > assumptions

Simple architecture > unnecessary complexity

Application functionality > marketing pages

Fast iteration > unnecessary perfection

The goal is to build VenueBite into a functional, credible full-stack software product.