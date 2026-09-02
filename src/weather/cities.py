from __future__ import annotations

from weather.models import City

DEFAULT_CITIES: tuple[City, ...] = (
    City("New York", 40.7128, -74.0060),
    City("Tokyo", 35.6895, 139.6917),
    City("London", 51.5074, -0.1278),
    City("Paris", 48.8566, 2.3522),
    City("Berlin", 52.5200, 13.4050),
    City("Sydney", -33.8688, 151.2093),
    City("Mumbai", 19.0760, 72.8777),
    City("Cape Town", -33.9249, 18.4241),
    City("Moscow", 55.7558, 37.6173),
    City("Rio de Janeiro", -22.9068, -43.1729),
)
