from urllib.parse import urlparse, urlsplit
import os


def is_url(url):
    return urlparse(url).scheme != ""


def filename_from_url(url):
    "%s%s" % os.path.splitext(os.path.basename(urlsplit(url).path))
