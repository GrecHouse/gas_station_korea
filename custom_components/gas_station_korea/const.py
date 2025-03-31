DOMAIN = "gas_station_korea"
NAME = "Gas Station Korea"
PLATFORM = "sensor"

SW_VERSION = '1.0.1'
MANUFACT   = 'GrecHouse'
MODEL = '주유소 유가정보'
ATTRIBUTION = 'Provided by GrecHouse'

NATIONAL_AVR = '전국평균'
WON = '원'
OIL_TYPE = {
    '01': '고급휘발유',
    '02': '휘발유',
    '03': '경유',
    '04': 'LPG',
    '05': '등유'
}

OIL_TYPE_CODE = {
    '01': 'B034',
    '02': 'B027',
    '03': 'D047',
    '04': 'K015', 
    '05': 'C004'
}

CONF_OIL_TYPE = 'oil_type'
CONF_STATION_ID = 'station_id'
CONF_STATION_NAME = 'station_name'

API_URL = 'https://raw.githubusercontent.com/GrecHouse/api/master/oil.json'
SUB_URL = 'https://map.kakao.com/api/place/info?output=json&confirmId={}'
