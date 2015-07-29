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
import logging
from rdflib import ConjunctiveGraph, URIRef, BNode
from rdflib.namespace import OWL, RDF, RDFS
from agora.fountain.server import app

log = logging.getLogger('agora_fountain.schema')

store_mode = app.config['STORE']
if 'persist' in store_mode:
    graph = ConjunctiveGraph('Sleepycat')
    graph.open('graph_store', create=True)
else:
    graph = ConjunctiveGraph()

log.info('Loading ontology...'),
graph.store.graph_aware = False
log.debug('\n{}'.format(graph.serialize(format='turtle')))
log.info('Ready')

_namespaces = {}
_prefixes = {}


def flat_slice(lst):
    lst = list(lst)
    for i, _ in enumerate(lst):
        while hasattr(lst[i], "__iter__") and not isinstance(lst[i], basestring):
            lst[i:i + 1] = lst[i]
    return set(lst)


def qname(uri):
    q = uri.n3(graph.namespace_manager)
    return q


def _extend_prefixed(pu):
    parts = pu.split(':')
    if len(parts) == 1:
        parts = ('', parts[0])
    try:
        return URIRef(_prefixes[parts[0]] + parts[1])
    except KeyError:
        return BNode(pu)


def prefixes(vid=None):
    context = graph
    if vid is not None:
        context = context.get_context(vid)
    return list(context.namespaces())


def contexts():
    return [str(x.identifier) for x in graph.contexts()]


def update_context(vid, g):
    context = graph.get_context(vid)
    graph.remove_context(context)
    add_context(vid, g)


def remove_context(vid):
    context = graph.get_context(vid)
    graph.remove_context(context)


def get_context(vid):
    return graph.get_context(vid)


def add_context(vid, g):
    vid_context = graph.get_context(vid)
    for t in g.triples((None, None, None)):
        vid_context.add(t)

    for (p, u) in g.namespaces():
        if p != '':
            vid_context.bind(p, u)

    _namespaces.update([(uri, prefix) for (prefix, uri) in graph.namespaces()])
    _prefixes.update([(prefix, uri) for (prefix, uri) in graph.namespaces()])


def get_types(vid=None):
    context = graph
    if vid is not None:
        context = context.get_context(vid)
    res = set([])
    q_class_result = context.query("""SELECT DISTINCT ?c ?x WHERE {{?c a owl:Class} UNION {?c rdfs:subClassOf ?x}}""")
    classes_set = flat_slice(q_class_result)
    res.update([qname(c) for c in classes_set if isinstance(c, URIRef)])
    q_class_result = context.query(
                    """SELECT DISTINCT ?r ?d WHERE {?p a owl:ObjectProperty. {?p rdfs:range ?r .} UNION {?p rdfs:domain ?d.}}""")
    classes_set = flat_slice(q_class_result)
    res.update([qname(c) for c in classes_set if isinstance(c, URIRef)])
    res.update([qname(x[0]) for x in context.query("""SELECT DISTINCT ?c WHERE {{?r owl:allValuesFrom ?c}
                                                    UNION {?a owl:someValuesFrom ?c}
                                                    UNION {?b owl:onClass ?c}}""") if isinstance(x[0], URIRef)])

    return res


def get_properties(vid=None):
    context = graph
    if vid is not None:
        context = context.get_context(vid)
    res = set([])
    res.update([qname(c or d) for (c, d) in
                context.query("SELECT ?c ?d WHERE { {?c a owl:ObjectProperty} UNION {?d a owl:DatatypeProperty} }")])
    res.update([qname(p[0]) for p in context.query("SELECT ?p WHERE { ?r a owl:Restriction. ?r owl:onProperty ?p }")])

    return res


def get_property_domain(prop, vid=None):
    context = graph
    if vid is not None:
        context = context.get_context(vid)
    res = map(lambda x: qname(x), context.objects(_extend_prefixed(prop), RDFS.domain))
    dom = set([])
    for t in res:
        dom.update(get_subtypes(t, vid))
        dom.add(t)
    res = [qname(c[0])
           for c in context.query("""SELECT ?c WHERE { ?c rdfs:subClassOf [ owl:onProperty %s ]}""" % prop)]
    dom.update(res)
    for t in res:
        dom.update(get_subtypes(t, vid))
    return dom


def is_object_property(prop, vid=None):
    context = graph
    if vid is not None:
        context = context.get_context(vid)
    type_res = context.query("""ASK {%s a owl:ObjectProperty}""" % prop)
    is_object = [_ for _ in type_res].pop()

    if not is_object:
        is_object = [_ for _ in
                     context.query("""ASK {?r owl:onProperty %s.
                                    {?r owl:someValuesFrom ?o} UNION
                                    {?r owl:allValuesFrom ?a} UNION
                                    {?r owl:onClass ?c} .}""" % prop)].pop()

    return is_object


