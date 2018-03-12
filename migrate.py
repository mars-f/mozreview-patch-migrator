# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
Extract MozReview patch data and write out the patch data as a HTML directory.
"""

import argparse
from collections import namedtuple

import os
from time import sleep

import requests

PATCHNAME_TEMPLATE = "r{}-diff{}.patch"

API_BASE_URL = 'https://reviewboard.mozilla.org/api'

REVISION_INDEX_TEMPLATE = """
<doctype html>
<html>
<head><title>MozReview patch archive for revision {revision}</title></head>
<h1>MozReview patch archive for revision {revision}</h1>
<body>
<ul>
<li><a href='..'>..</a></li>
{latest_link}
{difflist_links}
</ul>
</body>
</html>
"""

DIFF_LINK_TEMPLATE = """<li><a href="{target}">{text}</a></li>"""

DiffData = namedtuple('DiffData', 'review_id diff_id patch')


def call_api(path):
    response = requests.get(API_BASE_URL + path)
    response.raise_for_status()
    return response


def get_diff_count(review_id):
    path = '/review-requests/{}/diffs/'.format(review_id)
    data = call_api(path).json()
    return int(data['total_results'])


def get_patch_for_diff(review_id, diff_id):
    """Fetch the patch contents as a string of bytes."""
    # Fetch the raw diff via the regular site.  The raw diff we want isn't
    # accessible via the web API.
    url = 'https://reviewboard.mozilla.org/r/{}/diff/{}/raw'.format(review_id,
                                                                    diff_id)
    response = requests.get(url)
    response.raise_for_status()
    return response.content


def gather_diff_data(review_id, diff_id):
    patch = get_patch_for_diff(review_id, diff_id)
    return DiffData(review_id, diff_id, patch)


def save_patch(diffdata, output_dir):
    path = filepath_for_record(diffdata, output_dir)
    with open(path, 'wb') as fd:
        fd.write(diffdata.patch)
    print('wrote: {} {} bytes'.format(path, len(diffdata.patch)))


def filepath_for_record(diffdata, output_dir):
    filename = PATCHNAME_TEMPLATE.format(diffdata.review_id, diffdata.diff_id)
    path = os.path.join(
        revision_directory_name(output_dir, diffdata.review_id), filename)
    return path


def revision_directory_name(output_dir, revision_id):
    return os.path.join(output_dir, str(revision_id))


def make_revision_directory(output_dir, revision_id):
    dirname = revision_directory_name(output_dir, revision_id)
    if not os.path.isdir(dirname):
        os.mkdir(dirname)


def write_directory_index(output_dir, revision_id, diff_count):
    latest_diff_id = diff_count

    diff_links = []
    for diff_id in range(1, diff_count + 1):
        filename = PATCHNAME_TEMPLATE.format(revision_id, diff_id)
        link_html = DIFF_LINK_TEMPLATE.format(target=filename, text=filename)
        diff_links.append(link_html)

    # We want the list displayed newest to oldest
    diff_links.reverse()
    difflist_links = '\n'.join(diff_links)

    latest_filename = PATCHNAME_TEMPLATE.format(revision_id, latest_diff_id)
    latest_link = DIFF_LINK_TEMPLATE.format(
        target=latest_filename, text='latest.patch')

    index_html = REVISION_INDEX_TEMPLATE.format(
        revision=revision_id,
        latest_link=latest_link,
        difflist_links=difflist_links)

    index_filename = os.path.join(
        revision_directory_name(output_dir, revision_id), 'index.html')
    with open(index_filename, 'w') as index:
        index.write(index_html)
    print('wrote:', index_filename)


def record_revision(revision_id, output_dir, rate_limit):
    sleep(rate_limit)

    try:
        diff_count = get_diff_count(revision_id)
    except requests.ConnectionError as err:
        print("error: r{} {}".format(revision_id, err))
        return
    except requests.HTTPError as err:
        if err.response.status_code == 404:
            print("skipped: r{} (not found)".format(revision_id))
        else:
            print("error: r{} {}".format(revision_id, err))
        return

    make_revision_directory(output_dir, revision_id)

    for diff_id in range(1, diff_count + 1):
        sleep(rate_limit)

        try:
            diff_data = gather_diff_data(revision_id, diff_id)
        except (requests.HTTPError, requests.ConnectionError) as err:
            print("error: fetching diff r{} {}: {}".format(revision_id,
                                                           diff_id, err))
            continue

        save_patch(diff_data, output_dir)

    write_directory_index(output_dir, revision_id, diff_count)


def parse_revision_range_str(rev_range_str):
    rev_range_parts = rev_range_str.split('..')
    if len(rev_range_parts) == 2:
        start_rev = int(rev_range_parts[0])
        end_rev = int(rev_range_parts[1])
    else:
        rev = int(rev_range_str)
        start_rev = rev
        end_rev = rev
    return start_rev, end_rev


def ensure_output_directory(output_dir):
    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)


def parse_args():
    parser = argparse.ArgumentParser(
        description='Save MozReview patches to a directory')
    parser.add_argument(
        'revision', help='The revision or revision range to save.  Can be a single revision of the form \'XXXX\' or a range of revisions of the form \'XXXX..YYYY\'')
    parser.add_argument(
        '--limit',
        type=float,
        default=1.0,
        help='Rate-limit API requests to one request every LIMIT seconds.  Accepts floating-point numbers like \'0.5\'. (default %(default)s seconds)'
    )
    parser.add_argument(
        '--output-dir',
        default='site',
        help='Output directory for HTML pages and patches'
    )
    return parser.parse_args()


def main(opts):
    # sample data:
    # 169494: 4 patches
    # TODO make it so the script can update the existing extract

    start_rev, end_rev = parse_revision_range_str(opts.revision)

    ensure_output_directory(opts.output_dir)

    print("Outputting files to directory '{}'".format(opts.output_dir))
    print("Rate-limiting to {} seconds between requests".format(opts.limit))
    print()

    for rev_id in range(start_rev, end_rev + 1):
        record_revision(rev_id, opts.output_dir, opts.limit)

    # TODO output aws-cli command for sync

    print()
    print('Done.')


if __name__ == '__main__':
    opts = parse_args()
    main(opts)
