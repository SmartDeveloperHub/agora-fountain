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
from rdflib.namespace import RDFS

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


def __flat_slice(lst):
    """

    :param lst:
    :return:
    """
    lst = list(lst)
    for i, _ in enumerate(lst):
        while hasattr(lst[i], "__iter__") and not isinstance(lst[i], basestring):
            lst[i:i + 1] = lst[i]
    return set(filter(lambda x: x is not None, lst))


def __q_name(uri):
    """

    :param uri:
    :return:
    """
    q = uri.n3(graph.namespace_manager)
    return q


def __extend_prefixed(pu):
    """

    :param pu:
    :return:
    """
    parts = pu.split(':')
    if len(parts) == 1:
        parts = ('', parts[0])
    try:
        return URIRef(_prefixes[parts[0]] + parts[1])
    except KeyError:
        return BNode(pu)


def prefixes(vid=None):
    """

    :param vid:
    :return:
    """
    context = graph
    if vid is not None:
        context = context.get_context(vid)
    return list(context.namespaces())


def contexts():
    """

    :return:
    """
    return [str(x.identifier) for x in graph.contexts()]


def update_context(vid, g):
    """

    :param vid:
    :param g:
    :return:
    """
    context = graph.get_context(vid)
    graph.remove_context(context)
    add_context(vid, g)


def remove_context(vid):
    """

    :param vid:
    :return:
    """
    context = graph.get_context(vid)
    graph.remove_context(context)


def get_context(vid):
    """

    :param vid:
    :return:
    """
    return graph.get_context(vid)


def add_context(vid, g):
    """

    :param vid:
    :param g:
    :return:
    """
    vid_context = graph.get_context(vid)
    for t in g.triples((None, None, None)):
        vid_context.add(t)

    for (p, u) in g.namespaces():
        if p != '':
            vid_context.bind(p, u)

    _namespaces.update([(uri, prefix) for (prefix, uri) in graph.namespaces()])
    _prefixes.update([(prefix, uri) for (prefix, uri) in graph.namespaces()])


def get_types(vid=None):
    """

    :param vid:
    :return:
    """
    context = graph
    if vid is not None:
        context = context.get_context(vid)
    types = set([])
    q_class_result = context.query(
        """SELECT DISTINCT ?c ?x WHERE {
             {
               {?c a owl:Class}
               UNION
               {?c a rdfs:Class}
               FILTER(isURI(?c))
             }
             OPTIONAL
             {?c rdfs:subClassOf ?x FILTER(isURI(?x))}
           }""")
    classes_set = __flat_slice(q_class_result)
    types.update([__q_name(c) for c in classes_set])
    q_class_result = context.query(
        """SELECT DISTINCT ?r ?d WHERE {
             ?p a owl:ObjectProperty.
             {?p rdfs:range ?r FILTER(isURI(?r))}
             UNION
             {?p rdfs:domain ?d FILTER(isURI(?r))}
           }""")
    classes_set = __flat_slice(q_class_result)
    types.update([__q_name(c) for c in classes_set])
    types.update([__q_name(x[0]) for x in context.query(
        """SELECT DISTINCT ?c WHERE {
             {?r owl:allValuesFrom ?c}
             UNION
             {?a owl:someValuesFrom ?c}
             UNION
             {?b owl:onClass ?c}
             FILTER (isURI(?c))
           }""")])

    return types


def get_properties(vid=None):
    """

    :param vid:
    :return:
    """
    context = graph
    if vid is not None:
        context = context.get_context(vid)
    properties = set([])
    properties.update([__q_name(o or d) for (o, d) in
                       context.query(
                           """SELECT DISTINCT ?o ?d WHERE {
                                {?d a rdf:Property}
                                UNION
                                {?o a owl:ObjectProperty}
                                UNION
                                {?d a owl:DatatypeProperty}
                                UNION
                                {?r a owl:Restriction . ?r owl:onProperty ?o}
                              }""")])
    return properties


def get_property_domain(prop, vid=None):
    """

    :param prop:
    :param vid:
    :return:
    """
    context = graph
    if vid is not None:
        context = context.get_context(vid)
    dom = set([])
    domain_set = set([__q_name(c[0]) for c in context.query(
        """SELECT DISTINCT ?c WHERE {
             { %s rdfs:domain ?c }
             UNION
             { ?c rdfs:subClassOf [ owl:onProperty %s ] }
             FILTER (isURI(?c))
           }""" % (prop, prop))])
    dom.update(domain_set)
    for t in domain_set:
        dom.update(get_subtypes(t, vid))
    return dom


