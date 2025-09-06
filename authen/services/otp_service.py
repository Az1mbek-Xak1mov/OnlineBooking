import orjson
from redis import Redis

from root.settings import REDIS_URL


class OtpService:
    def __init__(self):
        self.redis_client = Redis.from_url(REDIS_URL, decode_responses=False)

    def _registration_key(self, phone: str) -> str:
        return f"registration:{phone}"

    def _otp_key(self, phone: str) -> str:
        return f"otp:{phone}"

    def save_user_temp(self, phone: str, user_data: dict, expire: int = 300) -> tuple[bool, int]:
        key = self._registration_key(phone)
        ttl = self.redis_client.ttl(key)
        if ttl > 0:
            return False, ttl
        self.redis_client.setex(key, expire, orjson.dumps(user_data))
        return True, 0

    def send_otp(self, phone: str, code: str, expire: int = 60) -> tuple[bool, int]:
        key = self._otp_key(phone)
        ttl = self.redis_client.ttl(key)
        if ttl > 0:
            return False, ttl
        self.redis_client.setex(key, expire, code)
        print(f"[DEBUG] OTP для {phone}: {code}")
        return True, 0

    def verify_otp(self, phone: str, code: str) -> tuple[bool, dict | None]:
        saved_code = self.redis_client.get(self._otp_key(phone))
        user_data = self.redis_client.get(self._registration_key(phone))

        if saved_code and saved_code.decode() == code:
            return True, orjson.loads(user_data) if user_data else None
        return False, None

    def delete_temp_data(self, phone: str) -> None:
        self.redis_client.delete(self._registration_key(phone))
        self.redis_client.delete(self._otp_key(phone))
