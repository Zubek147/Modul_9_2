from flask import Flask, render_template, request, redirect, url_for
import requests
import csv
from datetime import datetime
import os

app = Flask(__name__)

# Uzyskaj bieżącą ścieżkę do folderu, w którym znajduje się plik aplikacji
APP_FOLDER = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(APP_FOLDER, "currency_rates.csv")
last_update_date = None  # Dodaj zmienną globalną przechowującą datę ostatniej aktualizacji

def load_currency_rates():
    try:
        with open(CSV_FILE, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter=';')
            currency_rates = {}
            for row in reader:
                currency_rates[row["code"]] = {"currency": row["currency"], "bid": float(row["bid"]), "ask": float(row["ask"]), "date": row.get("date")}
            return currency_rates
    except FileNotFoundError:
        return None

def save_currency_rates(currency_rates):
    with open(CSV_FILE, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["code", "currency", "bid", "ask", "date"], delimiter=';')
        writer.writeheader()
        for code, data in currency_rates.items():
            writer.writerow({"code": code, "currency": data["currency"], "bid": data["bid"], "ask": data["ask"], "date": data.get("date")})

def fetch_currency_rates():
    response = requests.get("http://api.nbp.pl/api/exchangerates/tables/C?format=json")
    data = response.json()
    currency_rates = {rate["code"]: {"currency": rate["currency"], "bid": float(rate["bid"]), "ask": float(rate["ask"]), "date": data[0]["effectiveDate"]} for rate in data[0]["rates"]}
    global last_update_date
    last_update_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_currency_rates(currency_rates)
    return currency_rates

@app.route("/", methods=["GET", "POST"])
def info_and_download():
    global show_update_button
    if request.method == "POST":
        action = request.form.get("action")

        if action == "download":
            # Pobierz najnowsze dane z API i zapisz do pliku
            currency_rates = fetch_currency_rates()
            show_update_button = False
            return redirect(url_for("calculator"))
        elif action == "update":
            # Obsługa aktualizacji kursów
            currency_rates = fetch_currency_rates()
            print("Currency Codes:", currency_rates.keys())
            return render_template("calculator.html", result=None, currency_codes=(currency_rates.keys() if currency_rates else None), date=last_update_date)
    
    # Sprawdź, czy plik CSV istnieje
    show_update_button = os.path.exists(CSV_FILE)

    return render_template("info_and_download.html", show_update_button=show_update_button, date=last_update_date)

@app.route("/calculator", methods=["GET", "POST"])
def calculator():
    currency_rates = load_currency_rates()
    error_message = None

    if request.method == "POST":
        action = request.form.get("action")

        if action == "calculate":
            currency_code = request.form.get("currency")
            amount = request.form.get("amount")

            if not amount:
                amount = 0  # Jeśli pole jest puste, ustaw wartość na 0
            else:
                try:
                    amount = float(amount)
                except ValueError:
                    error_message = "Error, wprowadź prawidłową wartość liczbową"
                    return render_template("calculator.html", result=None, currency_codes=currency_rates.keys(), date=last_update_date, error_message=error_message)

            if currency_code not in currency_rates:
                return render_template("calculator.html", result=None, currency_codes=currency_rates.keys(), date=last_update_date, error_message=error_message)

            bid_rate = currency_rates[currency_code]["bid"]
            cost_pln = float(amount) * bid_rate
            date = currency_rates[currency_code]["date"]
            return render_template("calculator.html", result=f"Koszt {amount} {currency_code} to {cost_pln:.2f} PLN", currency_codes=currency_rates.keys(), date=last_update_date, error_message=error_message)

        elif action == "update":
            # Obsługa aktualizacji kursów
            currency_rates = fetch_currency_rates()
            return render_template("calculator.html", result=None, currency_codes=(currency_rates.keys() if currency_rates else None), date=last_update_date, error_message=error_message)

    return render_template("calculator.html", result=None, currency_codes=(currency_rates.keys() if currency_rates else None), date=last_update_date, error_message=error_message)

if __name__ == "__main__":
    app.run(debug=True)
