"""
#-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=#
  This file is part of the Smart Developer Hub Project:
    https://smartdeveloperhub.github.io

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
from rdflib import URIRef
import agora_fountain.index.core as index
from agora_fountain.vocab.schema import sem_g, onto_graph
from agora_fountain.server import app

@app.route('/ontology')
def get_ontology():
    response = make_response(sem_g.get_context(URIRef("http://sdh/ontology#skeleton")).serialize(format='turtle'))
    response.headers['Content-Type'] = 'text/turtle'

    return response


@app.route('/prefixes')
def get_prefixes():
    return jsonify(dict(onto_graph.namespaces()))

@app.route('/types')
def get_types():
    return jsonify({"types": index.get_types()})


@app.route('/types/<string:t>')
def get_type(t):
    return jsonify(index.get_type(t))


@app.route('/properties')
def get_properties():
    return jsonify({"properties": index.get_properties()})


@app.route('/properties/<string:prop>')
def get_property(prop):
    p = index.get_property(prop)

    return jsonify(p)


@app.route('/seeds')
def get_seeds():
    return jsonify({"seeds": index.get_seeds()})


@app.route('/seeds/<string:ty>')
def get_type_seeds(ty):
    return jsonify({"seeds": index.get_type_seeds(ty)})


@app.route('/seeds', methods=['POST'])
def add_seed():
    data = request.json
    index.add_seed(data.get('uri', None), data.get('type', None))
    return make_response()


@app.route('/paths/<elm>')
def get_path(elm):
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
