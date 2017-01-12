__author__ = 'krishnateja'

import logging
from flaskext.mysql import MySQL
from flask import Flask
from flask_ask import Ask, statement, question, session
from pymongo import MongoClient

mysql = MySQL()

app = Flask(__name__)
app.config.from_object(__name__)
app.config['MYSQL_DATABASE_USER'] = ''
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = ''
app.config['MYSQL_DATABASE_HOST'] = ''
mysql.init_app(app)

ask = Ask(app, "/")

logging.getLogger("flask_ask").setLevel(logging.DEBUG)

list_of_words = ['a', 'the']
hellp_message = ''


def search_mongo(column):
    cursor_mongo = column.find({"id": int(session.attributes['moviedb'])})
    data_len = cursor_mongo.count()
    if data_len > 0:
        for document in cursor_mongo:
            return document
    else:
        return None


def search_movie(movie_name):
    print(movie_name)
    found = False
    if movie_name.split(' ', 1)[0] in list_of_words:
        movie_name = movie_name.split(' ', 1)[1]
    else:
        pass
    cursor = mysql.connect().cursor()
    query = "SELECT themoviedb,title FROM netflix_movies.movies WHERE title LIKE '%" + movie_name + "%';"
    cursor.execute(query)
    data = cursor.fetchone()
    if len(data) == 0:
        message = 'Nope, Have not found the movie' + movie_name + 'in netflix.'
    else:
        message = 'Yes, I found ' + movie_name
        session.attributes['moviedb'] = data[0]
        found = True

    return message, found


def search_show(show_name):
    found = False
    if show_name.split(' ', 1)[0] in list_of_words:
        show_name = show_name.split(' ', 1)[1]
    else:
        pass
    cursor = mysql.connect().cursor()
    query = "SELECT themoviedb, title FROM netflix_movies.shows WHERE title LIKE '%" + show_name + "%';"

    cursor.execute(query)
    data = cursor.fetchone()
    if len(data) == 0:
        message = 'Nope, Have not found the show' + show_name + 'in netflix.'
    else:
        message = 'Yes, I found ' + show_name
        found = True
        session.attributes['moviedb'] = data[0]
    return message, found


def search_show_updates():
    print('This API has to be completed.')


def search_movie_updates():
    print('This API has to be completed.')


@ask.launch
def new_search():
    welcome_msg = 'What do you want to search for in Netflix?... shows or movies?'
    return question(welcome_msg)


@ask.intent("WelcomeIntent")
def search_for(search_for):
    session.attributes['search_attr'] = str(search_for)
    message = 'Sure, I can help you with that...'
    if str(search_for) == 'show' or str(search_for) == 'movie':
        message = message + 'What is the ' + str(search_for) + ' you want to search for.'
        return question(message)
    elif str(search_for) == 'shows' or str(search_for) == 'movies':
        message = message + 'What are the ' + str(search_for) + ' you want to search for.'
        return question(message)
    else:
        message = 'Sorry. You can say something like search for shows or movies.'
        return question(message)


@ask.intent("SearchIntent")
def search(search_name):
    message = 'Sorry, I think I miss heard you there. You can say things like Does netflix Have Narcos.'
    found = False

    if search_name == "" or search_name is None:
        return question(message)
    else:
        session.attributes['search_term'] = str(search_name)
        message, found = search_show(search_name)
    if found:
        session.attributes['search_attr'] = 'show'
        return question(message + '...Do you want more info about the show?')
    else:
        message, found = search_movie(search_name)
        if found:
            session.attributes['search_attr'] = 'movie'
            return question(message + '...Do you want more info about the movie?')
        else:
            return statement(message)


@ask.intent("MoreInfoIntent")
def search(more_info_search, search_name):
    search_name = search_name
    message_ending = "   Do you want to know anything else?"
    mongo_db_uri = ""
    client = MongoClient(uri)
    if search_name is not None:
        session.attributes['search_term'] = str(search_name)
        message, found = search_show(search_name)
        if found:
            session.attributes['search_attr'] = 'show'
            shows_coll = client.netflix_mongodb.netflix_shows
            search_data = search_mongo(shows_coll)
            if search_data is not None:
                if more_info_search == 'genre':
                    genres = search_data['genres']
                    message = ' It belongs to '
                    for genre in genres:
                        message += genre['name'] + "..."
                    message += message_ending
                    return question(message)
                elif more_info_search == 'overview':
                    overview = search_data['overview']
                    message = overview + message_ending
                    return question(message)
                else:
                    return statement('Sorry I could not quite understand what ' +more_info_search+' is. I can give you an overview or get you you the genre')
            else:
                return statement('Sorry I could not find any info about the show')
        else:
            message, found = search_movie(search_name)
            if found:
                session.attributes['search_attr'] = 'movie'
                return question(message + '. Do you want more info about the movie?')
            else:
                return statement(message)
    else:
        try:
            search_name = session.attributes['search_term']
        except:
            return question(
                'You can say things like what is the genre of Narcos or something like give me an overview of Shameless')
        session.attributes['search_term'] = str(search_name)
        message, found = search_show(search_name)
        if found:
            session.attributes['search_attr'] = 'show'
            shows_coll = client.netflix_mongodb.netflix_shows
            search_data = search_mongo(shows_coll)
            if search_data is not None:
                if more_info_search == 'genre':
                    genres = search_data['genres']
                    message = 'It belongs to '
                    for genre in genres:
                        message += genre['name'] + ". "
                    message += message_ending
                    return question(message)
                elif more_info_search == 'overview':
                    overview = search_data['overview']
                    message = overview + message_ending
                    return question(message)
                else:
                    return question('Sorry I could not find that info about the show but, I can give you an overview or the genre. You can say things like give me an overview or what is the genre?')
            else:
                return statement('Sorry I could not find any info about the show.')
        else:
            message, found = search_movie(search_name)
            if found:
                session.attributes['search_attr'] = 'movie'
                return question(message + ' Do you want more info about the movie?')
            else:
                return statement(message)


@ask.intent("AMAZON.HelpIntent")
def help_intent():
    message = 'You can say things like I want to search for shows... Does netflix have Narcos'
    return question(message)


@ask.intent("AMAZON.NoIntent")
def help_intent():
    message = 'Ok, Happy watching!!!'
    return statement(message)


@ask.intent("AMAZON.StopIntent")
def stop():
    message = 'Ok, Bye'
    return statement(message)


@ask.intent("AMAZON.CancelIntent")
def stop():
    message = 'Ok, Ciao'
    return statement(message)


if __name__ == '__main__':
    app.run()
