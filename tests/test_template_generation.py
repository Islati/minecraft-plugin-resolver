import textwrap
from collections import OrderedDict
import yaml
from yamlbro import install_patch, restore_yaml_comments

install_patch()
print("Installed yaml patch")

from mcresolver.scripts import write_file
import os


def test_template_generation():
    def get_name_from_key(key):
        return key.lower().replace('-', '_').replace('.', '_')

    __dirname, __init_python_script = os.path.split(os.path.abspath(__file__))
    ess_file = os.path.join(__dirname, 'essentials.yml')

    with open(ess_file, 'r') as yaml_file:
        default_essentials_config = yaml.safe_load(yaml_file)

    essentials_config = default_essentials_config.copy()

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

    flat_dictionary_template = OrderedDict()

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

    for key, value in default_essentials_config.items():
        if isinstance(value, dict) or isinstance(value, OrderedDict):
            # replica_dict[key] = value
            recursive_dictionary_collect(flat_dictionary_template, key, value)
        else:
            if isinstance(value, list):
                value.append('mcresolverdepth=1')  # Hack around the template, and add the depth to prepend to the node
            flat_dictionary_template[key] = value

    template_defaults = OrderedDict()
    node_types = {}

    for key, value in flat_dictionary_template.items():
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

            template_defaults[node_name] = tdval
            node_types[node_name] = value_type
            node_type = tdval.__class__.__name_
        except:
            template_defaults[node_name] = value
            node_types[node_name] = value_type
            node_type = value_type.__class__.__name__
        flat_dictionary_template[key] = "{{{{{node}}}}}".format(node=node_name)

    essentials_template = OrderedDict()

    for key, value in flat_dictionary_template.items():
        # print("Key %s=%s (%s)" % (key, value, type(value).__name__))
        assign_dict_nested_path(essentials_template, key, value)
        # print("%s=%s" % (node_name, value))

    # print(essentials_template)

    # config_yaml = default_essentials_config.dump(default_flow_style=False)
    # print(config_yaml)
    #

    essentials_template_dump = yaml.dump(essentials_template, default_flow_style=False, indent=2, width=1000)

    with open(ess_file, 'r') as essentials_default_data:
        default_essentials_data = essentials_default_data.read()

    essentials_template_dump = restore_yaml_comments(essentials_template_dump, default_essentials_data)

    for node, type in node_types.items():
        if type == "bool" or type == "int" or type == "float":
            essentials_template_dump = essentials_template_dump.replace("'{{{{{node}}}}}'".format(node=node),
                                                                        "{{{{{node}}}}}".format(node=node))
        elif type == "str":
            continue
        elif type == "list":
            item_list = template_defaults[node]
            depth = 2
            list_items = []
            for line in item_list:
                if 'mcresolverdepth' in line:
                    depth = int(line.split('=')[1])
                else:
                    list_items.append(line)

            depth = depth * 2
            item_depth = depth + 2

            # item_list = [line for line in item_list if 'mcresolverdepth' not in line]
            template_defaults[node] = list_items
            loop_statement = "\n{{% for {node}_item in {node} %}}{depth}- {{{{{node}_item}}}}\n{{% endfor %}}"
            loop_statement = loop_statement.format(depth=' ' * depth, node=node)
            essentials_template_dump = essentials_template_dump.replace(" '{{{{{node}}}}}'".format(node=node),
                                                                        loop_statement)

    # print(essentials_template_dump)
    essentials_final_template = ""
    for line in essentials_template_dump.splitlines():
        if 'mcresolverdepth' in line:
            print("Found depth line in %s" % line)
        else:
            essentials_final_template += line + "\n"

    defaults_dump = yaml.dump(template_defaults, default_flow_style=False)
    defaults_dump = defaults_dump.replace(": none", ": ")

    for key, value in template_defaults.items():
        assert key in defaults_dump
        assert key in essentials_template_dump
