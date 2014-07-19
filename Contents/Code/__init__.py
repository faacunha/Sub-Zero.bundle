# hdbits.org

import string, os, urllib, zipfile, re, copy
from babelfish import Language
from datetime import timedelta
import subliminal
import logger

OS_PLEX_USERAGENT = 'plexapp.com v9.0'

DEPENDENCY_MODULE_NAMES = ['subliminal', 'enzyme', 'guessit', 'requests']

def Start():
    HTTP.CacheTime = 0
    HTTP.Headers['User-agent'] = OS_PLEX_USERAGENT
    Log.Debug("START CALLED")
    logger.registerLoggingHander(DEPENDENCY_MODULE_NAMES)
    # configured cache to be in memory as per https://github.com/Diaoul/subliminal/issues/303
    subliminal.cache_region.configure('dogpile.cache.memory')

def ValidatePrefs():
    Log.Debug("Validate Prefs called.")
    return 

# Prepare a list of languages we want subs for
def getLangList():
    langList = {Language.fromietf(Prefs["langPref1"])}
    if(Prefs["langPref2"] != "None"):
        langList.update({Language.fromietf(Prefs["langPref2"])})
        
    return langList

def getProviders():
    providers = {'opensubtitles' : Prefs['provider.opensubtitles.enabled'],
                 'thesubdb' : Prefs['provider.thesubdb.enabled'],
                 'podnapisi' : Prefs['provider.podnapisi.enabled'],
                 'addic7ed' : Prefs['provider.addic7ed.enabled'],
                 'tvsubtitles' : Prefs['provider.tvsubtitles.enabled']
                 }
    return filter(lambda prov: providers[prov], providers)

def getProviderSettings():
    provider_settings = {'addic7ed': {'username': Prefs['provider.addic7ed.username'], 
                                      'password': Prefs['provider.addic7ed.password']
                                      }
                         }
    return provider_settings

class SubliminalSubtitlesAgentMovies(Agent.Movies):
    name = 'Subliminal Movie Subtitles'
    languages = [Locale.Language.English]
    primary_provider = False
    contributes_to = ['com.plexapp.agents.imdb']

    def search(self, results, media, lang):
        Log.Debug("MOVIE SEARCH CALLED")
        results.Append(MetadataSearchResult(id='null', score=100))


    def update(self, metadata, media, lang):
        videos = []
        Log.Debug("MOVIE UPDATE CALLED")
        for item in media.items:
            for part in item.parts:
                Log.Debug("Append: %s" % part.file)
                try:
                    scannedVideo = subliminal.video.scan_video(part.file, subtitles=True, embedded_subtitles=True)
                except ValueError:
                    Log.Warn("File could not be guessed by subliminal")
                    continue
                
                videos.append(scannedVideo)

        subtitles = subliminal.api.download_best_subtitles(videos, getLangList(), getProviders(), getProviderSettings())
        subliminal.api.save_subtitles(subtitles)

class SubliminalSubtitlesAgentTvShows(Agent.TV_Shows):
    
    name = 'Subliminal TV Subtitles'
    languages = [Locale.Language.English]
    primary_provider = False
    contributes_to = ['com.plexapp.agents.thetvdb']

    def search(self, results, media, lang):
        Log.Debug("TV SEARCH CALLED")
        results.Append(MetadataSearchResult(id='null', score=100))

    def update(self, metadata, media, lang):
        videos = []
        Log.Debug("TvUpdate. Lang %s" % lang)
        for season in media.seasons:
            for episode in media.seasons[season].episodes:
                for item in media.seasons[season].episodes[episode].items:
                    for part in item.parts:
                        Log.Debug("Append: %s" % part.file)
                        try:
                            scannedVideo = subliminal.video.scan_video(part.file, subtitles=True, embedded_subtitles=True)
                        except ValueError:
                            Log.Warn("File could not be guessed by subliminal")
                            continue
                        
                        videos.append(scannedVideo)

        subtitles = subliminal.api.download_best_subtitles(videos, getLangList(), getProviders(), getProviderSettings())

	if Prefs["subFolder"] != "current folder":
	    # specific subFolder requested, create it if it doesn't exist

            for video, video_subtitles in subtitles.items():
	        path = os.path.join(os.path.split(video.name)[0], Prefs["subFolder"])
	        if not os.path.exists(path):
		    os.makedirs(path)

	        subliminal.api.save_subtitles({video: video_subtitles}, directory=path)
	else:
	    subliminal.api.save_subtitles(subtitles)
