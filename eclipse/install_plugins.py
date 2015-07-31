import sys
import subprocess
import os

UPDATE_SITE_INSTALLS = {
    'egit': (
             'http://download.eclipse.org/egit/updates/', 
             'org.eclipse.egit',
             ),
    # currently doesn't work via update site :(
    # 'pydev': (
    #          'http://pydev.org/updates/', 
    #          'org.python.pydev.feature.feature.group',
    #          ),
    'theme': (
             'http://eclipse-color-theme.github.io/update/', 
             'com.github.eclipsecolortheme.feature.feature.group',
             ),
}

def get_eclipse_install_cmd(eclipse_path, update_site, feature_group):
    return (
            os.path.join(eclipse_path, 'eclipse'),
            '-nosplash',
            '-application', 'org.eclipse.equinox.p2.director',
            '-repository', update_site,
            '-destination', eclipse_path,
            '-installIU',  feature_group,
            )

if __name__ == '__main__':
    valid_plugin_names = ', '.join(sorted(UPDATE_SITE_INSTALLS.keys()))
    if len(sys.argv) == 1 or len(sys.argv) > 3:
        print("%s <eclipse_directory> <plugin_name_csv(optional)>" % __file__)
        print("Valid plugin names are %s" % valid_plugin_names)
        sys.exit(1)

    eclipse_dir = sys.argv[1]
    assert os.path.isdir(eclipse_dir), "Bad eclipse directory"
    assert os.path.isfile(os.path.join(eclipse_dir, 'eclipse')), "Couldn't find eclipse executable"

    if len(sys.argv) == 3:
        plugin_names = sys.argv[2].split(',')
        invalid_names = tuple(n for n in plugin_names if n not in UPDATE_SITE_INSTALLS)
        assert not invalid_names, ("Invalid plugin name(s) given: %s. "
                                   "Valid names are: %s" % (','.join(invalid_names),
                                                            valid_plugin_names))
        plugin_info = tuple(UPDATE_SITE_INSTALLS[name] 
                            for name in sys.argv[2].split(','))
    else:
        plugin_info = tuple(sorted(UPDATE_SITE_INSTALLS.values()))

    for update_site, feature_group in plugin_info:
        p = subprocess.Popen(
                             get_eclipse_install_cmd(
                                                     eclipse_dir,
                                                     update_site,
                                                     feature_group,
                                                    ),
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




