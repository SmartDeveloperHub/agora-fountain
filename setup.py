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

import json

from setuptools import setup, find_packages

__author__ = 'Fernando Serena'

with open("agora/fountain/metadata.json", 'r') as stream:
    metadata = json.load(stream)

setup(
    name="Agora-Fountain",
    version=metadata['version'],
    author=metadata['author'],
    author_email=metadata['email'],
    description=metadata['description'],
    license="Apache 2",
    keywords=["linked-data", "ontology", "path"],
    url=metadata['github'],
    download_url="https://github.com/smartdeveloperhub/agora-fountain/tarball/0.5.1-alpha1",
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['agora', 'agora.fountain'],
    install_requires=['flask', 'Flask-Negotiate', 'redis', 'hiredis', 'rdflib', 'networkx',
                      'futures',
                      'rfc3987'],
    classifiers=[],
    scripts=['fountain'],
    package_dir={'agora.fountain': 'agora/fountain', 'agora.fountain.server': 'agora/fountain/server'},
    package_data={'agora.fountain.server': ['templates/*.*', 'static/*.*'], 'agora.fountain': ['metadata.json']},
)
