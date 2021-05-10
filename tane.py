from click import STRING
from pandas import *
from collections import defaultdict
import click


class Tane:

    def __init__(self, data_2d, candidates, table_t, dict_partitions, FINAL_LIST_OF_ALL_DEPENDENCIES, COLUMN_HEADERS, ROW_LABELS_NUMBER):
        self.data_2d = data_2d
        self.CANDIDATES = candidates
        self.table_t = table_t
        self.DICT_PARTITIONS = dict_partitions
        self.FINAL_LIST_OF_ALL_DEPENDENCIES = FINAL_LIST_OF_ALL_DEPENDENCIES
        self.COLUMN_HEADERS = COLUMN_HEADERS
        self.ROW_LABELS_NUMBER = ROW_LABELS_NUMBER

    def findCplus(self, x):  # this computes the Cplus of x as an intersection of smaller Cplus sets
        thesets = []
        for a in x:
            if x.replace(a, '') in self.CANDIDATES.keys():
                temp = self.CANDIDATES[x.replace(a, '')]
            else:
                temp = self.findCplus(x.replace(a, ''))  # compute C+(X\{A}) for each A at a time
            # dictCplus[x.replace(a,'')] = temp
            thesets.insert(0, set(temp))
        if list(set.intersection(*thesets)) == []:
            cplus = []
        else:
            cplus = list(set.intersection(*thesets))  # compute the intersection in line 2 of pseudocode
        return cplus

    def compute_dependencies(self, level):
        for x in level:
            attr_candidates = []
            for a in x:
                x_without_a = x.replace(a, '')
                attr_candidates.insert(0, set(self.CANDIDATES[x_without_a]))
            self.CANDIDATES[x] = list(set.intersection(*attr_candidates))  # compute the intersection in line 2 of pseudocode

        for x in level:
            for a in x:
                if a in self.CANDIDATES[x]:
                    # if x=='BCJ': print "dictCplus['BCJ'] = ", dictCplus[x]
                    if self.validfd(x.replace(a, ''), a):  # line 5
                        self.FINAL_LIST_OF_ALL_DEPENDENCIES.append([x.replace(a, ''), a])  # line 6
                        self.CANDIDATES[x].remove(a)  # line 7

                        listofcols = self.COLUMN_HEADERS[:]
                        for j in x:  # this loop computes R\X
                            if j in listofcols: listofcols.remove(j)

                        for b in listofcols:  # this loop removes each b in R\X from C+(X)
                            if b in self.CANDIDATES[x]: self.CANDIDATES[x].remove(b)

    def validfd(self, y, z):
        if y == '' or z == '': return False
        ey = self.computeE(y)
        eyz = self.computeE(y + z)
        return ey == eyz

    def computeE(self, x):
        doublenorm = 0
        for i in self.DICT_PARTITIONS[''.join(sorted(x))]:
            doublenorm = doublenorm + len(i)
        e = (doublenorm - len(self.DICT_PARTITIONS[''.join(sorted(x))])) / float(self.ROW_LABELS_NUMBER)
        return e

    def check_superkey(self, x):
        return (self.DICT_PARTITIONS[x] == [[]]) or (self.DICT_PARTITIONS[x] == [])

    def prune(self, level):
        stufftobedeletedfromlevel = []
        for x in level:  # line 1
            if self.CANDIDATES[x] == []:  # line 2
                level.remove(x)  # line 3
            if self.check_superkey(x):  # line 4   ### should this check for a key, instead of super key??? Not sure.
                temp = self.CANDIDATES[x][:]
                for i in x:  # this loop computes C+(X) \ X
                    if i in temp: temp.remove(i)
                for a in temp:  # line 5
                    thesets = []
                    for b in x:
                        if not (''.join(sorted((x + a).replace(b, ''))) in self.CANDIDATES.keys()):
                            self.CANDIDATES[''.join(sorted((x + a).replace(b, '')))] = self.findCplus(
                                ''.join(sorted((x + a).replace(b, ''))))
                        thesets.insert(0, set(self.CANDIDATES[''.join(sorted((x + a).replace(b, '')))]))
                    if a in list(set.intersection(*thesets)):  # line 6
                        self.FINAL_LIST_OF_ALL_DEPENDENCIES.append([x, a])  # line 7
                # print "adding key FD: ", [x,a]
                if x in level: stufftobedeletedfromlevel.append(x)  # line 8
        for item in stufftobedeletedfromlevel:
            level.remove(item)

    def generate_next_level(self, level):
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
                        self.stripped_product(x, level[i], level[j], self.table_t)  # compute partition of x as pi_y * pi_z (where y is level[i] and z is level[j])
        return nextlevel

    def stripped_product(self, x, y, z, table_t):
        tableS = [''] * len(table_t)
        partitionY = self.DICT_PARTITIONS[
            ''.join(sorted(y))]  # partitionY is a list of lists, each list is an equivalence class
        partitionZ = self.DICT_PARTITIONS[''.join(sorted(z))]
        partitionofx = []  # line 1
        for i in range(len(partitionY)):  # line 2
            for t in partitionY[i]:  # line 3
                table_t[t] = i
            tableS[i] = ''  # line 4
        for i in range(len(partitionZ)):  # line 5
            for t in partitionZ[i]:  # line 6
                if (not (table_t[t] == 'NULL')):  # line 7
                    tableS[table_t[t]] = sorted(list(set(tableS[table_t[t]]) | set([t])))
            for t in partitionZ[i]:  # line 8
                if (not (table_t[t] == 'NULL')) and len(tableS[table_t[t]]) >= 2:  # line 9
                    partitionofx.append(tableS[table_t[t]])
                if not (table_t[t] == 'NULL'): tableS[table_t[t]] = ''  # line 10
        for i in range(len(partitionY)):  # line 11
            for t in partitionY[i]:  # line 12
                table_t[t] = 'NULL'
        self.DICT_PARTITIONS[''.join(sorted(x))] = partitionofx


