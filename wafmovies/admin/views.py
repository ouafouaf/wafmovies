import os, re
from flask import render_template, request, json, redirect, url_for, flash
from flask_login import login_required
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import SubmitField, StringField
from werkzeug.utils import secure_filename
from urllib import parse
from imdb import IMDb

from wafmovies import db
from . import admin 
from ..models import Release, Show, People, Storage, Country, Genre, Aka
from .. import services    # Helper functions



#####################
## Show: Edit      ##
#####################

# Edit Show / receive edition forms
# TODO: More options
@admin.route('/shows/<id>/edit', methods=['POST'])
@login_required
def show_edit(id):
    result = Show.query.filter_by(id=id).first()
    
    if 'user_rating' in request.form and request.form.get('user_rating') != '':
        result.user_rating = float(request.form.get('user_rating'))
        db.session.commit()

    if 'merge_to_show' in request.form and request.form.get('merge_to_show') != '' and request.form.get('hidden_release_id') != '':
        try:
            this_rls = Release.query.filter_by(id=int(request.form.get('hidden_release_id'))).first()
            new_show = Show.query.filter_by(id=int(request.form.get('merge_to_show'))).first()
            this_rls.show = new_show
            db.session.commit()
        except:
            print('Problem')

    if 'imdb_id' in request.form and request.form.get('imdb_id') != '':
        # if user sent an imdb id
        if request.form.get('imdb_id').isdigit():
            imdb_id = int(request.form.get('imdb_id'))
        # if user sent an imdb url
        elif "www.imdb.com/title/" in request.form.get('imdb_id'):
            try:
                imdb_id = re.search('tt(\d+)', request.form.get('imdb_id')).group(1)
            except:
                print('Invalid url.')
        # if user sent invalid data, flash error
        else:
            print('Invalid data')     
        # Try to fetch imdb with imdbpy
        try:
            ia = IMDb()
            imdb_object = ia.get_movie(imdb_id)
            result.imdb_id = imdb_id 
            db.session.commit()
            services.update_show_from_imdb(result, imdb_object)
            result.validated = True 
            db.session.commit()
        except:
            print('Invalid show ID')
            
    if 'title_edit' in request.form and request.form.get('title_edit') != '':
        result.title = request.form.get('title_edit')
        db.session.commit()
            
    if 'year_edit' in request.form and request.form.get('year_edit') != '':
        result.year = request.form.get('year_edit')
        db.session.commit()
            
    if 'add_aka_title' in request.form and request.form.get('add_aka_title') != '':
        new_aka = Aka(title=request.form.get('add_aka_title'))
        if 'add_aka_lang' in request.form and request.form.get('add_aka_lang') != '':
            new_aka.lang = request.form.get('add_aka_lang')
        db.session.add(new_aka)
        result.akas.append(new_aka)
        db.session.commit()
            
    if 'country_add_id' in request.form and request.form.get('country_add_id') != '':
        country = Country.query.filter(Country.id==int(request.form.get('country_add_id'))).first()
        if country and country not in result.countries:
            result.countries.append(country)
            db.session.commit()

    if 'country_add_name' in request.form and request.form.get('country_add_name') != '':
        country = Country.query.filter(Country.name.like(request.form.get('country_add_name'))).first()
        if country and country not in result.countries:
            result.countries.append(country)
            db.session.commit()

    if 'genre_add_id' in request.form and request.form.get('genre_add_id') != '':
        genre = Genre.query.filter(Genre.id==int(request.form.get('genre_add_id'))).first()
        if genre and genre not in result.genres:
            result.genres.append(genre)
            db.session.commit()

    if 'genre_add_name' in request.form and request.form.get('genre_add_name') != '':
        genre = Genre.query.filter(Genre.name.like(request.form.get('genre_add_name'))).first()
        if genre and genre not in result.genres:
            result.genres.append(genre)
            db.session.commit()
            
    if 'director_add_id' in request.form and request.form.get('director_add_id') != '':
        person = People.query.filter(People.id==int(request.form.get('director_add_id'))).first()
        if person and person not in result.directors:
            result.directors.append(person)
            db.session.commit()
            
    if 'director_add_imdbid' in request.form and request.form.get('director_add_imdbid') != '':
        if "www.imdb.com/name/" in request.form.get('director_add_imdbid'):
            try:
                imdb_id = re.search('nm(\d+)', request.form.get('director_add_imdbid')).group(1)
                print(imdb_id)
                person = People.query.filter(People.imdb_id==int(imdb_id)).first()
                print(type(person))
                if person and person not in result.cast:
                    result.directors.append(person)
                    db.session.commit()
                elif person is None:
                    ia = IMDb()
                    imdb_object = ia.get_person(imdb_id)        
                    new_person = People(name=imdb_object.get('name'), imdb_id=imdb_object.getID())
                    db.session.add(new_person)
                    result.directors.append(new_person)
                    db.session.commit()
            except:
                print('Error.')
            
    if 'actor_add_id' in request.form and request.form.get('actor_add_id') != '':
        person = People.query.filter(People.id==int(request.form.get('actor_add_id'))).first()
        if person and person not in result.cast:
            result.cast.append(person)
            db.session.commit()


    # End of edition, return Show page
    return redirect(url_for('home.show_page', id=id))


