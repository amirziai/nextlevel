import sys
from flask import Flask, request, jsonify, make_response, current_app, render_template, send_from_directory
from datetime import timedelta
from functools import update_wrapper

import data
from data import users

# flask app
app = Flask(__name__)
current_version = '03'


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


@app.route('/old/<version>', methods=['GET'])
@crossdomain(origin='*', headers='*', automatic_options=True)
def old(version=None):
    if not version:
        version = current_version

    return send_from_directory('.', 'index_v%s.html' % version)

@app.route('/user/<user>', methods=['GET'])
@crossdomain(origin='*', headers="*", automatic_options=True)
def user(user):
	try:
		user_ = users[int(user)]
		return jsonify(user=user_)
	except:
		pass


@app.route('/reset', methods=['GET'])
@crossdomain(origin='*', headers="*", automatic_options=True)
def reset():
    import imp
    imp.reload(data)
    from data import users

    return 'Done'

if __name__ == '__main__':
    try:
    	port = int(sys.argv[1])
    except:
    	port = 80

    app.run()
    # app.run(host='0.0.0.0', port=port, debug=True)