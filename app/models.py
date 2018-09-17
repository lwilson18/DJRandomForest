from app import db

# Create a data model for the database to be setup for the app
class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer(), unique=False, nullable=False)
    song_id = db.Column(db.String(100), unique=False, nullable=False)
    rating = db.Column(db.Integer(), unique=False, nullable=False)
    iteration = db.Column(db.Integer(), unique=False, nullable=False)
    confidence = db.Column(db.Integer(), unique=False, nullable=True)

    def __repr__(self):
        return "<User: {}, Song: {}, Rating: {}>".format(self.user_id,self.song_id,self.rating)