from dotenv import dotenv_values

config = dotenv_values(".env")

ENV = config.get("ENV", "dev")

DATABASE_URL = {
    "dev": "sqlite:///coupons.db",
    "prod": "postgresql://user:password@localhost:5432/coupons"  # Not active yet.
}[ENV]