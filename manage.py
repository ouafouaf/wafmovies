import sys
from imdb import IMDb 

from wafmovies import db, create_app 
from wafmovies.models import User, Show, People, Genre, Release
from wafmovies.services import update_show_from_imdb

app = create_app()
app.app_context().push()

def manager(): 

    # --create_user <name> <pw>    // To create a new user
    if len(sys.argv) >> 1 and sys.argv[1] == '--create_user' and len(sys.argv) == 4:
        if db.session.query(User).filter_by(username=sys.argv[2]).first() is None:
            new_user = User(username=sys.argv[2], password=sys.argv[3])
            db.session.add(new_user)
            db.session.commit()
            print(f'New user created: {sys.argv[2]} /  {sys.argv[3]}')
        else:
            print(f'Username {sys.argv[2]} already used... Please try another username')

    # --delete_user <name>    // To delete a user from database
    elif len(sys.argv) >> 1 and sys.argv[1] == '--delete_user' and len(sys.argv) == 3:
        result = db.session.query(User).filter_by(username=sys.argv[2]).first
        if result is not None:
            db.session.delete(result)
            db.session.commit()

    # --users      // To view existing users
    elif len(sys.argv) >> 1 and sys.argv[1] == '--users' and len(sys.argv) == 2:
        users = User.query.all()
        for u in users:
            print(f'{u.id}: {u.username}')

    # --create_db   // To create new database
    elif len(sys.argv) >> 1 and sys.argv[1] == '--create_db' and len(sys.argv) == 2:
        db.create_all()

    # --delete_db   // To delete database
    elif len(sys.argv) >> 1 and sys.argv[1] == '--delete_db' and len(sys.argv) == 2:
        db.drop_all()

    # --shows    // To show all shows
    elif len(sys.argv) >> 1 and sys.argv[1] == '--shows':
        result = db.session.query(Show).all()
        for s in result:
            print(f'{s.id}: {s.title} ({s.year})')


    # --update_all   // To update imdb data from imdb_id for validated shows.
    elif len(sys.argv) >> 1 and sys.argv[1] == '--update_all':
        ia = IMDb()
        all = db.session.query(Show).filter(Show.validated==True).filter(Show.plot_outline==None).all()
        #  .filter(~Show.countries.any()).all()
        for e in all: 
            try:
                result = ia.get_movie(e.imdb_id)
            except:
                print(f'## Failed: {e.title}')
                continue
            
            update_show_from_imdb(e, result)
            print(f"Updated #{e.id}: [{str(e.imdb_id).zfill(7)}] {e.title}")

    # --update_test   // Updater test
    elif len(sys.argv) >> 1 and sys.argv[1] == '--update_test':
        ia = IMDb()
        movie = db.session.query(Show).filter(Show.id==920).first()
        try:
            result = ia.get_movie(movie.imdb_id)
        except:
            print(f'## Failed: {movie.title}')

        update_show_from_imdb(movie, result)
        print(f"Updated: [{str(movie.imdb_id).zfill(7)}] {movie.title}")

    # --fetch_all   // To update imdb data from imdb_id or from first search result if no imdb_id found.
    #               // WARNING: Temporary function!! Dangerous if some show are not on imdb
    elif len(sys.argv) >> 1 and sys.argv[1] == '--fetch_all':
        ia = IMDb()
        # all = db.session.query(Show).all()
        all = db.session.query(Show).filter(Show.releases.any(Release.storage_id==4)).all()
        for e in all: 
            if e.imdb_id is None:
                try:
                    search = ia.search_movie(f"{e.title} ({e.year})")[0]
                    result = ia.get_movie(search.getID())
                except:
                    print(f'## Failed: {e.title}')
                    continue
            
            else:
                continue

            update_show_from_imdb(e, result)
            print(f"Updated: [{result.getID()}] {result.get('title')}")


    # HELP MENU
    else:
        print('--------------------------')
        print('[ WAFMOVIES MANAGER TOOL ]')
        print('--------------------------')
        print('  python manager.py --create_user <username> <password>       >>> Create a new administrator account.')
        print('  python manager.py --delete_user <username>                  >>> Delete a user')
        print('  python manager.py --users                                   >>> Show existing users.')

        print('  python manager.py --create_db                               >>> Create new empty database')
        print('  python manager.py --delete_db                               >>> Delete all database content. (WARNING!!)')

        print('  python manager.py --shows                                   >>> Show all shows')

        # print('  python manager.py --generate                                >>> Generate mock data in database.')
        # print('  python manager.py --import <filename.json> <disk number>    >>> Manually import mediainfo json from local directory')

        print('  python manager.py --update_all                              >>> Update from imdb (only validated shows)')
        print('  python manager.py --fetch_all                               >>> Update from imdb (using imdb_id or first search result)')

        print('')


if __name__ == '__main__':
    manager()