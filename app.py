from flask import Flask, render_template, request

app = Flask(__name__)


@app.route("/")
def home():
    location = request.args.get("location")

    population_score = 85
    income_score = 80
    rent_score = 55
    competition_score = 60

    return render_template(
        "index.html",
        location=location,
        population_score=population_score,
        income_score=income_score,
        rent_score=rent_score,
        competition_score=competition_score
    )


if __name__ == "__main__":
    app.run(debug=True)