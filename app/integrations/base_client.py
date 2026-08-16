import httpx
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class UpstreamError(Exception):
    """Base exception for upstream integration errors."""
    pass

class UpstreamTimeoutError(UpstreamError):
    """Raised when an upstream request times out."""
    pass

class UpstreamConnectionError(UpstreamError):
    """Raised when connection to upstream fails."""
    pass

class UpstreamResponseError(UpstreamError):
    """Raised when upstream returns an HTTP error status."""
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code

class UpstreamResponseValidationError(UpstreamError):
    """Raised when upstream response fails Pydantic schema validation."""
    pass

class BaseClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "X-Layer-Version": "1.0"
        }
        self.timeout = httpx.Timeout(settings.INTEGRATION_TIMEOUT_SECONDS, connect=2.0)

    async def _request(self, method: str, path: str, correlation_id: str, **kwargs) -> httpx.Response:
        url = f"{self.base_url}/{path.lstrip('/')}"
        headers = {**self.headers, "X-Correlation-ID": correlation_id}
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.request(method, url, headers=headers, **kwargs)
                response.raise_for_status()
                return response
            except httpx.TimeoutException as e:
                logger.error(f"Timeout connecting to upstream {url}: {str(e)}")
                raise UpstreamTimeoutError(f"Request to upstream service timed out: {url}")
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error {e.response.status_code} from upstream {url}: {e.response.text}")
                status_code = 502
                if e.response.status_code in [401, 403]:
                    status_code = 502  # Mask auth errors to client as gateway error
                elif e.response.status_code == 404:
                    status_code = 404
                raise UpstreamResponseError(
                    f"Upstream service returned error status {e.response.status_code}",
                    status_code=status_code
                )
            except httpx.RequestError as e:
                logger.error(f"Connection error to upstream {url}: {str(e)}")
                raise UpstreamConnectionError(f"Failed to establish connection to upstream service: {url}")
