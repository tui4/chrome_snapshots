#! /usr/bin/env python

import os
import subprocess
import sqlite3
import shutil
import datetime
import time
import calendar
import codecs

from jinja2 import Environment, PackageLoader
jinja_env = Environment(loader=PackageLoader('cs',
                                             'templates'))

def get_offset():
    is_dst = time.daylight and time.localtime().tm_isdst > 0
    utc_offset = - (time.altzone if is_dst else time.timezone)
    return utc_offset

def convert_chrome_time(chrome_time):
    base_time = datetime.datetime(1601,1,1)
    times = {}
    delta = datetime.timedelta(seconds = (chrome_time/10**6)
                               + get_offset())
    local_time = base_time + delta
    times['local'] = local_time
    times['time_of_day'] = "{0}:{1}".format(local_time.hour,
                                            local_time.minute)
    times['day'] = local_time.isoweekday()
    times['calendar'] = local_time.isoformat().split("T")[0]
    return times

def output_stuff(name, values):
    template = jinja_env.get_template(name)
    message = template.render(values = values)
    with codecs.open(name, 'w', 'utf-8') as f:
        f.write(message)

history_file = "/home/h/.config/chromium/Default/History"

# copy hisory file to tmp
temp_storage = "/tmp/.cs.History"
shutil.copyfile(history_file,temp_storage)

# open history file in sqlite
conn = sqlite3.connect(temp_storage)
c = conn.cursor()

r = c.execute('''select urls.title, urls.url, urls.visit_count, urls.last_visit_time from urls
order by urls.last_visit_time''')

values = {'main':[],
          'day':{},
          'calendar':{}}
calendar_values = {}
for i in r:
    converted_time = convert_chrome_time(i[3])
    for key in values.keys():
        try:
            item = converted_time[key]
        except KeyError:
            continue
        try:
            values[key][item] += 1
        except KeyError:
            values[key][item] = 1
    entry_values = {'title':i[0],
              'url':i[1],
              'visit_count':i[2],
              'times':convert_chrome_time(i[3])}
    values['main'].append(entry_values)

file_names = ['main', 'calendar', 'day']
for filename in file_names:
    if filename != 'main':
        res = []
        for key in sorted(values[filename].keys()):
            res.append((key,values[filename][key]))
        output_stuff(filename, res)
    else:
        output_stuff(filename, values[filename])
os.remove(temp_storage)
