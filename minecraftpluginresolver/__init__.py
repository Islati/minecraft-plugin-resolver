import os
from spiget import *
from bukget import *
from tqdm import tqdm
import cfscrape
import argparse
import yaml
import warnings
import functools

# todo implement downloading from BukkitDev and Jenkins / Link with versioning (Prefix with Bukkit:
# Todo or prefix with Spigot:
# todo or prefix with Link: <url>==<version-to-save-as>

parser = argparse.ArgumentParser(description="Configure the options to run the Mineraft Plugin Resolver by.")
parser.add_argument("-r", "-requirements", dest="requirements", metavar=('File containing plugin requirements'),
                    required=True,
                    help="Requirements file used to determined the plugins and their desired versions")

parser.add_argument('-l', "-location", dest="location", metavar=('Local directory to store the plugins retrieved'),
                    required=True,
                    help="Location to store the downloaded plugins in. If it doesn't exist, creation of it will be attempted")

parser.add_argument('-u', "--latest", dest="latest",
                    required=False, action="store_true",
                    help="By default, if the version included in your requirements file is invalid, use the latest available version of the resource")

args = None


def deprecated(func):
    """This is a decorator used to mark functions as deprecated.
    It results in a warning being emitted when the function is used."""

    @functools.wraps(func)
    def new_func(*args, **kwargs):
        warnings.warn_explicit(
            "Call to deprecated function. %s {}".format(func.__name__),
            category=DeprecationWarning,
            filename=func.func_code.co_filename,
            lineno=func.func_code.co_firstlineno + 1
        )
        return func(*args, **kwargs)

    return new_func


class ChangeDir:
    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    # Change directory with the new path
    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    # Return back to previous directory
    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)


class MinecraftPluginResolver(object):
    def __init__(self, arguments):
        self.requirements_file = arguments.requirements
        self.folder = arguments.location
        self.latest = arguments.latest
        self.spigot_resources = {}
        self.bukkit_resources = {}

        # Parse the yaml file holding all the requested plugins to resolve the plugins with further on.
        self.parse_yaml_file()

    def parse_yaml_file(self):
        resources = {}
        with open(self.requirements_file, 'r') as yaml_file:
            data_file = yaml.safe_load(yaml_file)
            print(data_file)

            # Now we collect all the resources requested on Bukkit,
            # and their desired versions.
            bukkit_data = data_file['Bukkit']

            for plugin_name in bukkit_data.keys():
                data = bukkit_data[plugin_name]
                version = data['version']

                if isinstance(plugin_name, int) or plugin_name.isdigit():
                    print("Invalid Bukkit plugin '%s', plugin name or slug (in plugins url) is required")
                    continue

                try:
                    bukkit_resource = BukkitResource.from_name(plugin_name)
                except ValueError:
                    print("Unable to retrieve Bukkit plugin %s (v. %s)" % (plugin_name, version))

                if not bukkit_resource.has_version(version=version):
                    if not self.latest:
                        print("Unable to retrieve version %s for %s" % (version, plugin_name))
                        continue
                    else:
                        self.bukkit_resources[plugin_name] = {
                            'version': 'latest',
                            'resource': bukkit_resource
                        }
                else:
                    self.bukkit_resources[plugin_name] = {
                        'version': version,
                        'resource': bukkit_resource
                    }

                print("Bukkit information retrieved on %s (v: %s)" % (
                    plugin_name, self.bukkit_resources[plugin_name]['version']))


        # Go ahead and collect all the Spigot resources in the yml file
        # and their desired versions (or latest)
        spigot_plugins = data_file['Spigot']
        for plugin_id in spigot_plugins.keys():
            spigot_resource = None

            plugin_data = spigot_plugins[plugin_id]
            version = plugin_data['version']
            name = plugin_data['name']

            if isinstance(plugin_id, int) or plugin_id.isdigit():
                spigot_resource = SpigotResource.from_id(plugin_id)
            else:
                print(
                    "Unable to retrieve Spigot plugin (%s) via its name... Potential feature in the future!" % name)
                continue

            if spigot_resource is None:
                print("Invalid plugin %s (v: %s)" % (name, version))
                continue

            if not spigot_resource.has_version(version=version):
                if not self.latest:
                    print("Unable to retrieve version %s for %s" % (version, name))
                    continue

                self.spigot_resources[plugin_id] = {
                    'version': 'latest',
                    'name': name,
                    'resource': spigot_resource,
                }
            else:
                self.spigot_resources[plugin_id] = {
                    'version': version,
                    'name': name,
                    'resource': spigot_resource
                }

            if isinstance(plugin_id, int):
                print("Spigot information retrieved on %s [id. %s] (v. %s)" % (name, plugin_id,
                                                                               self.spigot_resources[plugin_id][
                                                                                   'version']))

    def run(self):
        print("Collecting requested resources to run the Plugin Resolver by!")
        if not os.path.exists(os.path.expanduser(self.folder)):
            try:
                os.makedirs(os.path.expanduser(self.folder))
            except OSError:
                print("Unable to create directory: %s" % self.folder)
                return

        # Change the working directory to the requested
        # Folder to save plugins in.
        with ChangeDir(os.path.expanduser(self.folder)):
            print("Loading Resource information")
            tokens, user_agent = cfscrape.get_tokens('http://www.spigotmc.org')
            # First, iterate through all the bukkit plugins to resolve
            # and begin downloading them.
            print("Retrieving Bukkit Resources")
            for plugin, data in self.bukkit_resources.items():
                resource = data['resource']
                version = data['version']
                download_url = resource.get_download_link(version=version)
                file_name = resource.get_versioned_file_name(version=version)

                try:
                    download(file_name, download_url, tokens, user_agent)
                    print("Downloaded plugin %s to %s" % (resource.plugin_name, file_name))

                except FileNotFoundError:
                    print("Unable to download resource %s from %s" % (resource.plugin_name, download_url))

            print("Retrieving Spigot Resources")
            for plugin, data in self.spigot_resources.items():
                resource = data['resource']
                version = data['version']
                name = data['name']
                download_url = resource.get_download_link(version=version)
                requested_version = resource.version if version == "latest" else version

                if resource.external:
                    print('Unavailable Feature: Collecting external resources; Will be completed in future versions')
                    continue

                file_name = "%s-%s%s" % (name, requested_version, resource.file_type)
                try:
                    download(file_name, download_url, tokens, user_agent)
                    print("Downloaded plugin %s to %s" % (resource.name, file_name))
                except FileNotFoundError:
                    print("Unable to download resource %s from %s" % (resource.name, download_url))

        print("Finished Operations! Resolution complete!")


def download(filename, url, cookies, useragent):
    scraper = cfscrape.create_scraper()
    with open(filename, 'wb') as handle:
        response = scraper.get(url, cookies=cookies, headers={"User-Agent": useragent}, stream=True)

        if not response.ok:
            raise FileNotFoundError(
                'Unable to locate the resource %s at %s; Assure its valid in your spigot-test.txt file' % (
                    filename, url))
        # Something went wrong

        for block in tqdm(response.iter_content(1024)):
            handle.write(block)


if __name__ == "__main__":
    # TODO implement retrieval of file extension if not jar.
    # todo implement version compare of local file for potentially updating plugin without replacing?

    args = parser.parse_args()
    app = MinecraftPluginResolver(arguments=args)
    app.run()