def computeSingletonPartitions(listofcols, data_2d, dict_partitions):
    for a in listofcols:
        dict_partitions[a] = []
        for element in list_duplicates(data_2d[a].tolist()):
            if len(element[1]) > 1:  # ignore singleton equivalence classes
                dict_partitions[a].append(element[1])


def list_duplicates(seq):
    tally = defaultdict(list)
    for i, item in enumerate(seq):
        tally[item].append(i)
    return ((key, locs) for key, locs in tally.items()
            if len(locs) > 0)


def initialize_tane_from_file(input_file: STRING):
    DATA_2D = read_csv(input_file)

    ROW_LABELS_NUMBER = len(DATA_2D.index)
    COLUMN_HEADERS = list(DATA_2D.columns.values)  # returns ['A', 'B', 'C', 'D', .....]

    TABLE_T = ['NULL'] * ROW_LABELS_NUMBER  # this is for the table T used in the function stripped_product

    CANDIDATES = {'': COLUMN_HEADERS[:]}
    DICT_PARTITIONS = {}  # maps 'stringslikethis' to a list of lists, each of which contains indices
    computeSingletonPartitions(COLUMN_HEADERS, DATA_2D, DICT_PARTITIONS)

    return Tane(data_2d=DATA_2D, candidates=CANDIDATES, table_t=TABLE_T, dict_partitions=DICT_PARTITIONS,
                FINAL_LIST_OF_ALL_DEPENDENCIES=[], COLUMN_HEADERS=COLUMN_HEADERS, ROW_LABELS_NUMBER=ROW_LABELS_NUMBER)


@click.command()
@click.option(
    "-i",
    "--input_file",
    type=STRING,
    required=True,
    help="Path to the input file")
def main(input_file: STRING):
    tane = initialize_tane_from_file(input_file)

    L0 = []
    L1 = tane.COLUMN_HEADERS[:]  # L1 is a copy of listofcolumns
    l = 1
    L = [L0, L1]

    while L[l]:
        tane.compute_dependencies(L[l])
        tane.prune(L[l])
        temp = tane.generate_next_level(L[l])
        L.append(temp)
        l = l + 1

    print(f"List of all FDs: {tane.FINAL_LIST_OF_ALL_DEPENDENCIES}")
    print(f"Total number of FDs found: {len(tane.FINAL_LIST_OF_ALL_DEPENDENCIES)}")


if __name__ == '__main__':
    main()
