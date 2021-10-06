db.createUser(
    {
        user: "user",
        pwd: "pass",
        roles: [
            {
                role: "readWrite",
                db: "currencies_db"
            }
        ]
    }
)

db.auth('user', 'pass')

db = db.getSiblingDB("currencies_db");
db.currencies.drop();

db.currencies.insertMany([
            {"currency": "RUB", "rate": 1},
            {"currency": "USD", "rate": 82.5},
            {"currency": "EUR", "rate": 84.2},
            {"currency": "GBP", "rate": 98.8},
            {"currency": "UAH", "rate": 2.7},
            {"currency": "JPY", "rate": 0.65},
            {"currency": "KRW", "rate": 0.061},
        ]);