def get_property_range(prop, vid=None):
    context = graph
    if vid is not None:
        context = context.get_context(vid)
    sub_ts = set([])
    res = [t for t in context.objects(subject=_extend_prefixed(prop), predicate=RDFS.range)
           if isinstance(t, URIRef)]

    if is_object_property(prop, vid):
        for y in res:
            sub_ts.update([qname(z) for z in context.transitive_subjects(RDFS.subClassOf, y)
                           if isinstance(z, URIRef)])
            sub_ts.add(qname(y))
        res = [qname(r[0]) for r in
               context.query("""SELECT ?r WHERE { ?d owl:onProperty %s. ?d owl:allValuesFrom ?r.}""" % prop)
               if isinstance(r[0], URIRef)]
        sub_ts.update(res)
        for t in res:
            sub_ts.update(get_subtypes(t, vid))

        res = [qname(r[0]) for r in
               context.query("""SELECT ?r WHERE { ?d owl:onProperty %s. ?d owl:someValuesFrom ?r.}""" % prop)
               if isinstance(r[0], URIRef)]
        sub_ts.update(res)
        for t in res:
            sub_ts.update(get_subtypes(t, vid))

        res = [qname(r[0]) for r in
               context.query("""SELECT ?r WHERE { ?d owl:onProperty %s. ?d owl:onClass ?r.}""" % prop)
               if isinstance(r[0], URIRef)]
        sub_ts.update(res)
        for t in res:
            sub_ts.update(get_subtypes(t, vid))
    else:
        sub_ts.update([qname(r) for r in res])
        sub_ts.update([qname(r[0]) for r in
                       context.query("""SELECT ?r WHERE { ?d owl:onProperty %s. ?d owl:onDataRange ?r}""" % prop)
                       if isinstance(r[0], URIRef)])
    return sub_ts


def get_property_inverses(prop, vid=None):
    context = graph
    if vid is not None:
        context = context.get_context(vid)
    inverses = set([])
    inverses.update([qname(p) for p in context.objects(subject=_extend_prefixed(prop), predicate=OWL.inverseOf)
                     if isinstance(p, URIRef)])
    inverses.update([qname(p) for p in context.subjects(object=_extend_prefixed(prop), predicate=OWL.inverseOf)
                     if isinstance(p, URIRef)])

    return inverses


def get_supertypes(ty, vid=None):
    context = graph
    if vid is not None:
        context = context.get_context(vid)
    res = map(lambda x: qname(x), filter(lambda y: isinstance(y, URIRef),
                                         context.transitive_objects(_extend_prefixed(ty), RDFS.subClassOf)))
    return filter(lambda x: str(x) != ty, res)


def get_subtypes(ty, vid=None):
    context = graph
    if vid is not None:
        context = context.get_context(vid)
    res = map(lambda x: qname(x), filter(lambda y: isinstance(y, URIRef),
                                         context.transitive_subjects(RDFS.subClassOf, _extend_prefixed(ty))))

    return filter(lambda x: str(x) != ty, res)


def get_type_properties(ty, vid=None):
    context = graph
    if vid is not None:
        context = context.get_context(vid)
    res = set([])
    res.update(map(lambda x: qname(x), context.subjects(RDFS.domain, _extend_prefixed(ty))))
    res.update(
        [qname(p[0]) for p in context.query("""SELECT ?p WHERE {%s rdfs:subClassOf [ owl:onProperty ?p ]}""" % ty)
         if isinstance(p[0], URIRef)])
    for sc in get_supertypes(ty, vid):
        res.update(map(lambda x: qname(x), context.subjects(RDFS.domain, _extend_prefixed(sc))))

        res.update(
            [qname(p[0]) for p in context.query("""SELECT ?p WHERE {%s rdfs:subClassOf [ owl:onProperty ?p ]}""" % sc)
             if isinstance(p[0], URIRef)])

    return res


def get_type_references(ty, vid=None):
    context = graph
    if vid is not None:
        context = context.get_context(vid)
    query = """SELECT ?p WHERE { ?p rdfs:range %s }"""
    res = set([])
    res.update(map(lambda x: qname(x[0]), context.query(query % ty)))
    for sc in get_supertypes(ty, vid):
        res.update(map(lambda x: qname(x[0]), context.query(query % sc)))

    res.update([qname(x[0]) for x in context.query("""SELECT ?p WHERE {?r owl:onProperty ?p.
                                                                    {?r owl:someValuesFrom %s} UNION
                                                                    {?r owl:allValuesFrom %s} UNION
                                                                    {?r owl:onClass %s} .}""" % (ty, ty, ty))])
    return res
