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
7. python-iso8601

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

 * A label with "None" may be visible if there are no real tags

Todo
++++


Changelog
+++++++++

Version 1.2
-----------

 * Duplicates will be detected by date and filename during processing. This occurs for new files that are uploaded. 
   * Fingerprints are the first 4 bytes of a MD5 hash of {the lowercased filename and the ISO8601 date} concatenated with the last two bytes of the lowercased filename without an extension. This method is suited for JPEG files named like IMAGE_123456.jpg. Using truncated hashes of filenames and dates allows the fingerprint to be short and fast to compute which should be sufficient for home usage.
 * Will not crash on start up if the database isn't ready yet

Version 1.1
-----------

 * Support deleting photos through Manage
 * Improved navigation

Version 1.0
-----------

First release to support upload, editing, tagging, and browsing.

