import sys
import re
import string

if len(sys.argv) != 2:
    exit(1)

allowed_letters = ['K', 'Z', 'G', 'T', 'H', 'B', 'D', 'A', 'S', 'L', 'N', 'E', 'R', 'U', 'C', 'Y', ' ', '/', '%', '|', '.']
nl_on = ['G', 'T', 'H', 'Z']

def remove_escaped(chrs):
    while '(' in chrs:
        p = chrs.index('(')
        e = chrs.index(')')
        if ''.join(chrs[p:e+1]) not in ['(DPS)', '(HPS)']:
            exit(1)
        chrs = chrs[:p] + chrs[e + 1:]
    return chrs

def correct_nls(chrs):
    for c in nl_on:
        if chrs.count(c) != 1:
            exit(1)
        n = chrs.index(c)
        if chrs[n-1] != '|':
            exit(1)
        chrs = chrs[:n-1] + chrs[n+1:]
    chrs = chrs[:-1]
    if chrs.count('|') > 0:
        exit(1)
    return True

def all_allowed(chrs):
    for c in chrs:
        if c not in allowed_letters and c not in string.digits:
            exit(1)
    return True

def progress(chrs):
    s = ''.join(chrs)
    bosses = {'K': 10, 'G': 3, 'T': 10, 'H': 14, 'Z': 6}
    a = set()
    for i, m in enumerate(re.finditer(r'(.) .(\d+)/(\d+)', s)):
        r = m.group(1)
        p = int(m.group(2))
        t = int(m.group(3))
        a.add(r)
        if t != bosses[r]:
            exit(1)
        if p > t or p < 0:
            exit(1)
    if set(bosses.keys()) - a!= set():
        exit(1)
    return True

def percent(chrs):
    s = ''.join(chrs)
    for m in re.finditer(r'(\d+\.?\d*)%Y\/.(\d+\.?\d*)%', s):
        best_avg = float(m.group(1))
        median = float(m.group(2))
        if best_avg > 100 or median > 100 or best_avg < 0 or median < 0 or median > best_avg:
            exit(1)
    return True

def percent_color(chrs):
    s = ''.join(chrs)
    print(s)
    for m in re.finditer(r'(.)(\d+\.?\d*)%', s):
        percent = float(m.group(2))
        color_code = m.group(1)
        print(percent, color_code)
        print(color_code == 'L')
        if percent == 100 and color_code != 'A':
            exit(1)
        elif percent < 100 and percent >= 99 and color_code != 'S':
            exit(1)
        elif percent < 99 and  percent >= 95 and color_code != 'L':
            exit(1)
        elif percent < 95 and percent >= 85 and color_code != 'N':
            exit(1)
        elif percent < 85 and percent >= 75 and color_code != 'E':
            exit(1)
        elif percent < 75 and percent >= 50 and color_code != 'R':
            exit(1)
        elif percent < 50 and percent >= 25 and color_code != 'U':
            exit(1)
        elif percent < 25 and color_code != 'C':
            exit(1)
    return True

print(99.0 >= 99)
with open(sys.argv[1]) as f:
    s = f.read()
    for l in re.finditer(r'= "(.*)",?\n', s):
        chrs = remove_escaped(list(l.group(1)))
        print("All escaped strings are good.")
        correct_nls(chrs)
        print("All new lines are in the right place.")
        all_allowed(chrs)
        print("All characters in the string are allowed.")
        progress(chrs)
        print("The progress of all zones are correct")
        percent(chrs)
        print("The percentages are correct")
        percent_color(chrs)
        print("The coloring of the parses is correct.")
exit(0)

