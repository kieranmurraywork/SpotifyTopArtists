from nicegui import ui
from datetime import date
import SpotifyStreamingHistory
from SpotifyStreamingHistory import *

ANALYSIS_START_YEAR = 2014

RESULT_DATA = {}
RESULTS = {}
RESULT_TYPE = ""
sp = SpotifyStreamingHistory.create_spotify_client()
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
    def start_app():
        welcome.classes(add="opacity-0")
        ui.timer(0.7, lambda: main_ui.classes(remove="hidden opacity-0"), once=True)

    def streamsSetup():
        nonlocal dataOption, rangeOption, yearOption, playlistOption
        global RESULT_DATA
        global RESULTS
        global RESULT_TYPE
        global songuri

        type_ = dataOption.value
        range_ = int(rangeOption.value)
        year = yearOption.value
        playlist = playlistOption.value

        sp = SpotifyStreamingHistory.create_spotify_client()
        streams, song_pairs, artists, albums = SpotifyStreamingHistory.readInStreams(year)
        songuri = []
        match type_:
            case "Artists":
                RESULT_DATA = topArtists(artists, range_)
                print(RESULT_DATA)
                RESULT_TYPE = "artists"

            case "Songs":
                RESULT_DATA, outputImage = topSongs(song_pairs, range_, year, sp)
                for ((song, artist, uri), count) in RESULT_DATA:
                    songuri.append(uri)
                RESULT_TYPE = "songs"
                if playlist:
                    create_playlist(sp, songuri, outputImage, range_, year )

            case "Albums":
                RESULT_DATA = topAlbum(albums, range_, sp)
                print(RESULT_DATA)
                RESULT_TYPE = "albums"

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
            yearOption = ui.select(list(range(ANALYSIS_START_YEAR, date.today().year + 1)) + ["all"], label="Year").classes("w-64")
            rangeOption = ui.input(label="Range", placeholder="Enter a number").classes("w-64")
            playlistOption = ui.checkbox("Create a Playlist?",value=False).classes("w-64")

            ui.button("Read in Streams", on_click=streamsSetup, color="#1DB954")

@ui.page('/results')
def results_page():
    def get_album_cover(sp, track_uri):
        track = sp.track(track_uri)
        return track["album"]["images"][0]["url"]  # highest resolution

    def get_artist_uri(sp, artist_name):
        results = sp.search(q=f"artist:{artist_name}", type="artist", limit=1)
        items = results["artists"]["items"]
        if not items:
            return None
        return items[0]["uri"]

    def get_artist_image(sp, artist_name):
        results = sp.search(q=f"artist:{artist_name}", type="artist", limit=1)
        items = results["artists"]["items"]
        if not items:
            return None
        return items[0]["images"][0]["url"]  # highest resolution

    def uri_to_link(uri: str) -> str:
        parts = uri.split(':')  # ['spotify', 'track', '4pvb0WLRcMtbPGmtejJJ6y']
        if len(parts) != 3:
            return "#"  # or raise an error
        _, kind, id_ = parts
        return f"https://open.spotify.com/{kind}/{id_}"

    def get_album_uri_from_track(sp, track_uri):
        track = sp.track(track_uri)
        return track["album"]["uri"]

    # --- ARTISTS MODE ---
    if RESULT_TYPE == "artists":
        ui.label("Top Artists")
        with ui.row().classes("flex-wrap gap-0 justify-center"):
            for i, (artist, streams) in enumerate(RESULT_DATA, start=1):
                image_url = get_artist_image(sp, artist)
                uri = get_artist_uri(sp, artist)
                link = uri_to_link(uri) if uri else "#"

                with ui.link(target=link,new_tab=True).classes("no-underline"):
                    with ui.card().classes(
                            "w-1/2 bg-[#121212] text-white mb-3 p-3 border border-[#1DB95433] hover:bg-[#1DB95422] transition"
                    ):
                        with ui.row().classes("items-center gap-4 w-full"):
                            if image_url:
                                ui.image(image_url).classes("w-14 h-14 rounded-full")

                            ui.label(str(i)).classes("text-xl font-bold text-[#1DB954] w-8 text-center")
                            ui.label(artist).classes("font-bold text-[#1DB954] w-40 truncate")
                            ui.label(f"{streams} streams").classes("opacity-60 ml-auto")

    # --- SONGS MODE ---
    elif RESULT_TYPE == "songs":
        for i, ((song, artist, uri), streams) in enumerate(RESULT_DATA, start=1):
            cover_url = get_album_cover(sp, uri)
            link = uri_to_link(uri)

            with ui.link(target=link,new_tab=True).classes("no-underline"):
                with ui.card().classes(
                        "w-1/2 bg-[#121212] text-white mb-3 p-3 border border-[#1DB95433] hover:bg-[#1DB95422] transition"
                ):
                    with ui.row().classes("items-center gap-4 w-full"):
                        ui.image(cover_url).classes("w-14 h-14 rounded")
                        ui.label(str(i)).classes("text-xl font-bold text-[#1DB954] w-8 text-center")
                        ui.label(song).classes("font-bold text-[#1DB954] w-40 truncate")
                        ui.label(artist).classes("opacity-80 w-32 truncate")
                        ui.label(f"{streams} streams").classes("opacity-60 ml-auto")
    # --- ALBUMS MODE ---
    elif RESULT_TYPE == "albums":
        for i, ((album, artist, uri), streams) in enumerate(RESULT_DATA, start=1):
            album_link = uri_to_link(get_album_uri_from_track(sp, uri))
            cover_url = get_album_cover(sp, uri)

            with ui.link(target=album_link, new_tab=True).classes("no-underline"):
                with ui.card().classes(
                        "w-1/2 bg-[#121212] text-white mb-3 p-3 border border-[#1DB95433] hover:bg-[#1DB95422] transition"
                ):
                    with ui.row().classes("items-center gap-4 w-full"):
                        ui.image(cover_url).classes("w-14 h-14 rounded")
                        ui.label(str(i)).classes("text-xl font-bold text-[#1DB954] w-8 text-center")
                        ui.label(album).classes("font-bold text-[#1DB954] w-40 truncate")
                        ui.label(artist).classes("opacity-80 w-32 truncate")
                        ui.label(f"{streams} streams").classes("opacity-60 ml-auto")

    ui.button("Back", on_click=lambda: ui.navigate.to('/'), color="#1DB954")


ui.run(dark=True)