import os

from flask import Flask, jsonify, request, abort
from flask_restful import Api, reqparse, Resource
from flask_pymongo import PyMongo


app = Flask(__name__)

app.config.update(
    SERVER_NAME=os.environ.get('SERVER_NAME'),
    FLASK_DEBUG=os.environ.get('DEBUG'),
    MONGO_URI=os.environ.get('MONGO_URI')
)

mongodb_client = PyMongo(app)
db = mongodb_client.db

api = Api(app)
parser = reqparse.RequestParser()


@app.errorhandler(404)
def not_found(error):
    return jsonify(error=str(error)), 404


@app.errorhandler(400)
def bad_request(error):
    return jsonify(error=str(error)), 400


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify(error=str(error)), 500


class CreateInitData(Resource):
    def get(self):
        currency_names = ["RUB", "USD", "EUR", "GBP", "UAH", "JPY", "KRW"]
        existing_currencies = db.currencies.find({"currency": {"$in": currency_names}})
        result = {currency["currency"]: currency["rate"] for currency in existing_currencies}
        if result:
            abort(400, f"These currencies exist: {result}")

        db.currencies.insert_many([
            {"currency": "RUB", "rate": 1},
            {"currency": "USD", "rate": 72.5},
            {"currency": "EUR", "rate": 84.2},
            {"currency": "GBP", "rate": 98.8},
            {"currency": "UAH", "rate": 2.7},
            {"currency": "JPY", "rate": 0.65},
            {"currency": "KRW", "rate": 0.061},
        ])
        return jsonify(message="success")


class GetCourseCurrency(Resource):
    def get(self, currency_name):
        currency = db.currencies.find_one({"currency": currency_name})

        if not currency:
            abort(404, "Currency not found")

        return jsonify({currency["currency"]: currency["rate"]})


class ConvertCurrency(Resource):
    def post(self):
        parser.add_argument('from', type=str, help="'from' must be string")
        parser.add_argument('to', type=str, help="'to' must be string")
        parser.add_argument('value', type=int, help="'value' must be integer")
        args = parser.parse_args()
        currency_from = str(args['from'])
        currency_to = str(args['to'])
        value = int(args['value'])

        if ((len(currency_from) != 3)
                or (currency_from != currency_from.upper())):
            abort(400, "Wrong format 'from'")
        if ((len(currency_to) != 3)
                or (currency_to != currency_to.upper())):
            abort(400, "Wrong format 'to'")

        rate_currency_from = db.currencies.find_one({"currency": currency_from})["rate"]
        if not rate_currency_from:
            abort(404, "Currency 'from' not found")
        value_rub = rate_currency_from * value

        rate_currency_to = db.currencies.find_one({"currency": currency_to})["rate"]
        if not rate_currency_to:
            abort(404, "Currency 'to' not found")
        value_to = value_rub / rate_currency_to

        return jsonify({f"value_{currency_to}": round(value_to, 2)})


class CRUD(Resource):
    def get(self):
        currencies = db.currencies.find()
        result = {currency["currency"]: currency["rate"] for currency in currencies}
        return jsonify(result)

    def post(self):
        list_for_db = []
        currency_names = [key for key in request.json.keys()]
        existing_currencies = db.currencies.find({"currency": {"$in": currency_names}})
        result = {currency["currency"]: currency["rate"] for currency in existing_currencies}
        if result:
            abort(400, f"These currencies exist: {result}")

        for currency, rate in request.json.items():

            if (not (len(currency) == 3)
                    or not(currency == currency.upper())
                    or (isinstance(rate, str))):
                abort(400, "Wrong format")

            list_for_db.append({"currency": currency, "rate": rate})

        db.currencies.insert_many(list_for_db)
        return jsonify(message="success")

    def put(self):
        parser.add_argument('currency', type=str, help="'currency' must be string")
        parser.add_argument('rate', type=float, help="'rate' must be float")
        args = parser.parse_args()

        if((len(args['currency']) != 3)
                or (args['currency'] != args['currency'].upper())):
            abort(400, "Wrong format")

        result = db.currencies.replace_one(
            {'currency': args['currency']},
            {'currency': args['currency'], 'rate': args['rate']}
        )
        if result.raw_result["n"] == 0:
            abort(404, "This currency is not in the database")
        return jsonify(message="success")

    def delete(self):
        parser.add_argument('currency', type=str, help="'currency' must be string")
        args = parser.parse_args()
        if ((len(args['currency']) != 3)
                or (args['currency'] != args['currency'].upper())):
            abort(400, "Wrong format")

        result = db.currencies.delete_one({'currency': args['currency']})
        if result.raw_result["n"] == 0:
            abort(404, "This currency is not in the database")
        return jsonify(message="success")


api.add_resource(CreateInitData, '/create-init-data')
api.add_resource(GetCourseCurrency, '/<string:currency_name>')
api.add_resource(ConvertCurrency, '/convert-currency')
api.add_resource(CRUD, '/currencies')

if __name__ == "__main__":
    app.run()
