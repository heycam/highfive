from __future__ import absolute_import

from collections import defaultdict
import os

from eventhandler import EventHandler
from helpers import get_people_from_config

WATCHERS_CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'watchers.ini')


def build_message(mentions):
    message = ['Heads up! This PR modifies the following files:']
    for (watcher, file_names) in mentions.items():
        message.append(" * @{}: {}".format(watcher, ', '.join(file_names)))

    return '\n'.join(message)


class WatchersHandler(EventHandler):
    def on_pr_opened(self, api, payload):
        diff = api.get_diff()
        changed_files = []
        for line in diff.split('\n'):
            if line.startswith('diff --git'):
                changed_files.extend(line.split('diff --git ')[-1].split(' '))

        # Remove the `a/` and `b/` parts of paths,
        # And get unique values using `set()`
        changed_files = set(map(lambda f: f if f.startswith('/') else f[2:],
                                changed_files))

        watchers = get_people_from_config(api, WATCHERS_CONFIG_FILE)
        if not watchers:
            return

        mentions = defaultdict(list)
        for (watcher, watched_files) in watchers:
            watched_files = watched_files.split(' ')
            blacklisted_files = []
            for watched_file in watched_files:
                if watched_file.startswith('-'):
                    blacklisted_files.append(watched_file[1:])
            for blacklisted_file in blacklisted_files:
                watched_files.remove('-' + blacklisted_file)
            for changed_file in changed_files:
                for blacklisted_file in blacklisted_files:
                    if changed_file.startswith(blacklisted_file):
                        break
                else:
                    for watched_file in watched_files:
                        if changed_file.startswith(watched_file):
                            mentions[watcher].append(changed_file)

        if not mentions:
            return

        message = build_message(mentions)
        api.post_comment(message)

handler_interface = WatchersHandler
