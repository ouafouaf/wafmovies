import os
from sqlalchemy import or_, not_, and_, func
from sqlalchemy.orm import aliased
from sqlalchemy.sql import text
from imdb import IMDb

from wafmovies import db 
from .models import Release, Show, People, Storage, Country, Aka, Genre
from .models import show_genre, show_country, show_cast, show_dir


#################################
## URL Filters and Orders  ##
#################################

def generate_query(kwargs):
    '''
    Build SQL query
    **kwargs come from url / request.args.copy()
    Return a tuple: 
        result (the query result)
        number (the .count() of the query)
    '''
    sqlquery = Show.query

    if 'search_title' in kwargs and kwargs['search_title'] is not None:
        sqlquery = sqlquery.filter(Show.title.like('%' + kwargs['search_title'] + '%'))
    if 'search_people' in kwargs and kwargs['search_people'] is not None:
        alias1 = aliased(People)
        alias2 = aliased(People)
        sqlquery = sqlquery.join(alias1, Show.cast).join(alias2, Show.directors).filter(or_(alias1.name.like('%' + kwargs['search_people'] + '%'), alias2.name.like('%' + kwargs['search_people'] + '%'))).distinct(Show.id)
    if 'people' in kwargs and kwargs['people'] is not None:
        sqlquery = sqlquery.filter(or_(Show.cast.any(People.id==kwargs['people']), Show.directors.any(People.id==kwargs['people'])))
    if 'country' in kwargs and kwargs['country'] is not None:
        sqlquery = sqlquery.filter(Show.countries.any(Country.id==kwargs['country']))
    if 'genre' in kwargs and kwargs['genre'] is not None:
        sqlquery = sqlquery.filter(Show.genres.any(Genre.id==kwargs['genre']))
    if 'storage' in kwargs and kwargs['storage'] is not None:
        # sqlquery = sqlquery.filter(Show.releases.any(Release.storage_id==kwargs['storage']))  # very slow query
        sqlquery = db.session.query(Show).join(Release).join(Storage).filter(Storage.id==kwargs['storage'])
    
    # Docu toggle
    if 'docu' in kwargs and kwargs['docu']=='off':
        sqlquery = sqlquery.filter(~Show.genres.any(Genre.id==23))  # hardcoded genre ID
    if 'docu' in kwargs and kwargs['docu']=='on':
        sqlquery = sqlquery

    if not 'order' in kwargs or kwargs['order'] is None:
        if 'people' in kwargs and kwargs['people'] is not None:
            # default sorting by year_desc for people page
            sqlquery = sqlquery.order_by(Show.year.desc())
        else:
            # otherwise id desc as default:
            sqlquery = sqlquery.order_by(Show.title.asc())

    # Statistics filters
    if 'filter' in kwargs and kwargs['filter'] is not None:
        if kwargs['filter'] == "user_viewed":
            sqlquery = sqlquery.filter(Show.user_viewed==True)
        if kwargs['filter'] == "user_not_viewed":
            sqlquery = sqlquery.filter(Show.user_viewed.isnot(True))
        if kwargs['filter'] == "user_rated":
            sqlquery = sqlquery.filter(Show.user_rating!=None)

        if kwargs['filter'] == "shows_not_validated":
            sqlquery = sqlquery.filter(Show.validated==False)
        if kwargs['filter'] == "shows_no_imdb":
            sqlquery = sqlquery.filter(Show.no_imdb==True)
        if kwargs['filter'] == "shows_no_releases":
            sqlquery = sqlquery.filter(Show.releases==None)
        if kwargs['filter'] == "shows_dupe_releases":
            # sqlquery = sqlquery.join(Release).group_by(Show).having(func.count(Release.id) > 1)
            sqlquery = sqlquery.join(Release).filter(Release.delete.isnot(True)).group_by(Show).having(func.count(Release.id) > 1)
        if kwargs['filter'] == "shows_duplicate_imdb":
            sq = Show.query.with_entities(Show.imdb_id).group_by(Show.imdb_id).having(func.count(Show.imdb_id) > 1).subquery()
            sqlquery = sqlquery.filter(Show.imdb_id == sq.c.imdb_id).order_by(Show.imdb_id)
        if kwargs['filter'] == "releases_deleted":
            sqlquery = sqlquery.filter(Show.releases.any(Release.delete==True))
        
        # Special filters (for statistics page)
        if kwargs['filter'] == 'storage_all':
            sqlquery = Storage.query
        if kwargs['filter'] == 'releases_all':
            sqlquery = Release.query
        if kwargs['filter'] == 'shows_all':
            sqlquery = Show.query
        if kwargs['filter'] == 'people_all':
            sqlquery = People.query

        # Special filters (more statistics)
        if kwargs['filter'] == 'top_countries':
            sqlquery = db.session.query(Country, func.count(show_country.c.show_id).label('total')).join(show_country).group_by(Country).order_by(text('total DESC'))
        if kwargs['filter'] == 'top_genres':
            sqlquery = db.session.query(Genre, func.count(show_genre.c.show_id).label('total')).join(show_genre).group_by(Genre).order_by(text('total DESC'))
        if kwargs['filter'] == 'top_directors':
            sqlquery = db.session.query(People, func.count(show_dir.c.show_id).label('total')).join(show_dir).group_by(People).order_by(text('total DESC'))
        if kwargs['filter'] == 'top_actors':
            sqlquery = db.session.query(People, func.count(show_cast.c.show_id).label('total')).join(show_cast).group_by(People).order_by(text('total DESC'))
            
        # Codecs filter // not_x264
        if kwargs['filter'] == "not_x264":
            sqlquery = sqlquery.filter(not_(Show.releases.any(or_(Release.unique_id!=None, Release.delete==True))))

        # Resolution filter // HD, SD
        if kwargs['filter'] == "SD":
            sqlquery = sqlquery.filter(Show.releases.any(Release.is_sd))
        if kwargs['filter'] == "HD":
            sqlquery = sqlquery.filter(Show.releases.any(Release.is_hd))

        # Source filter // source_bluray, source_dvd, source_web, source_tv, no_source
        kw_bluray = ['bluray', 'blu-ray', 'bdrip']
        kw_dvd = ['dvd-rip', 'dvdrip']
        kw_web = ['web-rip', 'webrip', 'web-d', 'webdl']
        kw_tv = ['tvrip', 'hdtv']
        kw_all = kw_bluray+kw_dvd+kw_tv+kw_web

        if kwargs['filter'] == "source_bluray":
            sqlquery = sqlquery.filter(Show.releases.any(or_(*[Release.filename.contains(substring.lower()) for substring in kw_bluray])))
            # sqlquery = sqlquery.filter(Show.releases.any(Release.source_auto == 'BluRay'))   >> Hybrid property doesn't work
        if kwargs['filter'] == "source_dvd":
            sqlquery = sqlquery.filter(Show.releases.any(or_(*[Release.filename.contains(substring.lower()) for substring in kw_dvd])))
        if kwargs['filter'] == "source_web":
            sqlquery = sqlquery.filter(Show.releases.any(or_(*[Release.filename.contains(substring.lower()) for substring in kw_web])))
        if kwargs['filter'] == "source_tv":
            sqlquery = sqlquery.filter(Show.releases.any(or_(*[Release.filename.contains(substring.lower()) for substring in kw_tv])))
        if kwargs['filter'] == "no_source":
            sqlquery = sqlquery.filter(~Show.releases.any(or_(*[Release.filename.contains(substring.lower()) for substring in kw_all])))
        
  
    # Ordering 
    if 'order' in kwargs and kwargs['order'] is not None:
        if kwargs['order'] == "year_asc":
            sqlquery = sqlquery.order_by(Show.year.asc())
        if kwargs['order'] == "year_desc":
            sqlquery = sqlquery.order_by(Show.year.desc())
        if kwargs['order'] == "title_asc":
            sqlquery = sqlquery.order_by(Show.title.asc())
        if kwargs['order'] == "title_desc":
            sqlquery = sqlquery.order_by(Show.title.desc())
        if kwargs['order'] == "id_asc":
            sqlquery = sqlquery.order_by(Show.id.asc())
        if kwargs['order'] == "id_desc":
            sqlquery = sqlquery.order_by(Show.id.desc())
        if kwargs['order'] == "user_rating_asc":
            sqlquery = sqlquery.filter(Show.user_viewed==True).order_by(Show.user_rating.asc())
        if kwargs['order'] == "user_rating_desc":
            sqlquery = sqlquery.filter(Show.user_viewed==True).order_by(Show.user_rating.desc())
        if kwargs['order'] == "imdb_rating_asc":
            sqlquery = sqlquery.order_by(Show.imdb_rating.asc())
        if kwargs['order'] == "imdb_rating_desc":
            sqlquery = sqlquery.order_by(Show.imdb_rating.desc())

    return sqlquery




