"""
Sensor to indicate today's gas station fuel price in korea.
For more details about this platform, please refer to the documentation at
https://github.com/GrecHouse/gas_station_korea

HA 주유소 유가 센서 : 주유소 기름값을 알려줍니다.
"""
import logging
from datetime import datetime, timedelta
import ssl
import requests
import urllib3

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import Throttle

from .const import DOMAIN, MANUFACT, SW_VERSION, MODEL, CONF_STATION_ID, CONF_STATION_NAME, CONF_OIL_TYPE, OIL_TYPE, OIL_TYPE_CODE, API_URL, SUB_URL, ATTRIBUTION, NATIONAL_AVR, WON

_LOGGER = logging.getLogger(__name__)

MIN_TIME_BETWEEN_API_UPDATES = timedelta(seconds=30)
SCAN_INTERVAL = timedelta(seconds=7200)

async def async_setup_entry(hass, entry, async_add_entities):
    """통합 구성요소의 sensor 플랫폼 Entry 설정"""

    _LOGGER.debug(entry.data)

    station_id = entry.data.get(CONF_STATION_ID)
    station_name = entry.data.get(CONF_STATION_NAME)
    oil_type = entry.data.get(CONF_OIL_TYPE)
    oil_type_name = OIL_TYPE[oil_type]
    oil_type_code = OIL_TYPE_CODE[oil_type]

    sensors = []

    try:
        api = GasStationPriceAPI(hass, station_id, oil_type_name, oil_type_code)
        sensor = GasStationPriceSensor(station_id, station_name, oil_type, api)
        await sensor.async_update()
        sensors += [sensor]
    except Exception as ex:
        _LOGGER.error('Failed to update Gas Station Price API status Error: %s', ex)

    if sensors:
        async_add_entities(sensors)


class GasStationPriceAPI:
    """GasStationPrice API."""

    def __init__(self, hass, station_id, type_name, type_code):
        """Initialize the GasStationPrice API.."""
        self._hass = hass
        self.station_id = station_id
        self.type_name = type_name
        self.type_code = type_code
        self.result = {}

    @Throttle(MIN_TIME_BETWEEN_API_UPDATES)
    async def update(self):
        """Update function for updating api information."""

        _LOGGER.debug(f"update gas_station_korea : {self.station_id}-{self.type_name}")

        try:
            if self.station_id == '0':
                session = async_get_clientsession(self._hass)
                res = await session.get(API_URL, timeout=10)
                res.raise_for_status()
                response = await res.json(content_type=None)
                for oil in response['OIL']:
                    if self.type_code == oil['PRODCD']:
                        self.result['avg_date'] = oil['TRADE_DT']
                        self.result['avg_price'] = oil['PRICE']
                        self.result['avg_diff'] = oil['DIFF']
                        break
                #_LOGGER.debug(self.result)
            else:
                tsp = int(datetime.now().timestamp() * 1000)
                req_url = SUB_URL.format(self.station_id, tsp)
                #res = requests.get(req_url, timeout=10)
                #res = await get_legacy_session(self).get(req_url, timeout=10)
                session = async_get_clientsession(self._hass)
                res = await session.get(req_url, timeout=10)
                res.raise_for_status()
                response = await res.json()

                #{'isMapUser': False, 'isExist': False}
                if not response.get('isExist'):
                    _LOGGER.error('station_id is wrong.')
                else:
                    self.result['name'] = response['basicInfo']['placenamefull']

                    info = response['oilPriceInfo']
                    price_list = info['priceList']
                    #_LOGGER.debug(priceList)

                    self.result['date'] = info['baseDate']

                    if isinstance(price_list, list):
                        for price in price_list:
                            if self.type_name == price['type']:
                                self.result['price'] = price['price']
                                break
                    elif len(price_list) > 0:
                        if self.type_name == price_list['type']:
                            self.result['price'] = price_list['price']

                    #_LOGGER.debug(self.result)

        except Exception as ex:
            _LOGGER.error('Failed to update GasStationPrice API status Error: %s', ex)
            raise

class GasStationPriceSensor(SensorEntity):
    """Representation of a GasStationPrice Sensor."""

    def __init__(self, station_id, station_name, oil_type, api):
        """Initialize the GasStationPrice sensor."""
        self._entity_id = None
        self._name = station_name
        self.oil_type = oil_type
        self.price = 0
        self.station_id = station_id
        self.base_date = '-'
        self.diff = '-'
        self._api = api
        self.firmware_version = SW_VERSION
        self.model = MODEL
        self.manufacturer = MANUFACT

    @property
    def unique_id(self):
        """Return the entity ID."""
        return f'sensor.gas_station_{self.station_id}{self.oil_type}'

    @property
    def name(self):
        """Return the name of the sensor, if any."""
        if self._name is None:
            if self.station_id == "0":
                self._name = NATIONAL_AVR
        return f'{self._name}-{OIL_TYPE[self.oil_type]}'

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return 'mdi:gas-station'

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return WON

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.price

    @property
    def extra_state_attributes(self):
        """Attributes."""
        data = { 'oil_type': OIL_TYPE[self.oil_type], 'base_date': self.base_date }
        if self.diff != '-':
            data['price_diff'] = self.diff
        return data

    @property
    def device_info(self):
        """Information about this entity/device."""
        return {
            "identifiers": {(DOMAIN, self._name)},
            "name": self._name,
            "sw_version": self.firmware_version,
            "model": self.model,
            "manufacturer": self.manufacturer
        }

    @property
    def attribution(self):
        """Return the attribution."""
        return ATTRIBUTION

    async def async_update(self):
        """Get the latest state of the sensor."""
        if self._api is None:
            return

        await self._api.update()

        result = self._api.result

        if 'price' in result:
            if self._name is None:
                self._name = result.get('name')
            self.price = result.get('price').replace(",","").replace(WON,"")
            self.base_date = result.get('date')
        else:
            if self._name is None:
                if self.station_id == "0":
                    self._name = NATIONAL_AVR
                else:
                    self._name = self.station_id
            self.price = result.get('avg_price')
            self.base_date = result.get('avg_date')
            self.diff = result.get('avg_diff')

class CustomHttpAdapter (requests.adapters.HTTPAdapter):
    # "Transport adapter" that allows us to use custom ssl_context.
    def __init__(self, ssl_context=None, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)
    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = urllib3.poolmanager.PoolManager(
            num_pools=connections, maxsize=maxsize,
            block=block, ssl_context=self.ssl_context)

def get_legacy_session(self):
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
    #session = requests.session()
    session = async_get_clientsession(self._hass)
    session.mount('https://', CustomHttpAdapter(ctx))
    return session
