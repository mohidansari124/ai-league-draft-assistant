"""Optional static-data adapter. Runtime analysis never calls external services."""
import httpx
import re

class DataDragonService:
    base_url = "https://ddragon.leagueoflegends.com"

    def __init__(self, version=None):
        if version is None:
            response = httpx.get(f"{self.base_url}/api/versions.json", timeout=20)
            response.raise_for_status()
            version = response.json()[0]
        if not isinstance(version, str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
            raise ValueError("Invalid Data Dragon version")
        self.version = version

    def fetch_json(self, filename):
        url = f"{self.base_url}/cdn/{self.version}/data/en_US/{filename}.json"
        response = httpx.get(url, timeout=30)
        response.raise_for_status()
        return response.json()

    def fetch_portrait(self, champion_id):
        url = f"{self.base_url}/cdn/{self.version}/img/champion/{champion_id}.png"
        response = httpx.get(url, timeout=30)
        response.raise_for_status()
        return response.content
