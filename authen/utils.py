import random

import orjson
from redis import Redis

from root.settings import REDIS_URL


def generate_code(length: int = 6):
    return "".join(str(random.randint(0, 9)) for _ in range(length))


class OtpService:
    def __init__(self):
        self.redis_client = Redis.from_url(REDIS_URL, decode_responses=False)

    def _otp_key(self, phone: str, purpose: str = "login") -> str:
        return f"otp:{purpose}:{phone}"

    def save_user_temp(self, phone: str, user_data: dict, expire: int = 300) -> tuple[bool, int]:
        key = self._otp_key(phone, purpose="register")
        ttl = self.redis_client.ttl(key)
        if ttl > 0:
            return False, ttl
        self.redis_client.setex(key, expire, orjson.dumps(user_data))
        return True, 0

    def send_otp(self, phone: str, code: str, purpose: str = "login", expire: int = 300) -> tuple[bool, int]:
        key = self._otp_key(phone, purpose)
        ttl = self.redis_client.ttl(key)
        if ttl > 0:
            return False, ttl
        self.redis_client.setex(key, expire, code)
        print(f"[DEBUG] OTP для {phone} ({purpose}): {code}")  # В продакшене заменить на SMS
        return True, 0

    def verify_otp(self, phone: str, code: str, purpose: str = "login") -> tuple[bool, dict | None]:
        key = self._otp_key(phone, purpose)
        saved_code = self.redis_client.get(key)

        if not saved_code or saved_code.decode() != code:
            return False, None

        user_data = None
        if purpose == "register":
            user_data_key = key
            user_data_raw = self.redis_client.get(user_data_key)
            if user_data_raw:
                user_data = orjson.loads(user_data_raw)

        return True, user_data

    def delete_otp(self, phone: str, purpose: str = "login") -> None:
        key = self._otp_key(phone, purpose)
        self.redis_client.delete(key)
