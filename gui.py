import tkinter as tk
from datetime import date
from typing import Final

import SpotifyStreamingHistory
from SpotifyStreamingHistory import *
ANALYSIS_START_YEAR: Final[int] = 2014
"""
def streams():
    sp = SpotifyStreamingHistory.create_spotify_client()
    streams, song_pairs, artists, albums = SpotifyStreamingHistory.readInStreams("all")
    topSong = topSongs(song_pairs, 25,all,sp)

    def streams():
        sp = SpotifyStreamingHistory.create_spotify_client()
        streams, song_pairs, artists, albums = SpotifyStreamingHistory.readInStreams("all")
        topSong = topSongs(song_pairs, 25, all, sp)

    def main():
        application = tk.Tk()
        application.geometry("500x500")
        application.title("Spotify")
        label = tk.Label(application, text="Spotify Streaming History", font=("Arial", 20))
        label.pack(padx=20, pady=20)
        frame = tk.Frame(application)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=1)
        frame.rowconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        frame.rowconfigure(2, weight=1)
        btn1 = tk.Button(frame, text="Enable", font=("Arial", 20), command=streams)
        btn1.grid(row=0, column=0, sticky=tk.W + tk.E)
        label1 = tk.Label(frame, text="Read in Streams")
        label1.grid(row=0, column=1, sticky=tk.W + tk.E)
        btn2 = tk.Checkbutton(frame, text="Search", font=("Arial", 20))
        frame.pack(padx=20, pady=20, fill=tk.X)
        application.mainloop()
"""

class MyGUI:
    def __init__(self):
        self.application = tk.Tk()
        self.application.geometry("750x750")

        self.application.title("SpotifyStreamingHistory")
        self.bg = tk.PhotoImage(file="assets/Spotify Logo.png")
        self.label1 = tk.Label(self.application, image=self.bg, anchor="center")
        self.label1.place(x=0, y=0)
        self.label = tk.Label(self.application, text="Spotify Streaming History", font=("Arial", 20))
        self.label.pack(padx=20, pady=20)
        #Frame Setup
        self.frame = tk.Frame(self.application)
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=1)
        self.frame.rowconfigure(2, weight=1)
        self.frame.rowconfigure(3, weight=1)
        self.frame.rowconfigure(4, weight=1)
        self.frame.rowconfigure(5, weight=1)

        # Frame fill variables setup
        self.dataOption = tk.StringVar()
        self.rangeOption = tk.StringVar()
        self.yearOption = tk.StringVar()
        self.playlistOption = tk.BooleanVar()

        # Frame Setup
        self.dataType = tk.OptionMenu(self.frame , self.dataOption, "Albums", "Artists", "Songs" )
        self.dataType.grid(row=0, column=0)
        self.Typelabel = tk.Label(self.frame, text="Data Type", font=("Arial", 15))
        self.Typelabel.grid(row=0, column=1)
        self.streamsYear = tk.OptionMenu(self.frame , self.yearOption, *list(range(ANALYSIS_START_YEAR, date.today().year+1)) + ["all"])
        self.streamsYear.grid(row=1, column=0,)
        self.yearLabel = tk.Label(self.frame, text="Year", font=("Arial", 15))
        self.yearLabel.grid(row=1, column=1)
        self.streamsRange = tk.Entry(self.frame, textvariable=self.rangeOption)
        self.streamsRange.grid(row=2, column=0)
        self.rangeLabel = tk.Label(self.frame, text="Range", font=("Arial", 15))
        self.rangeLabel.grid(row=2, column=1)
        self.streamsPlaylist = tk.Checkbutton(self.frame, text="Create a Playlist?", variable=self.playlistOption)
        self.streamsPlaylist.grid(row=3, column=0)


        self.frame.pack(padx=20, pady=20, fill=tk.X)

        self.goButton = tk.Button(self.application, text="Read in Streams", command=self.streamBegins,font=("Arial", 20))
        self.goButton.pack(padx=20, pady=20)
        self.application.mainloop()

    def streamBegins(self):
        type = self.dataOption.get()
        range = int(self.rangeOption.get())
        year = self.yearOption.get()
        playlist = self.playlistOption.get()

        sp = SpotifyStreamingHistory.create_spotify_client()
        streams, song_pairs, artists, albums = SpotifyStreamingHistory.readInStreams(year)
        match type:
            case "Artists":
                topArtists(artists, range)
            case "Songs":
                uriList, outputImage = topSongs(song_pairs, range, year, sp)
                if playlist:
                    create_playlist(sp, uriList, outputImage, range, year)
            case "Albums":
                topAlbum(sp, albums, range)
MyGUI()