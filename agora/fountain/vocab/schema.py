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

import logging
from functools import wraps

from rdflib import ConjunctiveGraph, URIRef, BNode
from rdflib.graph import Graph
from rdflib.namespace import RDFS

from agora.fountain.cache import Cache, cached
from agora.fountain.server import app

__author__ = 'Fernando Serena'

log = logging.getLogger('agora.fountain.schema')
cache = Cache()


class ContextGraph(ConjunctiveGraph):
    def __init__(self, store='default', identifier=None):
        super(ContextGraph, self).__init__(store, identifier)

    def query(self, q, **kwargs):
        if q not in cache:
            r = set(super(ContextGraph, self).query(q))
            cache[q] = r
        return cache[q]

    def remove_context(self, context):
        super(ContextGraph, self).remove_context(context)
        return cache.clear()


store_mode = app.config['STORE']
if 'persist' in store_mode:
    graph = ContextGraph('Sleepycat')
    graph.open('graph_store', create=True)
else:
    graph = ConjunctiveGraph()

graph.store.graph_aware = False
log.debug('\n{}'.format(graph.serialize(format='turtle')))
log.info('Vocabulary loaded')

_namespaces = {}
_prefixes = {}


def __context(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        context = kwargs.get('context', None)
        if not isinstance(context, Graph):
            kwargs['context'] = graph.get_context(context) if context is not None else graph

        return f(*args, **kwargs)

    return cached(cache)(wrap)


def __flat_slice(lst):
    """

    :param lst:
    :return:
    """
    lst = filter(lambda x: x, list(lst))
    for i, _ in enumerate(lst):
        while hasattr(lst[i], "__iter__") and not isinstance(lst[i], basestring):
            lst[i:i + 1] = lst[i]
    return set(filter(lambda x: x is not None, lst))


def __q_name(term):
    """

    :param term:
    :return:
    """
    n3_method = getattr(term, "n3", None)
    if callable(n3_method):
        return term.n3(graph.namespace_manager)
    return term


def __query(g, q):
    result = g.query(q)
    return set([__q_name(x) for x in __flat_slice(result)])


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


def __extend_with(f, context, *args):
    args = __flat_slice(args)
    extension = __flat_slice([f(t, context=context) for t in args])
    return set.union(args, extension)


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
    cache.clear()


@__context
def prefixes(context=None):
    """

    :param context:
    :return:
    """
    return dict(context.namespaces())


@__context
def get_types(context=None):
    """

    :param context:
    :return:
    """
    return __query(context,
                   """SELECT DISTINCT ?c WHERE {
                        {
                            ?p a owl:ObjectProperty .
                            {
                                { ?p rdfs:range ?c }
                                UNION
                                { ?p rdfs:domain ?c }
                            }
                        }
                        UNION
                        {
                            ?p a owl:DatatypeProperty .
                            ?p rdfs:domain ?c .
                        }
                        UNION
                        { ?c a owl:Class }
                        UNION
                        { ?c a rdfs:Class }
                        UNION
                        { [] rdfs:subClassOf ?c }
                        UNION
                        { ?c rdfs:subClassOf [] }
                        UNION
                        {
                            ?r a owl:Restriction ;
                               owl:onProperty ?p .
                            {
                                ?p a owl:ObjectProperty .
                                { ?r owl:allValuesFrom ?c }
                                UNION
                                { ?r owl:someValuesFrom ?c }
                            }
                            UNION
                            { ?r owl:onClass ?c }
                        }
                        FILTER(isURI(?c))
                      }""")


@__context
def get_properties(context=None):
    """

    :param context:
    :return:
    """
    return __query(context, """SELECT DISTINCT ?p WHERE {
                                { ?p a rdf:Property }
                                UNION
                                { ?p a owl:ObjectProperty }
                                UNION
                                { ?p a owl:DatatypeProperty }
                                UNION
                                {
                                    [] a owl:Restriction ;
                                       owl:onProperty ?p .
                                }
                                FILTER(isURI(?p))
                              }""")


@__context
def is_object_property(prop, context=None):
    """

    :param prop:
    :param context:
    :return:
    """
    evidence = __query(context, """ASK {
                                    { %s a owl:ObjectProperty }
                                    UNION
                                    {
                                        ?r owl:onProperty %s .
                                        {
                                            { ?c a owl:Class }
                                            UNION
                                            { ?c rdfs:subClassOf [] }
                                        }
                                        {
                                            {
                                               ?r owl:onClass ?c .
                                            }
                                            UNION
                                            {
                                                ?r owl:someValuesFrom ?c .
                                            }
                                            UNION
                                            {
                                                ?r owl:allValuesFrom ?c .
                                            }
                                        }
                                    }
                                   }""" % (prop, prop))

    return evidence.pop()


@__context
def get_property_domain(prop, context=None):
    """

    :param prop:
    :param context:
    :return:
    """
    all_property_domains = context.query("""SELECT DISTINCT ?p ?c WHERE {
                             { ?p rdfs:domain ?c }
                             UNION
                             { ?c rdfs:subClassOf [ owl:onProperty ?p ] }
                             FILTER (isURI(?p) && isURI(?c))
                           }""")

    dom = map(lambda x: __q_name(x.c), filter(lambda x: __q_name(x.p) == prop, all_property_domains))
    return __extend_with(get_subtypes, context, dom)


@__context
def get_property_range(prop, context=None):
    """

    :param prop:
    :param context:
    :return:
    """
    all_property_ranges = context.query("""SELECT DISTINCT ?p ?r WHERE {
                                  {?p rdfs:range ?r}
                                  UNION
                                  {
                                        ?d owl:onProperty ?p.
                                        { ?d owl:allValuesFrom ?r }
                                        UNION
                                        { ?d owl:someValuesFrom ?r }
                                        UNION
                                        { ?d owl:onClass ?r }
                                        UNION
                                        { ?d owl:onDataRange ?r }
                                  }
                                  FILTER(isURI(?p) && isURI(?r))
                                }""")

    rang = map(lambda x: __q_name(x.r), filter(lambda x: __q_name(x.p) == prop, all_property_ranges))
    return __extend_with(get_subtypes, context, rang)


@__context
def get_property_inverses(prop, context=None):
    """

    :param prop:
    :param context:
    :return:
    """
    return __query(context, """SELECT DISTINCT ?i WHERE {
                                 {%s owl:inverseOf ?i}
                                 UNION
                                 {?i owl:inverseOf %s}
                               }""" % (prop, prop))


@__context
def get_supertypes(ty, context=None):
    """

    :param ty:
    :param context:
    :return:
    """
    res = map(lambda x: __q_name(x), filter(lambda y: isinstance(y, URIRef),
                                            context.transitive_objects(__extend_prefixed(ty), RDFS.subClassOf)))
    return set(filter(lambda x: str(x) != ty, res))


@__context
def get_subtypes(ty, context=None):
    """

    :param ty:
    :param context:
    :return:
    """
    res = map(lambda x: __q_name(x), filter(lambda y: isinstance(y, URIRef),
                                            context.transitive_subjects(RDFS.subClassOf, __extend_prefixed(ty))))

    return filter(lambda x: str(x) != ty, res)


@__context
def get_type_properties(ty, context=None):
    """

    :param ty:
    :param context:
    :return:
    """
    all_class_props = context.query("""SELECT DISTINCT ?c ?p WHERE {
                                            {?c rdfs:subClassOf [ owl:onProperty ?p ]}
                                            UNION
                                            {?p rdfs:domain ?c}
                                            FILTER (isURI(?p) && isURI(?c))
                                          }""")

    all_types = __extend_with(get_supertypes, context, ty)
    return set([__q_name(r.p) for r in all_class_props if __q_name(r.c) in all_types])


@__context
def get_type_references(ty, context=None):
    """

    :param ty:
    :param context:
    :return:
    """
    all_class_props = context.query("""SELECT ?c ?p WHERE {
                                        { ?r owl:onProperty ?p.
                                          {?r owl:someValuesFrom ?c}
                                          UNION
                                          {?r owl:allValuesFrom ?c}
                                          UNION
                                          {?r owl:onClass ?c}
                                        }
                                        UNION
                                        {?p rdfs:range ?c}
                                        FILTER (isURI(?p) && isURI(?c))
                                       }""")

    all_types = __extend_with(get_supertypes, context, ty)
    return set([__q_name(r.p) for r in all_class_props if __q_name(r.c) in all_types])
