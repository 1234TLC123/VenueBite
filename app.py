from flask import Flask, render_template, request

app = Flask(__name__)


def calculate_location_score(population, income, rent, competition):
    population_weight = 0.30
    income_weight = 0.30
    rent_weight = 0.20
    competition_weight = 0.20

    return (
        population * population_weight
        + income * income_weight
        + rent * rent_weight
        + competition * competition_weight
    )


@app.route("/")
def home():
    location = request.args.get("location")

    population_score = 85
    income_score = 80
    rent_score = 55
    competition_score = 60

    location_score = calculate_location_score(
        population_score,
        income_score,
        rent_score,
        competition_score
    )

    return render_template(
        "index.html",
        location=location,
        population_score=population_score,
        income_score=income_score,
        rent_score=rent_score,
        competition_score=competition_score,
        location_score=location_score
    )


if __name__ == "__main__":
    app.run(debug=True)
