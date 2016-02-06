from bukget import BukkitResource
import fnmatch
from importlib.util import spec_from_file_location
import os
from spiget import SpigotResource
from jinja2 import Environment
import requests
import yaml

__dirname, __init_python_script = os.path.split(os.path.abspath(__file__))


def get_config_from_url(url):
    return requests.get(url).text


def render_config_from_url(url, variables):
    config_data = get_config_from_url(url)
    return Environment().from_string(config_data).render(variables)


def render_config_from_string(config, variables):
    return Environment().from_string(config).render(variables)


def merge_configuration_options(config_options=None, defaults={}):
    """
    Merge all the nodes that are not present in config_options from defaults,
    to assure that the values passed to the template have an option to fill every node.

    :param config_options: Options that were passed to render the configuration by.
    :param defaults: Default values of configuration nodes, to fill in the blanks if missing in config_options
    :return: A dictionary of configuration options filled with all the missing values required to render a template.
    """

    if not config_options:
        config_options = {}

    options = config_options.copy()

    for key, value in defaults.items():
        if key not in options.keys():
            options[key] = value

    return options


def get_configuration_defaults(url=None, file=None):
    """
    Creates a dictionary of the default configuration values to provide when
    a value or option is not specified.

    Can be retrieved via a URL, or read from a file.

    :param url: URL of the page which contains the raw template defaults (think hosting a text file on a website)
    :param file: File to read the template defaults from.
    :return: Dictionary indexed by the key (template variable) and the value assigned to that template variable.
    """

    if url is None and file is None:
        raise ValueError("You must include either a url to retrieve the defaults from, or a file to read them from")

    defaults = {}
    template_default_content = None
    if url is not None:
        template_default_content = get_config_from_url(url)
    elif file is not None:
        template_default_content = get_config_from_file(file)

    if template_default_content is None:
        raise Exception("Unable to retrieve the configuration defaults from url or file")

    defaults = yaml.load(template_default_content)
    return defaults


def configure_plugin(resource, version, parent_folder, config_options=None, **kwargs):
    configuration_script = __get_configuring_script(resource, version)

    if configuration_script is None:
        return False

    configure_method = getattr(configuration_script, 'configure')
    if configure_method is None:
        raise AttributeError("Unable to find 'configure' method in configuration script")

    configure_method(parent_folder, config_options=config_options, **kwargs)
    return True


def get_config_from_file(file):
    with open(file, 'r') as config_file:
        return config_file.read().replace('\n', '')


def write_config_to_file(file, yaml):
    with open(file, 'w') as yaml_file:
        yaml_file.write(yaml)


def __get_plugin_identifier(resource):
    plugin_identifier = None

    if isinstance(resource, BukkitResource):
        plugin_identifier = resource.plugin_name
    elif isinstance(resource, SpigotResource):
        plugin_identifier = resource.resource_id
    else:
        return None

    return plugin_identifier


def __get_configuring_script(resource, version):
    plugin_identifier = str(__get_plugin_identifier(resource))
    config_script_names = __get_files_recursive(__dirname, "*.py")

    for config_script in config_script_names:
        if "__init__" in config_script:
            continue

        config_module = __import_module_from_file(config_script)

        if config_module is None:
            continue

        if not hasattr(config_module, "configure"):
            continue

        if not hasattr(config_module, '_plugin_id_'):
            continue

        if not hasattr(config_module, '_plugin_versions_'):
            continue

        config_plugin_id = getattr(config_module, "_plugin_id_")
        config_plugin_versions = getattr(config_module, "_plugin_versions_")

        if config_plugin_id is None or config_plugin_versions is None:
            continue

        if plugin_identifier.lower() != config_plugin_id.lower():
            continue

        # Version checking in a list, that way a config script can support multiple versions
        found_version = False

        if "all" in config_plugin_versions:
            found_version = True

        if found_version is False:
            for usable_version in config_plugin_versions:
                if version.lower() in usable_version.lower():
                    found_version = True
                    break

        if found_version:
            return config_module

    return None


def __get_files_recursive(path, match='*.py'):
    matches = []
    for root, dirnames, filenames in os.walk(path):
        for filename in fnmatch.filter(filenames, match):
            matches.append(os.path.join(root, filename))
        break
    return matches


def __import_module_from_file(full_path_to_module):
    """
    Import a module given the full path/filename of the .py file
    Python 3.4
    """

    module = None

    try:

        # Get module name and path from full path
        module_dir, module_file = os.path.split(full_path_to_module)
        module_name, module_ext = os.path.splitext(module_file)

        # Get module "spec" from filename
        spec = spec_from_file_location(module_name, full_path_to_module)

        module = spec.loader.load_module()

    except Exception as ec:
        # Simple error printing
        # Insert "sophisticated" stuff here
        print(ec)

    finally:
        return module
