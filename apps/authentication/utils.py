import random
import re

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

    def _user_data_key(self, phone: str) -> str:
        return f"user_temp:{phone}"

    def save_user_temp(self, phone: str, user_data: dict, expire: int = 300):
        key = f"user_temp:{phone}"
        self.redis_client.setex(key, expire, orjson.dumps(user_data))
        return True, 0

    def send_otp(self, phone: str, code: str, purpose="register", expire: int = 300):
        key = f"otp:{purpose}:{phone}"
        self.redis_client.setex(key, expire, code)
        print(f"[DEBUG] OTP для {phone} ({purpose}): {code}")
        return True, 0

    def verify_otp(self, phone: str, code: str, purpose="register"):
        otp_key = f"otp:{purpose}:{phone}"
        saved_code = self.redis_client.get(otp_key)
        if not saved_code or saved_code.decode() != code:
            return False, None

        user_data = None
        if purpose == "register":
            user_key = f"user_temp:{phone}"
            raw = self.redis_client.get(user_key)
            if raw:
                user_data = orjson.loads(raw)
        return True, user_data

    def delete_otp(self, phone: str, purpose: str = "login") -> None:
        otp_key = self._otp_key(phone, purpose)
        self.redis_client.delete(otp_key)

        if purpose == "register":
            user_data_key = self._user_data_key(phone)
            self.redis_client.delete(user_data_key)
