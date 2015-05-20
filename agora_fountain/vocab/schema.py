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
import os
from rdflib_virtuoso.vstore import VirtuosoStore
from rdflib import ConjunctiveGraph, URIRef
from rdflib.namespace import FOAF, DC
from StringIO import StringIO

sem_g = ConjunctiveGraph()
sem_path = '%(here)s/semantics.owl' % {"here": os.getcwd()}
sem_g.get_context(URIRef("http://sdh/ontology#skeleton")).load(sem_path, format='turtle')


def upload_ontology(g):
    skolem_onto = sem_g.skolemize().serialize(format='turtle')
    g.get_context(URIRef("http://sdh/ontology#skeleton")).remove((None, None, None))
    g.get_context(URIRef("http://sdh/ontology#skeleton")).parse(StringIO(skolem_onto), format='turtle')
    print g.get_context(URIRef("http://sdh/ontology#skeleton")).serialize(format='turtle')

vstore = VirtuosoStore('http://localhost:8890/sparql', 'http://sdh/ontology#skeleton')
graph = ConjunctiveGraph(vstore)

onto_graph = graph.get_context('http://sdh/ontology#skeleton')
onto_graph.namespace_manager.bind('sdh', 'http://sdh/ontology#')
onto_graph.namespace_manager.bind('foaf', FOAF)
onto_graph.namespace_manager.bind('dc', DC)


subjects = onto_graph.query('ASK {?s a ?Concept}')
any_concept = [_ for _ in subjects].pop()

# if not any_concept:
upload_ontology(graph)

namespaces = dict([(uri, prefix) for (prefix, uri) in onto_graph.namespaces()])


def prefix_uri(uri):
    for k in namespaces.keys():
        try:
            if uri.startswith(k):
                return '{}:{}'.format(namespaces.get(k), uri.replace(k, ''))
        except Exception:
            pass
    return uri


class Schema(object):
    def __init__(self):
        pass

    @property
    def prefixes(self):
        return list(onto_graph.namespaces())

    @property
    def types(self):
        res = onto_graph.query("SELECT ?c WHERE { ?c a owl:Class }")
        for st in res:
            yield prefix_uri(st[0])

    @property
    def properties(self):
        res = onto_graph.query("SELECT ?c ?d WHERE { {?c a owl:ObjectProperty} UNION {?d a owl:DatatypeProperty} }")
        for (c, d) in res:
            y = c
            if y is None:
                y = d
            yield prefix_uri(y)

    @staticmethod
    def get_property_domain(prop):
        res = onto_graph.query("""SELECT ?t ?c WHERE { %s rdfs:domain ?t . %s a ?c . }""" % (prop, prop))
        for (t, c) in res:
            yield prefix_uri(t)
            sub_ts = onto_graph.query("SELECT ?c WHERE { ?c rdfs:subClassOf <%s> OPTION(TRANSITIVE) }" % str(t))
            for st in sub_ts:
                yield prefix_uri(st[0])

    @staticmethod
    def is_object_property(prop):
        type_res = onto_graph.query("""ASK {%s a owl:ObjectProperty OPTION(TRANSITIVE)}""" % prop)
        return [_ for _ in type_res].pop()

    @staticmethod
    def get_property_range(prop):
        type_res = onto_graph.query("""ASK {%s a owl:ObjectProperty OPTION(TRANSITIVE)}""" % prop)
        is_object = [_ for _ in type_res].pop()

        if is_object:
            res = onto_graph.query("""SELECT ?t ?x WHERE { {%s rdfs:range [ owl:someValuesFrom ?t] } UNION
                                     {%s rdfs:range [ owl:onClass ?x] } . }""" % (prop, prop))
            for (t, x) in res:
                y = x
                if t is not None:
                    y = t
                yield prefix_uri(y)
                sub_ts = onto_graph.query("SELECT ?c WHERE { ?c rdfs:subClassOf <%s> OPTION(TRANSITIVE) }" % str(y))
                for st in sub_ts:
                    yield prefix_uri(st[0])
        else:
            res = onto_graph.query("""SELECT ?d WHERE { %s rdfs:range ?d }""" % prop)
            for d in res:
                yield prefix_uri(d[0])

    @staticmethod
    def get_supertypes(ty):
        res = onto_graph.query("SELECT ?c WHERE { %s rdfs:subClassOf ?c OPTION(TRANSITIVE) }" % ty)
        for st in res:
            yield prefix_uri(st[0])

    @staticmethod
    def get_subtypes(ty):
        res = onto_graph.query("SELECT ?c WHERE { ?c rdfs:subClassOf %s OPTION(TRANSITIVE) }" % ty)
        for st in res:
            yield prefix_uri(st[0])

    @staticmethod
    def get_type_properties(ty):
        res = onto_graph.query("""SELECT ?p WHERE { ?p rdfs:domain %s OPTION(TRANSITIVE) }""" % ty)
        for st in res:
            yield prefix_uri(st[0])

        for sc in Schema.get_supertypes(ty):
            res = onto_graph.query("""SELECT ?p WHERE { ?p rdfs:domain %s OPTION(TRANSITIVE) }""" % sc)
            for st in res:
                yield prefix_uri(st[0])

    @staticmethod
    def get_type_references(ty):
        query = """SELECT ?p WHERE { {?p rdfs:range [ owl:someValuesFrom %s]} UNION
                                      {?p rdfs:range [owl:onClass %s]}}"""
        res = onto_graph.query(query % (ty, ty))
        for st in res:
            yield prefix_uri(st[0])

        for sc in Schema.get_supertypes(ty):
            res = onto_graph.query(query % (sc, sc))
            for st in res:
                yield prefix_uri(st[0])
