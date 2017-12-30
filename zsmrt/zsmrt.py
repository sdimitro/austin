#!/usr/bin/python

SME_TYPE_FREE  = 0
SME_TYPE_ALLOC = 1
SME_TYPE_DEBUG = 2

class SpacemapDebugEntry(object):
    def __init__(self, type, txg, txg_pass):
        self.type, self.txg, self.txg_pass = type, txg, txg_pass

    def isdebug(self):
        return True

    def time_info(self):
        return '{:10d} {:2d}'.format(self.txg, self.txg_pass)

class SpacemapStandardEntry(object):
    def __init__(self, type, start, len):
        self.start, self.len, self.type = start, len, type
        self.debug = None

    def end(self):
        return self.start + self.len

    def isalloc(self):
        return (self.type == SME_TYPE_ALLOC)

    def isfree(self):
        return (self.type == SME_TYPE_FREE)

    def isdebug(self):
        return False

    def overlaps_with(self, start, len):
        target_end = start + len
        if self.start <= start and start < self.end():
            return True
        elif self.start < target_end and  target_end <= self.end():
            return True
        else:
            return False

    def _type_char(self):
        if self.isalloc():
            return "A"
        else:
            assert self.isfree()
            return "F"

    def _debug_info(self):
        if self.debug == None:
            return ""
        else:
            return self.debug.time_info()

    def __str__(self):
        debug_info = self._debug_info()
        return '{} {} [{:10x}, {:10x}] {:10x}'.format(debug_info,
                self._type_char(), self.start, self.end(), self.len)

def is_debug_line(tok):
    if tok == "ALLOC:" or tok == "FREE:":
        return True
    return False

def parse_debug_type(tok):
    if tok == "ALLOC:":
        return SME_TYPE_ALLOC
    else:
        assert tok == "FREE:"
        return SME_TYPE_FREE

def parse_standard_type(tok):
    if tok == "A":
        return SME_TYPE_ALLOC
    else:
        assert tok == "F"
        return SME_TYPE_FREE

def parse_entry_line(line):
    tokens = line.split()
    if is_debug_line(tokens[2]):
        type = parse_debug_type(tokens[2])
        txg  = int(tokens[4].strip(','))
        txg_pass = int(tokens[6])
        return SpacemapDebugEntry(type, txg, txg_pass)
    else:
        type  = parse_standard_type(tokens[2])
        start = int(tokens[4].split('-')[0], 16)
        len   = int(tokens[6], 16)
        return SpacemapStandardEntry(type, start, len)

def parse_file(path):
    with open(path) as f:
        entries = [parse_entry_line(line.strip()) for line in f]
    return entries

def squash_debug_entries(raw_entries):
    entries = []
    for re in raw_entries:
        if re.isdebug():
            debug_e = re
        else:
            re.debug = debug_e
            entries.append(re)
    return entries

def slurp_entries(path):
    return squash_debug_entries(parse_file(path))

def generate_timeline(start, len, entries):
    print("{:>10} {:>2} T [{:>10}, {:>10}] {:>10}".format("TXG",
        "P", "START", "END", "RUN"))
    txg, txg_pass = 0, 0
    for e in entries:
        if e.isdebug():
            txg, txg_pass = e.txg, e.txg_pass
        elif e.overlaps_with(start, len):
            print(e)

def cmd_get_timeline(start, len, path):
    entries = slurp_entries(path)
    generate_timeline(int(start, 16), int(len, 16), entries)

def main(start, len, path):
    cmd_get_timeline(start, len, path)

import sys

if __name__== "__main__":
    if len(sys.argv) != 4:
        print("Nope!")
        exit(1)

    start = sys.argv[1]
    len   = sys.argv[2]
    path  = sys.argv[3]
    main(start, len, path)
