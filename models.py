from run import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = "user"
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    pwd = db.Column(db.String(300), nullable=False, unique=True)

    def __repr__(self):
        return '<User %r>' % self.username
    
class Videos(db.Model):
    __tablename__ = "videos"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    ownership = db.Column(db.String(80), nullable=False)
    genre = db.Column(db.String(80), nullable=False)
    release_year = db.Column(db.Integer, nullable=False)
    bio = db.Column(db.String(1000), nullable=True)
    media_type = db.Column(db.String(80), nullable=False)

    def __repr__(self):
        return '<Videos %r>' % self.title