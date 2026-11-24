import os
import secrets

from nicegui import app, ui

import SpotifyStreamingHistory
from SpotifyStreamingHistory import available_years, topAlbum, topArtists, topSongs
from main import average_image, cover_to_rgb, create_playlist, download_covers
from spotify_lookup import artist_details, track_details

# Years offered in the dropdown, taken from the history files (includes the latest year)
YEARS = available_years()
# Load the history once at startup; each "Read in Streams" click then reuses it from memory.
SpotifyStreamingHistory.load_history()
# Each browser keeps its own results in app.storage.user, so two people using
# the app at once don't overwrite each other's results.
# Spotify API Client initilisation
sp = SpotifyStreamingHistory.create_spotify_client()
# Homepage initialisation and design creation
@ui.page('/')
def home_page():
    ui.add_head_html("""
    <style>
    .spotify-table {
        background-color: #121212;
        color: #FFFFFF;
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #1DB95433;
        width: 100%;
    }

    /* Target the actual table inside NiceGUI's wrapper */
    .spotify-table table {
        width: 100%;
        border-collapse: collapse;
    }

    /* Header row */
    .spotify-table thead tr {
        background-color: #1DB95422;
        cursor: pointer;
    }

    .spotify-table th {
        color: #1DB954;
        font-weight: bold;
        padding: 12px;
        text-align: left;
        font-size: 1.1rem;
        border-bottom: 1px solid #1DB95444;
    }

    /* Body rows */
    .spotify-table td {
        padding: 10px 12px;
        border-bottom: 1px solid #1DB95422;
    }

    /* Hover effect */
    .spotify-table tbody tr:hover {
        background-color: #1DB95411;
        cursor: pointer;
        transition: background-color 0.2s ease-in-out;
    }

    /* Remove last row border */
    .spotify-table tbody tr:last-child td {
        border-bottom: none;
    }
    </style>
    """)
    #Start page initialisation
    def start_app():
        welcome.classes(add="opacity-0")
        ui.timer(0.7, lambda: main_ui.classes(remove="hidden opacity-0"), once=True)
    #Stream ingestion code
    def streamsSetup():
        type_ = dataOption.value
        year = yearOption.value
        playlist = playlistOption.value
        try:
            range_ = int(rangeOption.value)
        except (TypeError, ValueError):
            range_ = 0
        if not type_ or year is None or range_ < 1:
            ui.notify("Choose a data type and year, and enter a range of 1 or more.", type="warning")
            return

        streams, song_pairs, artists, albums = SpotifyStreamingHistory.readInStreams(year)
        # plot=False: the web app doesn't show the matplotlib charts, so don't draw them
        match type_:
            case "Artists":
                result_data = topArtists(artists, range_, plot=False)
                result_type = "artists"

            case "Songs":
                # covers are only downloaded when they're needed for the playlist image
                result_data, outputImage = topSongs(song_pairs, range_, year, sp,
                                                    make_cover=playlist, plot=False)
                result_type = "songs"
                if playlist:
                    songuri = [uri for ((song, artist, uri), count) in result_data if uri]
                    create_playlist(sp, songuri, outputImage, range_, year)

            case "Albums":
                result_data = topAlbum(albums, range_, sp, plot=False)
                result_type = "albums"

        app.storage.user["result_data"] = result_data
        app.storage.user["result_type"] = result_type
        ui.navigate.to('/results')

    # --- WELCOME SCREEN ---
    welcome = ui.column().classes(
        "items-center justify-center w-full h-full absolute top-0 left-0 "
        "transition-all duration-700 opacity-0"
    )
    with welcome:
        ui.label("Welcome to Spotify Streaming History").classes("text-3xl font-bold")
        ui.button("Start", on_click=start_app, color="#1DB954")
    welcome.classes(remove="opacity-0")

    # --- MAIN UI ---
    main_ui = ui.column().classes(
        "items-center justify-center w-full h-full absolute top-0 left-0 "
        "transition-all duration-700 opacity-0 hidden"
    )
    with main_ui:
        ui.image("assets/Spotify Logo.png").classes("w-24 mb-2")
        ui.label("Spotify Streaming History").classes("text-xl font-bold mb-4")

        with ui.column().classes("items-center w-full"):
            dataOption = ui.select(["Albums", "Artists", "Songs"], label="Data Type").classes("w-64")
            yearOption = ui.select(YEARS + ["all"], label="Year").classes("w-64")
            rangeOption = ui.input(label="Range", placeholder="Enter a number").classes("w-64")
            playlistOption = ui.checkbox("Create a Playlist?",value=False).classes("w-64")

            ui.button("Read in Streams", on_click=streamsSetup, color="#1DB954")
