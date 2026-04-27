from main import *
from SpotifyStreamingHistory import *

def getSpotifyAlbumCovers(sp,albums):
    for album in albums:
        print(album)
        result = sp.search(q="album%2520"+album[0]+"%2520artist%3A"+album[1],type="album", limit=1)
        resultArtist = result['albums']
        print(resultArtist)
        resultArtistPicture = resultArtist['items'][0]['images'][0]['url']
        print(resultArtistPicture)

def main():
    sp = create_spotify_client()
    artists = ['Freeze','Taylor Swift','Taylor Swift','Taylor Swift','Taylor Swift','Taylor Swift','Taylor Swift','Taylor Swift','Taylor Swift','Taylor Swift','Taylor Swift','Taylor Swift']
    albums = ['Kygo', 'Fearless', 'Speak Now','Red','1989','Reputation', 'Lover', 'folklore', 'evermore', 'Midnights','THE TORTURED POETS DEPARTMENT','The Life Of A Showgirl']
    results = zip(artists, albums)
    getSpotifyAlbumCovers(sp,results)

if __name__ == '__main__':
    main()