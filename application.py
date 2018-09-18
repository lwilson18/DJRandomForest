import pandas as pd
from flask import render_template, request, redirect, session, url_for
from app import application, db
from app.models import Rating
import random
from modeling.dj_random_forest import DJRandomForest, visualize_audio_profile
import os
import logging

song_df = pd.read_sql("select * from songs",db.engine).sort_values('song_id')
DJ_RF = DJRandomForest(song_df) #convert everything into h2o frame
SONGS_PER_ITERATION = 10

@application.route('/', methods=['GET','POST'])
def start():
	user_id = random.getrandbits(16) #unique identifier
	# add information to session
	session['user_id'] = user_id
	session['iteration'] = 0
	session['song_ct'] = 0
	session['sampled_songs'] = {2: list(song_df.sample(SONGS_PER_ITERATION).song_id)}
	session['confidence'] = 2
	session['check_recommend'] = False
	session['audio_profile'] = pd.DataFrame(columns=song_df.columns[4:].tolist()+['iteration']).to_json()
	return redirect(url_for('train_redirect'))

@application.route('/redirect')
def train_redirect():
	user_id = session.get('user_id',None)
	iteration = session.get('iteration',None)
	song_ct = session.get('song_ct', None)
	# Remove audio profile visualization if it exists
	audio_profile_path = 'static/audio_profile_{}-{}.png'.format(user_id,iteration)
	if os.path.isfile(audio_profile_path): 
		os.remove(audio_profile_path)
	#Check if ready to get new recommendations
	if ((song_ct % SONGS_PER_ITERATION == 0) and (song_ct > 0)) or session.get('check_recommend',None):
		ratings_query = "select song_id, rating from rating where user_id={}".format(user_id)
		rated_songs = pd.read_sql(ratings_query, db.engine)
		# Need at least 1 positive and negative song
		if (len(rated_songs[rated_songs.rating < 0]) > 0) and \
		(len(rated_songs[rated_songs.rating > 0]) > 0):
			rated_song_data = rated_songs.merge(song_df, on='song_id')
			DJ_RF.recommend(rated_song_data)
			session['top_songs'] = DJ_RF.top_songs(SONGS_PER_ITERATION)
			session['sampled_songs'] = DJ_RF.sample(SONGS_PER_ITERATION)
			audio_profile = pd.read_json(session.get('audio_profile', None))
			audio_profile_update = DJ_RF.audio_profile()
			audio_profile_update['iteration'] = iteration
			session['audio_profile'] = audio_profile.append(audio_profile_update).to_json()
			session['iteration'] = iteration + 1
			session['check_recommend'] = False
		# Check one more song
		else:
			session['check_recommend'] = True
	sampled_songs = session.get('sampled_songs', None)
	confidence = str(session.get('confidence', None))
	if sampled_songs[confidence] == []:
		# if on the first iteration run out of songs, sample more
		sampled_songs = {confidence: list(song_df.sample(SONGS_PER_ITERATION).song_id)}
	song_id = sampled_songs[confidence].pop()
	session['sampled_songs'] = sampled_songs
	session['song_ct'] = song_ct + 1
	return redirect(url_for('song_pg',song_id=song_id))

@application.route('/song/<song_id>', methods=['GET','POST'])
def song_pg(song_id):
	preview_url = song_df.loc[song_df.song_id==song_id,"Preview"].item()
	iteration = session.get('iteration',None)
	confidence = session.get('confidence', None)
	if request.method == 'POST':
		rating = int(request.form['rating'])
		# get slider value
		if iteration > 0: # slider only appears after 1st iteration
			confidence = request.form['slider']
			session['confidence'] = confidence
		# save rating to database
		user_id = session.get('user_id',None)
		confidence = session.get('confidence', None)
		rating_entry = Rating(user_id=user_id,rating=rating,song_id=song_id,iteration=iteration,confidence=confidence)
		db.session.add(rating_entry)
		db.session.commit()
		# go to another song
		return redirect(url_for('train_redirect'))
	return render_template('song_pg.html', preview_url=preview_url, iteration=iteration,
						   confidence=confidence)

@application.route('/view_songs/<type>', methods=['GET','POST'])
def view_songs(type):
	if type == "all":
		user_id = session.get('user_id',None)
		ratings_query = "select song_id from rating where user_id={}".format(user_id)
		songs = pd.read_sql(ratings_query, db.engine)
	else:
		songs = pd.DataFrame({"song_id" : session.get('top_songs')})
	songs = songs.merge(song_df,how="left",on="song_id")[['Song','Artist','Album','Preview']]
	return render_template('view_songs.html', songs=songs)

@application.route("/audio_profile", methods=['GET','POST'])
def audio_profile():
	user_id = session.get('user_id',None)
	iteration = session.get('iteration',None)
	audio_profile = pd.read_json(session.get('audio_profile', None))
	image_signature = "{}-{}".format(user_id,iteration)
	visualize_audio_profile(audio_profile,image_signature)
	return render_template('view_audio_profile.html',image_signature=image_signature)
