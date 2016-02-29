import sys
from flask import Flask, request, jsonify, make_response, current_app, send_from_directory,\
    url_for, redirect, render_template
from datetime import timedelta, datetime
from functools import update_wrapper

from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager, UserMixin, logout_user, current_user, login_user
from oauth import OAuthSignIn
import ast

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
    'twitter': {
        'id': 'a',
        'secret': 'b'
    }
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
    return redirect(url_for('index'))


@app.route('/authorize/<provider>')
def oauth_authorize(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    return oauth.authorize()


@app.route('/callback/<provider>')
def oauth_callback(provider):
    if not current_user.is_anonymous:
        return redirect(url_for('index'))
    oauth = OAuthSignIn.get_provider(provider)
    social_id, username, email = oauth.callback()
    if social_id is None:
        flash('Authentication failed.')
        return redirect(url_for('index'))
    user = User.query.filter_by(social_id=social_id).first()
    if not user:
        user_new = User(social_id=social_id, nickname=username, email=email, data=str([0] * 15))
        db.session.add(user_new)
        db.session.commit()
    login_user(user, True)
    return redirect(url_for('index'))


# mongo
# mongo_url =
# conn = pm.MongoClient(mongo_url)
# db = conn['nextlevel']


movements = ['Deadlift', 'Front Squat', 'Weightlifting', 'Upper Body Pull',
            'Upper Body Pushing', 'Rings', 'Squat Endurance', 'Fran',
            'Diane', 'Annie', 'Running', 'Kettlebell',
            'Aerobic Power Intervals', 'Rowing', 'Flexibility']


def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def extract_from_json(json_, items):
    return [json_[item] for item in items]


def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True): 
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Credentials'] = 'true'
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator




@app.route('/', methods=['GET', 'OPTIONS'])
# @crossdomain(origin='*', headers="*", automatic_options=True)
def index():
    if not current_user.is_anonymous:
        return render_template('index_v07.html')
    else:
        return render_template('login.html')

# def home():
#     return send_from_directory('.', 'index_v%s.html' % current_version)

#
# @app.route('/old/<version>', methods=['GET'])
# @crossdomain(origin='*', headers='*', automatic_options=True)
# def old(version=None):
#     if not version:
#         version = current_version
#
#     return send_from_directory('.', 'index_v%s.html' % version)


@app.route('/privacy', methods=['GET'])
def privacy():
    return render_template('privacy.html')


@app.route('/user/<email>', methods=['GET'])
# @crossdomain(origin='*', headers="*", automatic_options=True)
def user(email):
    try:
        user = db.users.find_one({'email': email})

        if user:
            user.pop('_id', None)
            user.pop('dob', None)
            return jsonify(user=user)
        else:
            return jsonify({'status': 'not found'})
    except Exception, e:
        return e


@app.route('/data', methods=['GET'])
def get_user_data():
    return current_user.data


@app.route('/log', methods=['POST'])
# @crossdomain(origin='*', headers="*", automatic_options=True)
def log():
    try:
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
            print current_user

            user = current_user
            user.data = str(data)
            db.session.add(user)
            db.session.commit()
            # User.query.filter_by(social_id=current_user.social_id).first().update({'data': str(data)})

            return jsonify({'status': 'success'})
            # user = db.users.find_one({'email': email})
            #
            # if user:
            #     user_ = copy.deepcopy(user)
            #     user_['data'][movement_index] = score
            #     q = db.users.update(user, user_)
            #     print q
            #     return jsonify({'status': 'OK'})
            # else:
            #     return jsonify({'status': 'user not found'})


    except Exception, e:
        print e
        return jsonify({'error': e})


# @app.route('/reset/<pw>', methods=['GET'])
# @crossdomain(origin='*', headers="*", automatic_options=True)
# def reset(pw):
#     if pw == 'Xa928x<2!X!-_21a+x1KA@h':
#         # db.users.remove()
#         # db.users.create_index('email')
#         # db.users_log.create_index('users_log')
#
#         user = db.users.find_one({'email': 'test@test.com'})
#         user_ = copy.deepcopy(user)
#         user_['data'] = [0] * 15
#         db.users.replace_one(user, user_)
#
#         return 'Success'
#     else:
#         return 'Unauthorized'
#
#     # import imp
#     # imp.reload(data)
#     # from data import users


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)

    # try:
    #     port = int(sys.argv[1])
    # except:
    #     port = 80
    #
    # app.run(host='0.0.0.0')
    # # app.run(host='0.0.0.0', port=port, debug=True)