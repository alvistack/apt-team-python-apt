#!/usr/bin/python
#
# Copyright (C) 2010 Michael Vogt <mvo@ubuntu.com>
#
# Copying and distribution of this file, with or without modification,
# are permitted in any medium without royalty provided the copyright
# notice and this notice are preserved.
"""Unit tests for verifying the correctness of apt.progress"""
import unittest

import apt
import apt_pkg
import os

class TestAcquireProgress(apt.progress.base.AcquireProgress):
    def pulse(self, owner):
        self.pulsed = True

class TestProgress(unittest.TestCase):

    def setUp(self):
        basedir = os.path.abspath(os.path.dirname(__file__))
        # setup apt_pkg config
        apt_pkg.init()
        apt_pkg.config.set("APT::Architecture", "amd64")
        apt_pkg.config.set("Dir::Etc", basedir)
        apt_pkg.config.set("Dir::Etc::sourceparts", "/xxx")
        # setup lists dir
        if not os.path.exists("./tmp/partial"):
            os.makedirs("./tmp/partial")
        apt_pkg.config.set("Dir::state::lists", "./tmp")
        # create artifical line
        deb_line = "deb file:%s/data/fake-packages/ /\n" % basedir
        open("fetch_sources.list","w").write(deb_line)
        apt_pkg.config.set("Dir::Etc::sourcelist", "fetch_sources.list")

    def test_acquire_progress(self):
        progress = TestAcquireProgress()
        cache = apt.Cache()
        res = cache.update(progress)
        self.assertTrue(progress.pulsed)

if __name__ == "__main__":
    unittest.main()
