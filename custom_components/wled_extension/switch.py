import logging
from homeassistant.components.switch import SwitchEntity
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
from .api import WledApiError

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switch entities."""
    
    current_entities = {}

    @callback
    async def async_add_new_device(wled_entry_id: str):
        """Add a new WLED switch entity when a new device is found."""
        if wled_entry_id in current_entities:
            return

        _LOGGER.debug("switch.py: Received signal for new device: %s", wled_entry_id)
        
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
        
        new_entity = WledAudioReactiveSwitch(
            coordinator, 
            host, 
            device_name, 
            original_device.identifiers if original_device else None
        )
        
        current_entities[wled_entry_id] = new_entity
        async_add_entities([new_entity])

    @callback
    def async_remove_device(wled_entry_id: str):
        """Remove a WLED switch entity when its device is removed."""
        _LOGGER.debug("switch.py: Received signal to remove device: %s", wled_entry_id)
        
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


class WledAudioReactiveSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of the WLED Audio Reactive on/off switch."""
    
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
        
        self._attr_name = "Audio Reactive"
        self._attr_unique_id = f"{host}_audio_reactive"
        self._attr_icon = "mdi:waveform"
        self._attr_entity_category = EntityCategory.CONFIG
        # This switch will appear in the main "Controls" card
        
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

    @property
    def is_on(self) -> bool | None:
        """Return the state of the switch."""
        if not self.coordinator.data:
            return None # None makes it "unavailable"
        
        # Parse the full JSON to find our value
        try:
            return self.coordinator.data.get("state", {}).get("AudioReactive", {}).get("on", False)
        except (AttributeError, TypeError):
            return False

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the Audio Reactive mode on."""
        try:
            # 1. Make the API call
            await self.api.async_set_audio_reactive(True)
            
            # 2. Optimistically update the coordinator's data
            if self.coordinator.data:
                self.coordinator.data["state"]["AudioReactive"]["on"] = True
                self.async_write_ha_state() # Tell HA to update its UI
            await self.coordinator.async_refresh()
            # 3. Request a full refresh to confirm
            # await self.coordinator.async_request_refresh()
            
        except WledApiError as err:
            _LOGGER.error("Error turning on Audio Reactive: %s", err)
            # If it failed, request a refresh to get the *actual* state
            await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the Audio Reactive mode off."""
        try:
            # 1. Make the API call
            await self.api.async_set_audio_reactive(False)
            
            # 2. Optimistically update the coordinator's data
            if self.coordinator.data:
                self.coordinator.data["state"]["AudioReactive"]["on"] = False
                self.async_write_ha_state() # Tell HA to update its UI
            
            # 3. Request a full refresh to confirm
            await self.coordinator.async_refresh()
            # await self.coordinator.async_request_refresh()
            
        except WledApiError as err:
            _LOGGER.error("Error turning off Audio Reactive: %s", err)
            # If it failed, request a refresh to get the *actual* state
            await self.coordinator.async_request_refresh()