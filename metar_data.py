from collections import defaultdict
import xml.etree.ElementTree as ET
import datetime
import requests

from airports import AIRPORT_CODES

class MetarInfo:
    def __init__(
        self,
        airport_code,
        flightCategory,
        windDir,
        windSpeed,
        windGustSpeed,
        windGust,
        lightning,
        tempC,
        dewpointC,
        vis,
        altimHg,
        obs,
        skyConditions,
    ):
        self.airport_code = airport_code
        self.flightCategory = flightCategory
        self.windDir = windDir
        self.windSpeed = windSpeed
        self.windGustSpeed = windGustSpeed
        self.windGust = windGust
        self.lightning = lightning
        self.tempC = tempC
        self.dewpointC = dewpointC
        self.vis = vis
        self.altimHg = altimHg
        self.obs = obs
        self.skyConditions = skyConditions

    def __repr__(self):
        return f'MetarInfo<airportcode={self.airport_code}, flight_category={self.flightCategory}>'


class MetarInfos(defaultdict):
    @classmethod
    def from_xml(cls, xml_data):
        cls = MetarInfos()

        root = ET.fromstring(xml_data)
        for metar in root.iter("METAR"):
            stationId = metar.find("station_id").text
            if metar.find("flight_category") is None:
                print("Missing flight condition, skipping.")
                continue
            flightCategory = metar.find("flight_category").text
            windDir = ""
            windSpeed = 0
            windGustSpeed = 0
            windGust = False
            lightning = False
            tempC = 0
            dewpointC = 0
            vis = 0
            altimHg = 0.0
            obs = ""
            skyConditions = []
            if metar.find("wind_gust_kt") is not None:
                windGustSpeed = int(metar.find("wind_gust_kt").text)
                # windGust = (True if (ALWAYS_BLINK_FOR_GUSTS or windGustSpeed > WIND_BLINK_THRESHOLD) else False)
            if metar.find("wind_speed_kt") is not None:
                windSpeed = int(metar.find("wind_speed_kt").text)
            if metar.find("wind_dir_degrees") is not None:
                windDir = metar.find("wind_dir_degrees").text
            if metar.find("temp_c") is not None:
                tempC = int(round(float(metar.find("temp_c").text)))
            if metar.find("dewpoint_c") is not None:
                dewpointC = int(round(float(metar.find("dewpoint_c").text)))
            if metar.find("visibility_statute_mi") is not None:
                vis_str = metar.find("visibility_statute_mi").text
                vis_str = vis_str.replace("+", "")
                vis = int(round(float(vis_str)))
            if metar.find("altim_in_hg") is not None:
                altimHg = float(round(float(metar.find("altim_in_hg").text), 2))
            if metar.find("wx_string") is not None:
                obs = metar.find("wx_string").text
            if metar.find("observation_time") is not None:
                obsTime = datetime.datetime.fromisoformat(
                    metar.find("observation_time").text.replace("Z", "+00:00")
                )
            for skyIter in metar.iter("sky_condition"):
                skyCond = {
                    "cover": skyIter.get("sky_cover"),
                    "cloudBaseFt": int(skyIter.get("cloud_base_ft_agl", default=0)),
                }
                skyConditions.append(skyCond)
            cls[stationId] = MetarInfo(
                stationId,
                flightCategory,
                windDir,
                windSpeed,
                windGustSpeed,
                windGust,
                lightning,
                tempC,
                dewpointC,
                vis,
                altimHg,
                obs,
                skyConditions,
            )
        return cls
    
def get_metar_data():
    url = "https://aviationweather.gov/cgi-bin/data/dataserver.php?dataSource=metars&requestType=retrieve&format=xml&hoursBeforeNow=1.5&stationString="
    for airportcode in AIRPORT_CODES:
        url = url + airportcode + ","

    content = requests.get(url).text
    return MetarInfos.from_xml(content)