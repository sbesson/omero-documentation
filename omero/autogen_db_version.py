#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import glob
import os
import re
import sys

from pathlib import Path
from pkg_resources import parse_version


def get_mmp(sqlfile):
    # Only consider files/folders with version
    # OMERO<major>.<minor>__<patch>
    m = re.search(r'.*/?OMERO(\d+)\.(\d+)__(\d+)', sqlfile)
    if m is None:
        return None
    mmp = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return mmp


serverdir = Path(sys.argv[1])

current_mmp = None
current_version = None
directory = os.path.join(serverdir, 'sql', 'psql')
subfolders = [f.path for f in os.scandir(directory) if f.is_dir()]
for f in subfolders:
    ver = os.path.basename(os.path.normpath(f))
    if get_mmp(ver) is None:
        continue
    if current_version is None:
        current_version = ver
        current_mmp = get_mmp(current_version)
    else:
        if get_mmp(current_version) < get_mmp(ver):
            current_version = ver
            current_mmp = get_mmp(current_version)

sqlfiles = []
majorminorpatch = []
for f in glob.glob(os.path.join(directory, current_version, 'OMERO*.sql')):
    sql = os.path.basename(f)[:-4]
    mmp = get_mmp(sql)
    if mmp is None:
        continue
    majorminorpatch.append(mmp)
    sqlfiles.append(sql)

majorminorpatch = sorted(
    majorminorpatch, key=lambda m: (-m[0], -m[1], -m[2]))
for previous_mmp in majorminorpatch:
    if previous_mmp[0] < current_mmp[0] or (
            previous_mmp[0] == current_mmp[0] and
            previous_mmp[1] < current_mmp[1]):
        break


with open(sys.argv[2], "r") as sources:
    lines = sources.readlines()
with open(sys.argv[2], "w") as sources:
    for line in lines:
        if line.startswith("current_dbver"):
            sources.write('current_dbver = "%s"' % current_version)
            sources.write("\n")
        elif line.startswith("previous_dbver"):
            sources.write('previous_dbver = "OMERO%d.%d__%d"' % previous_mmp)
            sources.write("\n")
        else:
            sources.write(line)

#print('current_dbver = "%s"' % current_dbver)
#print('previous_dbver = "OMERO%d.%d%s__%d"' % previous_mmp)
