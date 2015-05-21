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
            y = c or d
            yield sem_g.qname(y)

    @staticmethod
    def get_property_domain(prop):
        res = map(lambda x: sem_g.qname(x), sem_g.objects(extend_prefixed(prop), RDFS.domain))
        dom = set([])
        for t in res:
            dom.update(Schema.get_subtypes(t))
            dom.add(t)
        return dom

    @staticmethod
    def is_object_property(prop):
        type_res = sem_g.query("""ASK {%s a owl:ObjectProperty}""" % prop)
        return [_ for _ in type_res].pop()

    @staticmethod
    def get_property_range(prop):
        if Schema.is_object_property(prop):
            res = map(lambda (t, x): t or x, sem_g.query("""SELECT ?t ?x WHERE { {%s rdfs:range [ owl:someValuesFrom ?t] } UNION
                                     {%s rdfs:range [ owl:onClass ?x] } . }""" % (prop, prop)))
            sub_ts = set([])
            for y in res:
                sub_ts.update(map(lambda z: sem_g.qname(z), sem_g.transitive_subjects(RDFS.subClassOf, y)))
                sub_ts.add(sem_g.qname(y))
            return sub_ts
        else:
            return map(lambda w: sem_g.qname(w), sem_g.objects(extend_prefixed(prop), RDFS.range))

    @staticmethod
    def get_supertypes(ty):
        res = map(lambda x: str(x.n3(sem_g.namespace_manager)),
                  sem_g.transitive_objects(extend_prefixed(ty), RDFS.subClassOf))
        return filter(lambda x: str(x) != ty, res)

    @staticmethod
    def get_subtypes(ty):
        res = map(lambda x: x.n3(sem_g.namespace_manager),
                  sem_g.transitive_subjects(RDFS.subClassOf, extend_prefixed(ty)))

        return filter(lambda x: str(x) != ty, res)

    @staticmethod
    def get_type_properties(ty):
        res = map(lambda x: sem_g.qname(x), sem_g.subjects(RDFS.domain, extend_prefixed(ty)))
        for sc in Schema.get_supertypes(ty):
            res.extend(map(lambda x: sem_g.qname(x), sem_g.subjects(RDFS.domain, extend_prefixed(sc))))

        return res

    @staticmethod
    def get_type_references(ty):
        query = """SELECT ?p WHERE { {?p rdfs:range [ owl:someValuesFrom %s]} UNION
                                      {?p rdfs:range [owl:onClass %s]}}"""
        res = map(lambda x: sem_g.qname(x[0]), sem_g.query(query % (ty, ty)))
        for sc in Schema.get_supertypes(ty):
            res.extend(map(lambda x: sem_g.qname(x[0]), sem_g.query(query % (sc, sc))))

        return res
