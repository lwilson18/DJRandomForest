from app import db
from app.models import *
import pandas as pd

def create_db() :
	db.create_all()
	song_df = pd.read_csv("data/Spotify_Songs.csv")
	song_df.to_sql("songs",db.engine,if_exists='replace',index=False)


if __name__ == "__main__":
	create_db()
	print(db.engine.table_names())

