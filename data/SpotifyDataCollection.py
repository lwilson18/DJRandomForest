"""
Author: Logan Wilson

This program is for collection of data from the Spotify API to be used for song recommendation.
Artist names are extracted from a dataset of songs that charted with Billboard, downloaded from:
https://github.com/walkerkq/musiclyrics
This program also requires registration with the Spotify Web API. More info is available at:
https://developer.spotify.com/web-api/
The result of this program is a csv file labelled "spotify_songs.csv".

Other dependences: pandas, numpy, scipy, and spotipy (python library for Spotify Web API - https://spotipy.readthedocs.io/en/latest/)
"""

import pandas as pd
import numpy as np
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import math
from scipy.stats import mode

#Set up credentials for spotipy
sp = spotipy.Spotify()

cid ="YOUR SPOTIFY API CLIENT ID"
secret = "YOUR SPOTIFY API CLIENT SECRET"
client_credentials_manager = SpotifyClientCredentials(client_id=cid, client_secret=secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
sp.trace=False

#Import data from Billboard
billboard = pd.read_csv("billboard_lyrics_1964-2015.csv", encoding = "ISO-8859-1")
#Many artists include 'featuring' - only show first artist
for artist in billboard[billboard.Artist.str.contains(" featuring")].Artist  :
    artist_fixed = artist.split(" featuring")[0]
    billboard.loc[billboard.Artist == artist,"Artist"] = artist_fixed
billboard = billboard[billboard.Year >= 2005] #Only interested in artists who have been popular in recent years

artists = pd.DataFrame(columns=["Artist","Artist_ID","Search_Related"])
#Query artist names in Spotify API to get Artist_IDs
for artist in billboard.Artist.unique() :
    try :
        result = sp.search(artist, type="artist", limit=1)['artists']['items'][0]
    except :
        continue
    artist_name = result['name'] 
    artist_id = result['id']
    artists = artists.append({"Artist":artist_name,"Artist_ID":artist_id,"Search_Related":False}, ignore_index=True)
artists = artists.drop_duplicates()

#For every artist, get their top 20 related artists, then their top 20 related artists, and so on, until number of unique artists is sufficiently large
#This loop ran twice for me
while len(artists) <= 5000:
    for ar_id in artists[artists.Search_Related==False].Artist_ID :
        rel = sp.artist_related_artists(ar_id)['artists']
        artists.loc[artists.Artist_ID == ar_id,"Search_Related"] = True
        for artist in rel :
            artist_name = artist['name']
            artist_id = artist['id']
            artists = artists.append({"Artist":artist_name,"Artist_ID":artist_id,"Search_Related":False}, ignore_index=True)
        artists = artists.drop_duplicates("Artist_ID")
artists = artists.reset_index(drop=True)[['Artist','Artist_ID']]

#For every artist, get all sub-genres, then classify every sub-genre by parent genre
genres = pd.DataFrame()
for i in range(math.ceil(len(artists)/50)) :
    ids = list(artists.iloc[i*50:(i+1)*50,].Artist_ID)
    sp_artists = sp.artists(ids)['artists']
    artist_sub_genres=[a['genres'] for a in sp_artists]
    artist_genres = []
    for sub_genre_list in artist_sub_genres :
        if len(sub_genre_list) == 0 :
            genre_list = np.nan
        else :
            genre_list = []
            for subgenre in sub_genre_list :
                if any(g in subgenre for g in ["blues","jazz","soul","motown","adult","afrobeats","funk"]):
                    genre = "Jazz"
                elif any(g in subgenre for g in ["dancehall","reggae","kompa","riddim"]):
                    genre = "Reggae"
                elif any(g in subgenre for g in ["soundtrack","score","broadway","hollywood","tunes"]):
                    genre = "Soundtrack"
                elif any(g in subgenre for g in ["country","folk","redneck"]):
                    genre = "Country"
                elif "latin" in subgenre :
                    genre = "Latin"
                elif any(g in subgenre for g in ["rock","metal","mellow gold","grunge","punk","emo","screamo","jam"]):
                    genre = "Rock"
                elif any(g in subgenre for g in ["house","edm","eurodance","electro","freestyle","trance","rave","wave","hands up","strut","hardstyle","techno","dubstep"]):
                    genre = "Dance / Electronic"
                elif any(g in subgenre for g in ["rap","r&b","trap", "hip hop","urban","new jack swing","crunk","hyphy","grime"]):
                    genre = "R&B / Hip-Hop"
                elif any(g in subgenre for g in ["pop","bubblegum","neo mellow","boy band","a cappella","opm","idol","francoton"]):
                    genre = "Pop"
                else : #Some sub-genres missing or obscure
                    genre = "Other"
                genre_list.append(genre)
        artist_genres.append(genre_list)
    genres = genres.append(pd.DataFrame({"Artist_ID":ids,"SubGenres":artist_sub_genres,"Genres":artist_genres}), ignore_index=True)
    
#For every artist, find the most common parent genre
def genre_mode(genre_list) :
    if type(genre_list) != list :
        return "Other"
    else:
        m = mode(genre_list).mode[0]
        if m == "Other" :
            genre_list = list(filter(lambda g: g != "Other", genre_list))
            if len(genre_list) == 0 :
                m = "Other"
            else :
                m = mode(genre_list).mode[0]
        return m
genres['Genre'] = genres.Genres.apply(genre_mode)

#For every artist, get top 10 tracks
songs = pd.DataFrame(columns=["Song_ID","Song","Artist_ID","Album","Preview"])
for artist_id in artists.Artist_ID :
    tracks=sp.artist_top_tracks(artist_id)['tracks']
    for track in tracks :
        song_name = track['name']
        album_name = track['album']['name']
        song_id = track['id']
        song_preview = track['preview_url']
        songs = songs.append({"Song_ID":song_id,"Song":song_name,"Artist_ID":artist_id,
                              "Album":album_name,"Preview":song_preview}, ignore_index=True)
songs = songs.drop_duplicates('Song_ID').merge(artists, on="Artist_ID")

#For every track, get audio features
song_features = pd.DataFrame()
for i in range(math.ceil(len(songs)/50)) :
    ids = list(songs.iloc[i*50:(i+1)*50,].Song_ID)
    features = sp.audio_features(ids)
    song_features = song_features.append(pd.DataFrame(list(filter(None,features))), ignore_index=True)

#Merge data into single dataframe
m=songs.merge(song_features.rename(columns={"id":"Song_ID"}), on = "Song_ID").merge(genres,on="Artist_ID")\
[['Song_ID', 'Song', 'Artist', 'Album','Genre','Preview','duration_ms','key','mode','tempo',
  'acousticness', 'danceability','energy','instrumentalness','liveness','loudness','speechiness','valence',
 'Pop','R&B / Hip-Hop','Dance / Electronic','Rock','Latin','Country','Jazz']]

#Remove tracks with no preview
m = m[m.Preview.notnull()]

#Export to csv
m.to_csv("Spotify_Songs.csv",index=False)
