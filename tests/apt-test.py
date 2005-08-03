import apt

if __name__ == "__main__":
    progress = apt.progress.OpTextProgress()
    cache = apt.Cache(progress)
    print cache
    for name in cache.keys():
        pkg = cache[name]
        if pkg.isUpgradable():
            pkg.markInstall()
    for pkg in cache.getChanges():
        #print pkg.Name()
        pass
    print "Broken: %s " % cache._depcache.BrokenCount
    print "InstCount: %s " % cache._depcache.InstCount

    # get a new cache
    cache = apt.Cache(progress)
    for name in cache.keys():
        import random
        if random.randint(0,1) == 1:
            cache[name].markDelete()
    print "Broken: %s " % cache._depcache.BrokenCount
    print "DelCount: %s " % cache._depcache.DelCount
