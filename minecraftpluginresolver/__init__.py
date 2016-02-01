import os
from spiget import *
from bukget import *
from tqdm import tqdm
import cfscrape
import argparse

# todo implement downloading from BukkitDev and Jenkins / Link with versioning (Prefix with Bukkit:
# Todo or prefix with Spigot:
# todo or prefix with Link: <url>==<version-to-save-as>

parser = argparse.ArgumentParser(description="Configure the options to run the Mineraft Plugin Resolver by.")
parser.add_argument("-r", required=True,
                    help="Requirements file used to determined the plugins and their desired versions")

parser.add_argument("-location", required=True,
                    help="Location to store the downloaded plugins in. If it doesn't exist, creation of it will be attempted")

parser.add_argument("--latest", required=False, action="store_true",
                    help="By default, if the version included in your spigot-test.txt file is invalid, use the latest available version of the resource")

args = None


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


class MinecraftPluginResolver:
    def __init__(self, arguments):
        self.requirements_file = arguments.r
        self.folder = arguments.location
        self.latest = arguments.latest
        # Retrieve the parsed requirements file in a dictionary for later use.
        self.parsed_requirements = self.parse_resources_file()
        self.spigot_resources = {}
        self.bukkit_resources = {}

    def collect_spigot_resources(self):
        for parsed_plugin, version in self.parsed_requirements.items():
            is_spigot_resource = parsed_plugin.startswith('s:')
            is_bukkit_resource = parsed_plugin.startswith('b:')

            if is_spigot_resource:
                plugin = parsed_plugin.split('s:')[1]
                resource = None
                if plugin.isdigit():
                    resource = SpigotResource.from_id(plugin)
                else:
                    resource = SpigotResource.from_name(plugin)

                if resource is None:
                    continue

                # If there's no available version of the requested version
                # Then see if we're to retrieve the latest version.
                # If we're unable to, due to the users request, then we skip!
                # Otherwise, we assign it to retrieve the latest version and move forth.
                if not resource.has_version(version):
                    if not self.latest:
                        print("Spigot Plugin '%s' has invalid requested version %s" % (
                            plugin, version))
                        continue
                    else:
                        self.spigot_resources[resource] = "latest"
                else:
                    self.spigot_resources[resource] = version

            elif is_bukkit_resource:
                plugin = parsed_plugin.split('b:')[1]
                if plugin.isdigit():
                    print("Invalid bukkit resource: %s" % plugin)
                    continue
                resource = BukkitResource.from_name(name=plugin, version=version)
                if not resource.has_version(version):
                    if not self.latest:
                        print("Bukkit Plugin '%s' has invalid requested version %s" % (plugin, version))
                        continue
                    self.bukkit_resources[resource] = "latest"
                else:
                    self.bukkit_resources[resource] = version

            else:
                print("Invalid requested resource: %s (Version %s)" % (parsed_plugin, version))

    def parse_resources_file(self):
        resources = {}
        with open(self.requirements_file, 'r') as lines:
            for line in lines:
                line = line.rstrip('\n')
                if "==" in line:
                    split_text = line.split('==', 1)
                    resource_name = split_text[0]
                    resource_version = split_text[1]
                    resources[resource_name] = resource_version
                elif '=' in line:
                    split_text = line.split('=', 1)
                    resource_name = split_text[0]
                    resource_version = split_text[1]
                    resources[resource_name] = resource_version
                else:
                    resources[line] = "latest"
        return resources

    def run(self):
        print("Collecting requested resources for SpigotResolver to run by!")
        self.collect_spigot_resources()
        if not os.path.exists(os.path.expanduser(self.folder)):
            try:
                os.makedirs(os.path.expanduser(self.folder))
            except OSError:
                print("Unable to create directory: %s" % self.folder)
                return

        # Change the working directory to the requested
        # Folder to save plugins in.
        with ChangeDir(os.path.expanduser(self.folder)):
            print("Generating token to retrieve Resources with")
            tokens, user_agent = cfscrape.get_tokens('http://www.spigotmc.org')
            for resource, version in self.spigot_resources.items():
                print("Retrieving resource information: %s (Version: %s)" % (resource.name, version))
                download_url = resource.get_download_link(version=version)
                requested_version = resource.version if version == "latest" else version

                if resource.external:
                    print('Unavailable Feature: Collecting external resources; Will be completed in future versions')
                    continue

                file_name = "%s-%s%s" % (resource.name, requested_version, resource.file_type)
                try:
                    download(file_name, download_url, tokens, user_agent)
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
