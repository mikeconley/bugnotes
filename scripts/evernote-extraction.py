#!/usr/bin/env python

import argparse
import datetime
import glob
import io
import logging
import os
import posixpath
import re
import shutil
import sys
import urllib
import urlparse

from bs4 import BeautifulSoup
from jinja2 import Template


"""
A script to extract useful things from an Evernote-exported bugnote
and toss it into a Jekyll post.
"""


DEFAULT_DEST = "../_posts"
DEFAULT_ASSETS = "../assets"
EXPECTED_BUG_HOSTNAME = "bugzilla.mozilla.org"
DEFAULT_FRONT_MATTER = """---
layout: post
title:  "{{ post_title }}"
date:   {{ post_date }}
tags:
---


"""

def extract(document, resources, destination, assets, folder, dry_run=False):
    logging.info("Identifying associated bug...")
    bug_tag = document.find("meta", {"name":"source-url"})
    if not bug_tag:
        logging.error("Could not find a bug in the HTML document in %s"
                     % folder)
        return

    bug_url = bug_tag['content']
    logging.debug("Extracted URL from source-url meta tag: %s" % bug_url)
    bug_url = urlparse.urlparse(bug_url)

    if bug_url.hostname != EXPECTED_BUG_HOSTNAME:
        logging.error("Expected a bug URL with hostname %s"
                      % EXPECTED_BUG_HOSTNAME)
        return

    query_dict = urlparse.parse_qs(bug_url.query)
    if 'id' not in query_dict:
        logging.error("Expected a bug ID in the URL %s" % bug_url.geturl())
        return

    bug_id = str(query_dict['id'][0])
    logging.info("Found a reference to bug #%s" % bug_id)

    bug_title_tag = document.find("title")
    if not bug_title_tag:
        logging.error("Could not find a title for the HTML document in %s"
                      % folder)
        return
    bug_title = bug_title_tag.string
    logging.info("Found a bug title: %s" % bug_title)

    if len(resources):
        # We have resources, meaning we're going to need to do some
        # swaps in the content, and we'll need to move these assets
        # into the assets folder.
        # Right now, I'm just doing replacements for image tags.
        images = document.findAll("img")
        resource_basenames = [os.path.basename(resource)
                              for resource in resources]
        for image in images:
            filename = posixpath.basename(urllib.unquote(image['src']))
            if filename not in resource_basenames:
                logging.error("Found a reference to a reference we can't "
                              "find: %s" % filename)
                return
            image['src'] = posixpath.join("assets", bug_id + "-" + filename)

        for resource in resources:
            new_filename = bug_id + "-" + os.path.basename(resource)
            new_location = os.path.join(assets, new_filename)
            logging.debug("Copying %s to %s..." % (resource, new_location))
            if not dry_run:
                shutil.copyfile(resource, new_location)

    logging.info("Adding bug link to head of post...")
    link = document.new_tag("a")
    link.string = bug_title
    link["href"] = bug_url.geturl()
    document.body.insert(0, link)

    date = datetime.date.today().strftime('%Y-%m-%d')

    post_filename = date + "-bug-" + bug_id + ".html"

    logging.info("Generating front matter...")

    fm_template = Template(DEFAULT_FRONT_MATTER)
    # The bug_title might have some quotes in it, which Jekyll will not like
    # unless we escape them.
    bug_title = bug_title.replace('"', '\\"')
    front_matter = fm_template.render(post_title=bug_title, post_date=date)

    logging.info("Extracting document body and inserting into post")
    content_string = ''.join([str(thing) for thing in document.body.contents])
    content = BeautifulSoup(content_string)

    post_path = os.path.join(destination, post_filename)
    if os.path.exists(post_path):
        logging.error("A file already exists at %s. Skipping..." % post_path)
        return

    logging.info("Writing to %s" % post_path)
    if not dry_run:
        with io.open(post_path, 'w', encoding='utf8') as f:
            f.write(front_matter)
            f.write(content.prettify())

    logging.info("Done!")


def main(options):
    if options.dry_run:
        logging.info("Doing a dry run.")

    logging.debug("Iterating %s supposed folders." % len(options.folders))
    for folder in options.folders:
        logging.info("Attempting an extraction from %s" % folder)

        # The folder must exist.
        if not os.path.exists(folder):
            logging.error("Folder %s does not exist. Skipping..." % folder)
            continue

        # The folder must contain an HTML document. If we find more than one...
        # that's confusing, and we'll skip.
        html_files = glob.glob(os.path.join(folder, "*.html"))
        if len(html_files) != 1:
            logging.error("Found %s HTML files in %s. Expected 1. Skipping..."
                          % (len(html_files), folder))
            continue

        document_file = html_files[0]
        document = BeautifulSoup(open(document_file))

        # The folder might have a resources folder. Get a handle on
        # each resource in that folder.
        resources = []
        resources_folders = glob.glob(os.path.join(folder, "*.resources"))
        if len(resources_folders) > 0:
            if len(resources_folders) > 1:
                logging.error("Found %s resources folders. Expected 0 or 1. "
                              "Skipping..." % (len(resources_folders)))
                continue

            # Get all of the resource files, and toss them into our resources
            # list.
            resource_folder = resources_folders[0]
            for resource_file in os.listdir(resource_folder):
                resources.append(os.path.join(resource_folder, resource_file))

        # Now send it all off to the glue factory!
        extract(document, resources, destination=options.destination,
                assets=options.assets, folder=folder,
                dry_run=options.dry_run)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--destination", action="store", dest="destination",
                        help=("Folder to output the extractions to. "
                              "Defaults to %s" % DEFAULT_DEST),
                        default=DEFAULT_DEST)
    parser.add_argument("--assets", action="store", dest="assets",
                        help=("Folder to output the assets to. "
                              "Defaults to %s" % DEFAULT_ASSETS),
                        default=DEFAULT_ASSETS)
    parser.add_argument("--dry-run", action="store_true", dest="dry_run",
                        help="Just simulate extraction and copying.")
    parser.add_argument("--verbose", action="store_true",
                        help="Print debugging messages to the console.")
    parser.add_argument("folders", metavar="FOLDER", nargs="+",
                        help="Evernote folders to extract from.")

    options, extra = parser.parse_known_args(sys.argv[1:])

    log_level = logging.DEBUG if options.verbose else logging.INFO
    logging.basicConfig(format="%(levelname)s:  %(message)s", level=log_level)

    sys.exit(main(options))
