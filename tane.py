from click import STRING
import pandas as pd
from collections import defaultdict
import click


class Tane:

    def __init__(self, data_2d, candidates, table_t, dict_partitions, final_list_of_all_dependencies, column_headers,
                 row_labels_number):
        self.data_2d = data_2d
        self.candidates = candidates
        self.t = table_t
        self.dict_partitions = dict_partitions
        self.final_list_of_all_dependencies = final_list_of_all_dependencies
        self.column_headers = column_headers
        self.row_labels_number = row_labels_number

    def findCplus(self, x):  # this computes the Cplus of x as an intersection of smaller Cplus sets
        thesets = []
        for a in x:
            x_without_a = x.replace(a, '')
            if x_without_a in self.candidates.keys():
                temp = self.candidates[x_without_a]
            else:
                temp = self.findCplus(x_without_a)  # compute C+(X\{A}) for each A at a time
            thesets.append(set(temp))
        return list(set.intersection(*thesets))

    def compute_dependencies(self, level):
        for x in level:
            attr_candidates = []
            for a in x:
                x_without_a = x.replace(a, '')
                attr_candidates.insert(0, set(self.candidates[x_without_a]))
            self.candidates[x] = list(set.intersection(*attr_candidates))  # compute the intersection in line 2 of pseudocode

        for x in level:
            for a in x:
                if a in self.candidates[x]:
                    # if x=='BCJ': print "dictCplus['BCJ'] = ", dictCplus[x]
                    if self.validfd(x.replace(a, ''), a):  # line 5
                        self.final_list_of_all_dependencies.append([x.replace(a, ''), a])  # line 6
                        self.candidates[x].remove(a)  # line 7

                        # TODO do funkcji, bo obrzydliwe
                        column_headers = self.column_headers[:]
                        for j in x:  # this loop computes R\X
                            if j in column_headers: column_headers.remove(j)

                        for b in column_headers:  # this loop removes each b in R\X from C+(X)
                            if b in self.candidates[x]: self.candidates[x].remove(b)

    def validfd(self, y, z):
        if y == '' or z == '': return False
        ey = self.computeE(y)
        eyz = self.computeE(y + z)
        return ey == eyz

    def computeE(self, x):
        doublenorm = 0
        for i in self.dict_partitions[''.join(sorted(x))]:
            doublenorm = doublenorm + len(i)
        e = (doublenorm - len(self.dict_partitions[''.join(sorted(x))])) / float(self.row_labels_number)
        return e

    def is_superkey(self, x):
        return (self.dict_partitions[x] == [[]]) or (self.dict_partitions[x] == [])

    def calculate_candidates_without_element(self, x):
        result = self.candidates[x][:]
        for i in x:
            if i in result:
                result.remove(i)

        return result

    def set_add(self, a, b):
        return ''.join(sorted(a + b))

    def set_substruct(self, a, b):
        return a.replace(b, '')

    def generate_candidate_sets(self, a, x):
        attr_with_candidate = self.set_add(x, a)
        # set w znaczeniu zbior algebraiczny
        candidate_sets = []
        for b in x:
            potential_candidate = self.set_substruct(attr_with_candidate, b)
            if potential_candidate not in self.candidates.keys():
                self.candidates[potential_candidate] = self.findCplus(potential_candidate)

            candidate_sets.append(set(self.candidates[potential_candidate]))

        return candidate_sets

    def prune(self, level):
        to_del_from_level = []
        for x in level:

            if not self.candidates[x]:
                level.remove(x)

            # odwróciliśmy logikę dla większej czytelności
            if not self.is_superkey(x):
                continue

            result = self.candidates[x][:]
            for i in x:
                if i in result:
                    result.remove(i)

            for a in result:
                sets = self.generate_candidate_sets(a, x)
                if a in set.intersection(*sets):
                    self.final_list_of_all_dependencies.append([x, a])

            if x in level:
                level.remove(x)


    def generate_prefix_block(self, level):
        prefix_block = []
        for i in range(len(level)):
            for j in range(i + 1, len(level)):
                attr1 = level[i]
                attr2 = level[j]
                if attr1 != attr2 and attr1[0:-1] == attr2[0:-1]:
                    prefix_block.append((attr1, attr2))

        return prefix_block

    def is_in_next_level(self, x, level):
        for a in x:
            x_without_a = x.replace(a, '')
            if x_without_a not in level:
                return False

        return True

    def generate_next_level(self, level):
        lower_level = []
        # w naszej implementacji prefix_blocks juz nie zawieraja y == z
        prefix_blocks = self.generate_prefix_block(level)
        for k in prefix_blocks:
            y, z = k
            # poniewaz y i z naleza do prefix_block, to sa identyczne na l-1 pozycjach
            x = y + z[-1]
            if self.is_in_next_level(x, level):
                lower_level.append(x)
                self.stripped_product(x, y, z)

        return lower_level

    def initialise_stripped_partitions(self, c1):
        s = [[]] * len(self.t)
        for i in range(len(c1)):
            for t in c1[i]:
                self.t[t] = i

        return s, self.t

    def stripped_product(self, x, y, z):
        c1 = self.dict_partitions[y]
        c2 = self.dict_partitions[z]
        pi = []

        # TODO niepotrzebne self.t
        s, self.t = self.initialise_stripped_partitions(c1)

        for i in range(len(c2)):
            for t in c2[i]:
                if self.t[t] != 'NULL':
                    s[self.t[t]] = s[self.t[t]] + [t]
                    
            for t in c2[i]:
                if self.t[t] != 'NULL':
                    if len(s[self.t[t]]) >= 2:
                        pi.append(s[self.t[t]])

                    s[self.t[t]] = ''

        for i in range(len(c1)):
            for t in c1[i]:
                self.t[t] = 'NULL'

        self.dict_partitions[x] = pi


def computeSingletonPartitions(columns, data_2d, dict_partitions):
    for a in columns:
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
    data_df = pd.read_csv(input_file)

    row_labels_number = len(data_df.index)
    columns_header = list(data_df.columns.values)  # returns ['A', 'B', 'C', 'D', .....]

    table_t = ['NULL'] * row_labels_number  # this is for the table T used in the function stripped_product

    candidates = {'': columns_header[:]}
    dict_partitions = {}  # maps 'stringslikethis' to a list of lists, each of which contains indices
    computeSingletonPartitions(columns_header, data_df, dict_partitions)

    return Tane(data_2d=data_df, candidates=candidates, table_t=table_t, dict_partitions=dict_partitions,
                final_list_of_all_dependencies=[], column_headers=columns_header, row_labels_number=row_labels_number)


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
    L1 = tane.column_headers[:]  # L1 is a copy of listofcolumns
    l = 1
    L = [L0, L1]

    while L[l]:
        tane.compute_dependencies(L[l])
        tane.prune(L[l])
        temp = tane.generate_next_level(L[l])
        L.append(temp)
        l = l + 1

    print(f"List of all FDs: {tane.final_list_of_all_dependencies}")
    print(f"Total number of FDs found: {len(tane.final_list_of_all_dependencies)}")


if __name__ == '__main__':
    main()
