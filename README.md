#Minecraft Plugin Resolver 🧩

Download & Configure plugins to automate your Minecraft server deployment 🔧



An example of this is Commons, the plugin framework also hosted on my GitHub account.
Commons supports multiple types of configuration, many options in the config, and
requires a few other files to function. (data-option.txt)

Though in simple use cases, there should be nodes available to script the configuration
generation simply though yml.

An example of this is presented below, for the Bukkit plugin 'Vault', the economy API.

   Vault: (config.yml)
```yaml

    Bukkit:
      Vault:
        version: 1.5.6
        configure:
          enabled: true
          folder: Vault
          file: config.yml
          config-template: https://raw.githubusercontent.com/TechnicalBro/minecraft-plugin-config-templates/master/Vault/config.yml
          config-defaults:
          options:
            update_check: true
```

In the above example, we're generating the folder where Vault stores its configuration
('Vault', inside the plugins folder; 'plugins/Vault'), along with a 'config.yml' file
to store the configuration of vault, inside the created folder.

The template option is used to render the configuration, where each of the keys and values inside
of the options node is passed to the template to fill it and generate a full config for the plugin.
The templating engine for this is Jinja2, which takes the key (variable name inside the template) and fills it
with the value (example: update_check inside the template, to fill 'update-check: {{update_check}}' will be
rendered to 'update-check: true' in this case, as the value under options is set to true.

_It's really quite simple._

The next option, is to provide the ability to execute a python script that handles the configuration
of plugins. With a simple, yet robust set of features inside the 'scripts' package along with the power
of Python, the possibilities are endless. The only thing that's required is a specific (base) structure
for the script is present, and the rest is up to the user!

Here's an example of what the configuration script for Commons would look like.

```python
    from minecraftpluginresolver.scripts import *

    _plugin_versions_ = ['1.8.8-3']
    _plugin_id_ = "15290"  # Spigot resource ID

    __config_template__ = "https://raw.githubusercontent.com/TechnicalBro/minecraft-plugin-config-templates/master/Commons/1.8.8-3/config.%s"
    __config_defaults__ = "https://raw.githubusercontent.com/TechnicalBro/minecraft-plugin-config-templates/feature-1-yaml-scripting-python-hooks/Commons/1.8.8-3/defaults.yml"

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
```

There are 3 required components for a configuration script. If you notice in the above example there's the following.

```python

    _plugin_versions_ = ['1.8.8-3']
    _plugin_id_ = "15290"  # Spigot resource ID

    .....

    def configure(parent_folder, config_options={}, **kwargs):
        ...
 ```

The plugin_versions is a list of all the versions (of the plugin) that this script can configure for.
Required, as most plugins have their configuration change throughout time.

The plugin_id is the identifier of the plugin, whether it's the name (Bukkit) or id (Spigot). This is required
to verify that the plugin we're configuring for is handled by a specific script.

Yay metavars!!! 🧪

Lastly, we've got the configure method, which takes a parent_folder parameter, config_options dictionary, and then
a variable amount of keyword arguments.

In the above example Commons depends on the config_type kwarg, to determine what kind of configuration to use:
Xml or Yml, as it support both.

In future versions of the resolver, there will likely be support for pulling plugins of a private URL, such as
a Jenkins build server, ftp host, direct link, so forth; Though that can be tackled when the time comes.
