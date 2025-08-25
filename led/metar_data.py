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
        latitude,
        longitude,
        obsTime
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
        self.latitude = latitude
        self.longitude = longitude
        self.observation_time = obsTime

    def __repr__(self):
        return f'MetarInfo<airportcode={self.airport_code}, flight_category={self.flightCategory}>'


class MetarInfos(defaultdict):
    @classmethod
    def _calculate_flight_category(cls, metar):
        """Calculate flight category based on visibility and ceiling."""
        vis = 10  # Default to 10+ miles
        if metar.get("visib"):
            vis_str = str(metar.get("visib")).replace("+", "")
            try:
                vis = float(vis_str)
            except (ValueError, TypeError):
                vis = 10
        
        # Find lowest ceiling
        ceiling = None
        if metar.get("clouds"):
            for cloud in metar.get("clouds", []):
                cover = cloud.get("cover", "").upper()
                if cover in ["BKN", "OVC"]:  # Broken or Overcast
                    base = cloud.get("base", 0)
                    if ceiling is None or base < ceiling:
                        ceiling = base
        
        # Determine flight category
        if ceiling is not None and ceiling < 500:
            return "LIFR"  # Low IFR
        elif vis < 1 or (ceiling is not None and ceiling < 500):
            return "LIFR"
        elif vis < 3 or (ceiling is not None and ceiling < 1000):
            return "IFR"
        elif vis <= 5 or (ceiling is not None and ceiling <= 3000):
            return "MVFR"  # Marginal VFR
        else:
            return "VFR"
    
    @classmethod
    def from_json(cls, json_data):
        """Parse JSON data from new API v4.0"""
        cls_instance = cls()
        
        for metar in json_data:
            stationId = metar.get("icaoId")
            if not stationId:
                continue
            
            # Calculate flight category from visibility and cloud data
            flightCategory = cls._calculate_flight_category(metar)
            if not flightCategory:
                continue
                
            windDir = str(metar.get("wdir", "")) if metar.get("wdir") is not None else ""
            windSpeed = metar.get("wspd", 0) or 0
            windGustSpeed = metar.get("wgst", 0) or 0
            windGust = False
            lightning = False
            tempC = int(round(metar.get("temp", 0))) if metar.get("temp") is not None else 0
            dewpointC = int(round(metar.get("dewp", 0))) if metar.get("dewp") is not None else 0
            vis = 0
            altimHg = (metar.get("altim", 0.0) / 33.8639) if metar.get("altim") else 0.0  # Convert hPa to inHg
            obs = metar.get("wxString", "") or ""
            latitude = metar.get("lat", 0)
            longitude = metar.get("lon", 0)
            skyConditions = []
            obsTime = None

            if metar.get("visib"):
                vis_str = str(metar.get("visib")).replace("+", "")
                try:
                    vis = int(round(float(vis_str)))
                except (ValueError, TypeError):
                    vis = 0

            if metar.get("obsTime"):
                try:
                    # obsTime is a Unix timestamp
                    obsTime = datetime.datetime.fromtimestamp(
                        metar.get("obsTime"), tz=datetime.timezone.utc
                    )
                except (ValueError, TypeError, OSError):
                    obsTime = None

            if metar.get("clouds"):
                for cloud in metar.get("clouds", []):
                    skyCond = {
                        "cover": cloud.get("cover"),
                        "cloudBaseFt": cloud.get("base", 0),
                    }
                    skyConditions.append(skyCond)

            cls_instance[stationId] = MetarInfo(
                stationId, flightCategory, windDir, windSpeed, windGustSpeed, windGust, lightning,
                tempC, dewpointC, vis, altimHg, obs, skyConditions, latitude, longitude, obsTime
            )
        return cls_instance

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
            latitude = 0
            longitude = 0
            skyConditions = []
            obsTime = None

            if metar.find('latitude') is not None:
                latitude = float(metar.find('latitude').text)
            if metar.find('longitude') is not None:
                longitude = float(metar.find('longitude').text)
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
                ).replace(tzinfo=datetime.timezone.utc)
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
                latitude,
                longitude,
                obsTime
            )
        return cls
    
def get_metar_data():
    url = "https://aviationweather.gov/cgi-bin/data/dataserver.php?dataSource=metars&requestType=retrieve&format=xml&hoursBeforeNow=1.5&stationString="
    for airportcode in AIRPORT_CODES:
        url = url + airportcode + ","
    content = requests.get(url).text
    return MetarInfos.from_xml(content)