import logging
from homeassistant.components.select import SelectEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.device_registry import (
    DeviceRegistry, 
    async_get as async_get_device_registry
)
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN
from .coordinator import WledExtendedDataCoordinator

_LOGGER = logging.getLogger(__name__)

# The options the user will see in the dropdown
SYNC_MODE_OPTIONS = ["Off", "Send", "Receive", "Unknown"]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the select entities."""
    
    current_entities = {}

    @callback
    async def async_add_new_device(wled_entry_id: str):
        """Add a new WLED select entity when a new device is found."""
        if wled_entry_id in current_entities:
            return

        _LOGGER.debug("select.py: Received signal for new device: %s", wled_entry_id)
        
        coordinator: WledExtendedDataCoordinator = hass.data[DOMAIN]["coordinators"].get(wled_entry_id)
        if not coordinator:
            _LOGGER.error("Coordinator for %s not found in hass.data", wled_entry_id)
            return

        wled_entry = hass.config_entries.async_get_entry(wled_entry_id)
        if not wled_entry:
            _LOGGER.error("Original WLED entry %s not found", wled_entry_id)
            return

        device_name = wled_entry.title
        host = coordinator.host
        
        dev_reg: DeviceRegistry = async_get_device_registry(hass)
        
        original_device = next(
            (device for device in dev_reg.devices.values() 
             if wled_entry_id in device.config_entries),
            None
        )
        
        new_entity = WledAudioSyncModeSelect(
            coordinator, 
            host, 
            device_name, 
            original_device.identifiers if original_device else None
        )
        
        current_entities[wled_entry_id] = new_entity
        async_add_entities([new_entity])

    @callback
    def async_remove_device(wled_entry_id: str):
        """Remove a WLED select entity when its device is removed."""
        _LOGGER.debug("select.py: Received signal to remove device: %s", wled_entry_id)
        
        entity = current_entities.pop(wled_entry_id, None)
        if entity:
            hass.async_create_task(entity.async_remove())

    entry.async_on_unload(
        async_dispatcher_connect(hass, f"{DOMAIN}_new_device", async_add_new_device)
    )
    entry.async_on_unload(
        async_dispatcher_connect(hass, f"{DOMAIN}_remove_device", async_remove_device)
    )

    if "coordinators" in hass.data[DOMAIN]:
        for wled_entry_id in hass.data[DOMAIN]["coordinators"].keys():
            await async_add_new_device(wled_entry_id)


class WledAudioSyncModeSelect(CoordinatorEntity, SelectEntity):
    """Representation of the WLED Audio Sync Mode select entity."""
    
    _attr_has_entity_name = True 

    def __init__(
        self, 
        coordinator: WledExtendedDataCoordinator, 
        host: str, 
        device_name: str,
        original_device_identifiers: set | None
    ):
        """Initialize the entity."""
        super().__init__(coordinator)
        self.api = coordinator.api_client
        
        self._attr_name = "Audio Sync Mode" 
        self._attr_unique_id = f"{host}_audio_sync_mode"
        self._attr_icon = "mdi:sync"
        self._attr_options = SYNC_MODE_OPTIONS
        self._attr_entity_category = EntityCategory.CONFIG
        
        if original_device_identifiers:
            self._attr_device_info = {
                "identifiers": original_device_identifiers
            }
        else:
            self._attr_device_info = {
                "identifiers": {(DOMAIN, host)},
                "name": f"{device_name} Extended",
                "manufacturer": "WLED",
            }

    # --- 1. THIS IS THE NEW PROPERTY ---
    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        # Check if coordinator has data
        if not super().available:
            return False
        
        # Now, also check if the Audio Reactive switch is on
        try:
            is_on = self.coordinator.data.get("state", {}).get("AudioReactive", {}).get("on", False)
            return is_on  # Only available if the switch is on
        except (AttributeError, TypeError):
            return False # Data is malformed, so unavailable
    # --- END OF NEW PROPERTY ---

    @property
    def current_option(self) -> str | None:
        """Return the currently selected option."""
        
        if not self.coordinator.data:
            return "Unknown"
        
        try:
            # Parse the full JSON to find our value
            raw_state = self.coordinator.data.get("info", {}).get("u", {}).get("UDP Sound Sync", ["Unknown"])[0].lower()
            
            if raw_state == "off":
                return "Off"
            elif raw_state == "receive mode":
                return "Receive"
            elif raw_state == "send mode":
                return "Send"
            else:
                return "Unknown"
        except (AttributeError, IndexError, TypeError):
            return "Unknown"

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if option in ("Off", "Send", "Receive"):
            await self.api.async_set_sync_mode(option)
            await self.coordinator.async_request_refresh()