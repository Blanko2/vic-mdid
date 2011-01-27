from django.conf import settings

#from package import PackagePresentation
from powerpoint import PowerPointPresentation
from viewpresentation import ViewPresentation
from flashcards import FlashCards
from printview import PrintView
from audiotextsync import AudioTextSync
from mediaplayer import MediaPlayer, EmbeddedMediaPlayer

if getattr(settings, 'MEGAZINE_VIEWER'):
    from megazine import MegazinePlayer
