#!/usr/bin/python
# -*- coding: utf-8 -*
import json
import codecs


def write_file(data, file_name):
    file = codecs.open(file_name, 'w', encoding='utf-8')
    file.write(data)
    file.close()

for file_name in ['kcc/councilors_terms.json', 'tcc/councilors.json', 'tcc/councilors_terms.json', 'tcc/meeting_minutes-11.json', 'tcc/bills-11.json', 'tncc/tnccp.json']:
    objs = json.load(open(file_name))
    dump_data = json.dumps(objs, sort_keys=True, indent=4, ensure_ascii=False)
    write_file(dump_data, 'pretty_format/%s' % file_name)
