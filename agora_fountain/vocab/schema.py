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
from rdflib import ConjunctiveGraph, URIRef
from rdflib.namespace import FOAF, DC, OWL, RDF, RDFS

sem_g = ConjunctiveGraph()
sem_path = '%(here)s/semantics.owl' % {"here": os.getcwd()}
sem_g.load(sem_path, format='turtle')
sem_g.namespace_manager.bind('sdh', 'http://sdh/ontology#')
sem_g.namespace_manager.bind('foaf', FOAF)
sem_g.namespace_manager.bind('dc', DC)

namespaces = dict([(uri, prefix) for (prefix, uri) in sem_g.namespaces()])
prefixes = dict([(prefix, uri) for (prefix, uri) in sem_g.namespaces()])


def extend_prefixed(pu):
    (p, u) = pu.split(':')
    return URIRef(prefixes[p] + u)

class Schema(object):
    def __init__(self):
        pass

    @property
    def prefixes(self):
        return list(sem_g.namespaces())

    @property
    def types(self):
        return map(lambda x: sem_g.qname(x), sem_g.subjects(RDF.type, OWL.Class))

    @property
    def properties(self):
        res = sem_g.query("SELECT ?c ?d WHERE { {?c a owl:ObjectProperty} UNION {?d a owl:DatatypeProperty} }")
        for (c, d) in res:
            y = c
            if y is None:
                y = d
            yield sem_g.qname(y)

    @staticmethod
    def get_property_domain(prop):
        res = sem_g.query("""SELECT ?t ?c WHERE { %s rdfs:domain ?t . %s a ?c . }""" % (prop, prop))
        for (t, c) in res:
            yield sem_g.qname(t)
            sub_ts = sem_g.transitive_subjects(RDFS.subClassOf, t)
            for st in sub_ts:
                yield sem_g.qname(st)

    @staticmethod
    def is_object_property(prop):
        type_res = sem_g.query("""ASK {%s a owl:ObjectProperty}""" % prop)
        return [_ for _ in type_res].pop()

    @staticmethod
    def get_property_range(prop):
        type_res = sem_g.query("""ASK {%s a owl:ObjectProperty}""" % prop)
        is_object = [_ for _ in type_res].pop()

        if is_object:
            res = sem_g.query("""SELECT ?t ?x WHERE { {%s rdfs:range [ owl:someValuesFrom ?t] } UNION
                                     {%s rdfs:range [ owl:onClass ?x] } . }""" % (prop, prop))
            for (t, x) in res:
                y = x
                if t is not None:
                    y = t
                yield sem_g.qname(y)
                sub_ts = sem_g.transitive_subjects(RDFS.subClassOf, y)
                for st in sub_ts:
                    yield sem_g.qname(st)
        else:
            res = sem_g.query("""SELECT ?d WHERE { %s rdfs:range ?d }""" % prop)
            for d in res:
                yield sem_g.qname(d[0])

    @staticmethod
    def get_supertypes(ty):
        res = map(lambda x: x.n3(sem_g.namespace_manager), sem_g.transitive_objects(extend_prefixed(ty),
                                                                                    RDFS.subClassOf))
        return filter(lambda x: str(x) != ty, res)

    @staticmethod
    def get_subtypes(ty):
        res = map(lambda x: x.n3(sem_g.namespace_manager), sem_g.transitive_subjects(RDFS.subClassOf,
                                                                                     extend_prefixed(ty)))

        return filter(lambda x: str(x) != ty, res)

    @staticmethod
    def get_type_properties(ty):
        res = sem_g.subjects(RDFS.domain, extend_prefixed(ty))
        for st in res:
            yield sem_g.qname(st)

        for sc in Schema.get_supertypes(ty):
            res = sem_g.subjects(RDFS.domain, extend_prefixed(sc))
            for st in res:
                yield sem_g.qname(st)

    @staticmethod
    def get_type_references(ty):
        query = """SELECT ?p WHERE { {?p rdfs:range [ owl:someValuesFrom %s]} UNION
                                      {?p rdfs:range [owl:onClass %s]}}"""
        res = sem_g.query(query % (ty, ty))
        for st in res:
            yield sem_g.qname(st[0])

        for sc in Schema.get_supertypes(ty):
            res = sem_g.query(query % (sc, sc))
            for st in res:
                yield sem_g.qname(st[0])
