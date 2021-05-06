from flask_login import UserMixin 
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func
from sqlalchemy.ext.hybrid import hybrid_property

from wafmovies import db, login_manager 

########################
## User model ##########
########################

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password_hash = db.Column(db.String(128))

    def __repr__(self):
        return f'<User {self.username}>'

    @property
    def password(self):
        # Prevent password from being accessed 
        raise AttributeError('Password is not a readable attribute')

    @password.setter
    def password(self, password):
        # Set password to hashed password
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        # Check if password matches hashed password
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader 
def load_user(user_id):
    # Flask-Login user loader
    return User.query.get(user_id)


##########################
## Association tables ####
##########################

# Actors in shows
show_cast = db.Table('show_cast',
    db.Column('people_id', db.Integer, db.ForeignKey('people.id'), primary_key=True),
    db.Column('show_id', db.Integer, db.ForeignKey('show.id'), primary_key=True))

# Directors in shows
show_dir = db.Table('show_dir',
    db.Column('people_id', db.Integer, db.ForeignKey('people.id'), primary_key=True),
    db.Column('show_id', db.Integer, db.ForeignKey('show.id'), primary_key=True))

# Countries in shows
show_country = db.Table('show_country',
    db.Column('country_id', db.Integer, db.ForeignKey('country.id'), primary_key=True),
    db.Column('show_id', db.Integer, db.ForeignKey('show.id'), primary_key=True))
    
# Genres in shows
show_genre = db.Table('show_genre',
    db.Column('genre_id', db.Integer, db.ForeignKey('genre.id'), primary_key=True),
    db.Column('show_id', db.Integer, db.ForeignKey('show.id'), primary_key=True))


##########################
## Show table ############
##########################

class Show(db.Model):
    __tablename__ = 'show'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String)               
    original_title = db.Column(db.String)   
    year = db.Column(db.Integer)
    plot_outline = db.Column(db.String)

    akas = db.relationship("Aka", backref="show")

    imdb_id = db.Column(db.Integer)
    imdb_rating = db.Column(db.Float)
    imdb_poster_uri = db.Column(db.String)
    custom_poster_uri = db.Column(db.String)

    validated = db.Column(db.Boolean, default=False)   # user can validate imdb_id
    no_imdb = db.Column(db.Boolean, default=False)     # user can flag show without imdb page

    user_rating = db.Column(db.Float)
    user_viewed = db.Column(db.Boolean, default=False)
    user_view_date = db.Column(db.DateTime)

    cast = db.relationship("People", secondary=show_cast, backref="acted_in")
    directors = db.relationship("People", secondary=show_dir, backref="directed_in")

    countries = db.relationship("Country", secondary=show_country, backref="shows")
    genres = db.relationship("Genre", secondary=show_genre, backref="shows")

    releases = db.relationship("Release", backref="show")
    
    def as_dict(self):
	    return {'name': self.title}
    


##########################
## People table ##########
##########################

class People(db.Model):
    __tablename__ = 'people'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

    imdb_id = db.Column(db.Integer)
    
    def as_dict(self):
	    return {'name': self.name}


##########################
## Release table #########
##########################

class Release(db.Model):
    __tablename__ = 'release'

    id = db.Column(db.Integer, primary_key=True)
    show_id = db.Column(db.Integer, db.ForeignKey('show.id'))

    filename = db.Column(db.String)     # from mediainfos
    dirname = db.Column(db.String)      # from mediainfos
    
    size = db.Column(db.Float)          # from mediainfos
    duration = db.Column(db.Float)      # from mediainfos
    bitrate = db.Column(db.Float)       # from mediainfos
    width = db.Column(db.Float)         # from mediainfos
    height = db.Column(db.Float)        # from mediainfos
    unique_id = db.Column(db.String)    # from mediainfos (unique identifier, only for mkv)

    storage_id = db.Column(db.Integer, db.ForeignKey('storage.id'))
    storage = db.relationship("Storage", backref="releases")

    source = db.Column(db.String)   # BluRay, DVD, Web, TV
    delete = db.Column(db.Boolean)

    @hybrid_property
    def is_hd(self):
        return self.width > 1024

    @hybrid_property
    def is_sd(self):
        return self.width <= 1024

    @hybrid_property
    def source_auto(self):
        '''
        Guess source from filename attribute
        (Doesn't work with filter queries / see services.generate_query())
        '''
        kw_bluray = ['bluray', 'blu-ray', 'bdrip']
        kw_dvd = ['dvd-rip', 'dvdrip']
        kw_web = ['web-rip', 'webrip', 'web-d', 'webdl']
        kw_tv = ['tvrip', 'hdtv']
        if any([e in self.filename.lower() for e in kw_bluray]):
            return 'BluRay'
        elif any([e in self.filename.lower() for e in kw_dvd]):
            return 'DVD'
        elif any([e in self.filename.lower() for e in kw_web]):
            return 'Web'
        elif any([e in self.filename.lower() for e in kw_tv]):
            return 'TV'
        else:
            return None


######################################
## Children tables           #########
######################################

class Storage(db.Model):
    '''
    Parent: Release
    Release.storage
    '''
    __tablename__ = 'storage'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)


class Country(db.Model):
    '''
    Parent: Show
    Show.countries
    '''
    __tablename__ = 'country'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)	
    
    def as_dict(self):
	    return {'name': self.name}

class Genre(db.Model):
    '''
    Parent: Show
    Show.genres
    '''
    __tablename__ = 'genre'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    
    def as_dict(self):
	    return {'name': self.name}


class Aka(db.Model):
    '''
    Parent: Show
    Show.akas
    '''
    __tablename__ = 'akas'
    id = db.Column(db.Integer, primary_key=True)
    show_id = db.Column(db.Integer, db.ForeignKey('show.id'))
    title = db.Column(db.String)
    lang = db.Column(db.String)  # Original / USA / France / China ...
