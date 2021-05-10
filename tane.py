from pandas import *
from collections import defaultdict
import sys


def list_duplicates(seq):
    tally = defaultdict(list)
    for i, item in enumerate(seq):
        tally[item].append(i)
    return ((key, locs) for key, locs in tally.items()
            if len(locs) > 0)


def findCplus(x):  # this computes the Cplus of x as an intersection of smaller Cplus sets
    global candidates
    thesets = []
    for a in x:
        if x.replace(a, '') in candidates.keys():
            temp = candidates[x.replace(a, '')]
        else:
            temp = findCplus(x.replace(a, ''))  # compute C+(X\{A}) for each A at a time
        # dictCplus[x.replace(a,'')] = temp
        thesets.insert(0, set(temp))
    if list(set.intersection(*thesets)) == []:
        cplus = []
    else:
        cplus = list(set.intersection(*thesets))  # compute the intersection in line 2 of pseudocode
    return cplus


def compute_dependencies(level):
    global candidates
    global finallistofFDs
    global listofcolumns

    for x in level:
        attr_candidates = []
        for a in x:
            x_without_a = x.replace(a, '')
            attr_candidates.insert(0, set(candidates[x_without_a]))
        candidates[x] = list(set.intersection(*attr_candidates))  # compute the intersection in line 2 of pseudocode

    for x in level:
        for a in x:
            if a in candidates[x]:
                # if x=='BCJ': print "dictCplus['BCJ'] = ", dictCplus[x]
                if validfd(x.replace(a, ''), a):  # line 5
                    finallistofFDs.append([x.replace(a, ''), a])  # line 6
                    candidates[x].remove(a)  # line 7

                    listofcols = listofcolumns[:]
                    for j in x:  # this loop computes R\X
                        if j in listofcols: listofcols.remove(j)

                    for b in listofcols:  # this loop removes each b in R\X from C+(X)
                        if b in candidates[x]: candidates[x].remove(b)


def validfd(y, z):
    if y == '' or z == '': return False
    ey = computeE(y)
    eyz = computeE(y + z)
    return ey == eyz


def computeE(x):
    global totaltuples
    global dictpartitions
    doublenorm = 0
    for i in dictpartitions[''.join(sorted(x))]:
        doublenorm = doublenorm + len(i)
    e = (doublenorm - len(dictpartitions[''.join(sorted(x))])) / float(totaltuples)
    return e


def check_superkey(x):
    global dictpartitions
    if ((dictpartitions[x] == [[]]) or (dictpartitions[x] == [])):
        return True
    else:
        return False


def prune(level):
    global candidates
    global finallistofFDs
    stufftobedeletedfromlevel = []
    for x in level:  # line 1
        if candidates[x] == []:  # line 2
            level.remove(x)  # line 3
        if check_superkey(x):  # line 4   ### should this check for a key, instead of super key??? Not sure.
            temp = candidates[x][:]
            for i in x:  # this loop computes C+(X) \ X
                if i in temp: temp.remove(i)
            for a in temp:  # line 5
                thesets = []
                for b in x:
                    if not (''.join(sorted((x + a).replace(b, ''))) in candidates.keys()):
                        candidates[''.join(sorted((x + a).replace(b, '')))] = findCplus(
                            ''.join(sorted((x + a).replace(b, ''))))
                    thesets.insert(0, set(candidates[''.join(sorted((x + a).replace(b, '')))]))
                if a in list(set.intersection(*thesets)):  # line 6
                    finallistofFDs.append([x, a])  # line 7
            # print "adding key FD: ", [x,a]
            if x in level: stufftobedeletedfromlevel.append(x)  # line 8
    for item in stufftobedeletedfromlevel:
        level.remove(item)


def generate_next_level(level):
    nextlevel = []
    for i in range(0, len(level)):  # pick an element
        for j in range(i + 1, len(level)):  # compare it to every element that comes after it.
            if ((not level[i] == level[j]) and level[i][0:-1] == level[j][0:-1]):  # i.e. line 2 and 3
                x = level[i] + level[j][-1]  # line 4
                flag = True
                for a in x:  # this entire for loop is for the 'for all' check in line 5
                    if not (x.replace(a, '') in level):
                        flag = False
                if flag == True:
                    nextlevel.append(x)
                    stripped_product(x, level[i], level[
                        j])  # compute partition of x as pi_y * pi_z (where y is level[i] and z is level[j])
    return nextlevel


def stripped_product(x, y, z):
    global dictpartitions
    global tableT
    tableS = [''] * len(tableT)
    partitionY = dictpartitions[''.join(sorted(y))]  # partitionY is a list of lists, each list is an equivalence class
    partitionZ = dictpartitions[''.join(sorted(z))]
    partitionofx = []  # line 1
    for i in range(len(partitionY)):  # line 2
        for t in partitionY[i]:  # line 3
            tableT[t] = i
        tableS[i] = ''  # line 4
    for i in range(len(partitionZ)):  # line 5
        for t in partitionZ[i]:  # line 6
            if (not (tableT[t] == 'NULL')):  # line 7
                tableS[tableT[t]] = sorted(list(set(tableS[tableT[t]]) | set([t])))
        for t in partitionZ[i]:  # line 8
            if (not (tableT[t] == 'NULL')) and len(tableS[tableT[t]]) >= 2:  # line 9
                partitionofx.append(tableS[tableT[t]])
            if not (tableT[t] == 'NULL'): tableS[tableT[t]] = ''  # line 10
    for i in range(len(partitionY)):  # line 11
        for t in partitionY[i]:  # line 12
            tableT[t] = 'NULL'
    dictpartitions[''.join(sorted(x))] = partitionofx


def computeSingletonPartitions(listofcols):
    global data2D
    global dictpartitions
    for a in listofcols:
        dictpartitions[a] = []
        for element in list_duplicates(data2D[
                                           a].tolist()):  # list_duplicates returns 2-tuples, where 1st is a value, and 2nd is a list of indices where that value occurs
            if len(element[1]) > 1:  # ignore singleton equivalence classes
                dictpartitions[a].append(element[1])


# ------------------------------------------------------- START ---------------------------------------------------

if len(sys.argv) > 1:
    infile = str(sys.argv[1])  # this would be e.g. "testdata.csv"

data2D = read_csv(infile)

totaltuples = len(data2D.index)
listofcolumns = list(data2D.columns.values)  # returns ['A', 'B', 'C', 'D', .....]


tableT = ['NULL'] * totaltuples  # this is for the table T used in the function stripped_product

L0 = []
candidates = {'': listofcolumns[:]}
dictpartitions = {}  # maps 'stringslikethis' to a list of lists, each of which contains indices
computeSingletonPartitions(listofcolumns)
finallistofFDs = []
# print dictCplus['NULL']
L1 = listofcolumns[:]  # L1 is a copy of listofcolumns
l = 1

L = [L0, L1]

while (not (L[l] == [])):
    compute_dependencies(L[l])
    prune(L[l])
    temp = generate_next_level(L[l])
    L.append(temp)
    l = l + 1

print(f"List of all FDs: {finallistofFDs}")
print(f"Total number of FDs found: {len(finallistofFDs)}")
