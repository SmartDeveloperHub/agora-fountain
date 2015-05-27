"""
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
  This file is part of the Smart Developer Hub Project:
    http://www.smartdeveloperhub.org

  Center for Open Middleware
        http://www.centeropenmiddleware.com/
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
  Copyright (C) 2015 Center for Open Middleware.
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

            http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
"""

__author__ = 'Fernando Serena'

from flask import make_response, request, jsonify
import agora_fountain.index.core as index
from agora_fountain.index.paths import calculate_paths
from agora_fountain.vocab.schema import sem_g, Schema
from agora_fountain.server import app
from flask_negotiate import consumes, produces
import json
from datetime import datetime as dt, timedelta as delta
from jobs import scheduler


class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


def vocab_prefix(uri):
    return [p for (p, u) in sem_g.namespaces() if u == uri and p != ''].pop()


@app.route('/vocabs')
# @produces('application/json')
def get_vocabularies():
    """
    Return the currently used ontology
    :return:
    """
    vocabs = Schema.get_vocabularies()
    response = make_response(json.dumps(vocabs))
    response.headers['Content-Type'] = 'application/json'

    return response

@app.route('/vocabs/<vid>')
def get_vocabulary(vid):
    """
    Return a concrete vocabulary
    :param vid: The identifier of a vocabulary (prefix)
    :return:
    """
    response = make_response(Schema.get_vocabulary(vid))
    response.headers['Content-Type'] = 'text/turtle'

    return response

def analyse_vocabulary(vid):
    index.extract_vocabulary(vid)
    calculate_paths()

@app.route('/vocabs', methods=['POST'])
@consumes('text/turtle')
def add_vocabulary():
    """
    Add a new vocabulary to the fountain
    :return:
    """
    try:
        vid = Schema.add_vocabulary(request.data)
    except IndexError:
        raise InvalidUsage('Ontology URI not found')

    scheduler.add_job(analyse_vocabulary, args=[vid])

    response = make_response()
    response.status_code = 201
    response.headers['Location'] = vid
    return response

@app.route('/vocabs/<vid>', methods=['PUT'])
@consumes('text/turtle')
def update_vocabulary(vid):
    """
    Updates an already contained vocabulary
    :return:
    """
    try:
        Schema.update_vocabulary(vid, request.data)
    except IndexError:
        raise InvalidUsage('Ontology URI not found')

    scheduler.add_job(analyse_vocabulary, args=[vid])

    response = make_response()
    response.status_code = 200
    return response


@app.route('/vocabs/<vid>', methods=['DELETE'])
def delete_vocabulary(vid):
    """
    Delete an existing vocabulary
    :return:
    """
    try:
        Schema.delete_vocabulary(vid)
    except IndexError:
        raise InvalidUsage('Ontology URI not found')

    scheduler.add_job(analyse_vocabulary, args=[vid])

    response = make_response()
    response.status_code = 200
    return response

@app.route('/prefixes')
def get_prefixes():
    """
    Return the prefixes dictionary of the ontology
    :return:
    """
    return jsonify(dict(sem_g.namespaces()))

@app.route('/types')
def get_types():
    """
    Return the list of supported types (prefixed)
    :return:
    """
    return jsonify({"types": index.get_types()})


@app.route('/types/<string:t>')
def get_type(t):
    """
    Return a concrete type description
    :param t: prefixed type e.g. foaf:Person
    :return: description of 't'
    """
    return jsonify(index.get_type(t))


@app.route('/properties')
def get_properties():
    """
    Return the list of supported properties (prefixed)
    :return:
    """
    return jsonify({"properties": index.get_properties()})


@app.route('/properties/<string:prop>')
def get_property(prop):
    """
    Return a concrete property description
    :param prop: prefixed property e.g. foaf:name
    :return: description of 'prop'
    """
    p = index.get_property(prop)

    return jsonify(p)


@app.route('/seeds')
def get_seeds():
    """
    Return the complete list of seeds available
    :return:
    """
    return jsonify({"seeds": index.get_seeds()})


@app.route('/seeds/<string:ty>')
def get_type_seeds(ty):
    """
    Return the list of seeds of a certain type
    :param ty: prefixed required type e.g. foaf:Person
    :return:
    """
    return jsonify({"seeds": index.get_type_seeds(ty)})


@app.route('/seeds', methods=['POST'])
def add_seed():
    """
    Add a new seed of a specific supported type
    :return:
    """
    data = request.json
    index.add_seed(data.get('uri', None), data.get('type', None))
    return make_response()


@app.route('/paths/<elm>')
def get_path(elm):
    """
    Return a path to a specific elem (either a property or a type, always prefixed)
    :param elm: The required prefixed type/property
    :return:
    """
    path_keys = index.r.keys('paths:{}:*'.format(elm))
    paths = []
    seed_paths = []
    for key in path_keys:
        path = index.r.get(key)
        paths.append(eval(path))

    for path in paths:
        for i, step in enumerate(path):
            type_seeds = index.get_type_seeds(step.get('type'))
            if len(type_seeds):
                sub_path = path[:i+1]
                sub_path = {'seeds': type_seeds, 'steps': [s for s in reversed(sub_path)]}
                if not (sub_path in seed_paths):
                    seed_paths.append(sub_path)
                    # break

    # It only returns seeds if elm is a type and there are seeds of it
    req_type_seeds = index.get_type_seeds(elm)
    if len(req_type_seeds):
        seed_paths.append({'seeds': req_type_seeds, 'steps': []})

    return jsonify({'paths': list(seed_paths)})
