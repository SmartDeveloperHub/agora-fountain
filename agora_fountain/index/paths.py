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

from agora_fountain.index import core as index


def build_property_paths(prop):
    paths = []
    domain = index.get_property(prop).get('domain')
    for ty in domain:
        path = [{'type': ty, 'property': prop}]
        refs = index.get_type(ty).get('refs')
        if not len(refs):
            paths.append(path)
        for r in refs:
            sub_paths = build_property_paths(r)
            for sp in sub_paths:
                new_path = path[:]
                new_path.extend(sp)
                paths.append(new_path)

    return paths


def build_type_paths(ty):
    def build_path(refs):
        for r in refs:
            yield build_property_paths(r)

    paths = list([])
    type_rep = index.get_type(ty)
    ty_refs = type_rep.get('refs')
    for p in build_path(ty_refs):
        paths.extend(p)

    for sub in type_rep.get('sub'):
        refs = index.get_type(sub).get('refs')
        for p in build_path(refs):
            paths.extend(p)

    return paths


print 'Building paths for properties:'
properties = index.get_properties()
for p in properties:
    print 'Paths for {}:'.format(p)
    paths = build_property_paths(p)
    for path in paths:
        print path
    if len(paths):
        for i, path in enumerate(paths):
            index.r.set('paths:{}:{}'.format(p, i), path)

print 'Building paths for types:'
types = index.get_types()
for ty in types:
    print 'Paths for {}:'.format(ty)
    paths = build_type_paths(ty)
    for path in paths:
        print path
    if len(paths):
        for i, path in enumerate(paths):
            index.r.set('paths:{}:{}'.format(ty, i), path)

print 'Ready.'
