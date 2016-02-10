import textwrap
from collections import OrderedDict
from spiget import SpigotResource
from bukget import BukkitResource
import sys
import yamlbro

from mcresolver.scripts import configure_plugin, write_file, get_config_from_file, save_plugin_config_script
from mcresolver.utils import is_url, filename_from_url, get_file_extension

from tqdm import tqdm

import yaml
from yamlbro import install_patch, restore_yaml_comments

import os
import shutil
import cfscrape
import argparse
import warnings
import functools

# Install yaml patch
install_patch()
# todo implement downloading from BukkitDev and Jenkins / Link with versioning (Prefix with Bukkit:
# Todo or prefix with Spigot:
# todo or prefix with Link: <url>==<version-to-save-as>

parser = argparse.ArgumentParser(description="Configure the options to run the Mineraft Plugin Resolver by.")
parser.add_argument("-r", "-requirements", dest="requirements", metavar=('*.yml Requirements File'),
                    required=False,
                    help="Requirements file used to determined the plugins and their desired versions")

parser.add_argument('-l', "-location", dest="location", metavar=('FOLDER'),
                    required=False,
                    help="Location to store the plugins, or generated configuration in. If it doesn't exist, creation of it will be attempted")

parser.add_argument('-u', "--latest", dest="latest",
                    required=False, action="store_true",
                    help="By default, if the version included in your requirements file is invalid, use the latest available version of the resource")

parser.add_argument('-g', '--generate', dest='generate', required=False, action='store',
                    help='Take a configuration file and attempt to generate a template, and defaults file from it')