# Update data from IMDb
@admin.route('/shows/<id>/update_data', methods=['GET', 'POST'])
def show_update_data(id):
    result = Show.query.filter_by(id=id).first()
    ia = IMDb()
    try:
        imdb_object = ia.get_movie(result.imdb_id)
        services.update_show_from_imdb(result, imdb_object)
    except:
        print('Invalid show id or imdb_id')
        return redirect(url_for('home.show_page', id=id))
    return redirect(url_for('home.show_page', id=id))
    

# Delete Show
# TODO: Make soft delete?
@admin.route('/shows/<id>/delete', methods=['GET'])
@login_required
def show_delete(id):
    this_show = Show.query.filter_by(id=id).first()
    this_show_id = this_show.id
    db.session.delete(this_show)
    db.session.commit()
    return redirect(url_for('home.homepage'))

##########################
## Show: quick actions  ##
##########################

# Check/uncheck Show as viewed
@admin.route('/shows/<id>/quick_flag_viewed', methods=['GET', 'POST'])
@admin.route('/shows/<id>/quick_flag_viewed/<prev_url>', methods=['GET'])
@login_required
def quick_flag_viewed(id, prev_url=None):
    result = Show.query.filter_by(id=id).first()
    if result.user_viewed == True:
        result.user_viewed = False
    else:
        result.user_viewed = True
    db.session.commit()
    if prev_url is not None:
        next = f'{request.url_root}{parse.unquote(prev_url)}'
        return redirect(next)
    return redirect(url_for('home.show_page', id=result.id))  

# Check/uncheck Show as validated
@admin.route('/shows/<id>/quick_flag_validated', methods=['GET'])
@admin.route('/shows/<id>/quick_flag_validated/<prev_url>', methods=['GET'])
@login_required
def quick_flag_validated(id, prev_url=None):
    result = Show.query.filter_by(id=id).first()
    if result.validated == True:
        result.validated = False
    else:
        result.validated = True
    db.session.commit()
    if prev_url is not None:
        next = f'{request.url_root}{parse.unquote(prev_url)}'
        return redirect(next)
    return redirect(url_for('home.show_page', id=result.id))  

# Check/uncheck Show as no_imdb
@admin.route('/shows/<id>/quick_flag_no_imdb', methods=['GET'])
@admin.route('/shows/<id>/quick_flag_no_imdb/<prev_url>', methods=['GET'])
@login_required
def quick_flag_no_imdb(id, prev_url=None):
    result = Show.query.filter_by(id=id).first()
    if result.no_imdb == True:
        result.no_imdb = False
    else:
        result.no_imdb = True
    db.session.commit()
    if prev_url is not None:
        next = f'{request.url_root}{parse.unquote(prev_url)}'
        return redirect(next)
    return redirect(url_for('home.show_page', id=result.id))  

