import os
import spiget
import subprocess
from tqdm import tqdm
import wget
import cfscrape


# todo if unable to locate resource then revert to using latest version?

def parse_spigot_resources(file):
    resources = {}
    with open(file, 'r') as lines:
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

    print("Parsed Resources")
    print(resources)
    return resources


def download(filename, url, cookies, useragent):
    scraper = cfscrape.create_scraper()
    with open(filename, 'wb') as handle:
        response = scraper.get(url, cookies=cookies, headers={"User-Agent": useragent}, stream=True)

        if not response.ok:
            raise FileNotFoundError(
                'Unable to locate the resource %s at %s; Assure its valid in your spigot.txt file' % (filename, url))
        # Something went wrong

        for block in tqdm(response.iter_content(1024)):
            handle.write(block)


if __name__ == "__main__":
    #TODO implement retrieval of file extension if not jar.
    #todo implement version compare of local file for potentially updating plugin without replacing?
    print("Retrieving Cloudflare Information")
    tokens, user_agent = cfscrape.get_tokens('http://www.spigotmc.org')

    desired_resources = parse_spigot_resources(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'spigot.txt'))
    for resource_id, resource_version in desired_resources.items():
        resource = None
        if resource_version.lower() == "latest":
            resource = spiget.get_resource(resource_id)
        else:
            resource = spiget.get_resource(resource_id, resource_version)

        resource_versioned_name = "%s.jar" % resource_id

        if 'name' not in resource:
            # Todo it's version specific, so we need to parse the name manually.
            print(resource)
            print("Unable to locate name value on resource (%s %s)" % (resource_id, resource_version))
        else:
            resource_versioned_name = "%s-%s.jar" % (resource['name'], resource['version'])

        print("Retrieving information for '%s'" % resource_versioned_name)
        url = spiget.get_resource_download(resource_id, resource_version)
        print("Downloading %s from %s" % (resource_versioned_name, url))
        try:
            download(resource_versioned_name, url, tokens, user_agent)
            print("Downloaded %s" % resource_versioned_name)
        except FileNotFoundError:
            print("Invalid Resource: %s (Version: %s)" % (resource_id, resource_versioned_name))
            continue

            # resource = spiget.get_resource('Commons')
            # print("Resource Name: %s" % resource_versioned_name)
            #
            # print("Retrieving download link for %s" % resource_versioned_name)
            # url = spiget.get_resource_download('Commons')
            #
            # print("Downloading File: %s" % resource_versioned_name)
            # download(resource_versioned_name, url, tokens, user_agent)
            # print("File Downloaded")
            #
            # # http_process = subprocess.Popen(
            # #     "http 'Cookie: %s' --download --continue --output %s %s" % (
            # #         "__cfduid=d105fd6f81194d37a13bd07832ccff7a31453829175; expires=Wed, 25-Jan-17 17:26:15 GMT; path=/; domain=.spigotmc.org; HttpOnly",
            # #         resource_versioned_name,
            # #         url.replace('\n','')
            # #     ),
            # #     shell=True, stdout=subprocess.PIPE,
            # #     stderr=subprocess.STDOUT)
            # #
            # # for line in http_process.stdout.readlines():
            # #     print(line)
            # #
            # # val = http_process.wait()