def is_object_property(prop, vid=None):
    """

    :param prop:
    :param vid:
    :return:
    """
    context = graph
    if vid is not None:
        context = context.get_context(vid)
    type_res = context.query("""ASK {%s a owl:ObjectProperty}""" % prop)
    object_evidence = [_ for _ in type_res].pop()

    if not object_evidence:
        object_evidence = [_ for _ in
                           context.query("""ASK {?r owl:onProperty %s.
                                    {?r owl:someValuesFrom ?o} UNION
                                    {?r owl:allValuesFrom ?a} UNION
                                    {?r owl:onClass ?c} .}""" % prop)].pop()
    return object_evidence


def get_property_range(prop, vid=None):
    """

    :param prop:
    :param vid:
    :return:
    """
    context = graph
    if vid is not None:
        context = context.get_context(vid)
    rang = set([])

    range_set = set([__q_name(r[0]) for r in context.query(
        """SELECT DISTINCT ?r WHERE {
             {%s rdfs:range ?r}
             UNION
             {?d owl:onProperty %s. ?d owl:allValuesFrom ?r. FILTER(isURI(?r))}
             UNION
             {?d owl:onProperty %s. ?d owl:someValuesFrom ?r. FILTER(isURI(?r))}
             UNION
             {?d owl:onProperty %s. ?d owl:onClass ?r. FILTER(isURI(?r))}
             UNION
             {?d owl:onProperty %s. ?d owl:onDataRange ?r. FILTER(isURI(?r))}
           }""" % (prop, prop, prop, prop, prop))])

    rang.update(range_set)
    for y in range_set:
        rang.update(get_subtypes(y, vid))
    return rang


def get_property_inverses(prop, vid=None):
    """

    :param prop:
    :param vid:
    :return:
    """
    context = graph
    if vid is not None:
        context = context.get_context(vid)
    inverses = set([])
    inverses.update([__q_name(i[0]) for i in context.query(
        """SELECT ?i WHERE {
             {%s owl:inverseOf ?i}
             UNION
             {?i owl:inverseOf %s}
           }""" % (prop, prop))])
    return inverses


def get_supertypes(ty, vid=None):
    """

    :param ty:
    :param vid:
    :return:
    """
    context = graph
    if vid is not None:
        context = context.get_context(vid)
    res = map(lambda x: __q_name(x), filter(lambda y: isinstance(y, URIRef),
                                            context.transitive_objects(__extend_prefixed(ty), RDFS.subClassOf)))
    return set(filter(lambda x: str(x) != ty, res))


def get_subtypes(ty, vid=None):
    """

    :param ty:
    :param vid:
    :return:
    """
    context = graph
    if vid is not None:
        context = context.get_context(vid)
    res = map(lambda x: __q_name(x), filter(lambda y: isinstance(y, URIRef),
                                            context.transitive_subjects(RDFS.subClassOf, __extend_prefixed(ty))))

    return filter(lambda x: str(x) != ty, res)


def get_type_properties(ty, vid=None):
    """

    :param ty:
    :param vid:
    :return:
    """
    context = graph
    if vid is not None:
        context = context.get_context(vid)
    props = set([])
    all_types = get_supertypes(ty, vid)
    all_types.add(ty)
    for sc in all_types:
        props.update(
            [__q_name(p[0]) for p in context.query(
                """SELECT ?p WHERE {
                     {%s rdfs:subClassOf [ owl:onProperty ?p ]}
                     UNION
                     {?p rdfs:domain %s}
                     FILTER (isURI(?p))
                   }""" % (sc, sc))])
    return props


def get_type_references(ty, vid=None):
    """

    :param ty:
    :param vid:
    :return:
    """
    context = graph
    if vid is not None:
        context = context.get_context(vid)
    refs = set([])
    all_types = get_supertypes(ty, vid)
    all_types.add(ty)
    for sc in all_types:
        refs.update(
            [__q_name(p[0]) for p in context.query(
                """SELECT ?p WHERE {
                    { ?r owl:onProperty ?p.
                      {?r owl:someValuesFrom %s}
                      UNION
                      {?r owl:allValuesFrom %s}
                      UNION
                      {?r owl:onClass %s}
                    }
                    UNION
                    {?p rdfs:range %s}
                    FILTER (isURI(?p))
                  }""" % (sc, sc, sc, sc))])
    return refs
