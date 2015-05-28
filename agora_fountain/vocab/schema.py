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
import StringIO
import time

__author__ = 'Fernando Serena'
import os
from rdflib import plugin, ConjunctiveGraph, URIRef, BNode, Graph
from rdflib.plugins.stores.concurrent import ConcurrentStore
from rdflib.store import Store
from rdflib.namespace import FOAF, DC, OWL, RDF, RDFS, XSD

from rdflib import plugin

print 'Loading ontology...',
# store_id = URIRef('rdflib_sqlite')
# store = plugin.get("SQLAlchemy", Store)(identifier=store_id)
# sem_g = ConjunctiveGraph(store, identifier=store_id)
# sem_g.open(URIRef('sqlite:///db.sqlite'), create=True)
# sem_g = ConjunctiveGraph(store='Sleepycat')
# store = plugin.get("Sleepycat", Store)(identifier=store_id)
# store = plugin.get("IOMemory", Store)()
# concurrent = plugin.get("Concurrent", Store)(store)
# sem_g = ConjunctiveGraph('Sleepycat')
sem_g = ConjunctiveGraph()
sem_g.store.graph_aware = False
# sem_g.open('graph_store', create=True)
print sem_g.serialize(format='turtle')

print 'Done.'

namespaces = {}
prefixes = {}


class SchemaException(Exception):
    def __init__(self, message):
        Exception.__init__(self)
        self.message = message

class DuplicateContext(SchemaException):
    def __init__(self, message):
        Exception.__init__(self)
        self.message = message

class UnknownContext(SchemaException):
    def __init__(self, message):
        Exception.__init__(self)
        self.message = message


def get_graph():
    g = ConjunctiveGraph(store='Sleepycat')
    g.open('graph_store', create=True)
    return g

