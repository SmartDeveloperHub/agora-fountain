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

import json

from flask import make_response, request, jsonify, render_template, url_for
from flask_negotiate import consumes

from agora.fountain.vocab.schema import prefixes
import agora.fountain.index.core as index
import agora.fountain.index.seeds as seeds
from agora.fountain.view.path import view_path
from agora.fountain.view.graph import view_graph
from agora.fountain.index.paths import calculate_paths, find_path
import agora.fountain.vocab.onto as vocs
from agora.fountain.server import app


class APIError(Exception):
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


class NotFound(APIError):
    def __init__(self, message, payload=None):
        super(NotFound, self).__init__(message, 404, payload)


class Conflict(APIError):
    def __init__(self, message, payload=None):
        super(Conflict, self).__init__(message, 409, payload)


@app.errorhandler(APIError)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.route('/vocabs')
def get_vocabularies():
    """
    Return the currently used ontology
    :return:
    """
    vocabs = vocs.get_vocabularies()
    vocabs = [(x, url_for('get_vocabulary', vid=x, _external=True)) for x in vocabs]
    response = make_response(json.dumps(dict(vocabs)))
    response.headers['Content-Type'] = 'application/json'

    return response


@app.route('/vocabs/<vid>')
def get_vocabulary(vid):
    """
    Return a concrete vocabulary
    :param vid: The identifier of a vocabulary (prefix)
    :return:
    """
    response = make_response(vocs.get_vocabulary(vid))
    response.headers['Content-Type'] = 'text/turtle'

    return response


def __analyse_vocabularies(vids):
    for vid in reversed(vids):
        index.extract_vocabulary(vid)
    calculate_paths()


def __check_seeds():
    seed_dict = seeds.get_seeds()
    types = index.get_types()
    obsolete_types = set.difference(set(seed_dict.keys()), set(types))
    for t in obsolete_types:
        seeds.delete_type_seeds(t)


@app.route('/vocabs', methods=['POST'])
@consumes('text/turtle')
def add_vocabulary():
    """
    Add a new vocabulary to the fountain
    :return:
    """
    try:
        vids = vocs.add_vocabulary(request.data)
    except vocs.VocabularyNotFound, e:
        raise APIError('Ontology URI not found')
    except vocs.DuplicateVocabulary, e:
        raise Conflict(e.message)

    __analyse_vocabularies(vids)

    response = make_response()
    response.status_code = 201
    response.headers['Location'] = url_for('get_vocabulary', vid=vids.pop(0), _external=True)
    return response


@app.route('/vocabs/<vid>', methods=['PUT'])
@consumes('text/turtle')
def update_vocabulary(vid):
    """
    Updates an already contained vocabulary
    :return:
    """
    try:
        vocs.update_vocabulary(vid, request.data)
    except IndexError:
        raise APIError('Ontology URI not found')
    except vocs.UnknownVocabulary, e:
        raise NotFound(e.message)
    except Exception, e:
        raise APIError(e.message)

    __analyse_vocabularies([vid])
    __check_seeds()

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
        vocs.delete_vocabulary(vid)
    except IndexError:
        raise APIError('Ontology URI not found')
    except vocs.UnknownVocabulary, e:
        raise NotFound(e.message)

    __analyse_vocabularies([vid])
    __check_seeds()

    response = make_response()
    response.status_code = 200
    return response


@app.route('/prefixes')
def get_prefixes():
    """
    Return the prefixes dictionary of the ontology
    :return:
    """
    return jsonify(prefixes())


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
    return jsonify({"seeds": seeds.get_seeds()})


@app.route('/seeds/<string:ty>')
def get_type_seeds(ty):
    """
    Return the list of seeds of a certain type
    :param ty: prefixed required type e.g. foaf:Person
    :return:
    """
    try:
        return jsonify({"seeds": seeds.get_type_seeds(ty)})
    except seeds.TypeNotAvailableError as e:
        raise NotFound(e.message)


@app.route('/seeds', methods=['POST'])
@consumes('application/json')
def add_seed():
    """
    Add a new seed of a specific supported type
    :return:
    """
    data = request.json
    try:
        sid = seeds.add_seed(data.get('uri', None), data.get('type', None))
        response = make_response(sid)
        response.headers['Location'] = url_for('get_seed', sid=sid, _external=True)
        response.status_code = 201
    except (seeds.TypeNotAvailableError, ValueError) as e:
        raise APIError(e.message)
    except seeds.DuplicateSeedError as e:
        raise Conflict(e.message)
    return response


@app.route('/seeds/id/<sid>')
def get_seed(sid):
    """
    Get the known information about a specific seed by id
    :return:
    """
    try:
        seed = seeds.get_seed(sid)
        return jsonify(seed)
    except seeds.InvalidSeedError, e:
        raise NotFound(e.message)


@app.route('/seeds/id/<sid>', methods=['DELETE'])
def delete_seed(sid):
    """
    Delete a specific seed by id
    :return:
    """
    try:
        seeds.delete_seed(sid)
        return make_response()
    except seeds.InvalidSeedError, e:
        raise NotFound(e.message)


@app.route('/paths/<elm>')
@app.route('/paths/<elm>/view')
def get_path(elm):
    """
    Return a path to a specific elem (either a property or a type, always prefixed)
    :param elm: The required prefixed type/property
    :return:
    """
    try:
        seed_paths, all_cycles = find_path(elm)
        if 'view' in request.url_rule.rule:
            nodes, edges, roots = view_path(elm, seed_paths)
            return render_template('graph-path.html',
                                   nodes=json.dumps(nodes),
                                   edges=json.dumps(edges), roots=json.dumps(roots))
        else:
            return jsonify({'paths': seed_paths, 'all-cycles': all_cycles})
    except seeds.TypeNotAvailableError, e:
        raise APIError(e.message)


@app.route('/graph/')
def show_graph():
    nodes, edges, roots = view_graph()

    return render_template('graph-vocabs.html',
                           nodes=json.dumps(nodes),
                           edges=json.dumps(edges), roots=json.dumps(roots))
