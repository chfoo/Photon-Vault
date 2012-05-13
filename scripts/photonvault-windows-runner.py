'''Simple script to run under Windows'''

import subprocess

def main():
    mongo_p = subprocess.Popen(['mongodb/bin/mongod.exe', '--dbpath',
                                'mongodb/data/db/'])
    photon_p = subprocess.Popen(['c:/program files/python2.7/python.exe', '-m',
                                 'photonvault.main', 'config.conf'])
    photon_p.wait()
    mongo_p.wait()


if __name__ == '__main__':
    main()
