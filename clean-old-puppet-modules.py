#!/usr/bin/env python
from __future__ import print_function

# clean-old-puppet-modules.py is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

import os
import re
import sys
from distutils.version import LooseVersion
import subprocess

links = []
broken = []
modules = []
two_last_modules = {}

for dirpath, dirnames, filenames in os.walk('.', followlinks=False):
  for filename in filenames:
    if re.search('__latest', filename): 
      path = os.path.join(dirpath,filename)
      if os.path.islink(path):
        target_path = os.readlink(path)
        # Resolve relative symlinks
        if not os.path.isabs(target_path):
          target_path = os.path.join(os.path.dirname(path),target_path)             
        if not os.path.exists(target_path):
          broken.append(path)
  for dirname in dirnames:
    if re.search('__latest', dirname):
      path = os.path.join(dirpath,dirname)
      if os.path.islink(path):
        target_path = os.readlink(path)
        # Resolve relative symlinks
        if not os.path.isabs(target_path):
          target_path = os.path.join(os.path.dirname(path),target_path)             
        if not os.path.exists(target_path):
          broken.append(path)
        else:
          links.append(path)

for b in broken:
  print('This link is broken. Need fixed it: ', b)

for l in links:
  module_name = re.sub(r'__latest', '', l)
  module_name = re.sub(r'./', '', module_name)
  if not module_name in modules:
    # print(module_name)
    modules.append(module_name)

for dirpath, dirnames, filenames in os.walk('.', followlinks=False):
  for dirname in dirnames:
    if re.search('__v', dirname):
      for module in modules:
        dirname_before__v = re.split("__v", dirname)[0]
        if module == dirname_before__v:
          if not module in two_last_modules:
            current_version_dirname = re.split("__v", dirname)[1]
            current_version_dirname = re.sub(r'_', '.', current_version_dirname)
            two_last_modules[module] = [current_version_dirname]
          else:
            current_version_dirname = re.split("__v", dirname)[1]
            current_version_dirname = re.sub(r'_', '.', current_version_dirname)
            two_last_modules[module].append(current_version_dirname)

for module,versions_list in two_last_modules.iteritems():
  if len(versions_list) > 2:
    sorted_list = sorted(versions_list, key=LooseVersion)
    two_last_modules[module] = sorted_list

for module,sorted_list in two_last_modules.iteritems():
  if len(sorted_list) > 2:
    print(module,sorted_list)

print('#################################################################')

for module,sorted_list in two_last_modules.iteritems():
  if len(sorted_list) > 2:
    list_for_delete = sorted_list[:-2]
    print('--------------------------')
    # print(module,list_for_delete)
    for version_for_delete in list_for_delete:
      version_for_delete = re.sub(r'\.', '_', version_for_delete)
      folder_name = '{0}__v{1}'.format(module,version_for_delete)
      if len(os.listdir(folder_name)) == 0:
        print('Remove empty folder: ', folder_name)
        os.rmdir(folder_name)
      else:
        print('Check directory: ', folder_name)
        process = subprocess.Popen("rpm -qf manifests", shell=True, stdout=subprocess.PIPE, cwd=folder_name)
        version_package_for_delete, error = process.communicate()
        print('Remove old package: ', version_package_for_delete)
        process = subprocess.Popen("yum -y remove {0}".format(version_package_for_delete), shell=True, stdout=subprocess.PIPE)
        output, error = process.communicate()
