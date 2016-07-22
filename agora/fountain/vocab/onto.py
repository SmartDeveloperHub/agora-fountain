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
import logging
import urlparse

from rdflib import Graph, RDF
from rdflib.namespace import OWL
from rdflib.plugins.parsers.notation3 import BadSyntax

import agora.fountain.vocab.schema as sch

__author__ = 'Fernando Serena'

log = logging.getLogger('agora.fountain.onto')


class VocabularyException(Exception):
    pass


class DuplicateVocabulary(VocabularyException):
    pass


class VocabularyNotFound(VocabularyException):
    pass


class UnknownVocabulary(VocabularyException):
    pass


def __load_owl(owl):
    """

    :param owl: The ontology to be loaded to the fountain
    :return:
    """
    owl_g = Graph()
    for f in ['turtle', 'xml']:
        try:
            owl_g.parse(source=StringIO.StringIO(owl), format=f)
            log.debug('Parsed ontology in {} format'.format(f))
            break
        except SyntaxError:
            pass

    if not len(owl_g):
        raise VocabularyException()

    found_ontos = list(owl_g.subjects(RDF.type, OWL.Ontology))
    if len(found_ontos) != 1:
        raise VocabularyNotFound("Incorrect number of ontology statements: {}".format(len(found_ontos)))

    uri = found_ontos.pop()

    vid = [p for (p, u) in owl_g.namespaces() if uri in u and p != '']
    imports = owl_g.objects(uri, OWL.imports)
    if not len(vid):
        vid = urlparse.urlparse(uri).path.split('/')[-1]
    else:
        vid = vid.pop()

    # (identifier, ontology uri, graph, imports)
    return vid, uri, owl_g, imports


def add_vocabulary(owl):
    """

    :param owl:
    :return:
    """
    vid, uri, owl_g, imports = __load_owl(owl)

    if vid in sch.contexts():
        raise DuplicateVocabulary('Vocabulary already contained')

    sch.add_context(vid, owl_g)
    vids = [vid]

    # Add imported vocabularies
    for im_uri in imports:
        log.debug('Importing {} from {}...'.format(im_uri, vid))
        im_g = Graph()
        try:
            im_g.load(im_uri, format='turtle')
        except BadSyntax:
            try:
                im_g.load(im_uri)
            except BadSyntax:
                log.error('bad syntax in {}'.format(im_uri))

        try:
            child_vids = add_vocabulary(im_g.serialize(format='turtle'))
            vids.extend(child_vids)
        except DuplicateVocabulary, e:
            log.debug('vocabulary already added: {}'.format(im_uri))
        except VocabularyNotFound, e:
            log.warning('uri not found for {}'.format(im_uri))
        except Exception, e:
            log.error(e.message)

    return vids


def update_vocabulary(vid, owl):
    """

    :param vid:
    :param owl:
    :return:
    """
    owl_vid, uri, owl_g, imports = __load_owl(owl)

    if vid != owl_vid:
        raise Exception("Identifiers don't match")

    if vid not in sch.contexts():
        raise UnknownVocabulary('Vocabulary id is not known')

    sch.update_context(vid, owl_g)


def delete_vocabulary(vid):
    """

    :param vid:
    :return:
    """
    if vid not in sch.contexts():
        raise UnknownVocabulary('Vocabulary id is not known')

    sch.remove_context(vid)


def get_vocabularies():
    """

    :return:
    """
    return sch.contexts()


def get_vocabulary(vid):
    """

    :param vid:
    :return:
    """
    return sch.get_context(vid).serialize(format='turtle')
