from flask import render_template, redirect, url_for, jsonify, request, current_app
from werkzeug.urls import url_encode
from flask_wtf import FlaskForm
from wtforms import StringField
from sqlalchemy import or_

from . import home 
from wafmovies.models import Show, People, Country, Genre
from .. import services


class SearchForm(FlaskForm):
    title_input = StringField(label="")
    people_input = StringField(label="")
    genre_input = StringField(label="")
    country_input = StringField(label="")


#####################
## Main Page
#####################

@home.route('/', methods=['GET', 'POST'])
def homepage():
    # Search Forms
    search_form = SearchForm()

    # Receive search forms
    if search_form.validate_on_submit():

        if search_form.title_input.data != '':
            return redirect(url_for('home.homepage', search_title=search_form.title_input.data))
        elif search_form.people_input.data != '':
            return redirect(url_for('home.homepage', search_people=search_form.people_input.data))
        elif search_form.genre_input.data != '':
            genre_result = Genre.query.filter(Genre.name.like('%' + search_form.genre_input.data + '%')).first()
            if genre_result is not None:
                return redirect(url_for('home.homepage', genre=genre_result.id))
            else:
                return redirect(url_for('home.homepage'))
        elif search_form.country_input.data != '':
            country_result = Country.query.filter(Country.name.like('%' + search_form.country_input.data + '%')).first()
            if country_result is not None:
                return redirect(url_for('home.homepage', country=country_result.id))
            else:
                return redirect(url_for('home.homepage'))

    # Build sql query:
    qry = services.generate_query(request.args.copy())
    page = request.args.get('page', 1, type=int)
    paginate_query = qry.paginate(page,current_app.config['ITEM_PER_PAGE'],False)
    

    return render_template('show_list.html', 
                            title='Home', 
                            result=paginate_query, 
                            search_form=search_form)




#####################
## Show Page
#####################

@home.route('/shows/<id>')
def show_page(id):
    result = Show.query.filter_by(id=id).first()
    return render_template('show_page.html', result=result)



#####################
## Statistics Page
#####################


@home.route('/statistics')
def statistics():
    # statistics = services.get_statistics()
    return render_template('statistics.html', title='Statistics')


#####################
## API (for search)
#####################

@home.route('/api/countries')
def api_countries():
	res = Country.query.all()
	list_countries = [r.as_dict() for r in res]
	return jsonify(list_countries)

@home.route('/api/genres')
def api_genres():
	res = Genre.query.all()
	list_genres = [r.as_dict() for r in res]
	return jsonify(list_genres)

@home.route('/api/people')
def api_people():
	res = People.query.all()
	list_people = [r.as_dict() for r in res]
	return jsonify(list_people)

@home.route('/api/shows')
def api_shows():
	res = Show.query.all()
	list_shows = [r.as_dict() for r in res]
	return jsonify(list_shows)


    

#####################
## CONTEXT PROCESSOR 
#####################

@home.context_processor
def utility_processor():

    def modify_query(**new_values):
        args = request.args.copy()
        for key, value in new_values.items():
            args[key] = value
        return '{}?{}'.format(request.url_root, url_encode(args))

    def current_query_count():
        return services.generate_query(request.args.copy()).count()

    def get_query_object(qry):
        ''' 
        input = {'key':'value'}
        output = sqlalchemy object
        '''
        (k, v), = qry.items()
        result = services.generate_query({k:v})
        return result.all()

    def get_query_count(qry):
        ''' 
        input = {'key':'value'}
        output = count rows of query
        '''
        (k, v), = qry.items()
        result = services.generate_query({k:v})
        return result.count()

    def get_data(id):
        if request.args.get('people'):
            res = People.query.filter_by(id=id).first()
            url = f"https://www.imdb.com/title/tt{str(res.imdb_id).zfill(7)}"
            return f"{res.name} / <a href='{url}'>IMDB</a>"
        if request.args.get('country'):
            res = Country.query.filter_by(id=id).first()
            return f"{res.name}"
        if request.args.get('genre'):
            res = Genre.query.filter_by(id=id).first()
            return f"{res.name}"

    def humanbytes(B):
        'Return the given bytes as a human friendly KB, MB, GB, or TB string'
        B = float(B)
        KB = float(1024)
        MB = float(KB ** 2) # 1,048,576
        GB = float(KB ** 3) # 1,073,741,824
        TB = float(KB ** 4) # 1,099,511,627,776

        if B < KB:
            return '{0} {1}'.format(B,'Bytes' if 0 == B > 1 else 'Byte')
        elif KB <= B < MB:
            return '{0:.2f} KB'.format(B/KB)
        elif MB <= B < GB:
            return '{0:.2f} MB'.format(B/MB)
        elif GB <= B < TB:
            return '{0:.2f} GB'.format(B/GB)
        elif TB <= B:
            return '{0:.2f} TB'.format(B/TB)

    def duration(time):
        seconds = int(time) 
        minute, sec = divmod(seconds, 60) 
        hour, minute = divmod(minute, 60) 
        return f"{hour}h{minute}m{sec}s"

    return dict(modify_query=modify_query, 
                get_data=get_data, 
                humanbytes=humanbytes, 
                duration=duration,
                get_query_count=get_query_count,
                get_query_object=get_query_object,
                current_query_count=current_query_count)




