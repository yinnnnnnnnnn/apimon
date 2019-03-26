import requests
# sending HTTP requests to REST APIs from application
from cassandra.cluster import Cluster
from flask import Flask, jsonify, request
import requests_cache
# “transparent persistent cache” for the requests module
from werkzeug.security import generate_password_hash, check_password_hash
# library to generate hash and verify password

requests_cache.install_cache(
    'pokemon_cache', backend='sqlite', expire_after=36000
)

cluster = Cluster(['cassandra'])
session = cluster.connect()
app = Flask(__name__, instance_relative_config=True)
# config in instance can overwrite
app.config.from_object('config')
app.config.from_pyfile('config.py')
API_BASE = app.config['API_BASE']  # read from config
URL_TEMPLATE_POKEMONS = API_BASE + "/pokemon"


@app.route('/pokemon', methods=['GET'])
def get_all_pokemons():
    """Get information about all pokemons

    Query parameters:
      - auth_token [Required] -- auth token for the user making the request
      - offset [Optional] -- offset index of result, default: 0
      - limit [Optional] -- size of the return result page, default: 20

    Successful response [200 OK]:
      - count -- total number of results
      - next -- URL for next page of results
      - previous -- URL for previous page of results
      - results -- Array of pokemon names and URLs
        - name -- name of pokemon
        - url -- URL for details of the specific pokemon
    """

    # require an auth token from an existing user to use the API
    auth_token = request.args.get('auth_token')  # hash based security
    user = get_user_by_auth_token(auth_token)
    if user is None:
        return jsonify({"error": "unauthorised!"}), 401

    # call external Pokemon API (pokeapi) for pokemon information
    url = URL_TEMPLATE_POKEMONS

    # forward any query parameters e.g offset
    if request.query_string is not None:
        url = url + "?" + request.query_string.decode('utf-8')

    # return result to client with 200 OK code if successful
    resp = requests.get(url)
    if resp.ok:
        return jsonify(resp.json()), 200
    else:
        return resp.reason, resp.status_code


@app.route('/user', methods=['POST'])
def register_user():
    """Register a user

    Payload parameters:
      - username [Required]
      - password [Required]
      - email [Required]

    Successful response [201 Created]:
      - <intentionally empty body>

    Unsuccessful response [409 Conflict]：
      - error -- error message
    """

    # detect if username already exist
    username = request.form['username']
    exsting_user = get_user_by_username(username)
    if exsting_user is not None:
        return jsonify({"error": "username already exist!"}), 409
    password = request.form['password']

    # generate password hash and auth token
    password_hash = generate_password_hash(password)
    auth_token = generate_password_hash(username + password)
    email = request.form['email']

    # save user to database
    session.execute("""
        INSERT INTO apimon.user (
            id, username, email, password_hash, auth_token, is_active, created
        )
        VALUES (
            uuid(), '{}', '{}', '{}', '{}', True, toTimestamp(now())
        )""".format(
            username, email, password_hash, auth_token
        )
    )

    return "", 201


@app.route('/login', methods=['POST'])
def login():
    """Login a user

    Payload parameters:
      - username [Required]
      - password [Required]

    Successful response [200 OK]:
      - auth_token -- auth token for the user making the request
    """

    username = request.form['username']
    password = request.form['password']
    exsting_user = get_user_by_username(username)

    # if username does not exist or password does not match the hash record
    # return 401 unauthorised error
    if (
        exsting_user is None
    ) or (
        not check_password_hash(exsting_user.password_hash, password)
    ):
        return jsonify({"error": "username/password incorrect!"}), 401

    # otherwise, return the auth token of the user with 200 OK code
    return jsonify({"auth_token": exsting_user.auth_token}), 200


@app.route('/user', methods=['PUT'])
def change_password():
    """Change a user's password

    Payload parameters:
      - auth_token [Required] -- auth token for the user under change
      - new_password [Required]

    Successful response [200 OK]:
      - auth_token -- new auth token for the user making the request
    """

    auth_token = request.form['auth_token']
    new_password = request.form['new_password']
    if auth_token is not None:
        existing_user = get_user_by_auth_token(auth_token)

        # if provided an valid auth token for the user under change
        if existing_user is not None and existing_user.auth_token == auth_token:

            # generate new password hash and auth token
            new_password_hash = generate_password_hash(new_password)
            new_auth_token = generate_password_hash(
                existing_user.username + new_password
            )

            # update database for the new password and auth token
            session.execute(
                """
                UPDATE apimon.user
                 SET password_hash = '{}', auth_token = '{}',
                  last_modified = toTimestamp(now())
                 WHERE username = '{}'
                """.format(
                    new_password_hash, new_auth_token, existing_user.username
                )
            )
            return jsonify({"auth_token": new_auth_token}), 200
    return jsonify({"error": "unauthorised!"}), 401


@app.route('/user/<username>', methods=['DELETE'])
def delete_user(username):
    """Delete a user

    Path parameters:
      - username

    Query parameters:
      - auth_token [Required] -- auth token for the user making the request

    Successful response [200 OK]:
      - <intentionally empty body>
    """

    auth_token = request.args.get('auth_token')

    # if provided an valid auth token for the user under change
    if auth_token is not None:
        user = get_user_by_username(username)
        if user is None:
            return jsonify({"error": "user not found!"}), 404
        if user.auth_token == auth_token:

            # delete the user from database
            session.execute(
                """
                DELETE FROM apimon.user where username = '{}'
                """.format(username)
            )

            return "", 200
    return jsonify({"error": "unauthorised!"}), 401


def get_user_by_username(username):
    """Get a user from database by username

    Parameters:
      - username [Required]
    """

    if username is not None:
        result_set = session.execute(
            """SELECT * FROM apimon.user
            WHERE username = '{}'""".format(username)
        )

        if result_set.current_rows:
            return result_set[0]

    return None


def get_user_by_auth_token(auth_token):
    """Get a user from database by auth token

    Parameters:
      - auth_token [Required]
    """

    if auth_token is not None:
        result_set = session.execute(
            """SELECT * FROM apimon.user
            WHERE auth_token = '{}'""".format(auth_token)
        )

        if result_set.current_rows:
            return result_set[0]

    return None


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80, debug=app.config['DEBUG'])