# Remove Original Title
@admin.route('/shows/<id>/remove_original_title', methods=['GET'])
@login_required
def quick_remove_original_title(id):
    result = Show.query.filter_by(id=id).first()
    result.original_title = ''
    db.session.commit()
    return redirect(url_for('home.show_page', id=result.id))  

# Remove aka
@admin.route('/shows/<id>/remove_aka/<akaid>', methods=['GET'])
@login_required
def quick_remove_aka(id, akaid):
    result = Show.query.filter_by(id=id).first()
    aka = Aka.query.filter_by(id=akaid).first()
    if aka in result.akas:
        result.akas.remove(aka)
        db.session.commit()
    return redirect(url_for('home.show_page', id=result.id))  


# Remove country
@admin.route('/shows/<id>/remove_country/<cid>', methods=['GET'])
@login_required
def quick_remove_country(id, cid):
    result = Show.query.filter_by(id=id).first()
    country = Country.query.filter_by(id=cid).first()
    if country in result.countries:
        result.countries.remove(country)
        db.session.commit()
    return redirect(url_for('home.show_page', id=result.id))  

# Remove genre
@admin.route('/shows/<id>/remove_genre/<gid>', methods=['GET'])
@login_required
def quick_remove_genre(id, gid):
    result = Show.query.filter_by(id=id).first()
    genre = Genre.query.filter_by(id=gid).first()
    if genre in result.genres:
        result.genres.remove(genre)
        db.session.commit()
    return redirect(url_for('home.show_page', id=result.id))  

# Remove director
@admin.route('/shows/<id>/remove_director/<pid>', methods=['GET'])
@login_required
def quick_remove_director(id, pid):
    result = Show.query.filter_by(id=id).first()
    person = People.query.filter_by(id=pid).first()
    if person in result.directors:
        result.directors.remove(person)
        db.session.commit()
    return redirect(url_for('home.show_page', id=result.id))  

# Remove actor
@admin.route('/shows/<id>/remove_actor/<pid>', methods=['GET'])
@login_required
def quick_remove_actor(id, pid):
    result = Show.query.filter_by(id=id).first()
    person = People.query.filter_by(id=pid).first()
    if person in result.cast:
        result.cast.remove(person)
        db.session.commit()
    return redirect(url_for('home.show_page', id=result.id))  


###################
## RELEASES      ##
###################

# Delete (permanent)
@admin.route('/release/<id>/delete', methods=['GET'])
@login_required
def release_delete(id):
    this_rls = Release.query.filter_by(id=id).first()
    this_show_id = this_rls.show.id
    db.session.delete(this_rls)
    db.session.commit()
    return redirect(url_for('home.show_page', id=this_show_id))

# Check/uncheck Release as deleted
@admin.route('/release/<id>/quick_flag_delete', methods=['GET'])
@login_required
def release_soft_delete(id, prev_url=None):
    this_rls = Release.query.filter_by(id=id).first()
    this_show_id = this_rls.show.id
    if this_rls.delete == True:
        this_rls.delete = False
    else:
        this_rls.delete = True
    db.session.commit()
    return redirect(url_for('home.show_page', id=this_show_id))  




######################
## Batch Upload      #
######################

class UploadForm(FlaskForm):

    validators = [
        FileRequired(message='There was no file!'),
        FileAllowed(['json'], message='Must be a json file!')]

    input_file = FileField('', validators=validators)
    storage_number = StringField('Storage label (disk number)')
    submit = SubmitField(label="Upload")


