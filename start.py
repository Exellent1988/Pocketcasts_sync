from pycketcasts.pocketcasts import PocketCast
import os
from dotenv import load_dotenv
import coloredlogs, logging
from pprint import pprint
import json
from mygpoclient import api, simple, public
import requests
import datetime
from tqdm import tqdm



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
gp = api.MygPodderClient(GPODDER_USER, GPODDER_PASS, GPODDER_SERVER)

# Podcasts aus Pocket Casts abrufen
logger.info("Get Pocketcasts Subscriptions")
pc_subscriptions = pocket.subscriptions
# logger.debug(pprint(pc_subscriptions[0]))

uuids = [podcast.uuid for podcast in pc_subscriptions]

# Anfrage an Pocket Casts zum Abrufen der Feed URLs
response = requests.post('https://refresh.pocketcasts.com/import/export_feed_urls', json={'uuids': uuids})
feed_urls = response.json()['result']

subs = []
gpodder_device = gp.get_devices()[0]
logger.info(f"Syncing to gPodder Device: {gpodder_device.caption}")

# Podcasts zu gPodder hinzufügen
for podcast in pc_subscriptions:
    feed_url = feed_urls.get(podcast.uuid)
    if feed_url:
        subs.append(feed_url)
        podcast.feed = feed_url
        logger.info(f"Podcast hinzugefügt: \"{podcast.title}\" mit URL: \"{feed_url}\"")

# Sync to Gpodder

try:
    gp.update_subscriptions(gpodder_device.device_id, [])
except:
    logger.error(f"Podcast konnten nicht gecleared werden")
try:
    gp.put_subscriptions(gpodder_device.device_id, subs)
except:
    logger.error(f"Podcast konnten nicht gesynct werden")


# Episodenstatus zu gPodder übertragen

logger.info(f"Starte Episoden Sync")

for podcast in pc_subscriptions:
    changes =[]
    episodes = podcast.episodes
    with tqdm(total=len(episodes), desc=f"{podcast.title} Episodes") as pbar:
        for episode in episodes:
            if episode.deleted:
                action = api.EpisodeAction(podcast.feed, episode.url, "delete", gpodder_device.device_id)
                changes.append(action)
                logger.info(f"{podcast.title}: season: {episode.season}.{episode.number} {episode.title} als gespielt markiert")
            else:
                action = api.EpisodeAction(podcast.feed, episode.url, "new", gpodder_device.device_id)
                changes.append(action)
                logger.info(f"{podcast.title}: season: {episode.season}.{episode.number} {episode.title} als neu markiert")
            pbar.update(1)
    
    try:
        syncresult = gp.upload_episode_actions(api.EpisodeActionChanges(changes, datetime.datetime.now().isoformat()))
        logger.info(f"{syncresult}")
    except:
        logger.error(f"Podcast {podcast.title} konnte Episodenstatus nicht syncen")

