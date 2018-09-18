import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt

def visualize_audio_profile(audio_profile,image_signature) :
	audio_profile = audio_profile.pivot(index="iteration",columns="variable",values="percent_importance")
	if len(audio_profile) == 1 :
		audio_profile.transpose().plot(kind='bar',legend=False, rot=45, title="Audio Feature % Importance")
		plt.xlabel("")
		plt.ylabel('% Importance')
		plt.tight_layout()
		plt.savefig('static/audio_profile_{}.png'.format(image_signature))
		#plt.savefig(url_for('static', filename='audio_profile_{}.png'.format(image_signature)))
	else :
		audio_profile.plot(colormap=plt.cm.gist_rainbow)
		lgd = plt.legend(loc='center left', bbox_to_anchor=(1, 0.5))
		plt.xticks(list(audio_profile.index))
		plt.ylabel("% Importance")
		plt.xlabel("Model Iteration")
		plt.title("Audio Feature % Importance")
		plt.savefig('static/audio_profile_{}.png'.format(image_signature), bbox_extra_artists=(lgd,), bbox_inches='tight')
		#plt.savefit(url_for('static', filename='audio_profile_{}.png'.format(image_signature)),bbox_extra_artists=(lgd,), bbox_inches='tight')