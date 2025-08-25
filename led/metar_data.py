from collections import defaultdict
import datetime
import requests
import logging

from airports import AIRPORT_CODES

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
        station_id = metar.get("icaoId", "UNKNOWN")
        
        vis = 10  # Default to 10+ miles
        if metar.get("visib"):
            vis_str = str(metar.get("visib")).replace("+", "")
            try:
                vis = float(vis_str)
            except (ValueError, TypeError):
                logger.warning(f"{station_id}: Invalid visibility value '{metar.get('visib')}', using default 10mi")
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
            category = "LIFR"  # Low IFR
        elif vis < 1 or (ceiling is not None and ceiling < 500):
            category = "LIFR"
        elif vis < 3 or (ceiling is not None and ceiling < 1000):
            category = "IFR"
        elif vis <= 5 or (ceiling is not None and ceiling <= 3000):
            category = "MVFR"  # Marginal VFR
        else:
            category = "VFR"
        
        ceiling_str = f"{ceiling}ft" if ceiling is not None else "unlimited"
        logger.debug(f"{station_id}: vis={vis}mi, ceiling={ceiling_str} -> {category}")
        
        return category
    
    @classmethod
    def from_json(cls, json_data):
        cls = MetarInfos()
        
        logger.info(f"Processing {len(json_data)} METAR records from JSON data")
        processed_count = 0
        skipped_count = 0

        for metar in json_data:
            stationId = metar.get("icaoId")
            if not stationId:
                logger.warning("METAR record missing icaoId, skipping")
                skipped_count += 1
                continue
            
            # Calculate flight category from visibility and cloud data
            flightCategory = cls._calculate_flight_category(metar)
            if not flightCategory:
                logger.warning(f"{stationId}: Unable to determine flight category, skipping")
                skipped_count += 1
                continue
                
            windDir = str(metar.get("wdir", "")) if metar.get("wdir") is not None else ""
            windSpeed = metar.get("wspd", 0) or 0
            windGustSpeed = metar.get("wgst", 0) or 0
            windGust = False
            lightning = False
            tempC = int(round(metar.get("temp", 0))) if metar.get("temp") is not None else 0
            dewpointC = int(round(metar.get("dewp", 0))) if metar.get("dewp") is not None else 0
            vis = 0
            altimHg = (metar.get("altim", 0.0) / 33.8639) if metar.get("altim") else 0.0  # Convert from hPa to inHg
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
                    logger.warning(f"{stationId}: Invalid obsTime timestamp '{metar.get('obsTime')}', setting to None")
                    obsTime = None

            if metar.get("clouds"):
                for cloud in metar.get("clouds", []):
                    skyCond = {
                        "cover": cloud.get("cover"),
                        "cloudBaseFt": cloud.get("base", 0),
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
            processed_count += 1
            logger.debug(f"{stationId}: Successfully processed - {flightCategory}, {tempC}°C, {windSpeed}kt")
        
        logger.info(f"JSON parsing complete: {processed_count} processed, {skipped_count} skipped")
        return cls
    
def get_metar_data():
    stations = ",".join(AIRPORT_CODES)
    url = f"https://aviationweather.gov/api/data/metar?ids={stations}&format=json&hours=1.5"
    
    logger.info(f"Fetching METAR data for {len(AIRPORT_CODES)} airports: {stations}")
    logger.debug(f"API URL: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        logger.info(f"Successfully fetched METAR data - HTTP {response.status_code}")
        
        json_data = response.json()
        logger.info(f"Received {len(json_data)} METAR records from API")
        
        metar_infos = MetarInfos.from_json(json_data)
        logger.info(f"Successfully parsed {len(metar_infos)} METAR records")
        
        return metar_infos
        
    except requests.RequestException as e:
        logger.error(f"Failed to fetch METAR data: {e}")
        raise
    except ValueError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_metar_data: {e}")
        raise