parser.add_argument('-pl', '--plugin', dest='genplugin', required=False, action='store',
                    help='Coupled with use of generate, its the name to assign config templates on generation')
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
        self.output_folder = arguments.location
        self.retrieve_latest_on_version_error = arguments.latest
        self.spigot_resources = OrderedDict()
        self.bukkit_resources = OrderedDict()

        # Application specific folders; For storing scripts, and other files.
        self.app_data_folder = os.path.expanduser("~/.mcresolver/")
        self.scripts_folder = os.path.join(self.app_data_folder, "scripts")

        # Used to handle the generation portion of mcresolver. Taking a configuration file
        # And generating a template, and set of default values for the template.
        self.generate_base_config_file = None if args.generate is None else os.path.expanduser(args.generate)
        self.generate_plugin_name = None if args.genplugin is None else args.genplugin

        # Initialize the mcresolver configuration folders and files.
        self.__init_app_config()

        if args.generate is not None and args.genplugin is not None:
            if self.output_folder is None:
                print(
                    "To generate plugin configuration, you also require the '-l [Folder]' flag, specifying where to save the generated configuration")
                parser.print_help()
                sys.exit(0)

            self.generate_templates()
            print("Generated config templates for %s and saved them to %s" % (
                self.generate_plugin_name, self.output_folder))
            sys.exit(0)

        elif args.requirements is None:
            print(textwrap.dedent("""\n
            ==================================
                McResolver Execution Error
            ==================================

                McResolver has limited ways it can be utilized, each of which
                with their own required options, variables, functionality and
                purpose.


                Retrieve and Configure Plugins
                ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

                    Download plugins from Bukkit and Spigot, then automatically configure
                    them to your likings.

                    This option requires you to use the '-r' or '--requirements' flag, to pass
                    a yml based file outlining the location to store your plugins and config (locally),
                    what plugins to download, and what options to pass to the configuration template, or script,
                    to generate the plugins config.


                Generate Configuration Files
                ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

                    Using fresh plugin configuration, or previously configured plugins you
                    pass a few flags (-g [config file], -gl [store location], and -gpl [Plugin name])
                    then McResolver will generate a Jinja2 Template, along with defaults file for you to
                    configure your plugins by.

                    The template will hold the structure of the configuration file, while the defaults file
                    is used to replace all variables that aren't defined when executing the 'Retrieve and Configure'
                    method described above.

                    This way, if you wish to deploy the same configuration for every plugin install, or have some deviate
                    in different ways you can do so, modifying only the values you wish to modify, while keeping all the
                    others exactly how you like them!


                Please use one of the methods listed above, and their required options when executing McResolver.
            """).format())

            parser.print_help()
            sys.exit(0)

        # Parse the yaml file holding all the requested plugins to resolve the plugins with further on.
        self.parse_config_file()

    def __init_app_config(self):
        if not os.path.exists(self.app_data_folder):
            os.makedirs(self.app_data_folder)

        if not os.path.exists(self.scripts_folder):
            os.makedirs(self.scripts_folder)

        if self.output_folder is not None and not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)

    def __cleanup(self):
        # shutil.rmtree(self.scripts_folder)
        pass

    def generate_templates(self):
        def get_name_from_key(key):
            return key.lower().replace('-', '_').replace('.', '_')

        def assign_dict_nested_path(dict, path, value):
            def get(d, keys):
                for key in keys:
                    if key not in d:
                        d[key] = OrderedDict()  # TODO Investigate? Might need to instance another object
                        #     # print("Assigned empty value to path %s" % path)
                    d = d[key]
                return d

            def set(d, keys, value):
                d = get(d, keys[:-1])
                d[keys[-1]] = value

            if '.' in path:
                set(dict, path.split('.'), value)
            else:
                dict[path] = value

        def recursive_dictionary_collect(template_dict, parent_key, data):
            for key, value in data.items():
                new_key = key if parent_key is None else "%s.%s" % (parent_key, key)
                if isinstance(value, dict) or isinstance(value, OrderedDict):
                    recursive_dictionary_collect(template_dict, new_key, value)
                else:
                    if isinstance(value, list):
                        depth = len(new_key.split('.')) * 2
                        value.append('mcresolverdepth=%s' % depth)
                    template_dict[new_key] = value

        flat_key_template = OrderedDict()

        default_pluginfile_data = yamlbro.load_yaml(self.generate_base_config_file)

        for key, value in default_pluginfile_data.items():
            if isinstance(value, dict) or isinstance(value, OrderedDict):
                # replica_dict[key] = value
                recursive_dictionary_collect(flat_key_template, key, value)
            else:
                if isinstance(value, list):
                    value.append(
                        'mcresolverdepth=1')  # Hack around the template, and add the depth to prepend to the node
                flat_key_template[key] = value

        template_default_node_values = OrderedDict()
        node_value_types = {}

        for key, value in flat_key_template.items():
            node_name = key
            if '.' in key:
                node_split = key.split('.')
                if len(node_split) >= 2:
                    node_name = ".".join(node_split[-2:])
                else:
                    node_name = node_split[-1]

            node_name = get_name_from_key(node_name)
            # print("Key [%s] Node-Name %s" % (key, node_name))
            # node_name = get_name_from_key(node_name)
            value_type = value.__class__.__name__

            try:
                tdval = type(value)(value)
                if value_type == "bool":
                    tdval = str(tdval).lower()

                template_default_node_values[node_name] = tdval
                node_value_types[node_name] = value_type
                node_type = tdval.__class__.__name__
            except:
                template_default_node_values[node_name] = value
                node_value_types[node_name] = value_type
                node_type = value_type.__class__.__name__

            flat_key_template[key] = "{{{{{node}}}}}".format(node=node_name)

        expanded_key_config_template = OrderedDict()

        for key, value in flat_key_template.items():
            assign_dict_nested_path(expanded_key_config_template, key, value)

        config_template = yaml.dump(expanded_key_config_template, default_flow_style=False, indent=2,
                                    width=1000)

        with open(self.generate_base_config_file, 'r') as default_configuration_data:
            default_plugin_config = default_configuration_data.read()

        config_template = restore_yaml_comments(config_template, default_plugin_config)

        # Loop through all the nodes and their values, then change the jinja2 template
        # Variable to follow the format required for that item..
        # The reason we do this is to re-assign types to values (via their template-names)
        # As by default they all are quoted and are treated as strings.
        # We don't want this!
        for node, type in node_value_types.items():
            if type == "bool" or type == "int" or type == "float":
                config_template = config_template.replace("'{{{{{node}}}}}'".format(node=node),
                                                          "{{{{{node}}}}}".format(node=node))
            elif type == "str":
                continue
            elif type == "list":
                # If the value of the item is a list
                # Then there's quite a few things we have to do in order to preserve the format of the file!
                # First of all involves getting the depth (via a default value generated and added into the list)
                # Though this won't wind up in the final template. We do this because we need to have
                # The valid number of spaces before the list items, otherwise YAML Will break.
                node_list_values = template_default_node_values[node].copy()
                depth = 0
                for line in node_list_values:
                    if 'mcresolverdepth' in line:
                        # The depth of the item will be indexed by this!
                        # Depth is determined by how many parent keys, are above the child node
                        # Multiplied by 2, for yaml conventions.
                        # Example: Top-Level lists only have 2 spaces
                        # Whereas a list under top.level.list would have 4
                        depth = int(line.split('=')[1])
                        break

                # Collect all the nodes list items that dont have a depth attribute
                node_list_values = [line for line in node_list_values if 'mcresolverdepth' not in line]
                # Then reassign this value to the template defaults,
                # as we don't want the depth to be inside the users
                template_default_node_values[node] = node_list_values
                # Next we generate a loop statement for inside the template
                # On our node, to assure all the items in the list are processed
                loop_statement = "\n{{% for {node}_item in {node} %}}{depth}- {{{{list_item}}}}\n{{% endfor %}}".format(
                    depth=' ' * depth, node=node
                )

                # Lastly, for this part, replace the previous {{node}} item with the new list-generating statement
                # That was created above.
                config_template = config_template.replace(" '{{{{{node}}}}}'".format(node=node),
                                                          loop_statement)

        # Get the file contents for the default template nodes and their values in a yaml output!
        defaults_file_contents = yaml.dump(template_default_node_values, default_flow_style=False)
        # Next up, we need to remove all the 'none' values inside of this file, as it's really not a good idea
        # to have yaml parse "none" values... It'd return a string. So we make them blank instead.
        defaults_file_contents = defaults_file_contents.replace(": none", ": ")
        write_file(os.path.join(self.output_folder, '%s-template.yml' % self.generate_plugin_name),
                   config_template)
        write_file(os.path.join(self.output_folder, '%s-defaults.yml' % self.generate_plugin_name),
                   defaults_file_contents)

    def parse_config_file(self):
        config = yamlbro.load_yaml(self.requirements_file)

        if 'target-folder' in config.keys() and self.output_folder is None:
            print("Info: Files and Configuration will be stored in %s" % self.output_folder)
            self.output_folder = os.path.expanduser(config['target-folder'])

            if not os.path.exists(self.output_folder):
                os.makedirs(self.output_folder)

        if 'Bukkit' in config.keys():
            bukkit_data = config['Bukkit']

            for plugin_name in bukkit_data.keys():
                data = bukkit_data[plugin_name]
                version = data['version']
                configure_after_download = False
                configure_options = {}
                configure_script = None
                template_file = None
                defaults_file = None
                plugin_folder = None
                kwargs = {}

                if 'configure' in data.keys():
                    if 'options' in data['configure']:
                        configure_after_download = True
                        for option, value in data['configure']['options'].items():
                            configure_options[option] = value

                    if 'args' in data['configure'].keys():
                        for key, value in data['configure']['args'].items():
                            kwargs[key] = value

                    if 'script' in data['configure'].keys():
                        configure_script = data['configure']['script']
                        print("Script found: %s" % configure_script)

                    if 'template' in data['configure'].keys():
                        template_file = data['configure']['template']

                    if 'defaults' in data['configure'].keys():
                        defaults_file = data['configure']['defaults']

                    if 'plugin-data-folder' in data['configure'].keys():
                        plugin_folder = data['configure']['plugin-data-folder']

                    if (template_file is not None and defaults_file is None) or (
                                    defaults_file is not None and template_file is None):
                        template_file = None
                        defaults_file = None
                        configure_after_download = False

                        print(textwrap.dedent("""\n
                            +==================================================================+
                                    Configuration Error for {name} ({version})
                            +==================================================================+

                                Generating a plugins configuration file via template & default configuration
                                requires the 'template', 'plugin-data-folder', and 'defaults' node to be present, and valid
                                inside your requirements file ({configuration}).

                                Using one without the others nulls the functionality, as a template has placeholders
                                for your config data, and the defaults file fills in the blanks where you
                                have not specified values. Using either without a plugin data folder doesn't make sense,
                                as you'd want to keep the template and defaults once it's generated.

                                McResolver will continue to download these plugins, though configuration cannot happen
                                unless you provide a template, plugin data folder, and defaults file, or a script that
                                handles the configuration.

                            +==================================================================+
                            """).format(name=plugin_name, version=version, configuration=self.requirements_file))

                if isinstance(plugin_name, int) or plugin_name.isdigit():
                    print("Invalid Bukkit plugin '%s', plugin name or slug (in plugins url) is required")
                    continue

                try:
                    bukkit_resource = BukkitResource.from_name(plugin_name)
                except ValueError:
                    print("Unable to retrieve Bukkit plugin %s (v. %s)" % (plugin_name, version))

                if not bukkit_resource.has_version(version=version):
                    if not self.retrieve_latest_on_version_error:
                        print("Unable to retrieve version %s for %s" % (version, plugin_name))
                        continue
                    else:
                        self.bukkit_resources[plugin_name] = {
                            'version': 'latest',
                            'name': plugin_name,
                            'resource': bukkit_resource,
                            'configure': configure_after_download,
                            'script': configure_script,
                            'configure-options': configure_options,
                            'kwargs': kwargs,
                            'template': template_file,
                            'defaults': defaults_file,
                            'plugin-folder': plugin_folder,
                        }
                else:
                    self.bukkit_resources[plugin_name] = {
                        'version': version,
                        'name': plugin_name,
                        'resource': bukkit_resource,
                        'configure': configure_after_download,
                        'script': configure_script,
                        'configure-options': configure_options,
                        'kwargs': kwargs,
                        'template': template_file,
                        'defaults': defaults_file,
                        'plugin-folder': plugin_folder,

                    }

                print("Bukkit information retrieved on %s (v: %s)" % (
                    plugin_name, self.bukkit_resources[plugin_name]['version']))

        # Go ahead and collect all the Spigot resources in the yml file
        # and their desired versions (or latest)
        if 'Spigot' in config.keys():
            spigot_plugins = config['Spigot']
            for plugin_id in spigot_plugins.keys():
                data = spigot_plugins[plugin_id]
                spigot_resource = None
                version = data['version']
                name = data['name']
                configure_after_download = False
                configure_script = None
                configure_options = {}
                template_file = None
                defaults_file = None
                plugin_folder = None
                kwargs = {}
                if 'configure' in data.keys():
                    if 'options' in data['configure']:
                        configure_after_download = True
                        for option, value in data['configure']['options'].items():
                            configure_options[option] = value

                    if 'args' in data['configure'].keys():
                        for key, value in data['configure']['args'].items():
                            kwargs[key] = value

                    if 'script' in data['configure'].keys():
                        configure_script = data['configure']['script']

                    if 'template' in data['configure'].keys():
                        template_file = data['configure']['template']

                    if 'defaults' in data['configure'].keys():
                        defaults_file = data['configure']['defaults']

                    if 'plugin-data-folder' in data['configure'].keys():
                        plugin_folder = data['configure']['plugin-data-folder']

                    if (template_file is not None and defaults_file is None) or (
                                    defaults_file is not None and template_file is None):
                        template_file = None
                        defaults_file = None
                        configure_after_download = False
                        print(textwrap.dedent("""\n
                            +==================================================================+
                                    Configuration Error for {name} ({version})
                            +==================================================================+

                                Generating a plugins configuration file via template & default configuration
                                requires the 'template', 'plugin-data-folder', and 'defaults' node to be present, and valid
                                inside your requirements file ({configuration}).

                                Using one without the others nulls the functionality, as a template has placeholders
                                for your config data, and the defaults file fills in the blanks where you
                                have not specified values. Using either without a plugin data folder doesn't make sense,
                                as you'd want to keep the template and defaults once it's generated.

                                McResolver will continue to download these plugins, though configuration cannot happen
                                unless you provide a template, plugin data folder, and defaults file, or a script that
                                handles the configuration.

                            +==================================================================+
                            """).format(name=name, version=version, configuration=self.requirements_file))

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
                    if not self.retrieve_latest_on_version_error:
                        print("Unable to retrieve version %s for %s" % (version, name))
                        continue

                    self.spigot_resources[plugin_id] = {
                        'version': 'latest',
                        'name': name,
                        'resource': spigot_resource,
                        'configure': configure_after_download,
                        'script': configure_script,
                        'configure-options': configure_options,
                        'kwargs': kwargs,
                        'template': template_file,
                        'defaults': defaults_file,
                        'plugin-folder': plugin_folder,

                    }
                else:
                    self.spigot_resources[plugin_id] = {
                        'version': version,
                        'name': name,
                        'resource': spigot_resource,
                        'configure': configure_after_download,
                        'script': configure_script,
                        'configure-options': configure_options,
                        'kwargs': kwargs,
                        'template': template_file,
                        'defaults': defaults_file,
                        'plugin-folder': plugin_folder,
                    }

                if isinstance(plugin_id, int):
                    print("Spigot information retrieved on %s [id. %s] (v. %s)" % (name, plugin_id,
                                                                                   self.spigot_resources[plugin_id][
                                                                                       'version']))

    def generate_plugin_configuration(self):
        plugins_folder = os.path.join(self.output_folder, "plugins")
        if not os.path.exists(plugins_folder):
            os.makedirs(plugins_folder)

        # Loop through all the available spigot resources and their data
        # To see if they're desired to be configured!
        for plugin, data in self.spigot_resources.items():
            configure = data['configure']
            values = data['configure-options']
            kwargs = data['kwargs']
            script = data['script']
            template = data['template']
            defaults = data['defaults']
            data_folder = data['plugin-folder']

            if not configure:
                continue

            if data_folder is not None:
                kwargs['plugin_folder'] = data_folder

            if script is not None:
                print("Script for %s is %s" % (data['name'], script))
                if is_url(script):
                    script = save_plugin_config_script(self.scripts_folder, script)
                else:
                    script = os.path.expanduser(data['script'])

            resource = data['resource']
            if configure_plugin(resource, data['version'], plugins_folder,
                                config_options=values, script=script, script_folder=self.scripts_folder, **kwargs):
                print("Configuration for %s has been generated!" % data['name'])
            else:
                print("Failed to create configuration for %s." % data['name'])

        for plugin, data in self.bukkit_resources.items():
            configure = data['configure']
            values = data['configure-options']
            script = data['script']
            kwargs = data['kwargs']
            data_folder = data['plugin-folder']

            if data_folder is not None:
                kwargs['plugin_folder'] = data_folder

            if not configure:
                continue

            if script is not None:
                if is_url(script):
                    script = save_plugin_config_script(self.scripts_folder, script)
                else:
                    script = os.path.expanduser(data['script'])
                print("Script is %s" % script)

            resource = data['resource']
            if configure_plugin(resource, data['version'], plugins_folder,
                                config_options=values, script=script, script_folder=self.scripts_folder, **kwargs):
                print("Configuration for %s has been created to your likings!" % data['name'])
            else:
                print("Failed to create configuration for %s." % data['name'])

    def run(self):
        print("Collecting requested resources to run the Plugin Resolver by!")
        if not os.path.exists(os.path.expanduser(self.output_folder)):
            try:
                os.makedirs(os.path.expanduser(self.output_folder))
            except OSError:
                print("Unable to create directory: %s" % self.output_folder)
                return

        # Change the working directory to the requested
        # Folder to save plugins in.
        with ChangeDir(os.path.expanduser(self.output_folder)):
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

                file_name = "%s-%s%s" % (name, requested_version, resource.file_type)
                try:
                    download(file_name, download_url, tokens, user_agent)
                    print("Downloaded plugin %s to %s" % (resource.name, file_name))
                except FileNotFoundError:
                    print("Unable to download resource %s from %s" % (resource.name, download_url))

        print("Beginning configuration generation!")
        self.generate_plugin_configuration()
        # Cleanup the access data retrieved by the plugin!

        print("Cleaning the trash!")
        self.__cleanup()
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
