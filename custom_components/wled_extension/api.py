import aiohttp
import async_timeout
import logging

from .const import USERMOD_POST_KEY

_LOGGER = logging.getLogger(__name__)

# Maps friendly HA names to the WLED API's numeric values
MODE_TO_WLED_API = {"Off": 0, "Send": 1, "Receive": 2}

class WledExtendedApiClient:
    """API client for WLED Audio Reactive (0.16.0-alpha firmware)."""
    
    def __init__(self, host: str, session: aiohttp.ClientSession):
        """Initialize the client."""
        self._host = host
        self._session = session
        
        self._get_url = f"http://{host}/json"
        self._post_url_state = f"http://{host}/json/state"
        self._post_url_settings = f"http://{host}/settings/um"

    async def async_get_data(self) -> dict:
        """Get the full JSON data from the WLED device."""
        _LOGGER.debug("Sending GET request to %s", self._get_url)
        try:
            async with async_timeout.timeout(10):
                response = await self._session.get(self._get_url)
                
                _LOGGER.debug("Received response status: %s", response.status)
                response.raise_for_status() # Will raise error if status >= 400
                
                json_data = await response.json()
                _LOGGER.debug("Successfully parsed JSON response")
                return json_data
                
        except aiohttp.ClientResponseError as err:
            _LOGGER.error("API GET request failed (ClientResponseError): %s", err)
            raise WledApiError(f"API Error: {err}") from err
        except aiohttp.ClientError as err:
            _LOGGER.error("API GET request failed (ClientError): %s", err)
            raise WledApiError(f"Client Error: {err}") from err
        except async_timeout.TimeoutError:
            _LOGGER.error("API GET request timed out for %s", self._host)
            raise WledApiError(f"Timeout connecting to {self._host}") from TimeoutError
        except Exception as err:
            _LOGGER.error("Unknown error during API GET request: %s", err)
            raise WledApiError(f"Unknown Error: {err}") from err

    async def async_set_sync_mode(self, mode: str) -> bool:
        """Set the sync mode (Off, Send, or Receive) via POST."""
        
        mode_value = MODE_TO_WLED_API.get(mode)
        if mode_value is None:
            _LOGGER.error("Invalid sync mode requested: %s", mode)
            return False

        form_data = {
            USERMOD_POST_KEY: mode_value
        }
        
        try:
            async with async_timeout.timeout(10):
                response = await self._session.post(self._post_url_settings, data=form_data)
                response.raise_for_status()
                return response.status == 200
        except Exception as err:
            raise WledApiError(f"Error sending command to WLED at {self._host}: {err}") from err

    async def async_set_audio_reactive(self, state: bool) -> bool:
        """Turn the Audio Reactive usermod on or off."""
        
        payload = {
            "AudioReactive": {
                "enabled": state
            }
        }
        
        try:
            async with async_timeout.timeout(10):
                response = await self._session.post(self._post_url_state, json=payload)
                response.raise_for_status()
                json_data = await response.json()
                return json_data.get("success", False)
        except Exception as err:
            raise WledApiError(f"Error sending AudioReactive command to WLED: {err}") from err

class WledApiError(Exception):
    """Exception to indicate an API error."""