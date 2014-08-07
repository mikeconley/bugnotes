#!/usr/bin/env python

import argparse
import glob
import logging
import os
import sys

from bs4 import BeautifulSoup


"""
A script to extract useful things from an Evernote-exported bugnote
and toss it into a Jekyll post.
"""


DEFAULT_DEST = "../_posts"


def extract(document, resources, destination, date):
    logging.info("Extracting post body...")
    contents = ''.join([str(tag) for tag in document.body.contents])

    logging.info("Extracting document %s with %s to %s on %s" %
                 (len(document), len(resources), destination, date))


def main(options):
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
                resources.append(resource_file)

        # Now send it all off to the glue factory!
        extract(document, resources, destination=options.destination,
                date=options.date)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", action="store", dest="date",
                        help=("Overrides the created date in the Evernote "
                              "document. Use YYYY-MM-DD."))
    parser.add_argument("--destination", action="store", dest="destination",
                        help=("Folder to output the extractions to. "
                              "Defaults to %s" % DEFAULT_DEST),
                        default=DEFAULT_DEST)
    parser.add_argument("--verbose", action="store_true",
                        help="Print debugging messages to the console.")
    parser.add_argument("folders", metavar="FOLDER", nargs="+",
                        help="Evernote folders to extract from.")

    options, extra = parser.parse_known_args(sys.argv[1:])

    log_level = logging.DEBUG if options.verbose else logging.INFO
    logging.basicConfig(format="%(levelname)s:  %(message)s", level=log_level)

    sys.exit(main(options))