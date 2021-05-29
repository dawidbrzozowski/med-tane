import time

from pandas import *
from collections import defaultdict
import numpy as NP
import itertools
import sys


def replace_element_in_tuple(tup, elementindex, elementval):
    if type(elementval) == tuple:
        elementval = elementval[0]
    newtup = list(tup)
    newtup[elementindex] = elementval
    newtup = tuple(newtup)
    return newtup


def add_element_in_tuple(create_condition_by_sub, ca):
    thelist = list(create_condition_by_sub)
    thelist.append(ca[0])
    return tuple(thelist)


def validcfd(xminusa, x, a, create_condition_by_sub, sp, ca):
    global dictpartitions
    if xminusa == '' or a == '':
        return False
    indexofa = x.index(a)
    newsp0 = add_element_in_tuple(create_condition_by_sub, ca)
    newsp1 = replace_element_in_tuple(sp, indexofa, ca)  # this is sp, except that in place of value of a we put ca
    if (x, newsp1) in dictpartitions.keys():
        if len(dictpartitions[(xminusa, create_condition_by_sub)]) == len(dictpartitions[(
                x,
                newsp1)]):  # and twodlen(dictpartitions[(xminusa, create_condition_by_sub)]) == twodlen(dictpartitions[(x, newsp1)]):
            return True
    return False


def twodlen(listoflists):
    summ = 0
    for item in listoflists:
        summ = summ + len(item)
    return summ


def greaterthanorequalto(upxminusa, create_condition_by_sub):  # this is actually greaterthan or equal to
    if upxminusa == create_condition_by_sub:
        return True
    flag = True
    for index in range(0, len(upxminusa)):
        if not (create_condition_by_sub[index] == '--'):
            if (not (upxminusa[index] == create_condition_by_sub[index])):
                flag = False
    return flag


def doublegreaterthan(upxminusa, create_condition_by_sub):
    if upxminusa == create_condition_by_sub:
        return False
    flag = True
    for index in range(0, len(upxminusa)):
        if (not create_condition_by_sub[index] == '--'):
            if (not (upxminusa[index] == create_condition_by_sub[index])):
                flag = False
    return flag


def compute_dependencies(level, listofcols):

    start = time.time()
    global dictCplus
    global finallistofCFDs
    global listofcolumns
    for (x, sp) in level:
        for a in x:
            for (att, ca) in dictCplus[(x, sp)]:
                if att != a:
                    continue

                newtup = create_condition_by_sub(sp, x, a)
                if validcfd(x.replace(a, ''), x, a, newtup, sp, ca) and not (
                        [x.replace(a, ''), a, [newtup, ca]] in finallistofCFDs):
                    finallistofCFDs.append([x.replace(a, ''), a, [newtup, ca]])
                    for (xx, up) in level:
                        if xx == x:
                            newtup0 = create_condition_by_sub(up, x,
                                                a)  ### tuple(y for y in up if not up.index(y)==x.index(a)) # this is up[X\A]
                            if up[x.index(a)] == ca[0] and greaterthanorequalto(newtup0, newtup):
                                if (a, ca) in dictCplus[(x, up)]: dictCplus[(x, up)].remove((a, ca))
                                listofcolscopy = listofcols[:]
                                for j in x:  # this loop computes R\X
                                    if j in listofcolscopy: listofcolscopy.remove(j)
                                for b_att in listofcolscopy:  # this loop removes each b in R\X from C+(X,up)
                                    stufftobedeleted = []
                                    for (bbval, sometup) in dictCplus[(x, up)]:
                                        if b_att == bbval:
                                            stufftobedeleted.append((bbval, sometup))
                                    for item in stufftobedeleted:
                                        dictCplus[(x, up)].remove(item)

    end = time.time()
    print(f"Compute dependencies time: {end - start}")

def prune(level):

    start = time.time()
    global dictCplus
    stufftobedeleted = []
    for (x, sp) in level:
        if len(dictCplus[(x, sp)]) == 0:
            stufftobedeleted.append((x, sp))
    for item in stufftobedeleted:
        level.remove(item)

    end = time.time()
    print(f"Compute dependencies time: {end - start}")

def computeCplus(level):
    start = time.time()
    global listofcolumns
    global dictCplus
    listofcols = listofcolumns[:]
    for (x, sp) in level:
        thesets = []
        for b in x:
            indx = x.index(b)
            spcopy = create_condition_by_sub(sp, x, b)
            spcopy2 = sp[:]
            if (x.replace(b, ''), spcopy) in dictCplus.keys():
                temp = dictCplus[(x.replace(b, ''), spcopy)]
            else:
                temp = []
            thesets.insert(0, set(temp))
        if list(set.intersection(*thesets)) == []:
            dictCplus[(x, sp)] = []
        else:
            dictCplus[(x, sp)] = list(set.intersection(*thesets))

    end = time.time()
    print(f"Compute C plus time: {end - start}")

def compute_initial_cplus(level):
    global listofcolumns
    global dictCplus
    computeCplus(level)
    for (a, ca) in level:
        stufftobedeleted = []
        for (att, val) in dictCplus[(a, ca)]:
            if att == a and not val == ca:
                stufftobedeleted.append((att, val))
        for item in stufftobedeleted:
            dictCplus[(a, ca)].remove(item)


