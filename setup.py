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

from setuptools import setup, find_packages

setup(
    name="Agora-Fountain",
    version="0.4.0-dev0",
    author="Fernando Serena",
    author_email="fernando.serena@centeropenmiddleware.com",
    description="The Agora core service for ontology paths discovery and seed management",
    license="Apache 2",
    keywords=["linked-data", "ontology", "path"],
    url="https://github.com/smartdeveloperhub/agora-fountain",
    download_url="https://github.com/smartdeveloperhub/agora-fountain/tarball/0.3.0-dev0",
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['agora'],
    install_requires=['flask', 'Flask-Negotiate', 'redis', 'hiredis', 'APScheduler', 'rdflib', 'networkx', 'futures',
                      'rfc3987'],
    classifiers=[],
    scripts=['fountain'],
    package_dir={'agora.fountain': 'agora/fountain', 'agora.fountain.server': 'agora/fountain/server'},
    package_data={'agora.fountain.server': ['templates/*.*', 'static/*.*']},
)
