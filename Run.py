from mutagen.id3 import APIC, ID3
import glob
from mutagen.easyid3 import EasyID3
import requests
from yt_dlp import YoutubeDL
import spotipy
import os
from youtubesearchpython import VideosSearch

YTDL = YoutubeDL()
Spotipe = spotipy.Spotify(auth_manager=spotipy.SpotifyClientCredentials(client_id="7e4d774b54a0431487f59eab9af61138", client_secret="525461cc1fa343de856dc138755ea0f5"))


def FixName(string):
    string = string.replace(":", "").replace("*", "#").replace(">", "").replace("<", "").replace("?", "").replace("|", "").replace("/", "").replace("\\", "").replace("【", "(").replace("】", ")").replace('"', "''")
    return string


def GetAlbumCover(Album):
    CoverUrl = ""
    Largest = 0
    for Cover in Album["images"]:
        if Cover["height"] > Largest:
            Largest = Cover["height"]
            CoverUrl = Cover["url"]
    return CoverUrl


def DownloadSong(Song, Directory, AccurateMode = True):
    authorz = ""
    for author in Song.Artists:
        authorz += f'{author}; '
    authorz = authorz[0: len(authorz) - 2]

    try:
        if AccurateMode:
            link = VideosSearch(f'intitle:"{Song.Name}" By: {authorz} -"full album"', limit=1).result()["result"][0]["link"]
        else:
            link = VideosSearch(Song.Name, limit=1).result()["result"][0]["link"]
    except:
        print(f"Could not find the song: {Song.Name}")
        return
    print(f"Downloading: {Song.Name}, from the YouTube url: {link}")
    Destination = Directory.split('\\')
    FileName = Destination[-1]
    Destination.remove(FileName)
    Destination[-1] = FixName(Destination[-1])
    Destination = "\\".join(Destination)
    FileName = FixName(Song.Name.split(" - ")[0])
    try:
        os.chdir(Destination)
    except FileNotFoundError:
        os.mkdir(Destination)
        os.chdir(Destination)

    DesiredPath = f"{Destination}\\{FileName}.mp3"
    if not os.path.isfile(DesiredPath):
        os.system(f"yt-dlp --restrict-filenames --rm-cache-dir --add-metadata -x --audio-format mp3 {link}")
        gitignore = open(".gitignore", "w")
        gitignore.write("*")
        gitignore.close()
        list_of_files = glob.glob(f"{Destination}\\*")  # * means all if need specific format then *.csv
        if True:
            latest_file = max(list_of_files, key=os.path.getctime)
            ShitPath = latest_file
        else:
            ShitPath = DesiredPath

        Meta = EasyID3(ShitPath)
        Meta["title"] = Song.Name
        Meta["author"] = authorz
        Meta["artist"] = authorz
        Meta["composer"] = authorz
        Meta["album"] = Song.Album
        # Meta["compilation"] = 1  #itunes compilation thing
        # Meta["albumartistsort"] = 1
        Meta.save(ShitPath)

        Cover = requests.get(Song.Cover).content
        Meta = ID3(ShitPath)
        Meta.add(APIC(encoding=3,mime='image/jpeg',type=3, desc=u'Cover',data=Cover))
        Meta.save(v2_version=3)
        os.rename(ShitPath, DesiredPath)
    else:
        print(f"{Song.Name} has already been downloaded!")


class Song:
    Name = "name not found"
    Album = "album not found"
    Artists = ["artists not found"]
    Cover = "https://assets.coingecko.com/coins/images/30246/large/photo_2023-05-04_16-06-17.jpg?1696529155"

    @classmethod
    def ManualInit(self, Name, Album, Artists, Cover):
        self.Name = Name
        self.Album = Album
        self.Artists = Artists
        self.Cover = Cover
        return self

    @classmethod
    def TrackInit(self, TrackData):
        self.Name = TrackData["name"]
        self.Album = TrackData["album"]["name"]
        artists = []
        for artist in TrackData["artists"]:
            artists.append(artist["name"])
            self.Artists = artists
        self.Cover = GetAlbumCover(TrackData["album"])
        return self


MediaUrl = input("Please enter a spotify URL:\n") # for now only tracks
while not MediaUrl.startswith("https://open.spotify.com/"):
    MediaUrl = input("ENTER A SPOTIFY URL:\n") # for now only tracks
SpotifyUrl = MediaUrl.split("/")
ID = SpotifyUrl[len(SpotifyUrl) - 1]
MediaType = SpotifyUrl[len(SpotifyUrl) - 2]
dir_path = f'{os.path.dirname(os.path.realpath(__file__))}\\Downloads\\'

if MediaType == "artist":
    ArtistName = Spotipe.artist(ID)["name"]
    TopTracks = Spotipe.artist_top_tracks(ID)
    if "followers" in TopTracks:
        ID = TopTracks["id"]
        TopTracks = Spotipe.artist_top_tracks(ID)

    for Track in TopTracks["tracks"]:
        ThisTrack = Song().TrackInit(Track)
        DownloadSong(ThisTrack, f'{dir_path}\\{ArtistName}\\)')
    # print(ID)
    # print(Spotipe.artist_top_tracks("5y8tKLUfMvliMe8IKamR32"))

if MediaType == "playlist":
    PlaylistName = Spotipe.playlist_items(ID)["name"]
    PlaylistTracks = Spotipe.playlist_items(ID)["tracks"]["items"]
    for Entry in PlaylistTracks:
        ThisSong = Song().TrackInit(Entry["track"])
        DownloadSong(ThisSong, f'{dir_path}\\{PlaylistName}\\)')

if MediaType == "album":
    Album = Spotipe.album(ID)
    AlbumTracks = Album["tracks"]["items"]

    for Track in AlbumTracks:
        artists = []
        for artist in Album["artists"]:
            artists.append(artist["name"])
        ThisSong = Song().ManualInit(Track["name"], Album["name"], artists, GetAlbumCover(Album))
        DownloadSong(ThisSong, f'{dir_path}\\{Album["name"]}\\')

if MediaType == "track":
    ThisSong = Song().TrackInit(Spotipe.track(ID)) # ID is already the tracks ID
    DownloadSong(ThisSong, f'{dir_path}\\UNSORTED SONGS\\')

input("Downloading complete! press ENTER to close...")


