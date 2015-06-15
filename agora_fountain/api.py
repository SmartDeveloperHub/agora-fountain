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

from flask import make_response, request, jsonify, render_template
from agora_fountain.vocab.schema import prefixes
import agora_fountain.index.core as index
from agora_fountain.index.paths import calculate_paths, pgraph
import agora_fountain.vocab.onto as vocs
from agora_fountain.server import app
from flask_negotiate import consumes
import json
from jobs import scheduler
import itertools
import base64


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
    response = make_response(vocs.get_vocabulary(vid))
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
        vid = vocs.add_vocabulary(request.data)
    except IndexError:
        raise APIError('Ontology URI not found')
    except vocs.DuplicateVocabulary, e:
        raise Conflict(e.message)

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
        vocs.update_vocabulary(vid, request.data)
    except IndexError:
        raise APIError('Ontology URI not found')
    except vocs.UnknownVocabulary, e:
        raise NotFound(e.message)
    except Exception, e:
        raise APIError(e.message)

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
        vocs.delete_vocabulary(vid)
    except IndexError:
        raise APIError('Ontology URI not found')
    except vocs.UnknownVocabulary, e:
        raise NotFound(e.message)

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


def __get_path(elm):
    paths = []
    seed_paths = []
    for path, score in index.r.zrange('paths:{}'.format(elm), 0, -1, withscores=True):
        paths.append((int(score), eval(path)))

    all_cycles = set([])

    for score, path in paths:
        for i, step in enumerate(path):
            ty = step.get('type')
            type_seeds = index.get_type_seeds(ty)
            if len(type_seeds):
                cycles = [int(c) for c in index.r.smembers('cycles:{}'.format(elm))]
                all_cycles = all_cycles.union(set(cycles))
                sub_path = {'cycles': cycles, 'seeds': type_seeds, 'steps': list(reversed(path[:i + 1]))}
                if not (sub_path in seed_paths):
                    seed_paths.append(sub_path)

    # It only returns seeds if elm is a type and there are seeds of it
    req_type_seeds = index.get_type_seeds(elm)
    if len(req_type_seeds):
        seed_paths.append({'seeds': req_type_seeds, 'steps': []})

    all_cycles = [{'cycle': int(cid), 'steps': eval(index.r.zrange('cycles', cid, cid).pop())} for cid in all_cycles]
    return list(seed_paths), all_cycles


def __graph_path(elm, paths, cycles):
    nodes = []
    edges = []
    roots = set([])
    mem_edges = set([])

    for path in paths:
        steps = path['steps']
        last_node = None
        last_prop = None
        for i, step in enumerate(steps):
            ty = step['type']
            prop = step['property']
            node_d = {'data': {'id': base64.b16encode(ty), 'label': ty, 'shape': 'roundrectangle',
                               'width': len(ty) * 10}}
            if not i:
                roots.add(base64.b16encode(ty))
                node_d['classes'] = 'seed'

            nodes.append(node_d)
            if last_node is not None and (last_node, last_prop, ty) not in mem_edges:
                edges.append(
                    {'data': {'id': 'e{}'.format(len(edges)), 'source': base64.b16encode(last_node), 'label': last_prop,
                              'target': base64.b16encode(ty)}})
                mem_edges.add((last_node, last_prop, ty))
            last_node = ty
            last_prop = prop

        if index.is_type(elm):
            nodes.append({'data': {'id': base64.b16encode(elm), 'label': elm, 'shape': 'roundrectangle',
                                   'width': len(elm) * 10}, 'classes': 'end'})
            if (last_node, last_prop, elm) not in mem_edges:
                edges.append(
                    {'data': {'id': 'e{}'.format(len(edges)), 'source': base64.b16encode(last_node), 'label': last_prop,
                              'target': base64.b16encode(elm)}})
                mem_edges.add((last_node, last_prop, elm))
        else:
            prop = index.get_property(elm)
            prop_range = prop['range']
            prop_range = [d for d in prop_range if not set.intersection(set(index.get_type(d).get('super')),
                                                                        set(prop_range))]
            prop_type = prop['type']
            for r in prop_range:
                shape = 'roundrectangle'
                if prop_type == 'data':
                    shape = 'ellipse'
                nodes.append({'data': {'id': base64.b16encode(r), 'label': r, 'shape': shape,
                                       'width': len(elm) * 10}})
                if (last_node, elm, r) not in mem_edges:
                    edges.append(
                        {'data': {'id': 'e{}'.format(len(edges)), 'source': base64.b16encode(last_node), 'label': elm,
                                  'target': base64.b16encode(r)}, 'classes': 'end'})
                    mem_edges.add((last_node, elm, r))

    return nodes, edges, list(roots)


