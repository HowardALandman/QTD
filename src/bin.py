#!/usr/bin/python3
""" Read output data from qtd.py and place into bins.
"""

__version__ = '0.0'

import sys
import seaborn as sns

# Read all the data from the files.
argv = sys.argv[1:]
#print(len(argv), "files to process")
# Create enough room to hold perfect data.
decay_times = [0] * (100000 * len(argv))
n = 0
for name in argv:
    with open(name) as f:
        for line in f:
            words = line.split()
            s = words[0]
            if not s.isdigit():
                continue
            try:
                t = float(words[-1])
            except ValueError:
                continue
            decay_times[n] = t
            n += 1

print("Got", n, "data points.")

#sns.set()

#_ = plt.hist(DATA_HERE, bins=100)
#_ = plt.xlabel("Time (uS)")
#_ = plt.ylabel("N")

#plt.show()
