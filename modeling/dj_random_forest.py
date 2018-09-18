import pandas as pd
import numpy as np
import h2o
from h2o.estimators.random_forest import H2ORandomForestEstimator
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
from flask import url_for

def bin_response(rating) :
    if rating >= 4 :
        bin_response = "like"
    else :
        bin_response = "dislike"
    return bin_response

def bin_weight(rating) :
    if rating >= 4 :
        weight = rating-3
    else :
        weight = 4-rating
    return weight

class DJRandomForest(object):
    def __init__(self, song_df):
        h2o.init()
        h2o.no_progress()
        self.song_df = song_df.sort_values('song_id')
        self.song_df_h2o = h2o.H2OFrame(self.song_df.drop(['Song','Artist','Album'],axis=1))
        self.X = ['Genre','mode', 'tempo', 'acousticness', 'danceability', 'energy', 
        'instrumentalness','liveness', 'loudness', 'speechiness', 'valence']
        self.classifier = H2ORandomForestEstimator(ntrees=350,min_rows=3)

    def recommend(self, training_df):
        self.training_df = training_df
        # Calculate binary response
        training_df['response'] = training_df.rating.apply(bin_response)
        # Calculate training weights
        training_df['weight'] = training_df.rating.apply(bin_weight)
        training_songs = list(training_df.song_id)
        # Convert to h2o-frame
        training_df_h2o = h2o.H2OFrame(training_df)
        self.classifier.train(self.X, "response", training_frame=training_df_h2o, weights_column="weight")
        #select songs for testing
        self.testing_df = self.song_df.loc[~self.song_df.song_id.isin(training_songs)]
        test_songs_h2o = self.song_df_h2o[~self.song_df_h2o['song_id'].isin(training_songs)]
        prediction = self.classifier.predict(test_songs_h2o).as_data_frame().like
        self.testing_df['Prediction'] = prediction
        self.testing_df = self.testing_df.sort_values('Prediction', ascending=False)

    def top_songs(self, n):
        return self.testing_df.sort_values('Prediction', ascending=False).head(n).song_id.values.tolist()

    def sample(self, n):
        song_dict = {}
        top_songs = self.top_songs(n)
        song_dict['2'] = top_songs
        self.testing_df = self.testing_df.loc[~self.testing_df.song_id.isin(top_songs)]
        sample_weights = self.testing_df.Prediction / self.testing_df.Prediction.sum()
        sampled_songs = self.testing_df.sample(n, weights=sample_weights)
        song_dict['1'] = sampled_songs.song_id.values.tolist()
        self.testing_df = self.testing_df.drop(sampled_songs.index)
        song_dict['0'] = self.testing_df.sample(n).song_id.values.tolist()
        return song_dict

    def audio_profile(self) :
        varimps = pd.DataFrame(self.classifier.varimp())[[0,3]].rename(columns={0:"variable",3:"percent_importance"})
        liked_songs = self.training_df[self.training_df.rating >= 4] #only consider liked songs when calculating weights
        for var in varimps.variable :
            if var != "Genre" :
                varimps.loc[varimps.variable==var,"weighted_mean"] = np.average(liked_songs[var],weights=liked_songs.weight)
            else : #for genre, use mode rather than weighted mean
                genres = liked_songs.Genre.unique()
                weights = [liked_songs.loc[liked_songs.Genre==g,"weight"].sum() for g in genres]
                genre_mode = genres[weights.index(max(weights))]
                varimps.loc[varimps.variable==var,"weighted_mean"] = genre_mode
        return varimps


def visualize_audio_profile(audio_profile,image_signature) :
    audio_profile = audio_profile.pivot(index="iteration",columns="variable",values="percent_importance")
    if len(audio_profile) == 1 :
        audio_profile.transpose().plot(kind='bar',legend=False, rot=45, title="Audio Feature % Importance")
        plt.xlabel("")
        plt.ylabel('% Importance')
        plt.tight_layout()
        plt.savefig('app/static/audio_profile_{}.png'.format(image_signature))
        #plt.savefig(url_for('static')+'/audio_profile_{}.png'.format(image_signature))
    else :
        audio_profile.plot(colormap=plt.cm.gist_rainbow)
        lgd = plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
        plt.xticks(list(audio_profile.index))
        plt.ylabel("% Importance")
        plt.xlabel("Model Iteration")
        plt.title("Audio Feature % Importance")
        plt.savefig('app/static/audio_profile_{}.png'.format(image_signature), bbox_extra_artists=(lgd,), bbox_inches='tight')
        #plt.savefig(url_for('static')+'/audio_profile_{}.png'.format(image_signature),bbox_extra_artists=(lgd,), bbox_inches='tight')
