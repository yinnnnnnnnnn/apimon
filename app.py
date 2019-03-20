import requests
import sys
from flask import Flask, jsonify, request
import requests_cache

requests_cache.install_cache('pokemon_cache', backend='sqlite', expire_after=36000)

app = Flask(__name__, instance_relative_config=True)
app.config.from_object('config')
app.config.from_pyfile('config.py')
API_BASE = app.config['API_BASE']
url_template_pokemons = API_BASE + "/pokemon"
url_template_pokemon = API_BASE + "/pokemon/{idOrName}"

@app.route('/pokemon', methods=['GET'])
def get_all_pokemons():
    url = url_template_pokemons
    if request.query_string is not None:
        url = url + "?" + request.query_string.decode('utf-8')

    resp = requests.get(url)
    if resp.ok:
        return jsonify(resp.json()), 200
    else:
        return resp.reason, resp.status_code

@app.route('/pokemon/<idOrName>', methods=['GET'])
def get_pokemon(idOrName):
    url = url_template_pokemon.format(idOrName = idOrName)

    resp = requests.get(url)
    if resp.ok:
        pokemon = { key: resp.json()[key] for key in ['id', 'name', 'height', 'weight', 'species', 'types'] }
        return jsonify(pokemon), 200
    else:
        return resp.reason, resp.status_code

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80, debug=app.config['DEBUG'])


