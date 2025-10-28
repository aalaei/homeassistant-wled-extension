import logging
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .api import WledExtendedApiClient, WledApiError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class WledExtendedDataCoordinator(DataUpdateCoordinator):
    """Manages polling for WLED usermod data."""
    
    def __init__(self, hass, api_client: WledExtendedApiClient, host: str):
        """Initialize the coordinator."""
        self.api_client = api_client
        self.host = host
        
        super().__init__(
            hass,
            _LOGGER,
            name=f"WLED SR ({host})",
            update_interval=timedelta(seconds=10),  # Poll every 10 seconds
        )

    async def _async_update_data(self):
        """Fetch data from API."""
        try:
            return await self.api_client.async_get_data()
        except WledApiError as err:
            raise UpdateFailed(f"Error fetching data: {err}") from err