@admin.route('/add', methods=['GET','POST'])
@login_required
def add():
    '''
    (PAGE) Send mediainfo JSON, add to database
    '''
    form = UploadForm()

    if request.method == 'POST' and form.validate_on_submit():

        d = form.input_file.data
        filename = secure_filename(d.filename)
        storage_number = form.storage_number.data

        # Save file
        d.save(filename)

        # Open file and process content
        with open(filename) as data_file:
            try:
                data = json.load(data_file) or None
                print(f"   [INFO] {len(data)} elements found.")
            except:
                return render_template('show_add_batch.html', form=form)

            # Calculate correct folder for movies
            max_depth = services.mediainfo_max_depth(data)

            # Clean data
            data = services.mediainfo_cleaner(data, max_depth)
            print(f"   [INFO] {len(data)} films found.")

            # Create log lists:
            releases_added = []
            releases_ignored = []

            # Add of fetch storage
            storage = Storage.query.filter_by(name=storage_number).first()
            if not(storage):
                storage = Storage(name=storage_number)
                db.session.add(storage)
                db.session.commit()
                print(f"test: storage added: id = {storage.id}, name = {storage.name}")

            # Check existing release in database for storage unit. Soft Delete if needed.
            services.mediainfo_compare_to_storage(data, storage.id)

            # Iterate list of shows
            for e in data:

                # Check for dupe files (using unique_id and storage)
                if e["media"]['track'][0].get('UniqueID'):
                    dupe_rls = db.session.query(Release).filter_by(unique_id=e["media"]['track'][0]['UniqueID'],size=e["media"]['track'][0]['FileSize'],duration=e["media"]['track'][0]['Duration'],storage_id=storage.id).first()
                    if dupe_rls is not None:
                        # Add to ignored
                        releases_ignored.append(['UID', e["media"]["@ref"].split('\\')[-1], dupe_rls.filename])
                        # Check if filename and dirname changed / update
                        dupe_rls.filename  = e["media"]["@ref"].split('\\')[-1]
                        dupe_rls.dirname   = e["media"]["@ref"].split('\\')[-2]
                        db.session.commit()
                        continue

                # Check for dupe avi files (using size/duration and storage)
                else: 
                    dupe_rls = db.session.query(Release).filter_by(size=e["media"]['track'][0]['FileSize'],duration=e["media"]['track'][0]['Duration'],storage_id=storage.id).first()
                    if dupe_rls is not None:
                        # Add to ignored
                        releases_ignored.append(['SIZE', e["media"]["@ref"].split('\\')[-1], dupe_rls.filename])
                        # Check if filename and dirname changed / update
                        dupe_rls.filename  = e["media"]["@ref"].split('\\')[-1]
                        dupe_rls.dirname   = e["media"]["@ref"].split('\\')[-2]
                        db.session.commit()
                        continue

                # Create Release object 
                r = Release()
                r.filename  = e["media"]["@ref"].split('\\')[-1]
                r.dirname   = e["media"]["@ref"].split('\\')[-2]
                r.size      = e["media"]['track'][0]['FileSize']
                r.duration  = e["media"]['track'][0]['Duration']
                r.bitrate   = e["media"]['track'][0]['OverallBitRate']
                r.width     = e["media"]['track'][1]['Width'] 
                r.height    = e["media"]['track'][1]['Height'] 
                if e["media"]['track'][0].get('UniqueID'):
                    r.unique_id = e["media"]['track'][0]['UniqueID']
                r.storage   = storage
            
                # Add release to database
                db.session.add(r)
                db.session.commit()

                # Create Show object
                s = Show()
                try:
                    s.title = re.sub('\(\d{4}\)$', '', r.dirname).strip()
                    s.year = re.findall('\((\d{4})\)', r.dirname)[0]
                except:
                    s.title = r.dirname
                s.releases.append(r)

                # Add show to database
                db.session.add(s)
                db.session.commit()

                releases_added.append(e["media"]["@ref"].split('\\')[-1])
            
        # Logs
        print(f"   [INFO] Import complete!")
        print(f"      --- {len(releases_added)} releases added.")
        print(f"      --- {len(releases_ignored)} releases ignored (dupes).")
        for r in releases_ignored:
            if r[1] != r[2]:
                print(f"          # {r[0]}: {r[1]} >> {r[2]}")

        # Delete temp json file
        os.remove(filename)

        return redirect(url_for('home.homepage'))

    return render_template('show_add_batch.html', form=form, title='Batch Add')
