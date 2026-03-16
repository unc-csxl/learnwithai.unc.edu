import httpx
import jwt
from datetime import datetime, timezone, timedelta
from ..config import Settings
from ..models.user import User
from ..models.unc import UNCDirectorySearch
from ..repositories.user_repository import UserRepository


class AuthenticationException(Exception): ...


class CSXLAuthService:
    def __init__(self, settings: Settings, user_repo: UserRepository):
        self._settings = settings
        self._user_repo = user_repo

    def verify_auth_token(self, token: str):
        params = {"token": token}

        with httpx.Client() as client:
            response = client.get(
                f"https://{self._settings.unc_auth_server_host}/verify", params=params
            )
            if response.status_code == httpx.codes.OK:
                body = response.json()
                onyen = body["uid"]
                pid = body["pid"]
                return (onyen, pid)
            else:
                raise AuthenticationException()

    def registered_user_from_onyen_pid(self, onyen: str, pid: str) -> User:
        user = self._user_repo.get_by_pid(pid)
        return user if user else self._register_new_user(onyen, pid)

    def _register_new_user(self, onyen: str, pid: str) -> User:
        user_info = self._unc_directory_lookup(pid)
        user = self._user_repo.register_user(
            User(
                name=user_info.displayName,
                pid=pid,
                onyen=onyen,
                email=user_info.mailIterator[0],
                family_name=user_info.snIterator[0],
                given_name=user_info.givenNameIterator[0],
            )
        )
        return user

    def _unc_directory_lookup(self, pid: str) -> UNCDirectorySearch:
        with httpx.Client() as client:
            response = client.get(f"https://directory.unc.edu/api/search/{pid}")
            if response.status_code == httpx.codes.OK:
                results = response.json()
                if len(results) > 0:
                    results[0]["pid"] = str(pid)
                    return UNCDirectorySearch.model_validate(results[0])
            return UNCDirectorySearch(pid=pid)

    def issue_jwt_token(self, user: User) -> str:
        expire_at = datetime.now(timezone.utc) + timedelta(days=1)
        payload = {"sub": str(user.id), "exp": expire_at}
        token = jwt.encode(
            payload, self._settings.jwt_secret, algorithm=self._settings.jwt_algorithm
        )
        return token

    def verify_jwt(self, token: str) -> str:
        """Decode a JWT and return the user ID (sub claim).

        Raises AuthenticationException on invalid or expired tokens.
        """
        try:
            payload = jwt.decode(
                token,
                self._settings.jwt_secret,
                algorithms=[self._settings.jwt_algorithm],
            )
            user_id: str = payload["sub"]
            return user_id
        except (jwt.InvalidTokenError, KeyError) as exc:
            raise AuthenticationException() from exc

    def get_user_by_id(self, user_id: str) -> User | None:
        return self._user_repo.get_by_id(user_id)
