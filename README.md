# DJ Random Forest
## Overview

DJ Random Forest is a Python application for recommending songs and creating audio profiles based on ratings and audio features via random forest machine learning using data collected from the Spotify Web API.

## Dependencies
DJ Random Forest requires the following libraries:
 * pandas
 * [H2O](https://h2o-release.s3.amazonaws.com/h2o/rel-turan/4/docs-website/h2o-py/docs/intro.html) 
  
Song recommendations are generated using the DJRandomForest class included under `modeling`.

## Data Collection

To create the database of song previews and features used to generate song recommendations, the Spotify Web API was queried via the script `SpotifyDataCollection` file under `data`. The initial data set used to extract artist names to query is available [here](https://github.com/walkerkq/musiclyrics).

Collect your own data via `SpotifyDataCollection` requires:
 * A valid API client ID/secret from Spotify (https://developer.spotify.com/web-api/)
 * pandas 
 * numpy
 * scipy
 * [spotipy](https://spotipy.readthedocs.io/en/latest/)

## Documentation
Read a technical discussion of the design and performance of DJ Random Forest [here](http://sites.northwestern.edu/msia/2018/02/09/dj-random-forest-song-recommendations-through-machine-learning/).