##############################
## IMDbPy Add or Fetch   ##
##############################

def add_or_fetch_people(imdbpy_person):
    '''
    checks if imdb person already in database
    creates new People item or fetches existing
    returns People object
    '''
    p_name = imdbpy_person['name']
    p_imdb_id = imdbpy_person.getID()
    result = People.query.filter_by(imdb_id=p_imdb_id).first()
    if result == None:
        new_person = People(name=p_name, imdb_id=p_imdb_id)
        db.session.add(new_person)
        db.session.commit()
        return new_person
    else:
        return result

def add_or_fetch_country(imdbpy_country):
    '''
    checks if imdb country already in database
    creates new Country item or fetches existing
    returns Country object
    '''
    result = Country.query.filter(Country.name==str(imdbpy_country)).first()
    if result == None:
        new_country = Country(name=imdbpy_country)
        db.session.add(new_country)
        db.session.commit()
        return new_country
    else:
        return result

def add_or_fetch_genre(imdbpy_genre):
    '''
    checks if imdb genre already in database
    creates new Genre item or fetches existing
    returns Genre object
    '''
    result = Genre.query.filter(Genre.name==str(imdbpy_genre)).first()
    if result == None:
        new_genre = Genre(name=imdbpy_genre)
        db.session.add(new_genre)
        db.session.commit()
        return new_genre
    else:
        return result


