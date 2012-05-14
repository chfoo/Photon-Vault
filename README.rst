============
Photon Vault
============
+++++++++++++++++++++++
Web-based photo manager
+++++++++++++++++++++++

Photon Vault is a simple web-based photo manager for your home's LAN. Use Photon Vault to keep your photos organized on a single computer.

Installation
============

You will need:

1. Python 2.7 (http://python.org)
2. Tornado Web (forked at https://github.com/chfoo/tornado)
3. pyexiv2 (http://tilloy.net/dev/pyexiv2/)
4. Python Image Library (PIL) (http://www.pythonware.com/products/pil/)
5. MongoDB (http://mongodb.org/)
6. pymongo

Python packages can be obtained from their respective websites, http://pypi.python.org, unofficial packages/installers, and easy_install. GNU/Linux users should use their distribution package managers.

Standalone directory layout
+++++++++++++++++++++++++++

Photon Vault works well as a standalone program. 

Here is an example directory layout::

    my_photos/
        mongodb/
            bin/
            data/
        photonvault/
        tornado/
        config.conf

Ready to use service installers are not yet available.

Getting started
===============

You can invoke the photonvault package like so::

    python -m photonvault.main config.conf

Then, open your web browser and go to http://localhost:8000. You can now upload, edit, and browse photos. Other computers can connect as well. There is no login system in place; anyone can edit the photos.

News
====

The official project page is http://launchpad.net/photonvault. A courtesy GitHub project is located at https://github.com/chfoo/Photon-Vault. (Best of both worlds ☺)


Bugs
++++

Important issues:

 * Uploading tar+gz and tar+bzip may not work. This issue will be investigated.

Todo
++++

Features that will be implemented:

 * Delete uploaded photos
 * Prevent uploading duplicates

Changelog
+++++++++

Version 1.0
-----------

First release to support upload, editing, tagging, and browsing.

