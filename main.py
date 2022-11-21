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

def RemoveUnacceptableCharacters(string):
    return string.replace(":", "").replace(">", "").replace("<", "").replace("?", "").replace("|", "").replace("/", "").replace("\\", "")

def GetSongName(Song, FromPlaylist):
    if FromPlaylist:
        Song = Song["track"]
    Artists = ""
    for Artist in Song["artists"]:
        if Artists != "":
            Artists += "; "
        Artists += f'{Artist["name"]}'

    return f"{Song['name']} - {Artists}"

def GetSongCoverUrl(Song):
    CoverUrl = ""
    Largest = 0
    for Cover in Song["album"]["images"]:
        if Cover["height"] > Largest:
            Largest = Cover["height"]
            CoverUrl = Cover["url"]
    return CoverUrl


def DownloadSong(Name, Directory, Album):
    AlbumName = Album[0]
    CoverURL = Album[1]
    link = VideosSearch(Name, limit=1).result()["result"][0]["link"]
    print(f"Downloading: {Name}, from the YouTube url: {link}")
    Destination = Directory.split('\\')
    FileName = Destination[-1]
    Destination.remove(FileName)
    Destination[-1] = RemoveUnacceptableCharacters(Destination[-1])
    Destination = "\\".join(Destination)
    FileName = Name.split(" - ")[0]

    try:
        os.chdir(Destination)
    except FileNotFoundError:
        os.mkdir(Destination)
        os.chdir(Destination)

    DesiredPath = f"{Destination}\\{FileName}.mp3"
    ShitPath = ""
    if not os.path.isfile(DesiredPath):
        os.system(f"youtube-dl --restrict-filenames --add-metadata -x --audio-format mp3 {link}")
        gitignore = open(".gitignore", "w")
        gitignore.write("*")
        gitignore.close()
        list_of_files = glob.glob(f"{Destination}\\*")  # * means all if need specific format then *.formatname
        latest_file = max(list_of_files, key=os.path.getctime)
        ShitPath = latest_file
        os.rename(ShitPath, DesiredPath)

        Meta = EasyID3(DesiredPath)
        Meta["title"] = Name.split(" - ")[0]
        Meta["author"] = Name.split(" - ")[1]
        #Meta["compilation"] = 1  #itunes compilation thing
        Meta.save(DesiredPath)

        Cover = requests.get(CoverURL).content
        Meta = ID3(DesiredPath)
        Meta.add(APIC(encoding=3,mime='image/jpeg',type=3, desc=u'Cover',data=Cover))
        Meta.save(v2_version=3)
    else:
        print(f"{Name} has already been downloaded!")


def main():
    MediaUrl = input("Enter Spotify Url:\n")
    SpotifyUrl = MediaUrl.split("/")
    ID = SpotifyUrl[-1]
    MediaType = SpotifyUrl[-2]
    SpotifyUrl = f"spotify:{MediaType}:{ID}"

    if MediaType == "playlist":
        Playlist = Spotipe.playlist_items(ID)["tracks"]["items"]
        PlaylistName = Spotipe.playlist_items(ID)["name"]
        print(f"Playlist identified: {PlaylistName}")

    if MediaType == "album":
        Album = Spotipe.album(ID)["tracks"]["items"]
        AlbumName = Spotipe.album(ID)["name"]
        AlbumCover = Spotipe.album(ID)["images"][0]["url"]
        AlbumAuthors = ""
        for Artist in Spotipe.album(ID)["artists"]:
            if AlbumAuthors != "":
                AlbumAuthors += ", "
            AlbumAuthors += f'{Artist["name"]}'
        print(f"Album identified: {AlbumName}. By: {AlbumAuthors}")

    print("Processing Music... ( This may take some time ! )")
    dir_path = os.path.dirname(os.path.realpath(__file__))

    if MediaType == "playlist":
        Queries = []
        for Track in Playlist:
            Queries.append((GetSongName(Track, True), (Track["track"]["album"]["name"], GetSongCoverUrl(Track))))

        for Video in Queries:
            DownloadSong(Video[0], f'{dir_path}\\{PlaylistName}\\{Video[0].replace("/", "")}.mp3', Video[1])

    elif MediaType == "track":
        Song = GetSongName(Spotipe.track(ID), False)
        Path = f'{dir_path}\\Songs\\{Song.replace("/", "")}.mp3'
        DownloadSong(Song, Path, (Spotipe.track(ID)["album"]["name"], GetSongCoverUrl(Spotipe.track(ID))))

    elif MediaType == "album":
        Queries = []
        for Track in Album:
            Queries.append(GetSongName(Track, False))
        for Video in Queries:
            DownloadSong(Video, f'{dir_path}\\{AlbumName} - {AlbumAuthors}\\{Video.replace("/", "")}.mp3', (AlbumName, AlbumCover))


if __name__ == "__main__":
    main()
    input("Press ENTER to continue...\n")
