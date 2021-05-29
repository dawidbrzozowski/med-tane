import time

from pandas import *
from collections import defaultdict
import numpy as NP
import itertools
import sys


def replace_element_in_tuple(tup, id, val):
    tmp = list(tup)
    tmp[id] = val
    return tuple(tmp)

def is_dependant(xminusa, x, a, create_condition_by_sub, sp, ca):
    global dictpartitions
    if xminusa == '' or a == '':
        return False

    tmp = list(sp)
    tmp[x.index(a)] = ca[0]
    sp_with_ca = tuple(tmp)

    if (x, sp_with_ca) in dictpartitions.keys():
        return len(dictpartitions[(xminusa, create_condition_by_sub)]) == len(dictpartitions[(x, sp_with_ca)])

def generate_columns_without_x(x):
    global listofcolumns
    columns = []

    for j in listofcolumns[:]:
        if j not in x:
            columns.append(j)

    return columns

def compute_dependencies(level, listofcols):

    start = time.time()
    global candidates_dict
    global result
    for (x, sp) in level:
        for a in x:
            for (att, ca) in candidates_dict[(x, sp)]:
                if att != a:
                    continue

                newtup = create_condition_by_sub(sp, x, a)
                if is_dependant(x.replace(a, ''), x, a, newtup, sp, ca):
                    result.append([x.replace(a, ''), a, [newtup, ca]])

                    for (xx, up) in level:
                        if xx == x:
                            newtup0 = create_condition_by_sub(up, x, a)
                            if up[x.index(a)] == ca[0] and newtup0 >= newtup:
                                if (a, ca) in candidates_dict[(x, up)]:
                                    candidates_dict[(x, up)].remove((a, ca))

                                for b_att in generate_columns_without_x(x):
                                    new_candidates = []
                                    for (bbval, sometup) in candidates_dict[(x, up)]:
                                        if b_att != bbval:
                                            new_candidates.append((bbval, sometup))

                                    candidates_dict[(x, up)] = new_candidates

    end = time.time()
    print(f"Compute dependencies time: {end - start}")


def prune(level):

    start = time.time()
    global candidates_dict
    new_level = []
    for (x, sp) in level:
        if candidates_dict[(x, sp)]:
            new_level.append((x, sp))

    end = time.time()
    print(f"Compute dependencies time: {end - start}")

    return new_level

def generate_c_plus(level):
    start = time.time()
    global listofcolumns
    global candidates_dict
    for (x, sp) in level:
        candidates = []
        for a in x:
            conditional_x_without_a = (x.replace(a, ''), create_condition_by_sub(sp, x, a))
            if conditional_x_without_a in candidates_dict.keys():
                candidates.insert(0, set(candidates_dict[conditional_x_without_a]))
            else:
                candidates = []
                break

        candidates_dict[(x, sp)] = list(set.intersection(*candidates))

    end = time.time()
    print(f"Compute C plus time: {end - start}")

def compute_initial_cplus(level):
    global listofcolumns
    global candidates_dict
    generate_c_plus(level)
    for (a, ca) in level:
        stufftobedeleted = []
        for (att, val) in candidates_dict[(a, ca)]:
            if att == a and not val == ca:
                stufftobedeleted.append((att, val))
        for item in stufftobedeleted:
            candidates_dict[(a, ca)].remove(item)


def populateL1(listofcols):
    l1 = []
    attributepartitions = computeAttributePartitions(listofcols)
    for a in listofcols:
        l1.append((a, ('--',)))
        for eqclass in attributepartitions[a]:
            l1.append((a, (str(data2D.iloc[eqclass[0]][a]),)))
    computeInitialPartitions(l1, attributepartitions)
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
        for element in list_duplicates(data2D[a].tolist()):
            if len(element[1]) > 0:
                attributepartitions[a].append(element[1])
    return attributepartitions


def list_duplicates(seq):
    tally = defaultdict(list)
    for i, item in enumerate(seq):
        tally[item].append(i)
    return ((key, locs) for key, locs in tally.items() if len(locs) > 0)


def append_next_level_if_possible(next_level, level, z, up):
    flag = True
    for att in z:
        up_without_a = create_condition_by_sub(up, z, att)
        z_without_a = z.replace(att, '')
        if (z_without_a, up_without_a) not in level:
            flag = False
            break

    if flag:
        next_level.append((z, up))


def generate_next_level(level):

    start = time.time()
    next_level = []
    for i in range(0, len(level)):
        for j in range(i + 1, len(level)):

            if level[i][0] != level[j][0] and level[i][0][0:-1] == level[j][0][0:-1] and level[i][1][0:-1] == level[j][1][0:-1]:
                z = level[i][0] + level[j][0][-1]
                up = level[i][1] + (level[j][1][-1], )
                partition_product((z, up), level[i], level[j])
                append_next_level_if_possible(next_level, level, z, up)

    end = time.time()
    print(f"generate next lvl C plus time: {end - start}")
    return next_level


def create_condition_by_sub(sp, x, a):
    return tuple(sp[i] for i in range(0, len(sp)) if i != x.index(a))


def partition_product(zup, xsp, ytp):

    start = time.time()

    global dictpartitions
    global table_t
    tableS = [[]] * len(table_t)
    partitionXSP = dictpartitions[xsp]
    partitionYTP = dictpartitions[ytp]
    partitionZUP = []
    for i in range(len(partitionXSP)):
        for t in partitionXSP[i]:
            table_t[t] = i

    for i in range(len(partitionYTP)):
        for t in partitionYTP[i]:
            if table_t[t] is not None:
                tableS[table_t[t]] = tableS[table_t[t]] + [t]

        for t in partitionYTP[i]:
            table_t_val = table_t[t]
            if table_t[t] is not None:
                if len(tableS[table_t_val]) >= 1:
                    partitionZUP.append(tableS[table_t_val])

            tableS[table_t_val] = []

    for i in range(len(partitionXSP)):
        for t in partitionXSP[i]:
            table_t[t] = None

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

data2D = read_csv(infile)

total_times = 0
total_calls = 0
totaltuples = len(data2D.index)
listofcolumns = list(data2D.columns.values)  # returns ['A', 'B', 'C', 'D', .....]
table_t = [None] * totaltuples  # this is for the table T used in the function partition_product
L0 = []

dictpartitions = {}  # maps 'stringslikethis' to a list of lists, each of which contains indices
result = []
L1 = populateL1(listofcolumns[:])
candidates_dict = {('', ()): L1[:]}
lvl = 1
L = [L0, L1]

compute_initial_cplus(L[lvl])

full_start = time.time()
while not (L[lvl] == []):
    if lvl > 1:
        generate_c_plus(L[lvl])

    compute_dependencies(L[lvl], listofcolumns[:])
    L[lvl] = prune(L[lvl])
    temp = generate_next_level(L[lvl])
    L.append(temp)
    lvl += 1
    # print "List of all CFDs: " , result
    # print "CFDs found: ", len(result), ", level = ", l-1

full_end = time.time()
print(f"Avg prune time: {total_times / total_calls}")
print(f"Total time: {full_end - full_start}")
print(f"List of all CFDs: {result}")
print(f"Total number of CFDs found: {len(result)}")
