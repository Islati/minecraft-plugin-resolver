from urllib.parse import urlparse, urlsplit
import os


def is_url(url):
    return urlparse(url).scheme != ""


def filename_from_url(url):
    if not is_url(url):
        if not os.path.exists(url):
            return None
        return "%s%s" % os.path.splitext(url)
    else:
        return "%s%s" % os.path.splitext(os.path.basename(urlsplit(url).path))


def get_file_extension(path):
    if is_url(path):
        return "%s" % os.path.splitext(os.path.basename(urlsplit(path).path))[1]
    else:
        if not os.path.exists(path):
            return None
        return "%s" % os.path.splitext(path)[1]
