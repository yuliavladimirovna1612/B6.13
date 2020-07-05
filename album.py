# импортируем необходимые сущности библиотеки bottle и SQLAlchemy
from bottle import route
from bottle import run
from bottle import HTTPError  # импортируем класс HTTPError
from bottle import request # импортируем объект request

import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# константа, указывающая способ соединения с базой данных
DB_PATH = "sqlite:///albums.sqlite3"
# базовый класс моделей таблиц
Base = declarative_base()


# Создаем классы исключений
class Error(Exception):
    pass

class AlreadyExists(Error):
    pass


# Создаем базовый класс (для работы с базой данных)
class Artist(Base):

    # Описывает структуру таблицы album, содержащую данные о музыкантах

    __tablename__ = 'album'

    id = sa.Column(sa.Integer, primary_key=True)
    year = sa.Column(sa.Integer)
    artist = sa.Column(sa.Text)
    genre = sa.Column(sa.Text)
    album = sa.Column(sa.Text)

# Устанавливаем соединение к базе данных и возвращаем объект сессии
def connect_db():
    # создаем соединение к базе данных
    engine = sa.create_engine(DB_PATH)
    # создаем описанные таблицы
    Base.metadata.create_all(engine)
    # создаем фабрику сессию
    session = sessionmaker(engine)
    # возвращаем сессию
    return session()

# Создаем функцию, которая сохраняет информацию в базу данных
def save(year, artist, genre, album):
    assert isinstance(year, int), "Некорректная дата"
    assert isinstance(artist, str), "Некорректный музыкант"
    assert isinstance(genre, str), "Некорректный жанр"
    assert isinstance(album, str), "Некорректный альбом"

    session = connect_db()
    saved_album = session.query(Artist).filter(Artist.album == album, Artist.artist == artist).first()
    if saved_album is not None:
        raise AlreadyExists("Альбом уже существует в базе данных и имеет #{}".format(saved_album.id))

    album = Artist(
        year=year,
        artist=artist,
        genre=genre,
        album=album
    )

    session.add(album)
    session.commit()
    return album


# Создание списка альбомов заданного музыканта с помощью стандартного декоратора route
@route("/albums/<artist>")
def albums(artist):
    session = connect_db()
    albums_list = session.query(Artist).filter(Artist.artist == artist).all()
    if not albums_list:
        message = "Альбомов {} не найдено".format(artist)
        result = HTTPError(404, message)
    else:
        album_count = session.query(Artist).filter(Artist.artist == artist).count()
        album_names = [album.album for album in albums_list]
        result = "Список альбомов {}:<br>".format(artist)
        result += "<br>".join(album_names)
        result += "<br>Количество альбомов {}".format(album_count)
    return result

# Внесение в базу данных нового музыканта и информации об альбомах
@route("/albums", method="POST")
def create_album():
    year = request.forms.get("year")
    artist = request.forms.get("artist")
    genre = request.forms.get("genre")
    album_name = request.forms.get("album")

    try:
        year = int(year)
    except ValueError:
        return HTTPError(400, "Указан некорректный год альбома")

    try:
        new_album = save(year, artist, genre, album_name)
    except AssertionError as err:
        result = HTTPError(400, str(err))
    except AlreadyExists as err:
        result = HTTPError(409, str(err))
    else:
        print("New #{} album successfully saved".format(new_album.id))
        result = "Альбом #{} успешно сохранен".format(new_album.id)
    return result

if __name__ == "__main__":
    # Запускаем веб-сервер с помощью функции run: указываем адрес узла и порт
    run(host="localhost", port=8080, debug=True)
    # Булев флаг debug=True запускает сервер в режиме отладки

# Для проверки работы приложения, после запуска локального сервера, введите
# в командную строку команды следующнго типа:
# Поиск музыканта - http http://localhost:8080/albums/Queen
# Добавление альбома - http -f POST localhost:8080/albums artist="Rihanna" genre="pop" year=2009 album="Rated R"