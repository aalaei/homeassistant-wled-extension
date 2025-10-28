from homeassistant import config_entries
import voluptuous as vol

from .const import DOMAIN

@config_entries.HANDLERS.register(DOMAIN)
class WledExtendedConfigFlow(config_entries.ConfigFlow):
    """Handle a config flow for WLED Extended."""
    
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        
        # Only allow a single instance of this integration
        await self.async_set_unique_id("wled_extended_global_listener")
        self._abort_if_unique_id_configured()
        
        if user_input is not None:
            # Create the single "global" config entry
            return self.async_create_entry(
                title="WLED Extended (Global)", 
                data={}
            )
        
        # Show the confirmation form
        return self.async_show_form(
            step_id="user"
        )