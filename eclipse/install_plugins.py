from __future__ import division
import abc
import collections
import logging
import time
import os
import subprocess
import sys
import zipfile

try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen

try:
    long()
except NameError:
    long = int

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.StreamHandler(sys.stdout))
LOGGER.setLevel(logging.DEBUG)


PLUGIN_INSTALLS = {
    'egit': UpdateSiteInstall(
                              'http://download.eclipse.org/egit/updates/',
                              'org.eclipse.egit',
                             ),
    # currently doesn't work via update site :(
    'pydev': ZipDropInInstall(
                              'http://downloads.sourceforge.net/project/pydev/pydev/PyDev%204.2.0/PyDev%204.2.0.zip',
                             ),
    'theme': UpdateSiteInstall(
                               'http://eclipse-color-theme.github.io/update/',
                               'com.github.eclipsecolortheme.feature.feature.group',
                              ),
}

class AbstractInstall(object):
    @abc.abstractmethod
    def install(self):
        raise NotImplementedError()
AbstractInstall = abc.ABCMeta(
                              AbstractInstall.__name__,
                              AbstractInstall.__bases__,
                              vars(AbstractInstall).copy(),
                              )

class AbstractDropInInstall(AbstractInstall):
    def __init__(self, archive_url):
        self.archive_url = archive_url
        assert (archive_url.startswith('http://') or
                archive_url.startswith('https://')), "Bad url prefix for: %s" % archive_url
        self.dl_filename = archive_url.split('/')[-1]

    @abc.abstractmethod
    def decompress_archive(self, archive_path, dropins_dir):
        raise NotImplementedError

    def install(self, eclipse_dir):
        dropins_dir = os.path.join(eclipse_dir, 'dropins')
        assert os.path.isdir(dropins_dir), "Missing dropins dir: %s" % dropins_dir
        full_path = os.path.join(dropins_dir, self.dl_filename)
        LOGGER.info("Downloading %s" % full_path)
        dl = urlopen(self.archive_url)
        try:
            start_time = time.time()
            with open(full_path, 'wb') as archive_file:
                archive_file.write(dl.read())
            LOGGER.info("Elapsed for dl: %0.fms" % ((time.time() - start_time) * 1000))
            self.decompress_archive(full_path, dropins_dir)
        finally:
            if os.path.exists(full_path):
                os.unlink(full_path)


class ZipDropInInstall(AbstractDropInInstall):
    def decompress_archive(self, archive_path, dropins_dir):
        with zipfile.ZipFile(archive_path, "r") as z:
            z.extractall(dropins_dir)

class UpdateSiteInstall(AbstractInstall):
    def __init__(self, update_site, feature_group):
        self.update_site = update_site
        self.feature_group = feature_group

    def get_eclipse_install_cmd(self, eclipse_path):
        return (
                os.path.join(eclipse_path, 'eclipse'),
                '-nosplash',
                '-application', 'org.eclipse.equinox.p2.director',
                '-destination', eclipse_path,
                '-repository', self.update_site,
                '-installIU',  self.feature_group,
                )

    def install(self, eclipse_dir):
        p = subprocess.Popen(
                             self.get_eclipse_install_cmd(eclipse_dir),
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT,
                             )
        output = 'start'
        while output:
            output = p.stdout.readline().decode('utf-8')
            print(output)
        p.wait()
        if p.returncode != 0:
            raise Exception("Command failed, returned %d" % p.returncode)

if __name__ == '__main__':
    sorted_plugin_names = sorted(PLUGIN_INSTALLS.keys())
    valid_plugin_names = ', '.join(sorted_plugin_names)
    if len(sys.argv) == 1 or len(sys.argv) > 3:
        print("%s <eclipse_directory> <plugin_name_csv(optional)>" % __file__)
        print("Valid plugin names are %s" % valid_plugin_names)
        sys.exit(1)

    eclipse_dir = sys.argv[1]
    assert os.path.isdir(eclipse_dir), "Bad eclipse directory"
    assert os.path.isfile(os.path.join(eclipse_dir, 'eclipse')), "Couldn't find eclipse executable"

    if len(sys.argv) == 3:
        plugin_names = sys.argv[2].split(',')
        invalid_names = tuple(n for n in plugin_names if n not in PLUGIN_INSTALLS)
        assert not invalid_names, ("Invalid plugin name(s) given: %s. "
                                   "Valid names are: %s" % (','.join(invalid_names),
                                                            valid_plugin_names))
        plugin_info = {name: PLUGIN_INSTALLS[name] for name in plugin_names}
    else:
        plugin_info = {name: PLUGIN_INSTALLS[name] for name in sorted_plugin_names}

    for name, plugin in sorted(plugin_info.items()):
        LOGGER.info("Installing %s" % name)
        plugin.install(eclipse_dir)



