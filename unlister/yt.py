"""Helpful classes and functions for working with YouTube's API"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging

from flask import current_app
from googleapiclient.discovery import build, Resource
from unlister import CONFIG_YOUTUBE_DEV_KEY

LOGGER = logging.getLogger(__name__)

YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

class VideoPrivacyStatus(Enum):
    """Defines the available privacy statuses for a YouTube video"""
    PRIVATE = "private"
    PUBLIC = "public"
    UNLISTED = "unlisted"

    @classmethod
    def from_api(cls, value):
        """Returns the `VideoPrivacyStatus` equivalent based off the provided `value` returned
        from YouTube's API"""
        for enum_value in cls:
            if enum_value.value == value:
                return enum_value

        # Uh... we don't know what this value is!
        raise KeyError("Unknown VideoPrivacyStatus \"{}\"".format(value))

@dataclass
class Video:
    """Encapsulates information about a YouTube video"""
    title: str
    id: str
    privacy: VideoPrivacyStatus
    published: datetime
    thumbnail: str
    uploader: str
    uploader_url: str
    url: str

    def as_json(self) -> dict:
        """Returns a JSON-serializable dictionary of the video"""
        return {
            "title": self.title,
            "id": self.id,
            "privacy": self.privacy.value,
            "published": self.published.isoformat(),
            "thumbnail": self.thumbnail,
            "uploader": self.uploader,
            "uploader_url": self.uploader_url,
            "url": self.url
        }

    @classmethod
    def from_playlist_item(cls, value):
        """
        Returns the `Video` equivalent based off the provided `value` returned from a `PlaylistItem`
        returned by YouTube's API.

        If the video from the provided `value` can't be parsed for any reason, then `None` will
        be returned.
        """
        try:
            # It's possible that the thumbnail and uploader won't be available if the video is
            # private. Therefore, be on the lookout for that.
            privacy = VideoPrivacyStatus.from_api(value["status"]["privacyStatus"])

            return cls(
                title=value["snippet"]["title"],
                privacy=privacy,
                id=value["snippet"]["resourceId"]["videoId"],
                # YouTube's ISO8601 datetime format has a "Z" at the end, which Python doesn't
                # support. Therefore, strip out the "Z" so that the datetime is parsable via
                # datetime.fromisoformat.
                published=datetime.fromisoformat(value["snippet"]["publishedAt"].rstrip("Z")),
                thumbnail=None if privacy == VideoPrivacyStatus.PRIVATE else
                    value["snippet"]["thumbnails"]["default"]["url"],
                uploader=None if privacy == VideoPrivacyStatus.PRIVATE else
                    value["snippet"]["videoOwnerChannelTitle"],
                uploader_url=None if privacy == VideoPrivacyStatus.PRIVATE else
                    "https://www.youtube.com/channel/{}".format(
                        value["snippet"]["videoOwnerChannelId"]),
                url="https://www.youtube.com/watch?v={}".format(value["snippet"]["resourceId"]["videoId"])
            )
        except Exception: # pylint: disable=broad-except
            # We can't parse it. :(
            LOGGER.error("Unable to parse the provided JSON: %s", value)
            return None

def youtube_client() -> Resource:
    """Creates an API client for accessing the YouTube API"""
    dev_key = current_app.config[CONFIG_YOUTUBE_DEV_KEY]
    return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=dev_key)
