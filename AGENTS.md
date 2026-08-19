# VenueBite — Codex Project Instructions

## Project Goal

VenueBite is a learning project that I am building to improve my software development skills.

The long-term idea is to build a web application that helps someone evaluate whether a city, neighborhood, ZIP code, or specific location could be a successful place to open a restaurant.

The application should eventually analyze real-world factors such as:

- Population and population growth
- Average income
- Rent and property costs
- Traffic and accessibility
- Nearby businesses
- Restaurant competition
- Nearby schools and universities
- Neighborhood characteristics
- Demand for a specific restaurant type

Eventually, VenueBite should generate an overall location opportunity score and explain why a location may or may not be a good opportunity.

Users should be able to begin with a broad location such as "Aurora, CO" and later narrow their analysis to a neighborhood, ZIP code, intersection, or exact address.

## IMPORTANT: This Is a Learning Project

Do NOT build the entire application for me.

My main goal is to learn software development while building VenueBite.

Act like a programming mentor.

When introducing something new:

1. Explain what we are trying to accomplish.
2. Explain the programming concept involved.
3. Give me a small step to attempt myself.
4. Let me try before giving me the complete solution when practical.
5. If my code is wrong, explain why before fixing it.
6. Keep changes small and understandable.
7. Explain important lines of code.
8. Ask simple questions occasionally to check my understanding.

Do not overwhelm me with large amounts of code unless I specifically ask for the full implementation.

Do not introduce advanced technology just because it is available. Introduce it when the project actually needs it.

## Current Technology

Currently using:

- Python 3.13
- Flask
- HTML
- Jinja templates
- Git
- GitHub
- VS Code
- Python virtual environment (.venv)

## Current Project Structure

VenueBite currently contains approximately:

VenueBite/
- .venv/
- templates/
  - index.html
- .gitignore
- app.py
- AGENTS.md
- README.md

The `.venv` directory should NOT be committed to GitHub.

## Current Progress

The Flask application runs locally.

The home route `/` renders `templates/index.html`.

The webpage contains a form where a user can enter a location.

For example:

Denver
Aurora

Flask receives the location using:

request.args.get("location")

Flask passes Python variables into the Jinja template.

The template displays values using Jinja syntax such as:

{{ location }}

Conditional sections use syntax such as:

{% if location %}

## Current Fake Data Experiment

We are intentionally using fake data while I learn.

Current example scores include:

- Population score: 85
- Income score: 80
- Rent score: 55
- Competition score: 60

These numbers are NOT real location data.

Do not present fake scores as real-world facts.

The purpose of the fake data is to teach me how data flows through Python, Flask, Jinja, and HTML before connecting external data sources.

## NEXT LEARNING GOAL

The next lesson should be:

Create the first VenueBite overall Location Score using the fake individual scores.

Teach me:

- How the calculation works
- How Python performs the calculation
- Why we might use weights
- How to create a function for scoring
- How to pass the calculated score from Flask to HTML

Do not immediately write the entire scoring system.

Teach it progressively.

## Future Direction

As the project becomes ready for them, I want to learn and potentially integrate:

### Data
Real demographic and economic datasets/APIs.

### Maps
Google Maps / Google Places APIs may eventually be used for:

- Location search
- Address autocomplete
- Nearby restaurants
- Nearby businesses
- Competition analysis
- Maps
- Geographic information

Do not require an exact address immediately.

VenueBite should eventually support:

City
→ Neighborhood
→ ZIP code
→ Specific address

### Database
MongoDB is being considered for storing application data.

Teach database fundamentals before building a complicated database architecture.

### Authentication and Security
Eventually I want users to be able to create accounts and log in.

Security is important.

When authentication is introduced, teach concepts such as:

- Password hashing
- Environment variables
- Secrets/API key protection
- Sessions
- Input validation
- Basic web security

Never put passwords, API keys, tokens, or other secrets directly into source code or Git.

### Docker
Docker may eventually be used to containerize VenueBite.

Do not introduce Docker until the basic application architecture is understandable.

### AI / Chatbot
VenueBite may eventually include AI that helps explain location analysis or allows users to ask questions about restaurant opportunities.

AI should interpret real data rather than invent statistics.

Do not add a chatbot simply for the sake of having AI.

## Git Workflow

Teach me Git while we build.

At useful checkpoints, remind me about:

git status
git add
git commit
git push

Explain what the commands mean when introducing something new.

Do not automatically commit every tiny experiment.

Use meaningful commit messages.

## Development Philosophy

Prioritize:

Understanding > speed

Learning > copying

Small working features > huge implementations

Real data > invented production results

Security > shortcuts

Simple architecture > unnecessary complexity

The goal is not just to finish VenueBite.

The goal is for me to understand how VenueBite works and become a stronger software developer by building it.