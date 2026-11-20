# homeassistant-stokercloud

This is an integration between Home Assistant and stokercloud.dk

I no longer own a NBE furnace, so at this point you can consider the code unmaintained. However, if you want to maintain it or if you have small PRs I'm happy to merge them. For the same reason Issues are disabled, as I don't have the opportunity to support the project.

# Install

You can install the plugin via HACS using the following steps.

[![image](https://github.com/user-attachments/assets/e99278d9-5121-40a4-b9c7-af48561a9140)](https://my.home-assistant.io/redirect/hacs_repository/?owner=KristianOellegaard&repository=homeassistant-stokercloud&category=integration)



Manual Install:
1. Open HACS
2. Click the three dots on the top right
4. Click "Custom repositories"
5. Add https://github.com/KristianOellegaard/homeassistant-stokercloud and a category of your choice (integration will work just fine)

# Adding the integration

Go to **Settings -> Devices & services**

![image](https://github.com/user-attachments/assets/c2137e41-156d-4814-829a-ac763e08d873)

**+ ADD INTEGRATION** (Can be found in the bottom right corner)

![image](https://github.com/user-attachments/assets/e99278d9-5121-40a4-b9c7-af48561a9140)

Search for **NBE**

![image](https://github.com/user-attachments/assets/f2424009-c2bf-480a-adcd-1ad48b1c67f8)

Insert your Stokercloud username (This can be found in your stokercloud URL. https://stokercloud.dk/v3/#/USERNAME/main-page)

![image](https://github.com/user-attachments/assets/1cc6e285-b653-436b-9396-ed3c3a47f0d4)

Currently the integration is read-only so you do not need to enter your password

If the entities added are "Unknown" - Please give the integration a few minutes to fetch the data.
An alternative to waiting is to restart HA.


# Pellet energy and consumption history

The integration provides pellet use as energy, in two forms:

* **`Pellet Energy` sensor** - total pellet consumption (kg) multiplied by 4.8 kWh/kg, a typical value for wood pellets (the `CALORIFIC_VALUE_KWH_PER_KG` constant in `const.py`). It is a `total_increasing` energy sensor.
* **Imported statistics** - on startup, and then once an hour, the integration reads StokerCloud's consumption history and imports it as long-term statistics: `hass_stokercloud:pellet_consumption_<id>` (kg) and `hass_stokercloud:pellet_energy_<id>` (kWh), where `<id>` is your lowercased StokerCloud username. The first run back-fills the history StokerCloud provides (about 24 days); later runs append each completed hour. These are not entities; find them in the Energy dashboard's source picker or in a statistics graph card.

In the Energy dashboard, pick **either** the `Pellet Energy` sensor **or** the imported `pellet_energy` statistic as the source, **not both**, or the same pellets are counted twice. Choose the imported statistic if you want the back-filled history; choose the sensor if you only need data from now on.