##############################
## IMDbPy Helper Functions  ##
##############################

def update_show_from_imdb(show_object, imdbpy_object):
    '''
    updates Show (and children) from imdb
    arg1: Show object
    arg2: imdbpy movie object
    '''
    if not show_object.validated:
        # If IMDb Validated, do not update important data.
        # It allows to manually edit shows, as update won't reset all the data.
        # TODO: Add manual edition

        show_object.title = imdbpy_object.get('title')
        show_object.imdb_id = imdbpy_object.getID()

    show_object.year = imdbpy_object.get('year')
    show_object.imdb_rating = imdbpy_object.get('rating')

    if imdbpy_object.get('plot outline'):
        show_object.plot_outline = imdbpy_object.get('plot outline')

    if imdbpy_object.get('cast'):
        # Get casting
        # TODO: Deal with custom user data?
        show_object.cast.clear()
        for a in imdbpy_object.get('cast'):
            person = add_or_fetch_people(a)
            if person not in show_object.cast:
                show_object.cast.append(person)

    if imdbpy_object.get('directors'):
        # Get directors
        # TODO: Deal with custom user data?
        show_object.directors.clear()
        for d in imdbpy_object.get('directors'):
            person = add_or_fetch_people(d)
            if person not in show_object.directors:
                show_object.directors.append(person)

    if imdbpy_object.get('countries'):
        # Get countries
        show_object.countries.clear()
        for c in imdbpy_object.get('countries'):
            country = add_or_fetch_country(c)
            if country not in show_object.countries:
                show_object.countries.append(country)

    if imdbpy_object.get('genres'):
        # Get genres
        show_object.genres.clear()
        for g in imdbpy_object.get('genres'):
            genre = add_or_fetch_genre(g)
            if genre not in show_object.genres:
                show_object.genres.append(genre)

    if imdbpy_object.get('cover url'):
        # Poster data
        # TODO: Add custom cover
        # TODO: Add multiple posters
        show_object.imdb_poster_uri = url_clean(imdbpy_object.get('cover url'))

    # Get AKAS
    # Issue: Require extra imdbpy request, takes more time
    # TODO: Improve / Make optional
    ia = IMDb()
    ia.update(imdbpy_object, ['release dates'])
    if imdbpy_object.get('raw akas'):
        # show_object.akas.clear()
        for aka in imdbpy_object.get('raw akas'):
            if isinstance(aka, dict) and 'countries' in aka:

                # Quick fix to add French original title on French films
                if not show_object.validated and imdbpy_object.get('countries')[0] == 'France' and '(original title)' in aka['countries']:
                    show_object.title = aka['title']  

                # Add imdb title as aka title
                if not Aka.query.filter_by(show_id=show_object.id, title=imdbpy_object.get('title'), lang='IMDb title').first():
                    alt = Aka()
                    alt.title = imdbpy_object.get('title')
                    alt.lang = 'IMDb title'
                    alt.show_id = show_object.id
                    db.session.add(alt)
                
                # Get original title
                if '(original title)' in aka['countries']:
                    show_object.original_title = aka['title']

                ## Fetch accepted akas types:
                match_akas = ['France', 'USA', 'China']
                if any(element in aka['countries'] for element in match_akas):
                    if not Aka.query.filter_by(show_id=show_object.id, title=aka['title'], lang=aka['countries']).first():
                        alt = Aka()
                        alt.title = aka['title']
                        alt.lang = aka['countries']
                        alt.show_id = show_object.id
                        db.session.add(alt)
    
    db.session.commit()



