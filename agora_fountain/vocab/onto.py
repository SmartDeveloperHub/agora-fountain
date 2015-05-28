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

from rdflib import Graph, RDF
from rdflib.namespace import OWL
import StringIO
import agora_fountain.vocab.schema as sch

class VocabularyException(Exception):
    def __init__(self, message):
        Exception.__init__(self)
        self.message = message

class DuplicateVocabulary(VocabularyException):
    def __init__(self, message):
        Exception.__init__(self)
        self.message = message

class UnknownVocabulary(VocabularyException):
    def __init__(self, message):
        Exception.__init__(self)
        self.message = message


def __load_owl(owl):
    owl_g = Graph()
    owl_g.parse(source=StringIO.StringIO(owl), format='turtle')

    uri = list(owl_g.subjects(RDF.type, OWL.Ontology)).pop()
    vid = [p for (p, u) in owl_g.namespaces() if uri in u and p != ''].pop()
    return vid, uri, owl_g


def add_vocabulary(owl):
    vid, uri, owl_g = __load_owl(owl)

    if vid in sch.contexts():
        raise DuplicateVocabulary('Vocabulary already contained')

    sch.add_context(vid, owl_g)
    return vid

def update_vocabulary(vid, owl):
    owl_vid, uri, owl_g = __load_owl(owl)

    if vid != owl_vid:
        raise Exception("Identifiers don't match")

    if vid not in sch.contexts():
        raise UnknownVocabulary('Vocabulary id is not known')

    sch.update_context(vid, owl_g)

def delete_vocabulary(vid):
    if vid not in sch.contexts():
        raise UnknownVocabulary('Vocabulary id is not known')

    sch.remove_context(vid)

def get_vocabularies():
    return sch.contexts()

def get_vocabulary(vid):
    return sch.get_context(vid).serialize(format='turtle')
