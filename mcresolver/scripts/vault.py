from mcresolver.scripts import *

_plugin_versions_ = ['all']
_plugin_id_ = "vault"

__config_template__ = "https://raw.githubusercontent.com/TechnicalBro/minecraft-plugin-config-templates/master/Vault/config.yml"

__config_defaults = {
    'update_check': 'true'
}


def configure(parent_folder, config_options={}, **kwargs):
    vault_folder = os.path.join(parent_folder, 'Vault')

    if not os.path.exists(vault_folder):
        os.makedirs(vault_folder)

    config_file = os.path.join(vault_folder, 'config.yml')

    options = merge_configuration_options(config_options, __config_defaults)

    yml_data = render_config_from_url(__config_template__, variables=options)
    write_file(config_file, yml_data)
