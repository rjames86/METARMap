from threading import local
import requests
from dateutil import parser
from dateutil.tz import gettz
import datetime
import json
import logging

logger = logging.getLogger(__name__)

class AirportData:
    URL = "https://aviationweather.gov/api/data/metar?format=json&hours=1.5&ids="
    METAR_TAGS = [
        "altim_in_hg",
        "dewpoint_c",
        "elevation_m",
        "flight_category",
        "latitude",
        "longitude",
        "maxT_c",
        "metar_type",
        "minT_c",
        "observation_time",
        "sea_level_pressure_mb",
        "station_id",
        "temp_c",
        "visibility_statute_mi",
        "wind_dir_degrees",
        "wind_speed_kt",
        "raw_text",
    ]

    ATTRIBUTE_TAGS = {
        "sky_condition": [
            "sky_cover",
            "cloud_base_ft_agl",
        ],
    }

    READABLE_NAMES = dict(
        dewpoint_c="Dewpoint",
        elevation_m="Elevation",
        flight_category="Category",
        latitude="Latitude",
        longitude="Longitude",
        maxT_c="Max Temp",
        metar_type="Metar Type",
        minT_c="Min Temp",
        observation_time="Time",
        sea_level_pressure_mb="Pressure",
        station_id="Station ID",
        temp_c="Temp",
        visibility_statute_mi="Visibility",
        wind_dir_degrees="Wind Direction",
        wind_speed_kt="Wind Speed",
        wind_and_speed="Wind/Speed",
        sea_level_pressure_hg="Pressure (Hg)",
        raw_text="Raw Text",
        sky_condition="Sky Condition",
    )

    TIMEZONE = "America/Denver"

    def __init__(self):
        self.airport_code = "KOGD"
        self.last_run = datetime.datetime.now(tz=gettz("America/Denver"))

        self._data = None

    def __getitem__(self, item):
        return getattr(self, item)

    @property
    def wind_and_speed(self):
        return "%sº @ %s kts" % (self.wind_dir_degrees, self.wind_speed_kt)

    @property
    def raw_text(self):
        return self.data.get("raw_text")

    @property
    def altim_in_hg(self):
        return self.data.get("altim_in_hg")

    @property
    def dewpoint_c(self):
        return self.data.get("dewpoint_c")

    @property
    def elevation_m(self):
        return self.data.get("elevation_m")

    @property
    def flight_category(self):
        return self.data.get("flight_category")

    @property
    def latitude(self):
        return self.data.get("latitude")

    @property
    def longitude(self):
        return self.data.get("longitude")

    @property
    def maxT_c(self):
        return self.data.get("maxT_c")

    @property
    def metar_type(self):
        return self.data.get("metar_type")

    @property
    def minT_c(self):
        return self.data.get("minT_c")

    @property
    def sky_condition(self):
        if self.data.get("sky_condition") is None:
            return None
        data = self.data.get("sky_condition")
        to_return = "%s" % data["sky_cover"]
        if "cloud_base_ft_agl" in data:
            to_return += ". Cloud base: %s" % data["cloud_base_ft_agl"]
        return to_return

    @property
    def observation_time(self):
        time_data = self.data.get("observation_time")
        if time_data:
            dt = parser.parse(time_data)
            local_dt = dt.astimezone(gettz(self.TIMEZONE))
            return local_dt.strftime("%Y-%m-%d %H:%M")
        else:
            return None

    @property
    def sea_level_pressure_mb(self):
        return self.data.get("sea_level_pressure_mb")

    @property
    def sea_level_pressure_hg(self):
        if self.sea_level_pressure_mb is None:
            return 'N/A'
        return "%0.2f Hg" % (float(self.sea_level_pressure_mb) * 0.029530)

    @property
    def station_id(self):
        return self.data.get("station_id")

    @property
    def temp_c(self):
        return "%sº C" % self.data.get("temp_c")

    @property
    def visibility_statute_mi(self):
        return self.data.get("visibility_statute_mi")

    @property
    def wind_dir_degrees(self):
        return self.data.get("wind_dir_degrees")

    @property
    def wind_speed_kt(self):
        return self.data.get("wind_speed_kt")

    @property
    def data(self):
        if self._data is None:
            try:
                json_data = self.get_content()
                if not json_data:
                    self._data = {}
                    return self._data

                # Handle multiple records for same station, take latest
                station_records = []
                for metar in json_data:
                    if metar.get("icaoId") == self.airport_code:
                        station_records.append(metar)

                if not station_records:
                    self._data = {}
                    return self._data

                # Get latest record by obsTime
                latest_record = max(station_records, key=lambda r: r.get("obsTime", 0))

                # Map JSON fields to expected property names
                result = {
                    "altim_in_hg": (latest_record.get("altim", 0.0) / 33.8639) if latest_record.get("altim") else None,  # Convert hPa to inHg
                    "dewpoint_c": latest_record.get("dewp"),
                    "elevation_m": latest_record.get("elev"),
                    "flight_category": latest_record.get("fltCat"),
                    "latitude": latest_record.get("lat"),
                    "longitude": latest_record.get("lon"),
                    "maxT_c": None,  # Not available in JSON API
                    "metar_type": "METAR",  # Default
                    "minT_c": None,  # Not available in JSON API
                    "observation_time": self._convert_obs_time(latest_record.get("obsTime")),
                    "sea_level_pressure_mb": latest_record.get("altim"),  # Already in hPa/mb
                    "station_id": latest_record.get("icaoId"),
                    "temp_c": latest_record.get("temp"),
                    "visibility_statute_mi": latest_record.get("visib"),
                    "wind_dir_degrees": latest_record.get("wdir"),
                    "wind_speed_kt": latest_record.get("wspd"),
                    "raw_text": latest_record.get("rawOb", ""),
                }

                # Handle sky condition
                clouds = latest_record.get("clouds", [])
                if clouds:
                    cloud = clouds[0]  # Take first cloud layer
                    result["sky_condition"] = {
                        "sky_cover": cloud.get("cover"),
                        "cloud_base_ft_agl": cloud.get("base")
                    }
                else:
                    result["sky_condition"] = None

                self._data = result

            except Exception as e:
                logger.error(f"Error parsing METAR data: {e}")
                self._data = {}

        return self._data

    def _convert_obs_time(self, obs_time_unix):
        """Convert Unix timestamp to ISO datetime string"""
        if obs_time_unix is None:
            return None
        try:
            dt = datetime.datetime.fromtimestamp(obs_time_unix, tz=datetime.timezone.utc)
            return dt.isoformat().replace("+00:00", "Z")
        except (ValueError, TypeError, OSError):
            return None

    def should_refresh(self):
        now = datetime.datetime.now(tz=gettz(self.TIMEZONE))
        delta = now - self.last_run
        if delta.total_seconds() / 60 > 15:
            self.last_run = datetime.datetime.now(tz=gettz("America/Denver"))
            self._data = None
            return True
        return False

    def get_content(self):
        print("Fetching fresh airport data...")
        try:
            url = self.URL + self.airport_code
            logger.debug(f"Fetching METAR data from: {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Failed to fetch METAR data: {e}")
            return []
        except ValueError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return []

    def write_json(self):
        with open("airport_data", "wb+") as f:
            json.dump(f, self.data)