@app.route('/paths/<elm>')
@app.route('/paths/<elm>/view')
def get_path(elm):
    """
    Return a path to a specific elem (either a property or a type, always prefixed)
    :param elm: The required prefixed type/property
    :return:
    """
    seed_paths, all_cycles = __get_path(elm)
    if 'view' in request.url_rule.rule:
        nodes, edges, roots = __graph_path(elm, seed_paths, all_cycles)
        return render_template('graph-path.html',
                               nodes=json.dumps(nodes),
                               edges=json.dumps(edges), roots=json.dumps(roots))
    else:
        return jsonify({'paths': seed_paths, 'all-cycles': all_cycles})


@app.route('/graph/')
def show_graph():
    types = []
    nodes = []
    edges = []
    roots = []

    ibase = 0
    nodes_dict = dict([(nid, base64.b16encode(nid)) for nid in pgraph.nodes()])
    for (nid, data) in pgraph.nodes(data=True):
        if data.get('ty') == 'type':
            types.append(nid)
            has_seeds = len(index.get_type_seeds(nid))
            node_d = {'data': {'id': nodes_dict[nid], 'label': nid, 'shape': 'roundrectangle',
                               'width': len(nid) * 10}}
            if has_seeds:
                roots.append(nodes_dict[nid])
                node_d['classes'] = 'seed'
            nodes.append(node_d)
            ibase += 1
        elif data.get('ty') == 'prop' and data.get('object'):
            dom = [t for (t, _) in pgraph.in_edges(nid)]
            ran = [t for (_, t) in pgraph.out_edges(nid)]
            dom = [d for d in dom if not set.intersection(set(index.get_type(d).get('super')), set(dom))]
            ran = [r for r in ran if not set.intersection(set(index.get_type(r).get('super')), set(ran))]

            op_edges = list(itertools.product(*[dom, ran]))
            edges.extend([{'data': {'id': 'e{}'.format(ibase + i), 'source': nodes_dict[s], 'label': nid,
                                    'target': nodes_dict[tg]}} for i, (s, tg) in enumerate(op_edges)])
            ibase += len(op_edges) + 1
        else:
            ran = data.get('range')
            if len(ran):
                dom = [t for (t, _) in pgraph.in_edges(nid)]
                dom = [d for d in dom if not set.intersection(set(index.get_type(d).get('super')), set(dom))]
                dp_edges = list(itertools.product(*[dom, ran]))

                for i, (s, t) in enumerate(dp_edges):
                    rid = 'n{}'.format(len(nodes_dict) + len(nodes))
                    nodes.append({'data': {'id': rid, 'label': t, 'width': len(t) * 10, 'shape': 'ellipse'}})
                    edges.append({'data': {'id': 'e{}'.format(ibase + i), 'source': nodes_dict[s], 'label': nid,
                                           'target': rid}})
                ibase += len(dp_edges) + 1

    for t in types:
        supertypes = index.get_type(t).get('super')
        supertypes = [s for s in supertypes if not set.intersection(set(index.get_type(s).get('sub')),
                                                                    set(supertypes))]
        st_edges = [{'data': {'id': 'e{}'.format(ibase + i), 'source': nodes_dict[st], 'label': '',
                              'target': nodes_dict[t]}, 'classes': 'subclass'}
                    for i, st in enumerate(supertypes) if st in nodes_dict]
        if len(st_edges):
            edges.extend(st_edges)

        ibase += len(st_edges) + 1

    return render_template('graph-vocabs.html',
                           nodes=json.dumps(nodes),
                           edges=json.dumps(edges), roots=json.dumps(roots))
