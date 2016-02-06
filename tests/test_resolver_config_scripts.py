from bukget import BukkitResource
import os
import shutil
from minecraftpluginresolver.scripts import *


def test_vault_156():
    vault = BukkitResource.from_name('vault', version='latest')
    assert vault is not None
    test_dir, test_script = os.path.split(os.path.abspath(__file__))
    config_dir = os.path.join(test_dir, "plugins")
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)

    assert os.path.exists(config_dir)

    configure_plugin(vault, vault.get_latest_version(), config_dir)

    vault_folder = os.path.join(config_dir, "Vault")
    assert os.path.exists(vault_folder)

    vault_config_file = os.path.join(vault_folder, "config.yml")

    assert os.path.exists(vault_config_file) and os.path.isfile(vault_config_file)
    assert "update-check: true" in get_config_from_file(os.path.join(vault_folder, vault_config_file))

    configure_plugin(vault, vault.get_latest_version(), config_dir, config_options={'update_check': 'false'})

    shutil.rmtree(config_dir)
    assert not os.path.exists(config_dir)


def test_commons_1883():
    commons = SpigotResource.from_id('15290')
    assert commons is not None
    test_dir, test_script = os.path.split(os.path.abspath(__file__))
    config_dir = os.path.join(test_dir, "plugins")
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)

    assert os.path.exists(config_dir)

    configure_plugin(commons, "1.8.8-3", config_dir)

    commons_folder = os.path.join(config_dir, "Commons")
    assert os.path.exists(commons_folder)

    commons_config_file = os.path.join(commons_folder, "config.yml")

    assert os.path.exists(commons_config_file) and os.path.isfile(commons_config_file)
    configure_plugin(commons, commons.get_latest_version(), config_dir,
                     config_options={'enable_join_messages': 'false'}, config_type='yml')
    assert "enable-join-message: false" in get_config_from_file(os.path.join(commons_folder, commons_config_file))

    configure_plugin(commons, commons.get_latest_version(), config_dir,
                     config_options={'enable_join_messages': 'false'}, config_type='xml')

    commons_config_file = os.path.join(commons_folder, "config.xml")

    assert '<enable-join-messages>false</enable-join-messages>' in get_config_from_file(
        os.path.join(commons_folder, commons_config_file))

    shutil.rmtree(config_dir)
    assert not os.path.exists(config_dir)
