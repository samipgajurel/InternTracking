from django.core import signing

TOKEN_SALT = "accounts.email.verify"

def make_verify_token(user_id: int) -> str:
    return signing.dumps({"uid": user_id}, salt=TOKEN_SALT)

def read_verify_token(token: str, max_age_seconds: int = 60 * 60 * 24) -> int:
    data = signing.loads(token, salt=TOKEN_SALT, max_age=max_age_seconds)
    return int(data["uid"])
