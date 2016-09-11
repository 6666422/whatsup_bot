def read_file(fn, prefix="files/"):
    f = open(prefix + fn)
    ret = f.read().strip()
    f.close()
    return ret
