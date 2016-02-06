from minecraftpluginresolver.scripts import *

_plugin_versions_ = ['1.8.8-3']
_plugin_id_ = "15290"  # Spigot resource ID

__config_template__ = "https://raw.githubusercontent.com/TechnicalBro/minecraft-plugin-config-templates/master/Commons/1.8.8-3/config.%s"
__config_defaults__ = "https://raw.githubusercontent.com/TechnicalBro/minecraft-plugin-config-templates/master/Commons/1.8.8-3/defaults.yml"


def configure(parent_folder, config_options={}, **kwargs):
    commons_folder = os.path.join(parent_folder, 'Commons')

    if not os.path.exists(commons_folder):
        os.makedirs(commons_folder)

    # Get the default configuration values for Commons, incase some aren't present in the options.
    defaults = get_configuration_defaults(url=__config_defaults__)

    # Create a full dictionary of all the options required to render the template, merging
    # in the missing values from the default config.
    options = merge_configuration_options(config_options, defaults)

    # Commons supports multiple configuration options, yml and xml (likely more in the future)
    # So a kwarg is optionally passed to specify the type of configuration to render.
    config_type = kwargs.get('config_type', 'yml')

    config_file = os.path.join(commons_folder, 'config.%s' % config_type)

    # Render the configuration of Commons from the url, with the options (and defaults included)
    commons_config = render_config_from_url(__config_template__ % config_type, options)
    # Lastly write the configuration to the file specified!
    write_config_to_file(config_file, commons_config)
    print("Configuration for Commons 1.8.8-3 has been rendered!")
