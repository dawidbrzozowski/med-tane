import time
from collections import defaultdict

import click
import pandas as pd
from click import STRING
import visualisation as vis
from string import ascii_uppercase


class Tane:


    def __init__(self, data_2d):
        self.data_2d = data_2d

        row_labels_number = len(data_2d.index)
        columns_header = list(data_2d.columns.values)

        self.column_to_name, self.name_to_column = self._create_column_maps(columns_header)
        data_2d.columns = self.name_to_column.keys()

        initial_candidates = [item for item in self.name_to_column.keys()]
        self.candidates = {'': initial_candidates}

        self.final_list_of_all_dependencies = []
        self.attrs = initial_candidates
        self.row_labels_number = row_labels_number

        self._generate_global_partitions(initial_candidates, data_2d)

    def _generate_global_partitions(self, columns, data_2d):
        self.partitions = {}
        for a in columns:
            self.partitions[a] = []
            for element in self._list_duplicates(data_2d[a].tolist()):
                if len(element[1]) > 1:
                    self.partitions[a].append(element[1])

    def _list_duplicates(self, seq):
        tally = defaultdict(list)
        for i, item in enumerate(seq):
            tally[item].append(i)
        return ((key, locs) for key, locs in tally.items()
                if len(locs) > 0)

    def _map_multiset_to_names(self, column):

        name_string = ""
        for c in column:
            name = self.name_to_column[c]
            name_string = name_string + name + ","

        return name_string[:-1]


    def _get_name_from_column(self, column):
        if len(column) > 1:
            return self._map_multiset_to_names(column)
        else:
            return self.name_to_column[column]


    def get_final_list_of_all_dependencies(self):

        renamed_dep_list = []
        for dep in self.final_list_of_all_dependencies:

            dep_start = self._get_name_from_column(dep[0])
            dep_end = self._get_name_from_column(dep[1])

            renamed_dep = [dep_start, dep_end]
            renamed_dep_list.append(renamed_dep)

        return renamed_dep_list

    def _create_column_maps(self, columns):
        i = 0
        column_to_name = {}
        name_to_column = {}
        for c in ascii_uppercase:

            if i >= len(columns):
                break

            column_to_name[columns[i]] = c
            name_to_column[c] = columns[i]
            i = i + 1

        return column_to_name, name_to_column

    def search_for_candidates(self, x):
        thesets = []
        for a in x:
            x_without_a = self.set_substruct(x, a)
            if x_without_a in self.candidates.keys():
                temp = self.candidates[x_without_a]
            else:
                temp = self.search_for_candidates(x_without_a)
            thesets.append(set(temp))
        return list(set.intersection(*thesets))

    def compute_candidates_without_attr(self, x):
        attrs = self.attrs[:]
        for j in x:
            if j in attrs:
                attrs.remove(j)

        return attrs

    def compute_dependencies(self, level):
        for x in level:
            attr_candidates = []
            for a in x:
                x_without_a = self.set_substruct(x, a)
                attr_candidates.insert(0, set(self.candidates[x_without_a]))
            self.candidates[x] = list(set.intersection(*attr_candidates))

        for x in level:
            for a in x:
                if a in self.candidates[x]:
                    if self.is_functional_dependency(self.set_substruct(x, a), a):
                        self.final_list_of_all_dependencies.append([x.replace(a, ''), a])
                        self.candidates[x].remove(a)

                        for b in self.compute_candidates_without_attr(x):
                            if b in self.candidates[x]:
                                self.candidates[x].remove(b)

    def is_functional_dependency(self, a, b):
        if not a or not b:
            return False

        return self.check_error(a) == self.check_error(self.set_add(a, b))

    def check_error(self, x):
        total = 0
        for i in self.partitions[x]:
            total = total + len(i)

        return (total - len(self.partitions[x])) / self.row_labels_number

    def is_super_key(self, x):
        return not self.partitions[x] or not self.partitions[x][0]

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
                self.candidates[potential_candidate] = self.search_for_candidates(potential_candidate)

            candidate_sets.append(set(self.candidates[potential_candidate]))

        return candidate_sets

    def prune(self, level):
        for x in level:

            if not self.candidates[x]:
                level.remove(x)

            # odwróciliśmy logikę dla większej czytelności
            if not self.is_super_key(x):
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
        s_tab = [[]] * self.row_labels_number
        t_tab = [None] * self.row_labels_number
        for i in range(len(c1)):
            for t in c1[i]:
                t_tab[t] = i

        return s_tab, t_tab

    def stripped_product(self, x, y, z):
        c1 = self.partitions[y]
        c2 = self.partitions[z]
        pi = []

        s_tab, t_tab = self.initialise_stripped_partitions(c1)

        for i in range(len(c2)):
            for t in c2[i]:
                if t_tab[t] is not None:
                    s_tab[t_tab[t]] = s_tab[t_tab[t]] + [t]

            for t in c2[i]:
                if t_tab[t] is not None:
                    if len(s_tab[t_tab[t]]) >= 2:
                        pi.append(s_tab[t_tab[t]])

                    s_tab[t_tab[t]] = []

        for i in range(len(c1)):
            for t in c1[i]:
                t_tab[t] = None

        self.partitions[x] = pi

def initialize_tane_from_file(input_file: STRING):
    data_df = pd.read_csv(input_file)
    return Tane(data_2d=data_df)

@click.command()
@click.option(
    "-i",
    "--input_file",
    type=STRING,
    required=True,
    help="Path to the input file")
def main(input_file: STRING):
    start = time.time()

    tane = initialize_tane_from_file(input_file)

    L0 = []
    L1 = tane.attrs[:]  # L1 is a copy of listofcolumns
    l = 1
    L = [L0, L1]

    while L[l]:
        print(f"Current level is {l}")
        tane.compute_dependencies(L[l])
        tane.prune(L[l])
        temp = tane.generate_next_level(L[l])
        L.append(temp)
        l = l + 1

    print(f"List of all FDs: {tane.get_final_list_of_all_dependencies()}")
    print(f"Total number of FDs found: {len(tane.get_final_list_of_all_dependencies())}")

    end = time.time()
    print(f"Runtime of the program is {end - start}")

    visualiser = vis.Visualiser(tane.get_final_list_of_all_dependencies())


if __name__ == '__main__':
    main()
