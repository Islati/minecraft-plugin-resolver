Plugin Resolver 🧩
===

## Using McResolver CLI _(.yml requirements file)_
```
$ python -m mcresolver --requirements/-r <config-file> --location/-l <loc_to_store_plugins> (--latest/-u)
```

## Generating configuration templates from existing config.yml
```
$ python -m mcresolver --generate/-g <config-file> --plugin <name>
```

[(Example) Commons Configuration](https://github.com/Islati/minecraft-plugin-config-templates/tree/master/Commons/1.8.8-3)

*Download & Configure plugins automatically 🔧*
An example of this is presented below, for the Bukkit plugin 'Vault', the economy API.

### Configuration example
```yaml

    Bukkit:
      Vault:
        version: 1.5.6
        configure:
          enabled: true
          folder: Vault
          file: config.yml
          #Name of the plugin data folder
          plugin-data-folder: Vault
          # Template link for the processor
          template: https://raw.githubusercontent.com/Islati/minecraft-plugin-config-templates/master/Vault/config.yml
          # Script to create the configuration.
          script: https://github.com/Islati/minecraft-plugin-config-templates/blob/master/Vault/vault_all.py
          # Defaults file gives us values to assign to variables
          defaults: https://github.com/Islati/minecraft-plugin-config-templates/blob/master/Vault/defaults.yml
          # This is vaults config.yml file here, the options are for the config file.
          options:
            update_check: true
```

👉 When we run this:
* ✅ We generate the config folder for vault inside the plugins folder (_'plugins/Vault/'_)
* ✅ Inside the created folder, we generate the _'config.yml'_ file using a mix of `defaults.yml` and the `config.yml` _template_.

The template option is used to render the configuration, where each of the keys and values inside
of the options node is passed to the template to fill it and generate a full config for the plugin.
The templating engine for this is Jinja2, which takes the key (variable name inside the template) and fills it
with the value (example: update_check inside the template, to fill 'update-check: {{update_check}}' will be
rendered to 'update-check: true' in this case, as the value under options is set to true.

_It's really quite simple._

## Example Python script to generate `config.yml` for [Commons](https://github.com/Islati/Commons) 🥽
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

    # Which versions of the plugin this script can configure.
    _plugin_versions_ = ['1.8.8-3']
    # Identifier of the plugin. whether it's the name (bukkit) or id (spigot)
    _plugin_id_ = "15290"  # Spigot resource ID

    
    def configure(parent_folder, config_options={}, **kwargs):
        #TODO: Write your code to configure plugins here.
        pass
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
