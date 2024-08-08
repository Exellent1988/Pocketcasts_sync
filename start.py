from library.pycketcasts.pocketcasts import PocketCast
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
coloredlogs.install(level='INFO', logger=logger)

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


# From PocketCasts:
#             {
#     "uuid": "038d8af5-a4f7-40fa-9aac-0d639f59caa3",
#     "url": "https://freakshow.fm/podlove/file/3730/s/feed/c/m4a/fs132-denk-nicht-in-layern-denk-in-schichten.m4a",
#     "published": "2014-05-15T09:04:36Z",
#     "duration": 13991,
#     "fileType": "audio/x-m4a",
#     "title": "Denk nicht in Layern, denk in Schichten!",
#     "size": "89447831",
#     "playingStatus": 1,
#     "playedUpTo": 0,
#     "starred": false,
#     "podcastUuid": "05f2f750-19a2-012e-ffaf-00163e1b201c",
#     "podcastTitle": "Freak Show",
#     "episodeType": "full",
#     "episodeSeason": 2,
#     "episodeNumber": 132,
#     "isDeleted": true,
#     "author": "Metaebene Personal Media - Tim Pritlove",
#     "bookmarks": []
# }
# PlayingStatus 0: not played
# PlayingStatus 1: reset to unheared
# PlayingStatus 2: in progress
# PlayingStatus 3: finished



logger.info(f"Starte Postcast-Episoden Verarbeitung")
now_str = f"{datetime.datetime.now().isoformat()}"
for podcast in pc_subscriptions:
    changes = []
    try:
        logger.info(f"Hole Episodeninfos zu Podcast: {podcast.title}")
        episodes = podcast.episodes
    except:
        logger.error(f" Episodeninfos zu Podcast: {podcast.title} konnten nicht abgerufen werden")
        continue

    logger.info(f"Generiere Changes")
    with tqdm(total=len(episodes), desc=f"{podcast.title} Episodes") as pbar:
        for episode in episodes:
            if episode.playing_status >= 2:
                try:
                    episode = episode.details()
                except:
                    logger.error(f"Couldn't receive Episode Details:a{episode.uuid}")
                    continue
            if episode.playing_status == 2:
                action = api.EpisodeAction(podcast.feed, episode.url, "play", gpodder_device.device_id,now_str,0,episode.current_position,episode.duration)
                changes.append(action)
                logger.debug(f"{podcast.title}: season: {episode.season}.{episode.number} {episode.title} als in Progressgespielt markiert")
            elif episode.playing_status == 3:
                action = api.EpisodeAction(podcast.feed, episode.url, "play", gpodder_device.device_id,now_str,0,episode.duration,episode.duration)
                changes.append(action)
                logger.debug(f"{podcast.title}: season: {episode.season}.{episode.number} {episode.title} als done markiert")
            pbar.update(1)
        # for change in changes:
    #     logger.info(f"{pprint(change.to_dictionary())}")
    try:
        if len(changes) >0: 
            syncresult = gp.upload_episode_actions(changes)
            logger.info(f"Podcast {podcast.title} erfolgreich syncronisiert {syncresult}")
    except:
        logger.error(f"Podcast {podcast.title} konnte Episodenstatus nicht syncen")

