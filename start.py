import pocketcasts
import requests
import os
from dotenv import load_dotenv
import coloredlogs, logging

# Logger konfigurieren
logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG', logger=logger)

# .env Datei laden
load_dotenv()

# Zugangsdaten
POCKETCASTS_USERNAME = os.getenv('POCKETCASTS_USERNAME')
POCKETCASTS_PASSWORD = os.getenv('POCKETCASTS_PASSWORD')
GPODDER_SERVER = os.getenv('GPODDER_SERVER')

# Pocket Casts API einrichten
client = pocketcasts.Client(username=POCKETCASTS_USERNAME, password=POCKETCASTS_PASSWORD)

# Episoden aus Pocket Casts abrufen
episodes = client.get_all_episodes()

# Episoden zu gPodder Server übertragen
for episode in episodes:
    data = {
        'url': episode.url,
        'title': episode.title,
        'description': episode.description,
    }
    response = requests.post(f'{GPODDER_SERVER}/api/2/data/', json=data)
    if response.status_code == 200:
        logger.info(f"Erfolgreich übertragen: {episode.title}")
    else:
        logger.error(f"Fehler beim Übertragen der Episode: {episode.title}")