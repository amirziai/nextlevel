import sys
from flask import Flask, request, jsonify, make_response, current_app, send_from_directory,\
    url_for, redirect, render_template, Response
from datetime import timedelta, datetime
from functools import update_wrapper

from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager, UserMixin, logout_user, current_user, login_user
from oauth import OAuthSignIn
import ast
from functools import wraps

# flask app
current_version = '07'
app = Flask(__name__)
app.config['SECRET_KEY'] = 'F!12Z@r47j\3yXm J xu&R~>X@H!j<<mM]Lwf/,?KXTxQ!'
app.config['MONGO_URI'] = '127.0.0.1:27017'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['OAUTH_CREDENTIALS'] = {
    'facebook': {
        'id': '940836925972002',
        'secret': '4c954cbadb8c15ea65c49585f2c794c5'
    },
}

db = SQLAlchemy(app)
lm = LoginManager(app)
lm.login_view = 'index'


# Facebook login stuff
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    social_id = db.Column(db.String(64), nullable=False, unique=True)
    nickname = db.Column(db.String(64), nullable=False)
    data = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(64), nullable=False)


@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')


@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    if not current_user.is_anonymous:
        return redirect('/')
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()


@app.route('/callback/<provider>')
def oauth_callback(provider):
    if not current_user.is_anonymous:
        return redirect('/')

    oauth = OAuthSignIn.get_provider(provider)
    social_id, username, email = oauth.callback()
    if social_id is None:
        flash('Authentication failed.')
        return redirect('/')

    user = User.query.filter_by(social_id=social_id).first()
    if not user:
        user = User(social_id=social_id, nickname=username, email=email, data=str([0] * 15))
        db.session.add(user)
        db.session.commit()
    login_user(user, True)
    return redirect('/')


movements = ['Deadlift', 'Front Squat', 'Weightlifting', 'Upper Body Pulling',
            'Upper Body Pushing', 'Rings', 'Squat Endurance', 'Fran',
            'Diane', 'Annie', 'Running', 'Kettlebell',
            'Aerobic Power Intervals', 'Rowing', 'Flexibility']


def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def extract_from_json(json_, items):
    return [json_[item] for item in items]


@app.route('/', methods=['GET'])
def index():
    if not current_user.is_anonymous:
        return render_template('index_v07.html')
    else:
        return render_template('login.html')


@app.route('/privacy', methods=['GET'])
def privacy():
    return render_template('privacy.html')


@app.route('/data', methods=['GET'])
def get_user_data():
    if not current_user.is_anonymous:
        return current_user.data
    else:
        return jsonify({'status': 'not authorized'})


@app.route('/log', methods=['POST'])
def log():
    try:
        if not current_user.is_anonymous:
            movement, score = extract_from_json(request.json, ['movement', 'score'])

            # log it
            with open('entries.log', 'a') as f:
                f.write('%s,%s,%s,%s\n' % (current_user.email, movement, score, timestamp()))

            movement_index = None

            for i, m in enumerate(movements):
                if m.replace(' ', '') == movement:
                    movement_index = i
                    break

            if movement_index is not None:
                print movement_index
                data = current_user.data
                data = ast.literal_eval(data)
                data[movement_index] = float(score)
                user = current_user
                user.data = str(data)
                db.session.add(user)
                db.session.commit()

                return jsonify({'status': 'success'})
        else:
            return jsonify({'status': 'not authorized'})


    except Exception, e:
        print e
        return jsonify({'error': e})


# admin
def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == 'nate' and password == '91jcsa9x@#x!'


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
            'Could not verify your access level for that URL.\n'
            'You have to login with proper credentials', 401,
            {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)

    return decorated


@app.route('/admin', methods=['GET'])
@requires_auth
def admin():
    return render_template('admin.html')


@app.route('/admin_data', methods=['GET'])
@requires_auth
def admin_data():
    import sqlite3
    conn = sqlite3.connect("db.sqlite")
    rs = conn.execute("select * from users")

    l = []
    for r in rs:
        l.append({'email': r[4], 'data': r[3]})

    return jsonify(results=l)


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)