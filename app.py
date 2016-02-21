import sys
from flask import Flask, request, jsonify, make_response, current_app, render_template, send_from_directory
from flask import session  # new
import pymongo as pm
from datetime import timedelta, datetime
from functools import update_wrapper
import copy

# flask app
current_version = '06'
app = Flask(__name__)
app.secret_key = 'F!12Z@r47j\3yXm J xu&R~>X@H!j<<mM]Lwf/,?KXTxQ!'

# TODO: remove
# import data
# from data import users

# mongo
mongo_url = '127.0.0.1:27017'
conn = pm.MongoClient(mongo_url)
db = conn['nextlevel']

movements = ['Deadlift', 'Front Squat', 'Weightlifting', 'Upper Body Pull',
            'Upper Body Pushing', 'Rings', 'Squat Endurance', 'Fran',
            'Diane', 'Annie', 'Running', 'Kettlebell',
            'Aerobic Power Intervals', 'Rowing', 'Flexibility'];


def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


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

@app.route('/', methods=['GET'])
@crossdomain(origin='*', headers="*", automatic_options=True)
def home():
    return send_from_directory('.', 'index_v%s.html' % current_version)


@app.route('/options', methods=['GET'])
@crossdomain(origin='*', headers="*", automatic_options=True)
def options():
    return send_from_directory('.', 'options.js')

@app.route('/old/<version>', methods=['GET'])
@crossdomain(origin='*', headers='*', automatic_options=True)
def old(version=None):
    if not version:
        version = current_version

    return send_from_directory('.', 'index_v%s.html' % version)

@app.route('/user/<email>', methods=['GET'])
@crossdomain(origin='*', headers="*", automatic_options=True)
def user(email):
    try:
        user = db.users.find_one({'email': email})

        if user:
            user.pop('_id', None)
            user.pop('dob', None)
            return jsonify(user=user)
        else:
            return 'Not found'
    except Exception, e:
		return e


def extract_from_json(json_, items):
    return [json_[item] for item in items]


@app.route('/log', methods=['POST'])
@crossdomain(origin='*', headers="*", automatic_options=True)
def log():
    try:
        print request.json
        email, movement, score = extract_from_json(request.json, ['user', 'movement', 'score'])
        db.users_log.insert_one({'user': email, 'movement': movement, 'score': score, 'timestamp': timestamp()})
        
        movement_index = None

        print email
        print movement
        print score

        for i, m in enumerate(movements):
            if m.replace(' ', '') == movement:
                movement_index = i
                break

        if movement_index is not None:
            print movement_index
            user = db.users.find_one({'email': email})

            if user:
                user_ = copy.deepcopy(user)
                user_['data'][movement_index] = score
                q = db.users.update(user, user_)
                print q
                return jsonify({'status': 'OK'})
            else:
                return jsonify({'status': 'user not found'})


    except Exception, e:
        print e
        return jsonify({'error': e})


@app.route('/reset/<pw>', methods=['GET'])
@crossdomain(origin='*', headers="*", automatic_options=True)
def reset(pw):
    if pw == 'Xa928x<2!X!-_21a+x1KA@h':
        # db.users.remove()
        # db.users.create_index('email')
        # db.users_log.create_index('users_log')

        user = db.users.find_one({'email': 'test@test.com'})
        user_ = copy.deepcopy(user)
        user_['data'] = [0] * 15
        db.users.replace_one(user, user_)

        return 'Success'
    else:
        return 'Unauthorized'

    # import imp
    # imp.reload(data)
    # from data import users


if __name__ == '__main__':
    try:
    	port = int(sys.argv[1])
    except:
    	port = 80

    app.run(host='0.0.0.0')
    # app.run(host='0.0.0.0', port=port, debug=True)