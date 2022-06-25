from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

API_KEY = "YOUR API KEY FROM https://developers.themoviedb.org/3/search/search-movies"

app = Flask(__name__)
app.config['SECRET_KEY'] = 'RANDOM STRING'
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///movies.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
Bootstrap(app)


class EditForm(FlaskForm):
    new_rating = StringField('Your Rating Out of 10 e.g. 7.5', validators=[DataRequired()])
    new_review = StringField('Your Review', validators=[DataRequired()])
    button = SubmitField("Done", validators=[DataRequired()])

class AddMovieForm(FlaskForm):
    movie_title = StringField("Movie Title", validators=[DataRequired()])
    button = SubmitField("Add Movie", validators=[DataRequired()])

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    year = db.Column(db.Integer)
    description = db.Column(db.String(10000))
    rating = db.Column(db.Float)
    ranking = db.Column(db.Integer)
    review = db.Column(db.String(250))
    img_url = db.Column(db.String(250))
db.create_all()


new_movie = Movie(
    title="Phone Booth",
    year=2002,
    description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
    rating=7.3,
    ranking=10,
    review="My favourite character was the caller.",
    img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
)


@app.route("/")
def home():
    all_movies = db.session.query(Movie).all()
    all_ratings = {movie.id: movie.rating for movie in all_movies}

    for i in range(len(all_ratings)):
        max_rating = None
        for id in all_ratings:
            if max_rating == None:
                max_rating = all_ratings[id]
                id_with_max_rating = id
            elif all_ratings[id] > max_rating:
                max_rating = all_ratings[id]
                id_with_max_rating = id

        Movie.query.filter_by(id=id_with_max_rating).first().ranking = i + 1
        all_ratings.pop(id_with_max_rating)

    all_movies = db.session.query(Movie).order_by(-Movie.ranking)

    return render_template("index.html", movies=all_movies)

@app.route('/edit', methods=["GET", "POST"])
def edit():
    id = request.args.get("id")
    movie = Movie.query.get(id)
    form = EditForm()
    if form.validate_on_submit():
        new_rating = form.data["new_rating"]
        new_review = form.data["new_review"]
        movie.rating = new_rating
        movie.review = new_review
        db.session.commit()
        return redirect(url_for('home'))

    return render_template("edit.html", movie=movie, form=form)

@app.route('/delete', methods=["GET", "POST"])
def delete():
    id = request.args.get("id")
    movie = Movie.query.get(id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/add', methods=["GET", "POST"])
def add():
    form = AddMovieForm()
    if form.validate_on_submit():
        payload = {
            "api_key": API_KEY,
            "query": form.data["movie_title"]
        }
        response = requests.get("https://api.themoviedb.org/3/search/movie", params=payload)
        text = response.json()["results"]
        list_of_dicts = [dict1 for dict1 in text]
        return render_template("select.html", all_movies=list_of_dicts)
    return render_template("add.html", form=form)

@app.route("/find")
def find_movie():
    id = request.args.get("id")
    payload = {
        "api_key": API_KEY,
        "language": "pl-PL",
    }
    MOVIE_DB_INFO_URL = "https://api.themoviedb.org/3/movie"
    MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"
    response = requests.get(f"{MOVIE_DB_INFO_URL}/{id}", params=payload)
    text = response.json()

    title = text["title"]
    img_url = f'{MOVIE_DB_IMAGE_URL}{text["poster_path"]}'
    year = text["release_date"].split("-")[0]
    description = text["overview"]
    print(title, img_url, year, description)

    new_movie = Movie(title=title, year=year, description=description, img_url=img_url)
    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for("edit", id=Movie.query.filter_by(title=title).first().id))


if __name__ == '__main__':
    app.run(debug=True)