def imdbpy_search_results_to_dict(search_results):
    '''
    return readable list of dictionaries from imdb search results
    '''
    results = []
    for e in search_results:
        result = {}
        result['title'] = e.get('title')
        result['year'] = e.get('year')
        result['imdb_id'] = e.getID()
        result['imdb_link'] = 'https://www.imdb.com/title/tt' + e.getID()
        results.append(result)
    return results


#################################
## IMDb Poster URL Cleaner  ##
#################################

def url_clean(url):
    base, ext = os.path.splitext(url)
    i = url.count('@')
    s2 = url.split('@')[0]
    url = s2 + '@' * i + ext
    return url


##########################
## Mediainfos Helpers   ##
##########################

def mediainfo_max_depth(mediainfo_data):
    '''
    For batch adding from mediainfo json data.

    Calculates the correct path depth where movies are stored
    in order to avoid adding extra content in subfolders
    returns max_depth variable

    E://FILMS/Titanic (1997)/Titanic.mkv         # Will be accepted
    E://FILMS/Titanic (1997)/Extras/Extra01.mkv  # Will be ignored
    '''
    max_depth = None
    extensions = ['.mkv', '.avi', '.mp4']

    for e in mediainfo_data:
        if "VideoCount" in e["media"]["track"][0]:
            for i, j in enumerate(e["media"]["@ref"].split('\\')):
                if any(extension in j for extension in extensions):
                    if max_depth is None or max_depth > i + 1:
                        max_depth = i + 1
    return max_depth



def mediainfo_cleaner(mediainfo_data, max_depth):
    '''
    For batch adding from mediainfo json data.

    Returns readable custom data from raw mediainfo data
    uses max_depth to filter out subfolder contents
    TODO: integrate external subtitles
    '''
    data = []
    for e in mediainfo_data:
        if "VideoCount" not in e["media"]["track"][0]:  
            # Include only video files
            continue
        if len(e["media"]["@ref"].split('\\')) > max_depth:   
            # Not include subfolders (bonus...)
            continue
        data.append(e)
    return data


def mediainfo_cleaner(mediainfo_data, max_depth):
    '''
    For batch adding from mediainfo json data.

    Returns readable custom data from raw mediainfo data
    uses max_depth to filter out subfolder contents
    TODO: integrate external subtitles
    '''
    data = []
    for e in mediainfo_data:
        if "VideoCount" not in e["media"]["track"][0]:  
            # Include only video files
            continue
        if len(e["media"]["@ref"].split('\\')) > max_depth:   
            # Not include subfolders (bonus...)
            continue
        data.append(e)
    return data


def mediainfo_compare_to_storage(mediainfo_clean_data, storage_id):
    '''
    For soft-deleting Release that are not anymore on a storage unit.
    '''
    # Get Unique IDs and file_size from mediainfo in an array
    list_unique_ids = [e["media"]['track'][0].get('UniqueID') for e in mediainfo_clean_data]
    list_sizes_and_duration = [(e["media"]['track'][0]['FileSize'], e["media"]['track'][0]['Duration']) for e in mediainfo_clean_data]

    # Loop through database release for same storage
    storage = Storage.query.filter_by(id=storage_id).first()
    for r in storage.releases: 
        if r.delete == True:
            continue
        elif (r.unique_id) in list_unique_ids:
            continue 
        elif (r.size, r.duration) in list_sizes_and_duration:
            continue 
        else:
            r.delete = True 
            print(f"      --- {r.filename} not found in json. soft-delete.")
            db.session.commit()
        
