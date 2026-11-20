from homeassistant.const import CONF_USERNAME
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

DOMAIN = "hass_stokercloud"
DATA_SCHEMA = vol.Schema({vol.Required(CONF_USERNAME): cv.string})
PLATFORMS = ['sensor', 'water_heater']

# Energy content of wood pellets, used for the Pellet Energy sensor and the
# imported statistics. ~4.8 kWh/kg is typical for ENplus A1 pellets.
CALORIFIC_VALUE_KWH_PER_KG = 4.8
