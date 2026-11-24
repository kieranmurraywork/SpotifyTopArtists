main.py
-
Script used to connect to Spotify and return your top most played songs in a given time range (short,medium & long term), with the ability to create a playlist and a slideshow of these songs.

Also generates a heatmap of the covers of your most listened to song.

Flags
-
-r: --range - Time range for top tracks (Options: short_term, medium_term (default), long_term)

-l: --limit - Number of tracks to fetch (default: 50)

-p: --playlist - Generate a playlist for your top songs (off unless given, e.g. `python main.py -p`)

-s: --slideshow - Generate a slideshow for your top songs (off unless given)

Requires Spotify API access - WIP

SpotifyStreamingHistory.py
-
Script that takes Spotify's provided Extended Streaming History data and outputs users top songs, artists or albums for a given range.

Steps:
-
1. Visit https://www.spotify.com/uk/account/privacy/ and tick the Extended Streaming History box, then request your data.
2. Spotify will email you a zip folder of your streaming history
3. Extract this folder into the Spotify Top Artists directory. Any folder whose name starts with "Spotify Extended Streaming History" is read, so several exports can sit side by side.
4. Run the script with your preferred flags
5. Enjoy!

Only plays of 30 seconds or more are counted, matching how Spotify counts a stream.

Flags
-
-t: --type - Whether to show top songs, top artists, or top albums. Options - (artists, albums, songs; default: songs)

-y --year - Specify what year you would like to receive the data from. Options - (any year in your history, or "all" for entire streaming history, default: all)

-r --range - Number of items to show (default: 10)

-p --playlist - Create a playlist of your top songs (off unless given)

-f --first_played SONG ARTIST - Show when you first played a song, e.g. `-f "august" "Taylor Swift"`

-i --ignore ARTIST [ARTIST ...] - Artists to leave out of the results
