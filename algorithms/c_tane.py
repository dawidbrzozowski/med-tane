import time

from pandas import *
from collections import defaultdict
import numpy as NP
import itertools
import sys


class CTaneFileNotFoundError(Exception):
    pass


class CTane:

    def __init__(self, data_file):
        self.data = read_csv(data_file)

        self.columns = list(self.data.columns.values)
        self.table_t = [None] * len(self.data.index)
        self.layer_0 = []
        self.partitions = {}
        self.levels = [[], self.set_attr_in_level(self.columns[:])]
        self.candidates_dict = {('', ()): self.levels[1][:]}
        self.results = []

    def run(self):
        lvl_id = 1
        self.compute_initial_cplus(self.levels[lvl_id])

        full_start = time.time()
        while not (self.levels[lvl_id] == []):
            if lvl_id > 1:
                self.generate_c_plus(self.levels[lvl_id])

            self.compute_dependencies(self.levels[lvl_id])
            self.levels[lvl_id] = self.prune(self.levels[lvl_id])
            temp = self.generate_next_level(self.levels[lvl_id])
            self.levels.append(temp)
            lvl_id += 1

        full_end = time.time()
        print(f"Total time: {full_end - full_start}")
        print(f"List of all CFDs: {self.results}")
        print(f"Total number of CFDs found: {len(self.results)}")

    def replace_element_in_tuple(self, tup, id, val):
        tmp = list(tup)
        tmp[id] = val
        return tuple(tmp)

    def set_tuple_val_at(self, item: tuple, index, value):
        tmp = list(item)
        tmp[index] = value
        return tuple(tmp)

    def get_new_condition_if_dependant(self, x, a, sp, ca):
        x_without_a = (self.set_sub(x, a))
        if not a or not x_without_a:
            return False

        sp_with_ca = self.set_tuple_val_at(sp, x.index(a), ca[0])
        new_condition = self.create_condition_by_sub(sp, x, a)
        if (x, sp_with_ca) in self.partitions.keys():
            if len(self.partitions[x_without_a, new_condition]) == len(self.partitions[(x, sp_with_ca)]):
                return new_condition

        return None

    def generate_columns_without_x(self, x):
        new_columns = []
        for j in self.columns[:]:
            if j not in x:
                new_columns.append(j)

        return new_columns


    def generate_new_candidates(self, attribute, x, cond, dep_to_remove: tuple):
        new_candidates = []
        for (candidate_attribute, candidate_condition) in self.candidates_dict[(x, cond)]:
            if attribute != candidate_attribute and dep_to_remove != (candidate_attribute, candidate_condition):
                new_candidates.append((candidate_attribute, candidate_condition))

        return new_candidates

    def get_candidates_with_value(self, candidates, x):
        return [item for a in x for item in candidates if a in item[0]]

    def get_matching_candidates_in_level(self, level, x):
        return [item for item in level if x == item[0]]

    def set_sub(self, x, a):
        return x.replace(a, '')

    def get_candidate(self, x, cond):
        return self.candidates_dict[(x, cond)]

    def compute_dependencies(self, level):

        start = time.time()
        for (x, original_condition) in level:
            for (attr, ca) in self.get_candidates_with_value(self.get_candidate(x, original_condition), x):

                new_cond = self.get_new_condition_if_dependant(x, attr, original_condition, ca)
                if not new_cond:
                    continue

                self.results.append([self.set_sub(x, attr), attr, [new_cond, ca]])
                for (_, matching_candidate_condition) in self.get_matching_candidates_in_level(level, x):

                    if matching_candidate_condition[x.index(attr)] == ca[0] \
                            and self.create_condition_by_sub(matching_candidate_condition, x, attr) >= new_cond:

                        for column_without_x in self.generate_columns_without_x(x):
                            self.candidates_dict[(x, matching_candidate_condition)] = \
                                self.generate_new_candidates(column_without_x, x, matching_candidate_condition, (attr, ca))

        end = time.time()
        print(f"Compute dependencies time: {end - start}")

    def prune(self, level):
        start = time.time()
        new_level = []
        for (x, sp) in level:
            if self.candidates_dict[(x, sp)]:
                new_level.append((x, sp))

        end = time.time()
        print(f"Compute dependencies time: {end - start}")

        return new_level

    def generate_c_plus(self, level):
        start = time.time()
        for (x, sp) in level:
            candidates = []
            for a in x:
                conditional_x_without_a = (x.replace(a, ''), self.create_condition_by_sub(sp, x, a))
                if conditional_x_without_a in self.candidates_dict.keys():
                    candidates.insert(0, set(self.candidates_dict[conditional_x_without_a]))
                else:
                    candidates = []
                    break

            self.candidates_dict[(x, sp)] = list(set.intersection(*candidates))

        end = time.time()
        print(f"Compute C plus time: {end - start}")

    def compute_initial_cplus(self, level):
        self.generate_c_plus(level)
        for (a, ca) in level:
            stufftobedeleted = []
            for (att, val) in self.candidates_dict[(a, ca)]:
                if att == a and not val == ca:
                    stufftobedeleted.append((att, val))
            for item in stufftobedeleted:
                self.candidates_dict[(a, ca)].remove(item)

    def set_attr_in_level(self, columns):
        l1 = []
        attrs = self.computeattrs(columns)
        for a in columns:
            l1.append((a, ('--',)))
            for attr in attrs[a]:
                l1.append((a, (str(self.data.iloc[attr[0]][a]),)))
        self.initialise_partitiions(l1, attrs)
        return l1

    def initialise_partitiions(self, level1, attrs):
        for (a, sp) in level1:
            self.partitions[(a, sp)] = []
            self.partitions[(a, sp)] = attrs[a]

    def computeattrs(self, columns):
        attrs = {}
        for a in columns:
            attrs[a] = []
            for element in self.list_duplicates(self.data[a].tolist()):
                if len(element[1]) > 0:
                    attrs[a].append(element[1])
        return attrs

    def list_duplicates(self, seq):
        tally = defaultdict(list)
        for i, item in enumerate(seq):
            tally[item].append(i)
        return ((key, locs) for key, locs in tally.items() if len(locs) > 0)

    def append_next_level_if_possible(self, next_level, level, z, up):
        flag = True
        for att in z:
            up_without_a = self.create_condition_by_sub(up, z, att)
            z_without_a = z.replace(att, '')
            if (z_without_a, up_without_a) not in level:
                flag = False
                break

        if flag:
            next_level.append((z, up))

    def generate_next_level(self, level):
        start = time.time()
        next_level = []
        for i in range(0, len(level)):
            for j in range(i + 1, len(level)):

                if level[i][0] != level[j][0] and level[i][0][0:-1] == level[j][0][0:-1] and level[i][1][0:-1] == level[j][1][0:-1]:
                    z = level[i][0] + level[j][0][-1]
                    up = level[i][1] + (level[j][1][-1], )
                    self.partition_product((z, up), level[i], level[j])
                    self.append_next_level_if_possible(next_level, level, z, up)

        end = time.time()
        print(f"generate next lvl C plus time: {end - start}")
        return next_level

    def create_condition_by_sub(self, sp, x, a):
        return tuple(sp[i] for i in range(0, len(sp)) if i != x.index(a))

    def partition_product(self, zup, xsp, ytp):

        table_s = [[]] * len(self.table_t)
        partition_xsp = self.partitions[xsp]
        partition_ytp = self.partitions[ytp]
        self.partitions[zup] = []
        for i in range(len(partition_xsp)):
            for t in partition_xsp[i]:
                self.table_t[t] = i

        for i in range(len(partition_ytp)):
            for t in partition_ytp[i]:
                if self.table_t[t] is not None:
                    table_s[self.table_t[t]] = table_s[self.table_t[t]] + [t]

            for t in partition_ytp[i]:
                table_t_val = self.table_t[t]
                if self.table_t[t] is not None:
                    if len(table_s[table_t_val]) >= 1:
                        self.partitions[zup].append(table_s[table_t_val])

                table_s[table_t_val] = []

        for partition_xsp_val in partition_xsp:
            for t in partition_xsp_val:
                self.table_t[t] = None



def main():
    if len(sys.argv) <= 1:
        raise CTaneFileNotFoundError('No input file provided')

    data_file = str(sys.argv[1])
    c_tane = CTane(data_file)
    c_tane.run()


if __name__ == '__main__':
    main()

