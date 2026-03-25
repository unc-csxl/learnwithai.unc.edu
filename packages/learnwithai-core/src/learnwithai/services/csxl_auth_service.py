"""Integration logic for UNC CSXL authentication and local JWT issuance."""

import httpx
import jwt
from datetime import datetime, timezone, timedelta
from ..config import Settings
from ..tables.user import User
from ..models.unc import UNCDirectorySearch
from ..repositories.user_repository import UserRepository


class AuthenticationException(Exception): ...


class CSXLAuthService:
    """Coordinates CSXL authentication with local user provisioning."""

    def __init__(self, settings: Settings, user_repo: UserRepository):
        """Initializes the authentication service.

        Args:
            settings: Application settings used for external service configuration.
            user_repo: Repository used to read and persist users.
        """
        self._settings = settings
        self._user_repo = user_repo

    def verify_auth_token(self, token: str) -> tuple[str, int]:
        """Validates a CSXL auth token and returns the UNC identity pair.

        Args:
            token: CSXL token returned by the UNC auth flow.

        Returns:
            A tuple of ``(onyen, pid)``.

        Raises:
            AuthenticationException: If the upstream verification fails.
        """
        params = {"token": token}

        with httpx.Client() as client:
            response = client.get(
                f"https://{self._settings.unc_auth_server_host}/verify", params=params
            )
            if response.status_code == httpx.codes.OK:
                body = response.json()
                onyen = body["uid"]
                pid = int(body["pid"])
                return (onyen, pid)
            else:
                raise AuthenticationException()

    def registered_user_from_onyen_pid(self, onyen: str, pid: int) -> User:
        """Loads or creates a user record for the authenticated UNC identity.

        Args:
            onyen: UNC onyen for the authenticated user.
            pid: UNC PID for the authenticated user.

        Returns:
            An existing or newly registered user.
        """
        user = self._user_repo.get_by_pid(pid)
        return user if user else self._register_new_user(onyen, pid)

    def _register_new_user(self, onyen: str, pid: int) -> User:
        """Creates a new user record from UNC directory data.

        Args:
            onyen: UNC onyen for the authenticated user.
            pid: UNC PID for the authenticated user.

        Returns:
            The newly persisted user record.
        """
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

    def _unc_directory_lookup(self, pid: int) -> UNCDirectorySearch:
        """Retrieves user profile data from the UNC directory service.

        Args:
            pid: UNC PID to look up.

        Returns:
            A normalized directory search result, or an empty placeholder result.
        """
        with httpx.Client() as client:
            response = client.get(f"https://directory.unc.edu/api/search/{pid}")
            if response.status_code == httpx.codes.OK:
                results = response.json()
                if len(results) > 0:
                    results[0]["pid"] = str(pid)
                    return UNCDirectorySearch.model_validate(results[0])
            return UNCDirectorySearch(pid=str(pid))

    def issue_jwt_token(self, user: User) -> str:
        """Issues a short-lived JWT for a known user.

        Args:
            user: Authenticated user to encode into the token subject.

        Returns:
            Encoded JWT string.
        """
        expire_at = datetime.now(timezone.utc) + timedelta(days=1)
        payload = {"sub": str(user.pid), "exp": expire_at}
        token = jwt.encode(
            payload, self._settings.jwt_secret, algorithm=self._settings.jwt_algorithm
        )
        return token

    def verify_jwt(self, token: str) -> int:
        """Decodes a JWT and returns the user PID.

        Delegates to :func:`learnwithai.auth.verify_jwt`.

        Args:
            token: Encoded JWT issued by this service.

        Returns:
            The user PID stored in the token subject claim.

        Raises:
            AuthenticationException: If the token is invalid or expired.
        """
        from ..auth import verify_jwt

        return verify_jwt(token, self._settings)

    def get_user_by_pid(self, pid: int) -> User | None:
        """Looks up a user by PID.

        Args:
            pid: UNC person identifier.

        Returns:
            The matching user when found; otherwise, ``None``.
        """
        return self._user_repo.get_by_pid(pid)