def populateL1(listofcols):
    global k_suppthreshold
    l1 = []
    attributepartitions = computeAttributePartitions(listofcols)
    for a in listofcols:
        l1.append((a, ('--',)))
        for eqclass in attributepartitions[a]:
            if len(eqclass) >= k_suppthreshold:
                l1.append((a, (str(data2D.iloc[eqclass[0]][a]),)))
    computeInitialPartitions(l1,
                             attributepartitions)  # populates the dictpartitions with the initial partitions (X,sp) where X is a single attribute
    return l1


def computeInitialPartitions(level1, attributepartitions):
    global data2D
    global dictpartitions  # dictpartitions[(x,sp)] is of the form [[0,1,2]]. So simply a list of lists of indices
    for (a, sp) in level1:
        dictpartitions[(a, sp)] = []
        dictpartitions[(a, sp)] = attributepartitions[a]

def computeAttributePartitions(listofcols):  # compute partitions for every attribute
    global data2D
    attributepartitions = {}
    for a in listofcols:
        attributepartitions[a] = []
        for element in list_duplicates(data2D[
                                           a].tolist()):  # list_duplicates returns 2-tuples, where 1st is a value, and 2nd is a list of indices where that value occurs
            if len(element[1]) > 0:  # if >1, then ignore singleton equivalence classes
                attributepartitions[a].append(element[1])
    return attributepartitions


def list_duplicates(seq):
    tally = defaultdict(list)
    for i, item in enumerate(seq):
        tally[item].append(i)
    return ((key, locs) for key, locs in tally.items()
            if len(locs) > 0)


def is_subset(z, up):
    global dictpartitions
    global k_suppthreshold
    sumofmatches = 0
    for eqclass in dictpartitions[(z, up)]:
        sumofmatches = sumofmatches + len(eqclass)

    return sumofmatches >= k_suppthreshold

def generate_next_level(level):

    start = time.time()
    nextlevel = []
    for i in range(0, len(level)):
        for j in range(i + 1, len(level)):
            if level[i][0] != level[j][0] and level[i][0][0:-1] == level[j][0][0:-1] and level[i][1][0:-1] == level[j][1][0:-1]:
                z = level[i][0] + level[j][0][-1]
                up = tuple(list(level[i][1]) + [level[j][1][-1]])
                partition_product((z, up), level[i], level[j])
                if is_subset(z, up):
                    flag = True
                    for att in z:
                        up_zminusa = create_condition_by_sub(up, z, att)
                        zminusa = z.replace(att, '')
                        if not ((zminusa, up_zminusa) in level):
                            flag = False
                    if flag:
                        nextlevel.append((z, up))

    end = time.time()
    print(f"generate next lvl C plus time: {end - start}")
    return nextlevel


def create_condition_by_sub(sp, x, a):
    return tuple(sp[i] for i in range(0, len(sp)) if i != x.index(a))


def partition_product(zup, xsp, ytp):

    start = time.time()

    global dictpartitions
    global tableT
    tableS = [[]] * len(tableT)
    partitionXSP = dictpartitions[xsp]
    partitionYTP = dictpartitions[ytp]
    partitionZUP = []
    for i in range(len(partitionXSP)):
        for t in partitionXSP[i]:
            tableT[t] = i

    for i in range(len(partitionYTP)):
        for t in partitionYTP[i]:
            if tableT[t] is not None:
                tableS[tableT[t]] = tableS[tableT[t]] + [t]

        for t in partitionYTP[i]:
            if tableT[t] is not None:
                if len(tableS[tableT[t]]) >= 1:
                    partitionZUP.append(tableS[tableT[t]])

            tableS[tableT[t]] = []

    for i in range(len(partitionXSP)):
        for t in partitionXSP[i]:
            tableT[t] = None

    dictpartitions[zup] = partitionZUP
    dictpartitions[zup] = partitionZUP

    end = time.time()
    global total_times
    global total_calls

    total_times += end - start
    total_calls += 1
    print(f"\tpartition_product time: {end - start}")

# ------------------------------------------------------- START ---------------------------------------------------
if len(sys.argv) > 1:
    infile = str(sys.argv[1])
if len(sys.argv) > 2:
    k_suppthreshold = int(sys.argv[2])

data2D = read_csv(infile)

total_times = 0
total_calls = 0
totaltuples = len(data2D.index)
listofcolumns = list(data2D.columns.values)  # returns ['A', 'B', 'C', 'D', .....]
tableT = [None] * totaltuples  # this is for the table T used in the function partition_product
L0 = []

dictpartitions = {}  # maps 'stringslikethis' to a list of lists, each of which contains indices
finallistofCFDs = []
L1 = populateL1(listofcolumns[:])
dictCplus = {('', ()): L1[:]}
lvl = 1
L = [L0, L1]

compute_initial_cplus(L[lvl])

full_start = time.time()
while not (L[lvl] == []):
    if lvl > 1:
        computeCplus(L[lvl])

    compute_dependencies(L[lvl], listofcolumns[:])
    prune(L[lvl])
    temp = generate_next_level(L[lvl])
    L.append(temp)
    lvl += 1
    # print "List of all CFDs: " , finallistofCFDs
    # print "CFDs found: ", len(finallistofCFDs), ", level = ", l-1

full_end = time.time()
print(f"Avg prune time: {total_times / total_calls}")
print(f"Total time: {full_end - full_start}")
print(f"List of all CFDs: {finallistofCFDs}")
print(f"Total number of CFDs found: {len(finallistofCFDs)}")
