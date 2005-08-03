# cache.py - apt cache abstraction
#  
#  Copyright (c) 2005 Canonical
#  
#  Author: Michael Vogt <michael.vogt@ubuntu.com>
# 
#  This program is free software; you can redistribute it and/or 
#  modify it under the terms of the GNU General Public License as 
#  published by the Free Software Foundation; either version 2 of the
#  License, or (at your option) any later version.
# 
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
# 
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
#  USA

import apt_pkg
from apt import Package
from apt.progress import OpTextProgress
from UserDict import UserDict

class Cache(object):
    """ Package cache object """
    def __init__(self, progress=None):
        self._callbacks = {}
        self.Open(progress)

    def _runCallbacks(self, name):
        """ internal helper to run a callback """
        if self._callbacks.has_key(name):
            for callback in self._callbacks[name]:
                apply(callback)
        
    def open(self, progress):
        """ Open the package cache, after that it can be used like
            a dictionary
        """
        self._runCallbacks("cache_pre_open")
        self._cache = apt_pkg.GetCache(progress)
        self._depcache = apt_pkg.GetDepCache(self._cache)
        self._records = apt_pkg.GetPkgRecords(self._cache)
        self._dict = {}


        # build the packages dict
        if progress != None:
            progress.Op = "Building data structures"
        i=last=0
        size=len(self._cache.Packages)
        for pkg in self._cache.Packages:
            if progress != None and last+100 < i:
                progress.update(i/float(size)*100)
                last=i
            # drop stuff with no versions (cruft)
            if len(pkg.VersionList) > 0:
                self._dict[pkg.Name] = Package(self._cache, self._depcache,
                                               self._records, self, pkg)
            i += 1
        if progress != None:
            progress.done()
        self._runCallbacks("cache_post_open")
        
    def __getitem__(self, key):
        return self._dict[key]

    def has_key(self, key):
        try:
            self._dict[key]
        except KeyError:
            return False
        return True

    def __len__(self):
        return len(self._dict)

    def keys(self):
        return self._dict.keys()

    def getChanges(self):
        """ Get the marked changes """
        changes = [] 
        for name in self._dict.keys():
            p = self._dict[name]
            if p.markedUpgrade() or p.markedInstall() or p.markedDelete() or \
               p.markedDowngrade() or p.markedReinstall():
                changes.append(p)
        return changes

    def upgrade(self, DistUpgrade=False):
        """ Upgrade the all package, DistUpgrade will also install
            new dependencies
        """
        self.cachePreChange()
        self._depcache.Upgrade(DistUpgrade)
        self.cachePostChange()

    def commit(self, fprogress, iprogress):
        """ Apply the marked changes to the cache """
        self._depcache.Commit(fprogress, iprogress)

    # cache changes
    def cachePostChange(self):
        " called internally if the cache has changed, emit a signal then "
        self._runCallbacks("cache_post_change")

    def cachePreChange(self):
        """ called internally if the cache is about to change, emit
            a signal then """
        self._runCallbacks("cache_pre_change")

    def connect(self, name, callback):
        """ connect to a signal, currently only used for
            cache_{post,pre}_changed """
        if not self._callbacks.has_key(name):
            self._callbacks[name] = []
        self._callbacks[name].append(callback)

# ----------------------------- experimental interface
class Filter(object):
    """ Filter base class """
    def apply(self, pkg):
        """ Filter function, return True if the package matchs a
            filter criteria and False otherwise
        """
        return True

class MarkedChangesFilter(Filter):
    """ Filter that returns all marked changes """
    def apply(self, pkg):
        if pkg.markedInstall() or pkg.markedDelete() or pkg.markedUpgrade():
            return True
        else:
            return False

class FilteredCache(object):
    """ A package cache that is filtered.

        Can work on a existing cache or create a new one
    """
    def __init__(self, cache=None, progress=None):
        if cache == None:
            self.cache = Cache(progress)
        else:
            self.cache = cache
        self.cache.connect("cache_post_change", self.filterCachePostChange)
        self.cache.connect("cache_post_open", self.filterCachePostChange)
        self._filtered = {}
        self._filters = []
    def __len__(self):
        return len(self._filtered)
    
    def __getitem__(self, key):
        return self.cache._dict[key]

    def keys(self):
        return self._filtered.keys()

    def has_key(self, key):
        try:
            self._filtered[key]
        except KeyError:
            return False
        return True

    def _reapplyFilter(self):
        " internal helper to refilter "
        self._filtered = {}
        for pkg in self.cache._dict.keys():
            for f in self._filters:
                if f.apply(self.cache._dict[pkg]):
                    self._filtered[pkg] = 1
                    break
    
    def setFilter(self, filter):
        " set the current active filter "
        self._filters = []
        self._filters.append(filter)
        #self._reapplyFilter()
        # force a cache-change event that will result in a refiltering
        self.cache.cachePostChange()

    def filterCachePostChange(self):
        " called internally if the cache changes, emit a signal then "
        #print "filterCachePostChange()"
        self._reapplyFilter()

#    def connect(self, name, callback):
#        self.cache.connect(name, callback)

    def __getattr__(self, key):
        " we try to look exactly like a real cache "
        #print "getattr: %s " % key
        if self.__dict__.has_key(key):
            return self.__dict__[key]
        else:
            return getattr(self.cache, key)
            

def cache_pre_changed():
    print "cache pre changed"

def cache_post_changed():
    print "cache post changed"


# internal test code
if __name__ == "__main__":
    print "Cache self test"
    apt_pkg.init()
    c = Cache(OpTextProgress())
    c.connect("cache_pre_change", cache_pre_changed)
    c.connect("cache_post_change", cache_post_changed)
    print c.has_key("aptitude")
    p = c["aptitude"]
    print p.name()
    print len(c)

    for pkg in c.keys():
        x= c[pkg].name()

    c.upgrade()
    changes = c.getChanges()
    print len(changes)
    for p in changes:
        #print p.name()
        x = p.name()

    print "Testing filtered cache (argument is old cache)"
    f = FilteredCache(c)
    f.cache.connect("cache_pre_change", cache_pre_changed)
    f.cache.connect("cache_post_change", cache_post_changed)
    f.cache.upgrade()
    f.setFilter(MarkedChangesFilter())
    print len(f)
    for pkg in f.keys():
        #print c[pkg].name()
        x = f[pkg].name()
    
    print len(f)

    print "Testing filtered cache (no argument)"
    f = FilteredCache(progress=OpTextProgress())
    f.cache.connect("cache_pre_change", cache_pre_changed)
    f.cache.connect("cache_post_change", cache_post_changed)
    f.cache.upgrade()
    f.setFilter(MarkedChangesFilter())
    print len(f)
    for pkg in f.keys():
        #print c[pkg].name()
        x = f[pkg].name()
    
    print len(f)
