from flask import Flask, render_template, request

app = Flask(__name__)

import requests

import csv

response = requests.get("http://api.nbp.pl/api/exchangerates/tables/C?format=json")
data = response.json()

rates = data[0]["rates"]

csv_file = "currency_rates.csv"

currency_rates = {}
with open(csv_file, mode='r', newline='') as file:
    reader = csv.DictReader(file, delimiter=';')
    # Nagłówki kolumn
    for row in reader:
        currency_rates[row["code"]] = {"currency":row["currency"], "bid":float(row["bid"]), "ask": float(row["ask"])}

print(f"Dane zostały zapisane do pliku {csv_file}")

@app.route("/", methods=["GET", "POST"])
def calculator():
    if request.method == "POST":
        currency_code = request.form.get("currency")
        amount = float(request.form.get("amount"))

        if currency_code in currency_rates:
            bid_rate = currency_rates[currency_code]["bid"]
            cost_pln = amount * bid_rate
            return render_template("index.html", result=f"Koszt {amount} {currency_code} to {cost_pln:.2f} PLN", currency_codes=currency_rates.keys())

    return render_template("index.html", result=None, currency_codes=currency_rates.keys())

if __name__ == "__main__":
    app.run(debug=True)