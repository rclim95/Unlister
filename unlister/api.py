"""The API Blueprint for Unlister"""
from datetime import datetime

from flask import Blueprint, jsonify, request, current_app
from googleapiclient.errors import HttpError
from unlister.yt import youtube_client, Video

bp = Blueprint("api", __name__, url_prefix="/api")

@bp.post("/playlist/<playlist_id>")
def get_unlisted_videos(playlist_id):
    """Finds unlisted videos (given a playlist ID) and returns the unlisted videos found"""
    # Get some additional arguments that can be passed to this request method (but aren't required)
    privacy_filter_arg = request.args.get("privacy", default="public,unlisted", type=str)
    before_date_arg = request.args.get("before", default=None, type=str)

    # Parse the above arguments into something we understand
    privacy_filter = privacy_filter_arg.split(",")
    try:
        if before_date_arg is not None:
            before_date = datetime.strptime(before_date_arg, "%Y-%m-%d")
        else:
            before_date = None
    except ValueError:
        current_app.logger.warning(
            "\"%s\" could be not parsed into \"%%Y-%%m-%%d\" format. Ignoring.", before_date_arg)
        before_date = None

    try:
        # Get the playlist items from the playlist provided.
        # See: https://developers.google.com/youtube/v3/docs/playlistItems/list
        yt = youtube_client()
        yt_request = yt.playlistItems().list(
            playlistId=playlist_id,
            part="snippet,status,contentDetails",
            maxResults=50)
        results = []

        # Go through each paginated response in the playlist...
        while yt_request:
            # Execute our request.
            yt_response = yt_request.execute()

            # And record the privacy status and some information about the video we're interested in
            for playlist_item in yt_response.get("items", []):
                video = Video.from_playlist_item(playlist_item)
                if video is None:
                    # This video couldn't be parsed.
                    continue

                # Apply our filter, if we have some.
                if video.privacy.value in privacy_filter and \
                (before_date is None or video.published <= before_date):
                    results.append(video.as_json() | {
                        "published_friendly": video.published.strftime("%Y-%m-%d %H:%M:%S")
                    })

            # Move on to the next page :)
            yt_request = yt.playlistItems().list_next(yt_request, yt_response)

        return jsonify(results)
    except Exception as ex:
        current_app.logger.error(
            "Unable to get unlisted videos from YouTube playlist ID \"%s\"",
            playlist_id,
            exc_info=True
        )

        # Is this a HttpError?
        if isinstance(ex, HttpError):
            if ex.status_code == 404:
                # The YouTube playlist ID specified is invalid or is private.
                return (jsonify({
                    "error": "The playlist could not be found or is private."
                }), 404)

        # Otherwise, assume it's an application error.
        return (jsonify({
            "error": str(ex)
        }), 500)
