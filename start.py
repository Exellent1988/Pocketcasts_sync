from pycketcasts import PocketCast
import os
from dotenv import load_dotenv
import coloredlogs, logging
import pprint
from mygpoclient import api
pp = pprint.PrettyPrinter(indent=4)


# Logger konfigurieren
logger = logging.getLogger(__name__)
coloredlogs.install(level='DEBUG', logger=logger)

# .env Datei laden
load_dotenv()

# Zugangsdaten
POCKETCASTS_USERNAME = os.getenv('POCKETCASTS_USERNAME')
POCKETCASTS_PASSWORD = os.getenv('POCKETCASTS_PASSWORD')
GPODDER_SERVER = os.getenv('GPODDER_SERVER')
GPODDER_USER = os.getenv('GPODDER_USER')
GPODDER_PASS = os.getenv('GPODDER_PASS')

# Pocket Casts API einrichten
pocket = PocketCast(POCKETCASTS_USERNAME, POCKETCASTS_PASSWORD)
gpodder = api.MygPodderClient(GPODDER_USER,GPODDER_PASS, GPODDER_SERVER)

# Episoden aus Pocket Casts abrufen
podcasts = pocket.subscriptions

