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
import os
from rdflib import ConjunctiveGraph, URIRef, BNode
from rdflib.namespace import FOAF, DC, OWL, RDF, RDFS, XSD

print 'Loading ontology...',
sem_g = ConjunctiveGraph()
sem_path = '%(here)s/semantics.owl' % {"here": os.getcwd()}
sem_g.load(sem_path, format='turtle')
# sem_g.namespace_manager.bind('sdh', 'http://sdh/ontology#')
sem_g.namespace_manager.bind('scm', 'http://www.smartdeveloperhub.org/vocabulary/sdh/v1/scm#')
sem_g.namespace_manager.bind('foaf', FOAF)
sem_g.namespace_manager.bind('dc', DC)
sem_g.namespace_manager.bind('xsd', XSD)
sem_g.namespace_manager.bind('doap', 'http://usefulinc.com/ns/doap#')

namespaces = dict([(uri, prefix) for (prefix, uri) in sem_g.namespaces()])
prefixes = dict([(prefix, uri) for (prefix, uri) in sem_g.namespaces()])

print sem_g.serialize(format='turtle')

print 'Done.'


def qname(uri):
    q = uri.n3(sem_g.namespace_manager)
    # if ':' not in q:
    #     q = ':' + q
    return q

def extend_prefixed(pu):
    parts = pu.split(':')
    if len(parts) == 1:
        parts = ('', parts[0])
    try:
        return URIRef(prefixes[parts[0]] + parts[1])
    except KeyError:
        return BNode(pu)


class Schema(object):
    def __init__(self):
        pass

    @property
    def prefixes(self):
        return list(sem_g.namespaces())

    @property
    def types(self):
        res = set([])
        res.update([qname(x) for x in sem_g.subjects(RDF.type, OWL.Class) if isinstance(x, URIRef)])
        res.update([qname(x[0]) for x in
                    sem_g.query("""SELECT ?o WHERE {?p a owl:ObjectProperty. ?p rdfs:range ?o .}""")
                    if isinstance(x[0], URIRef)])
        res.update([qname(x) for x in sem_g.objects(predicate=RDFS.domain) if isinstance(x, URIRef)])
        res.update([qname(x[0]) for x in sem_g.query("""SELECT DISTINCT ?c WHERE {{?r owl:allValuesFrom ?c}
                                                        UNION {?a owl:someValuesFrom ?c}
                                                        UNION {?b owl:onClass ?c}}""")])

        return res

    @property
    def properties(self):
        res = set([])
        res.update([qname(c or d) for (c, d) in
                    sem_g.query("SELECT ?c ?d WHERE { {?c a owl:ObjectProperty} UNION {?d a owl:DatatypeProperty} }")])
        res.update([qname(p[0]) for p in sem_g.query("SELECT ?p WHERE { ?r a owl:Restriction. ?r owl:onProperty ?p }")])

        return res

    @staticmethod
    def get_property_domain(prop):
        res = map(lambda x: qname(x), sem_g.objects(extend_prefixed(prop), RDFS.domain))
        dom = set([])
        for t in res:
            dom.update(Schema.get_subtypes(t))
            dom.add(t)
        dom.update([qname(c[0])
                    for c in sem_g.query("""SELECT ?c WHERE { ?c rdfs:subClassOf [ owl:onProperty %s ]}""" % prop)])
        return dom

    @staticmethod
    def is_object_property(prop):
        type_res = sem_g.query("""ASK {%s a owl:ObjectProperty}""" % prop)
        is_object = [_ for _ in type_res].pop()

        if not is_object:
            is_object = [_ for _ in
                         sem_g.query("""ASK {?r owl:onProperty %s.
                                        {?r owl:someValuesFrom ?o} UNION
                                        {?r owl:allValuesFrom ?a} UNION
                                        {?r owl:onClass ?c} .}""" % prop)].pop()

        return is_object

    @staticmethod
    def get_property_range(prop):
        sub_ts = set([])
        res = [t for t in sem_g.objects(subject=extend_prefixed(prop), predicate=RDFS.range)
               if isinstance(t, URIRef)]

        if Schema.is_object_property(prop):
            for y in res:
                sub_ts.update([qname(z) for z in sem_g.transitive_subjects(RDFS.subClassOf, y)
                               if isinstance(z, URIRef)])
                sub_ts.add(qname(y))
            sub_ts.update([qname(r[0]) for r in
                           sem_g.query("""SELECT ?d WHERE { ?r owl:onProperty %s. ?r owl:allValuesFrom ?d.}""" % prop)])
            sub_ts.update([qname(r[0]) for r in
                           sem_g.query("""SELECT ?d WHERE { ?r owl:onProperty %s. ?r owl:someValuesFrom ?d.}""" % prop)])
            sub_ts.update([qname(r[0]) for r in
                           sem_g.query("""SELECT ?d WHERE { ?r owl:onProperty %s. ?r owl:onClass ?d.}""" % prop)])
        else:
            sub_ts.update([qname(r) for r in res])
            sub_ts.update([qname(r[0]) for r in
                           sem_g.query("""SELECT ?d WHERE { ?r owl:onProperty %s. ?r owl:onDataRange ?d}""" % prop)])
        return sub_ts

    @staticmethod
    def get_supertypes(ty):
        res = map(lambda x: qname(x), filter(lambda y: isinstance(y, URIRef),
                  sem_g.transitive_objects(extend_prefixed(ty), RDFS.subClassOf)))
        return filter(lambda x: str(x) != ty, res)

    @staticmethod
    def get_subtypes(ty):
        res = map(lambda x: qname(x), filter(lambda y: isinstance(y, URIRef),
                  sem_g.transitive_subjects(RDFS.subClassOf, extend_prefixed(ty))))

        return filter(lambda x: str(x) != ty, res)

    @staticmethod
    def get_type_properties(ty):
        res = set([])
        res.update(map(lambda x: qname(x), sem_g.subjects(RDFS.domain, extend_prefixed(ty))))
        for sc in Schema.get_supertypes(ty):
            res.update(map(lambda x: qname(x), sem_g.subjects(RDFS.domain, extend_prefixed(sc))))

        res.update([qname(p[0]) for p in sem_g.query("""SELECT ?p WHERE {%s rdfs:subClassOf [ owl:onProperty ?p ]}""" % ty)
                    if isinstance(p[0], URIRef)])

        return res

    @staticmethod
    def get_type_references(ty):
        query = """SELECT ?p WHERE { ?p rdfs:range %s }"""
        res = set([])
        res.update(map(lambda x: qname(x[0]), sem_g.query(query % ty)))
        for sc in Schema.get_supertypes(ty):
            res.update(map(lambda x: qname(x[0]), sem_g.query(query % sc)))

        res.update([qname(x[0]) for x in sem_g.query("""SELECT ?p WHERE {?r owl:onProperty ?p.
                                                                        {?r owl:someValuesFrom %s} UNION
                                                                        {?r owl:allValuesFrom %s} UNION
                                                                        {?r owl:onClass %s} .}""" % (ty, ty, ty))])

        return res
