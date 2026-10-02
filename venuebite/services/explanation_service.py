"""Pure, deterministic interpretation of scores and their evidence; no data fetching."""

from dataclasses import dataclass

from venuebite.distance import METERS_PER_MILE
from venuebite.scoring import CLASSIFICATION_BANDS, RISK_THRESHOLD, STRENGTH_THRESHOLD


MAX_STRENGTHS = 2
MAX_RISKS = 4
CLOSE_DIRECT_RADIUS_MILES = 0.5
CLOSE_DIRECT_MINIMUM = 2


@dataclass(frozen=True)
class ExplanationItem:
    key: str
    label: str
    score: float
    weighted_points: float
    status: str
    explanation: str


@dataclass(frozen=True)
class ExplanationReport:
    summary: str
    strengths: tuple[ExplanationItem, ...]
    risks: tuple[ExplanationItem, ...]
    quality_notes: tuple[str, ...]
    assumptions: str
    no_numeric_risks: bool


def _competition_context(competition):
    if not competition or not competition.available:
        return "", False
    close_count = sum(row.is_direct and row.distance_meters <= CLOSE_DIRECT_RADIUS_MILES * METERS_PER_MILE
                      for row in competition.rows)
    text = (f"{competition.model.level} observed pressure: {competition.direct_count} direct matches "
            f"among {len(competition.rows)} returned restaurants within {competition.radius_miles:g} mi.")
    if competition.nearest_direct_meters is not None:
        text += f" Nearest direct match: {competition.nearest_direct_label}."
    if close_count >= CLOSE_DIRECT_MINIMUM:
        text += f" {close_count} direct matches are within {CLOSE_DIRECT_RADIUS_MILES:g} mi."
    if not competition.rows:
        text += " An empty provider sample is not proof that no restaurants exist."
    return text, close_count >= CLOSE_DIRECT_MINIMUM


def _real_context(key, strong, demographics, competition):
    census = demographics.data if demographics else None
    if key == "population":
        value = f" ({census.population:,} people)" if census and census.population is not None else ""
        return (f"Tract population context{value} is a relative strength in this model."
                if strong else f"Tract population context{value} scores below the review threshold.") + " This is not a customer or demand estimate."
    if key == "income":
        value = f" (${census.median_household_income:,})" if census and census.median_household_income is not None else ""
        return (f"Household purchasing-power context{value} is a relative strength in this tract."
                if strong else f"Household purchasing-power context{value} needs closer review.") + " It does not measure disposable income or restaurant spending."
    if key == "competition":
        context, _ = _competition_context(competition)
        return context or ("The observed competition factor indicates lower pressure." if strong else "Observed competitive pressure warrants closer review.")
    return "The occupancy factor indicates more favorable affordability context." if strong else "Occupancy affordability context needs closer review."


def _gap_context(factor, source):
    if factor.key == "rent" and source.status in {"demo", "fallback"}:
        text = "Commercial rent remains demo, not live market data. Verify occupancy costs before a site decision."
    elif source.status == "partial":
        text = f"{factor.label} has only partial usable evidence; verify the missing inputs."
    elif source.status == "unavailable":
        text = f"{factor.label} evidence is unavailable; this factor is not supported by verified data."
    else:
        text = f"{factor.label} uses fictional demo {'fallback' if source.status == 'fallback' else 'data'}, not verified site evidence."
    if source.reason:
        text += f" {source.reason}"
    if source.status == "partial":
        text += " Half of this factor's coverage weight is credited; its score is unchanged."
    else:
        text += " It contributes no real-data coverage."
    return text


def explain_analysis(score, provenance, coverage, *, demographics=None, competition=None):
    strengths, risks = [], []
    _, close_direct = _competition_context(competition)
    for factor in score.factors:
        source = provenance[factor.key]
        if source.status != "real":
            text = _gap_context(factor, source)
            priority = factor.weight * (1 - next(item.credit for item in coverage.factors if item.key == factor.key))
            target = risks
        elif factor.score < RISK_THRESHOLD or (factor.key == "competition" and close_direct):
            text = _real_context(factor.key, False, demographics, competition)
            priority = (100 - factor.score) * factor.weight / 100
            target = risks
        elif factor.score >= STRENGTH_THRESHOLD:
            text = _real_context(factor.key, True, demographics, competition)
            priority = factor.weighted_points
            target = strengths
        else:
            continue
        text += f" Score {factor.score:g}/100 contributes {factor.weighted_points_label} points at {factor.weight_percent}% weight."
        item = ExplanationItem(factor.key, factor.label, factor.score, factor.weighted_points, source.status, text)
        target.append((priority, item))
    # Stable sorting keeps centralized factor order for equal contributions or risk priorities.
    strengths = tuple(item for _, item in sorted(strengths, key=lambda pair: -pair[0])[:MAX_STRENGTHS])
    risks = tuple(item for _, item in sorted(risks, key=lambda pair: -pair[0])[:MAX_RISKS])
    summary = f"VenueBite scores this location at {score.overall_score:.1f}/100. "
    if strengths:
        summary += "Relative model strengths: " + ", ".join(f"{item.label.lower()} ({item.weighted_points:.2f} points)" for item in strengths) + ". "
    else:
        summary += "No fully real-data factor meets the strength threshold. "
    if competition and competition.available:
        summary += f"{competition.model.level} observed competition pressure. "
    gaps = [factor.label.lower() for factor in score.factors if provenance[factor.key].status != "real"]
    if gaps:
        summary += "Evidence needs verification for " + ", ".join(gaps) + ". "
    summary += f"Data Coverage is {coverage.percent:g}%, not a probability of business success."

    notes = []
    if demographics:
        notes.append("Census ACS 5-year estimates are survey-based; available 90% margins of error are shown below. The containing tract is demographic context, not a trade area or customer count. Uncertainty does not silently adjust scores or coverage.")
    if competition:
        notes.append("Mapbox restaurants are an observed provider sample, not an exhaustive business census. Search caps, matching and proximity affect comparisons; usable sample coverage is not completeness of local restaurant discovery.")
        if competition.available:
            notes.append(competition.coverage_note)
    if provenance["rent"].status in {"demo", "fallback"}:
        notes.append("Commercial rent remains demo; residential rent is not a substitute. No live commercial occupancy cost has been verified.")
    notes.append("Data Coverage credits usable factor evidence, not accuracy, statistical confidence, concept demand, or probability of success. Model weights and thresholds are not scientifically validated.")
    weights = ", ".join(f"{factor.label} {factor.weight_percent}%" for factor in score.factors)
    bands = ", ".join(f"{key} at {minimum}+" if minimum else f"{key} below {CLASSIFICATION_BANDS[-2][0]}" for minimum, _, key in CLASSIFICATION_BANDS)
    assumptions = (f"Factor weights: {weights}. Higher factor scores always mean better opportunity. "
                   f"Strengths start at {STRENGTH_THRESHOLD}; risks are below {RISK_THRESHOLD}. "
                   "Only fully real-data factors qualify as strengths; demo, partial and unavailable inputs add verification risks. "
                   f"Overall classifications: {bands}. Overall uses the unrounded weighted sum, rounded once to one decimal before classification; displayed contributions use two decimals. "
                   "These MVP thresholds and weights are not scientifically validated.")
    return ExplanationReport(summary, strengths, risks, tuple(dict.fromkeys(note for note in notes if note)), assumptions,
                             not any(factor.score < RISK_THRESHOLD for factor in score.factors))