def qname(uri):
    q = uri.n3(sem_g.namespace_manager)
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
        self.__graph = sem_g

    @staticmethod
    def get_prefixes(self):
        return list(self.__graph.namespaces())

    def get_types(self, vid=None):
        context = self.__graph
        if vid is not None:
            context = context.get_context(vid)
        res = set([])
        res.update([qname(x) for x in context.subjects(RDF.type, OWL.Class) if isinstance(x, URIRef)])
        res.update([qname(x[0]) for x in
                    context.query("""SELECT ?o WHERE {?p a owl:ObjectProperty. ?p rdfs:range ?o .}""")
                    if isinstance(x[0], URIRef)])
        res.update([qname(x) for x in context.objects(predicate=RDFS.domain) if isinstance(x, URIRef)])
        res.update([qname(x[0]) for x in context.query("""SELECT DISTINCT ?c WHERE {{?r owl:allValuesFrom ?c}
                                                        UNION {?a owl:someValuesFrom ?c}
                                                        UNION {?b owl:onClass ?c}}""")])

        return res

    def get_properties(self, vid=None):
        context = self.__graph
        if vid is not None:
            context = context.get_context(vid)
        res = set([])
        res.update([qname(c or d) for (c, d) in
                    context.query("SELECT ?c ?d WHERE { {?c a owl:ObjectProperty} UNION {?d a owl:DatatypeProperty} }")])
        res.update([qname(p[0]) for p in context.query("SELECT ?p WHERE { ?r a owl:Restriction. ?r owl:onProperty ?p }")])

        return res

    def get_property_domain(self, prop, vid=None):
        context = self.__graph
        if vid is not None:
            context = context.get_context(vid)
        res = map(lambda x: qname(x), context.objects(extend_prefixed(prop), RDFS.domain))
        dom = set([])
        for t in res:
            dom.update(self.get_subtypes(t, vid))
            dom.add(t)
        dom.update([qname(c[0])
                    for c in context.query("""SELECT ?c WHERE { ?c rdfs:subClassOf [ owl:onProperty %s ]}""" % prop)])
        return dom

    def is_object_property(self, prop, vid=None):
        context = self.__graph
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

    def get_property_range(self, prop, vid=None):
        context = self.__graph
        if vid is not None:
            context = context.get_context(vid)
        sub_ts = set([])
        res = [t for t in context.objects(subject=extend_prefixed(prop), predicate=RDFS.range)
               if isinstance(t, URIRef)]

        if self.is_object_property(prop, vid):
            for y in res:
                sub_ts.update([qname(z) for z in context.transitive_subjects(RDFS.subClassOf, y)
                               if isinstance(z, URIRef)])
                sub_ts.add(qname(y))
            sub_ts.update([qname(r[0]) for r in
                           context.query("""SELECT ?d WHERE { ?r owl:onProperty %s. ?r owl:allValuesFrom ?d.}""" % prop)])
            sub_ts.update([qname(r[0]) for r in
                           context.query("""SELECT ?d WHERE { ?r owl:onProperty %s. ?r owl:someValuesFrom ?d.}""" % prop)])
            sub_ts.update([qname(r[0]) for r in
                           context.query("""SELECT ?d WHERE { ?r owl:onProperty %s. ?r owl:onClass ?d.}""" % prop)])
        else:
            sub_ts.update([qname(r) for r in res])
            sub_ts.update([qname(r[0]) for r in
                           context.query("""SELECT ?d WHERE { ?r owl:onProperty %s. ?r owl:onDataRange ?d}""" % prop)])
        return sub_ts

    def get_supertypes(self, ty, vid=None):
        context = self.__graph
        if vid is not None:
            context = context.get_context(vid)
        res = map(lambda x: qname(x), filter(lambda y: isinstance(y, URIRef),
                  context.transitive_objects(extend_prefixed(ty), RDFS.subClassOf)))
        return filter(lambda x: str(x) != ty, res)

    def get_subtypes(self, ty, vid=None):
        context = self.__graph
        if vid is not None:
            context = context.get_context(vid)
        res = map(lambda x: qname(x), filter(lambda y: isinstance(y, URIRef),
                  context.transitive_subjects(RDFS.subClassOf, extend_prefixed(ty))))

        return filter(lambda x: str(x) != ty, res)

    def get_type_properties(self, ty, vid=None):
        context = self.__graph
        if vid is not None:
            context = context.get_context(vid)
        res = set([])
        res.update(map(lambda x: qname(x), context.subjects(RDFS.domain, extend_prefixed(ty))))
        for sc in self.get_supertypes(ty, vid):
            res.update(map(lambda x: qname(x), context.subjects(RDFS.domain, extend_prefixed(sc))))

        res.update([qname(p[0]) for p in context.query("""SELECT ?p WHERE {%s rdfs:subClassOf [ owl:onProperty ?p ]}""" % ty)
                    if isinstance(p[0], URIRef)])

        return res

    def get_type_references(self, ty, vid=None):
        context = self.__graph
        if vid is not None:
            context = context.get_context(vid)
        query = """SELECT ?p WHERE { ?p rdfs:range %s }"""
        res = set([])
        res.update(map(lambda x: qname(x[0]), context.query(query % ty)))
        for sc in self.get_supertypes(ty, vid):
            res.update(map(lambda x: qname(x[0]), context.query(query % sc)))

        res.update([qname(x[0]) for x in context.query("""SELECT ?p WHERE {?r owl:onProperty ?p.
                                                                        {?r owl:someValuesFrom %s} UNION
                                                                        {?r owl:allValuesFrom %s} UNION
                                                                        {?r owl:onClass %s} .}""" % (ty, ty, ty))])

        return res

    @staticmethod
    def __load_owl(owl):
        owl_g = Graph()
        owl_g.parse(source=StringIO.StringIO(owl), format='turtle')

        uri = list(owl_g.subjects(RDF.type, OWL.Ontology)).pop()
        vid = [p for (p, u) in owl_g.namespaces() if uri in u and p != ''].pop()
        return vid, uri, owl_g

    @staticmethod
    def add_vocabulary(owl):
        vid, uri, owl_g = Schema.__load_owl(owl)

        if len(filter(lambda x: str(x.identifier) == vid, sem_g.contexts())):
            raise DuplicateContext('Vocabulary already contained')

        owl_context = sem_g.get_context(vid)
        for t in owl_g.triples((None, None, None)):
            owl_context.add(t)

        for (p, u) in owl_g.namespaces():
            if p != '':
                owl_context.bind(p, u)

        namespaces.update([(uri, prefix) for (prefix, uri) in sem_g.namespaces()])
        prefixes.update([(prefix, uri) for (prefix, uri) in sem_g.namespaces()])

        return vid

    @staticmethod
    def update_vocabulary(vid, owl):
        owl_vid, uri, owl_g = Schema.__load_owl(owl)

        if vid != owl_vid:
            raise Exception("Identifiers don't match")

        if not len(filter(lambda x: str(x.identifier) == vid, sem_g.contexts())):
            raise UnknownContext('Vocabulary id is not known')

        context = sem_g.get_context(vid)
        sem_g.remove_context(context)
        for t in owl_g.triples((None, None, None)):
            context.add(t)

        for (p, u) in owl_g.namespaces():
            if p != '':
                context.bind(p, u)

    @staticmethod
    def delete_vocabulary(vid):
        if not len(filter(lambda x: str(x.identifier) == vid, sem_g.contexts())):
            raise UnknownContext('Vocabulary id is not known')

        context = sem_g.get_context(vid)
        sem_g.remove_context(context)

    @staticmethod
    def get_vocabularies():
        return map(lambda x: str(x.identifier), sem_g.contexts())

    @staticmethod
    def get_vocabulary(vid):
        return sem_g.get_context(URIRef(vid)).serialize(format='turtle')

