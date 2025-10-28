import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, Event
from homeassistant.const import CONF_HOST, Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.update_coordinator import UpdateFailed

from .const import DOMAIN
from .api import WledExtendedApiClient
from .coordinator import WledExtendedDataCoordinator

_LOGGER = logging.getLogger(__name__)

# Your manual fix
EVENT_CONFIG_ENTRY_CREATED = "config_entry_created"
EVENT_CONFIG_ENTRY_REMOVED = "config_entry_removed"

# --- THIS IS THE CHANGE ---
# We now load both 'select' and 'switch'
PLATFORMS: list[Platform] = [Platform.SELECT, Platform.SWITCH]
# --- END OF CHANGE ---

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WLED Extended from a config entry."""
    
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["coordinators"] = {}
    
    async def async_setup_wled_device(wled_entry: ConfigEntry):
        """Set up a coordinator and signal platform setup."""
        if wled_entry.entry_id in hass.data[DOMAIN]["coordinators"]:
            _LOGGER.debug("WLED device %s already set up", wled_entry.title)
            return

        host = wled_entry.data.get(CONF_HOST)
        if not host:
            _LOGGER.error("WLED entry %s has no host", wled_entry.title)
            return

        _LOGGER.debug("Setting up WLED Extended for: %s", wled_entry.title)
        
        session = async_get_clientsession(hass)
        api_client = WledExtendedApiClient(host, session)
        coordinator = WledExtendedDataCoordinator(hass, api_client, host)
        
        try:
            await coordinator.async_config_entry_first_refresh()
        except UpdateFailed as err:
            _LOGGER.warning("Failed to fetch data from %s: %s. Entity will be 'Unknown'.", host, err)
        except Exception as err:
            _LOGGER.error("Unexpected error setting up %s: %s", host, err)
            return
            
        hass.data[DOMAIN]["coordinators"][wled_entry.entry_id] = coordinator
        
        # Send a signal to *both* platforms
        async_dispatcher_send(hass, f"{DOMAIN}_new_device", wled_entry.entry_id)

    async def async_unload_wled_device(wled_entry_id: str):
        """Unload a coordinator and signal platform removal."""
        _LOGGER.debug("Unloading WLED Extended for entry ID: %s", wled_entry_id)
        hass.data[DOMAIN]["coordinators"].pop(wled_entry_id, None)
        async_dispatcher_send(hass, f"{DOMAIN}_remove_device", wled_entry_id)

    async def async_wled_entry_listener(event: Event):
        """Listen for WLED entries being added or removed."""
        entry_data = event.data.get("entry", {})
        
        if entry_data.get("domain") != "wled":
            return
        
        wled_entry_id = entry_data.get("entry_id")
        if not wled_entry_id:
            return

        if event.event_type == EVENT_CONFIG_ENTRY_CREATED:
            _LOGGER.debug("WLED entry created: %s", wled_entry_id)
            wled_entry = hass.config_entries.async_get_entry(wled_entry_id)
            if wled_entry:
                hass.async_create_task(async_setup_wled_device(wled_entry))
        elif event.event_type == EVENT_CONFIG_ENTRY_REMOVED:
            _LOGGER.debug("WLED entry removed: %s", wled_entry_id)
            hass.async_create_task(async_unload_wled_device(wled_entry_id))

    # This will now set up both SELECT and SWITCH platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    listeners = [
        hass.bus.async_listen(EVENT_CONFIG_ENTRY_CREATED, async_wled_entry_listener),
        hass.bus.async_listen(EVENT_CONFIG_ENTRY_REMOVED, async_wled_entry_listener),
    ]
    
    async def _async_unload_listeners():
        """A coroutine function to remove listeners."""
        for remove_listener in listeners:
            remove_listener()

    entry.async_on_unload(_async_unload_listeners)
    
    _LOGGER.info("Scanning for existing WLED devices...")
    for wled_entry in hass.config_entries.async_entries(domain="wled"):
        hass.async_create_task(async_setup_wled_device(wled_entry))

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop("coordinators", None)
        
    return unload_ok