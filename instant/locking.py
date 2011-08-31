"""File locking for the cache system, to avoid problems
when multiple processes work with the same module.
Only works on UNIX systems.

Two python libraries can be used:

  flufl : A nfs safe which can be downloaded from:

          https://launchpad.net/flufl.lock

  fcntl : A builtin Python module which only works on posix machines
          and it is does unfortunately not work on nfs

"""

__all__ = ["get_lock", "release_lock", "release_all_lock"]

import os.path
from output import instant_error, instant_assert, instant_debug
from paths import validate_cache_dir

try:
    import flufl
    fcntl = None
except:
    flufl = None
    try:
        import fcntl
    except:
        fcntl = None

# Keeping an overview of locks currently held,
# to avoid deadlocks within a single process.
_lock_names = {} # lock.fileno() -> lockname
_lock_files = {} # lockname -> lock
_lock_count = {} # lockname -> number of times this lock has been aquired and not yet released

if flufl:
    def get_lock(cache_dir, module_name):
        "Get a new file lock."
        
        from flufl.lock.tests.subproc import acquire
        from flufl.lock import Lock
        from datetime import timedelta
        
        lockname = module_name + ".lock"
        count = _lock_count.get(lockname, 0)
        
        instant_debug("Acquiring lock %s, count is %d." % (lockname, count))
        
        cache_dir = validate_cache_dir(cache_dir)
        lockname = os.path.join(cache_dir, lockname)
        acquire(lockname, timedelta(seconds=1))
        lock = Lock(lockname)
        lock.lock()
        
        return lock
    
    def release_lock(lock):
        "Release a lock currently held by Instant."
        if lock.is_locked:
            hostname, pid, lockname = lock.details
            instant_debug("Releasing lock %s." % (lockname))
            lock.unlock()

    def release_all_locks():
        pass

if fcntl:
    def get_lock(cache_dir, module_name):
        "Get a new file lock."
        global _lock_names, _lock_files, _lock_count
        
        lockname = module_name + ".lock"
        count = _lock_count.get(lockname, 0)
        
        instant_debug("Acquiring lock %s, count is %d." % (lockname, count))
        
        if count == 0:
            cache_dir = validate_cache_dir(cache_dir)
            lock = open(os.path.join(cache_dir, lockname), "w")
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            _lock_names[lock.fileno()] = lockname
            _lock_files[lockname] = lock
        else:
            lock = _lock_files[lockname]
        
        _lock_count[lockname] = count + 1
        return lock
    
    def release_lock(lock):
        "Release a lock currently held by Instant."
        global _lock_names, _lock_files, _lock_count
        
        lockname = _lock_names[lock.fileno()]
        count = _lock_count[lockname]

        instant_debug("Releasing lock %s, count is %d." % (lockname, count))

        instant_assert(count > 0, "Releasing lock that Instant is supposedly not holding.")
        instant_assert(lock is _lock_files[lockname], "Lock mismatch, might be something wrong in locking logic.")
        
        del _lock_files[lockname]
        del _lock_names[lock.fileno()]
        _lock_count[lockname] = count - 1
        
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
        lock.close()
    
    def release_all_locks():
        "Release all locks currently held by Instant."
        locks = _lock_files.values()
        for lock in locks:
            release_lock(lock)
        instant_assert(all(_lock_count[lockname] == 0 for lockname in _lock_count), "Lock counts not zero after releasing all locks.")

else:
    # Windows systems have no fcntl, implement these otherwise if locking is needed on windows
    def get_lock(cache_dir, module_name):
        return None
    
    def release_lock(lock):
        pass

    def release_all_locks():
        pass
    
