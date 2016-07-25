#!/usr/bin/env python

import base64
import io
import os
import requests
import time

BZ_API_KEY_PATH = '../BZ_API_KEY'
DIRS_PATH = 'dirs.txt'
API_ENDPOINT = 'https://bugzilla.mozilla.org/rest/'
BUGNOTES_SITE = 'http://people.mozilla.org/~mconley2/bugnotes/'
ATTACHMENTS_PATH = '../attachments'

# Get our API key first...
with io.open(BZ_API_KEY_PATH, 'r', encoding='utf8') as f:
    BZ_API_KEY = f.read().strip()

# Now read in a dirs.txt that lists the directories
# of zip files we're going to attach...
with io.open(DIRS_PATH, 'r', encoding='utf8') as f:
    DIRS = f.read().splitlines()

for this_dir in DIRS:
    bug_num = this_dir.split('-')[1]
    attachment = os.path.join(this_dir, this_dir + '.zip')
    with io.open(os.path.join(ATTACHMENTS_PATH, attachment), 'rb') as f:
        data = base64.b64encode(f.read())

    url = API_ENDPOINT + 'bug/' + bug_num + '/attachment'

    r = requests.post(url, data={
        'id': [bug_num],
        'is_patch': 0,
        'comment': BUGNOTES_SITE + this_dir + '.html',
        'is_markdown': 0,
        'summary': 'Bugnotes',
        'content_type': 'application/zip',
        'data': data,
        'file_name': this_dir + '.zip',
        'obsoletes': [],
        'flags': [],
        'api_key': BZ_API_KEY})

    print "Posted for bug " + bug_num
    time.sleep(2)