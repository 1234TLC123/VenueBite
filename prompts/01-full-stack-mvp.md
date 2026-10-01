# VenueBite Sprint 01 — Full-Stack MVP

## Objective

Transform the existing VenueBite Flask prototype into a functional, application-first restaurant location intelligence MVP.

VenueBite should feel like a real software application, NOT a marketing website.

For this sprint, continue using clearly labeled mock/demo data. Do not connect real APIs yet.

## Before Making Changes

Before editing anything:

1. Read `AGENTS.md`.
2. Inspect the entire existing repository.
3. Run `git status`.
4. Check the current Git branch.
5. Inspect the existing Flask application and templates.
6. Preserve useful existing functionality.

Do not commit.
Do not push.

## Main User Experience

The user should be able to:

1. Open VenueBite.
2. Enter a location such as `Aurora, CO`.
3. Select or enter a restaurant concept such as `Congolese Restaurant`.
4. Click `Analyze Location`.
5. Receive a VenueBite Location Opportunity Score.
6. See the individual factors affecting the score.
7. See a location/map area.
8. See area insights.
9. See nearby competition.
10. See strengths and risks.
11. Immediately analyze another location.

## Application Layout

Build an application-style interface.

The navigation should include:

- Analyze
- Compare
- Saved Locations
- Find an Area

Only `Analyze` needs to work during this sprint.

The other features may be marked `Coming Soon`.

Do not build large marketing sections.

The analysis tool should be the main focus of the page.

## Analysis Form

Create a form containing:

- Location
- Restaurant concept/type
- Analyze Location button

Use POST for analysis submissions.

Validate input on the server.

Blank locations or restaurant concepts should display a useful validation message instead of causing an error.

## Analysis Workspace

After analysis, display something conceptually similar to:

+-------------------------------------------------------------+
| VenueBite | Analyze | Compare | Saved | Find an Area        |
+-------------------------------------------------------------+

| Location / Map            | VenueBite Opportunity Score     |
|                           |                                 |
| Map placeholder           |           0-100                 |
| Selected location         |     Opportunity classification  |
|                           |                                 |
|                           | Population       XX             |
|                           | Income           XX             |
|                           | Rent             XX             |
|                           | Competition      XX             |

Below this area display:

- Area Insights
- Nearby Competition
- Strengths
- Risks

Make the interface responsive for desktop and mobile.

## Map

Do NOT integrate Google Maps yet.

Create a professional placeholder for the future interactive map.

Display the analyzed location inside the map/location area.

Clearly indicate that live map data will be added later.

Do not create a fake interactive map.

## Mock Data

Continue using mock data during this sprint.

Existing example scores:

- Population: 85
- Income: 80
- Rent: 55
- Competition: 60

These numbers are NOT verified real-world statistics.

Clearly label mock/demo information in the UI.

Do not present these values as factual information about Aurora, Denver, or any other real location.

Move mock data into a dedicated service/provider instead of placing the values directly inside Flask routes or templates.

## Scoring Engine

Create a dedicated scoring module.

Do NOT keep scoring formulas directly inside Flask routes.

The scoring engine should:

- Accept individual factor scores.
- Use centralized weights.
- Calculate an overall score from 0 to 100.
- Return individual factors.
- Return an opportunity classification.
- Generate deterministic strengths.
- Generate deterministic risks.
- Be easy to test.
- Be easy to expand later.

Use reasonable MVP weights and document them.

Do not claim the weighting model is scientifically validated.

## Area Insights

Create a demo Area Insights section using structured mock data.

Clearly label the information as demo/sample data.

The architecture should allow this mock provider to be replaced with real demographic/economic data later.

## Nearby Competition

Create a demo Nearby Competition section.

Use sample restaurant records only to demonstrate the interface.

Clearly identify them as demo records.

Design the service so this can eventually be replaced by Google Places or another real provider.

## Architecture

Refactor the application where appropriate.

Aim for approximately:

VenueBite/
    app.py

    venuebite/
        __init__.py
        routes.py
        scoring.py

        services/
            __init__.py
            mock_data_service.py

    templates/
        base.html
        index.html
        results.html
        _search_form.html

    static/
        css/
            style.css
        js/
            main.js

    tests/
        test_scoring.py
        test_routes.py

    prompts/
        01-full-stack-mvp.md

    .env.example
    .gitignore
    requirements.txt
    README.md
    AGENTS.md

This structure is guidance.

Inspect the existing project first and use the simplest maintainable architecture.

## Flask

Keep Flask + Jinja for this sprint.

Do not introduce React, Vue, or another frontend framework.

Routes should primarily handle:

- HTTP requests
- Validation
- Calling services/business logic
- Rendering responses

Business logic should live outside route handlers.

## Design

Make VenueBite look like modern location-intelligence software.

Prioritize:

- Clean dashboard
- Location analysis workspace
- Large visible Opportunity Score
- Factor cards
- Map/location context
- Area insights
- Nearby competition
- Strengths and risks
- Professional spacing
- Responsive design

Do NOT turn VenueBite into a marketing landing page.

The application itself is the product.

## Security

Do not hardcode API keys, passwords, tokens, or secrets.

Make sure `.env` is ignored by Git.

If needed, create `.env.example` containing placeholders only.

Validate user input server-side.

Do not render user input as trusted HTML.

## Testing

Add tests for the important MVP behavior.

At minimum test:

### Scoring

- Overall score calculation
- Score boundaries
- Classification
- Invalid factor values where appropriate

### Flask Routes

- GET `/`
- Successful analysis POST
- Empty location
- Missing restaurant concept

Run the tests after implementation.

## Requirements

Create or update `requirements.txt`.

Only include dependencies actually required by the current application.

Do not install future technology unnecessarily.

## README

Update `README.md` with:

- What VenueBite is
- Current features
- Mock-data limitation
- Project structure
- Installation instructions
- How to run the application
- How to run tests
- High-level roadmap

## Definition of Done

Sprint 01 is complete when:

1. VenueBite starts successfully.
2. The analysis interface works.
3. A user can enter a location.
4. A user can enter/select a restaurant concept.
5. Analysis uses POST.
6. Input validation works.
7. Mock data is separated into a service/provider.
8. Scoring is separated from Flask routes.
9. VenueBite calculates an Opportunity Score.
10. Factor scores are displayed.
11. Opportunity classification is displayed.
12. A map/location placeholder exists.
13. Area Insights are displayed.
14. Demo nearby competition is displayed.
15. Strengths are displayed.
16. Risks are displayed.
17. Demo data is clearly labeled.
18. The interface works reasonably on desktop and mobile.
19. Tests exist and pass.
20. README is updated.
21. No secrets are introduced.
22. Existing useful functionality is preserved where appropriate.
23. Nothing is committed.
24. Nothing is pushed.

## Final Verification

After implementation:

1. Run the test suite.
2. Run Python syntax/compile checks.
3. Verify the Flask application starts.
4. Verify the home page.
5. Verify successful analysis.
6. Verify validation errors.
7. Run `git diff`.
8. Run `git status`.
9. Check that no secrets were introduced.

Then give me an engineering summary containing:

- What you implemented
- Files created
- Files modified
- Architecture decisions
- Test results
- Any unresolved issues
- Recommended next sprint

Do NOT commit.

Do NOT push.

Stop after Sprint 01.