# Results page initialisation
@ui.page('/results')
def results_page():
    RESULT_DATA = app.storage.user.get("result_data", [])
    RESULT_TYPE = app.storage.user.get("result_type", "")

    # All Spotify lookups for the page happen up front: tracks in batches of 50, artists in
    # parallel, and anything looked up before comes straight from the cache.
    if RESULT_TYPE in ("songs", "albums"):
        tracks = track_details(sp, [uri for ((_, _, uri), _) in RESULT_DATA])
    elif RESULT_TYPE == "artists":
        artist_info = artist_details(sp, [artist for (artist, _) in RESULT_DATA])

    # Album cover for a track, from the batched lookup
    def get_album_cover(track_uri):
        return tracks.get(track_uri, {}).get("cover")
    # Creates a url link from the uri to allow the user to access the songs from the webapp
    def uri_to_link(uri: str) -> str:
        if not uri:
            return "#"
        parts = uri.split(':')  # ['spotify', 'track', '4pvb0WLRcMtbPGmtejJJ6y']
        if len(parts) != 3:
            return "#"  # or raise an error
        _, kind, id_ = parts
        return f"https://open.spotify.com/{kind}/{id_}"
    # Returns the album uri when given a spotify track uri
    def get_album_uri_from_track(track_uri):
        return tracks.get(track_uri, {}).get("album_uri")

    def get_collage(covers):
        """Average of the given cover URLs, as a PIL image for display in the browser."""
        return average_image([cover_to_rgb(img) for img in download_covers(covers)])
    # --- ARTISTS MODE ---
    if RESULT_TYPE == "artists":
        ui.label("Top Artists")
        with ui.row().classes("flex-wrap gap-0 justify-center"):
            for i, (artist, streams) in enumerate(RESULT_DATA, start=1):
                image_url = artist_info[artist]["image"]
                uri = artist_info[artist]["uri"]
                link = uri_to_link(uri) if uri else "#"

                with ui.card().classes(
                        "w-1/2 bg-[#121212] text-white mb-3 p-3 border border-[#1DB95433] hover:bg-[#1DB95422] transition"
                ):
                    with ui.row().classes("items-center gap-4 w-full"):
                        if image_url:
                            ui.image(image_url).classes("w-14 h-14 rounded-full")

                        ui.label(str(i)).classes("text-xl font-bold text-[#1DB954] w-8 text-center")
                        ui.label(artist).classes("font-bold text-[#1DB954] w-40 truncate")
                        ui.label(f"{streams} streams").classes("opacity-60 ml-auto")
                    with ui.link(target=link, new_tab=True).classes("no-underline").style('color:white'):
                        ui.button("Go To Spotify", color="#1DB954")
    # --- SONGS MODE ---
    elif RESULT_TYPE == "songs":
        album_covers = []
        for i, ((song, artist, uri), streams) in enumerate(RESULT_DATA, start=1):
            cover_url = get_album_cover(uri)
            link = uri_to_link(uri)
            if cover_url:
                album_covers.append(cover_url)
            with ui.card().classes(
                    "w-1/2 bg-[#121212] text-white mb-3 p-3 border border-[#1DB95433] hover:bg-[#1DB95422] transition"
            ):
                with ui.row().classes("items-center gap-4 w-full"):
                    if cover_url:
                        ui.image(cover_url).classes("w-14 h-14 rounded")
                    ui.label(str(i)).classes("text-xl font-bold text-[#1DB954] w-8 text-center")
                    ui.label(song).classes("font-bold text-[#1DB954] w-40 truncate")
                    ui.label(artist).classes("opacity-80 w-32 truncate")
                    ui.label(f"{streams} streams").classes("opacity-60 ml-auto")
                with ui.link(target=link,new_tab=True).classes("no-underline").style('color:white'):
                    ui.button("Go To Spotify",color="#1DB954",)
        with ui.dialog() as dialog, ui.card().style('width: 600px; max-width: none'):
            ui.label("Generated Collage")
            collage = ui.image().classes("w-full")

        def show_collage():
            # Built only when asked for, and shown in the browser rather than on the server
            if not album_covers:
                ui.notify("None of these songs have cover art.", type="warning")
                return
            collage.set_source(get_collage(album_covers))
            dialog.open()

        ui.button("Generate Collage", on_click=show_collage, color="#1DB954")
    # --- ALBUMS MODE ---
    elif RESULT_TYPE == "albums":
        for i, ((album, artist, uri), streams) in enumerate(RESULT_DATA, start=1):
            album_link = uri_to_link(get_album_uri_from_track(uri))
            cover_url = get_album_cover(uri)

            with ui.card().classes(
                    "w-1/2 bg-[#121212] text-white mb-3 p-3 border border-[#1DB95433] hover:bg-[#1DB95422] transition"
            ):
                with ui.row().classes("items-center gap-4 w-full"):
                    if cover_url:
                        ui.image(cover_url).classes("w-14 h-14 rounded")
                    ui.label(str(i)).classes("text-xl font-bold text-[#1DB954] w-8 text-center")
                    ui.label(album).classes("font-bold text-[#1DB954] w-40 truncate")
                    ui.label(artist).classes("opacity-80 w-32 truncate")
                    ui.label(f"{streams} streams").classes("opacity-60 ml-auto")
                with ui.link(target=album_link,new_tab=True).classes("no-underline").style('color:white'):
                    ui.button("Go To Spotify",color="#1DB954",)
    ui.button("Back", on_click=lambda: ui.navigate.to('/'), color="#1DB954")


# storage_secret signs the per-browser storage cookie. Set NICEGUI_STORAGE_SECRET in .env
# to keep sessions across restarts; otherwise a new random secret is used each run.
ui.run(dark=True, storage_secret=os.getenv("NICEGUI_STORAGE_SECRET") or secrets.token_hex(32))