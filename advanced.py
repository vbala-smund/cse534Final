#!/usr/bin/python

import collections
import re
import simplejson
import json
from datetime import datetime

words = []
graph = {}
allnodes = {}
revlist = []
new = collections.OrderedDict()


transit_paths = {}
non_decimal = re.compile(r'[^\d.]+')
delete_more = re.compile(r'( --More-- [^\d*>]*)')


def put(data, filename):
        jsondata = simplejson.dumps(data, indent=4, skipkeys=True, sort_keys=True)
        fd = open(filename, 'w')
        fd.write(jsondata)
        fd.close()

def degree_calc():
    neighbours = {}
    as_paths = []
    degree = {}
    data_file = '2016 04' #Name of downloaded local file
    with open(data_file, 'r') as f:
        for i, line in enumerate(f):
            if '?' in line:
                continue
            temp = line[:-1]
            if 'More' in temp:
                temp = delete_more.sub('', temp)
            words = temp[61:].split()[:-1]
            words.reverse()
            #TODO change to numbers
            if len(words) > 0:
                try:
                    path = (map(int, words))
                except ValueError:
                    only_num_words = [non_decimal.sub(' ', x) for x in words]
                    split_words = []
                    for x in only_num_words:
                        split_words.extend(x.split())

                    path = (map(int, split_words))
            for x, y in zip(path, path[1:]):
                if x != y:
                    try:
                        neighbours[int(x)].add(int(y))
                    except KeyError:
                        neighbours[int(x)] = set([int(y)])
                    try:
                        neighbours[int(y)].add(int(x))
                    except KeyError:
                        neighbours[int(y)] = set([int(x)])
                as_paths.append(path)
    f.close()
    total_routing_entries = i
    for node in neighbours:
        degree[node] = len(neighbours[node])

    print "Degree Done"

    for path in as_paths:
        flag = False
        max_key = max(path, key=degree.get)
        for x, y in zip(path, path[1:]):
            if x != y:
                if x == max_key:
                    flag = True
                try:
                    if flag == False:
                        transit_paths[(x,y)] += 1
                    else:
                        transit_paths[(y,x)] += 1
                except KeyError:
                    if flag == False:
                        transit_paths[(x,y)] = 1
                    else:
                        transit_paths[(y,x)] = 1

    L = 1
    classified_result = {}
    results_by_class = {}
    results_by_class['s'] = set()
    results_by_class['cp'] = set()
    results_by_class['pc'] = set()
    results_by_class['peer'] = set()
    for path in as_paths:
        for ui, ui_1 in zip(path, path[1:]):
            if ui != ui_1:
                if (transit_paths.has_key((ui, ui_1)) and transit_paths.has_key((ui_1, ui))) and ( (transit_paths[ui_1,ui]> L and  transit_paths[ui,ui_1] > L) or (transit_paths[ui,ui_1] <=  L and transit_paths[ui,ui_1] > 0 and transit_paths[ui_1,ui] <=  L and transit_paths[ui_1,ui] > 0 ) ):
                    if not classified_result.has_key((ui, ui_1)):
                        classified_result[(ui, ui_1)] = 's'
                        results_by_class['s'].add((ui, ui_1))
                elif (transit_paths.has_key((ui_1, ui)) and transit_paths[(ui_1,ui)] > L ) or ( not transit_paths.has_key((ui, ui_1))):
                    if not classified_result.has_key((ui, ui_1)):
                        classified_result[(ui, ui_1)] = 'pc'
                        results_by_class['pc'].add((ui, ui_1))
                elif (transit_paths.has_key((ui, ui_1)) and transit_paths[(ui, ui_1)] > L ) or ( not transit_paths.has_key((ui_1, ui))):
                    if not classified_result.has_key((ui, ui_1)):
                        classified_result[(ui, ui_1)] = 'cp'
                        results_by_class['cp'].add((ui, ui_1))
                else:
                    print (ui,ui_1)


    not_peering = set()
    for path in as_paths:
        edgeNodeEcountered = False

        smallest_degree_node = min(path, key=degree.get)
        first_index_of_smallest_degree = path.index(smallest_degree_node)
        try:
            preceding_node          = path[first_index_of_smallest_degree - 1]
            preceding_degree        = degree[preceding_node]
            successive_node         = path[first_index_of_smallest_degree + 1]
            successive_degree       = degree[successive_node]
        except IndexError:
            edgeNodeEcountered = True

        for node, nextnode in zip(path, path[1:]):
            if node != nextnode:
                if (path.index(node) < first_index_of_smallest_degree - 2) \
                        or (path.index(node) < first_index_of_smallest_degree + 1 ) :
                    not_peering.add((node, nextnode))
                elif edgeNodeEcountered:
                    not_peering.add((node, nextnode))
                else:
                    if classified_result[(node, nextnode)] != 's':
                        if preceding_degree > successive_degree:
                            not_peering.add((smallest_degree_node, successive_degree))
                        else:
                            not_peering.add((preceding_node, smallest_degree_node))


    R = 60
    for path in as_paths:
        for node, nextnode in zip(path, path[1:]):
            if node != nextnode and not( (node, nextnode) in not_peering) and not( (nextnode, node) in not_peering) \
                    and degree[node]/degree[nextnode] < R and degree[node]/degree[nextnode] > 1/R :
                classified_result[(node, nextnode)] = 'peer'
                results_by_class['peer'].add((node, nextnode))






    results_by_node = {}
    set_of_nodes = set()

    for (x,y) in classified_result:
        set_of_nodes.add(x)
        set_of_nodes.add(y)
        category = classified_result[(x,y)]
        if results_by_node.has_key(x):
            results_by_node[x][category].append(y)
        else:
            results_by_node[x] = {'s':[],'cp':[],'pc':[],'peer':[],}
            results_by_node[x][category].append(y)
        if results_by_node.has_key(y):
            results_by_node[y][category].append(x)
        else:
            results_by_node[y] = {'s':[],'cp':[],'pc':[],'peer':[],}
            results_by_node[y][category].append(x)



    put(list(results_by_class['s']),'./sol/s.json')
    put(list(results_by_class['cp']),'./sol/cp.json')
    put(list(results_by_class['pc']),'./sol/pc.json')
    put(list(results_by_class['peer']),'./sol/peer.json')
    print len(results_by_node)
    with open('./sol/by_node.json', 'w') as outfile:
        json.dump(results_by_node, outfile)
    list_of_nodes = list(set_of_nodes)
    with open('./sol/list_of_nodes.json', 'w') as outfile:
        json.dump(list_of_nodes, outfile)

    pc = s = cp = peer = 0
    for x in classified_result:
        if classified_result[x] == 'cp':
            cp+=1
        if classified_result[x] == 'pc':
            pc += 1
        if classified_result[x] == 's':
            s += 1
        if classified_result[x] == 'peer':
            peer += 1

    print "Classified Edges:"
    print len(classified_result)
    print "Sibling, P2C, C2P, Peering:"
    print s,pc,cp,peer
    with open('./sol/final_results.txt', 'a') as outfile:
        outfile.write('\nName of file: ' + data_file)
        outfile.write('\nDate/Time: '+ str(datetime.utcnow()))
        outfile.write('\nTotal Routing Entries: '+ str(total_routing_entries))
        outfile.write('\nTotal Edges: '+ str(len(classified_result))+" "+str(peer+s+pc+cp))
        outfile.write('\nSibling: ' + str(s) + 'Peer: ' + str(peer) + 'P2C: ' + str(pc) + 'C2P: '+str(cp))
        outfile.write('\nR-value: '+str(R))
        outfile.write('\n----------------------------------------------------------------------------------\n\n\n\n\n\n')


if __name__ == '__main__':
    from time import time
    t0 = time()
    degree_calc()
    t1 = time()
    print 'Time Taken', t1 - t0
