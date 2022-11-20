import igraph as ig
import matplotlib.pyplot as plt
import copy
import json
import requests
from hosts_switches import hs


def find_link(src, dst):
    """Function that finds link between source device and destination device and returns list with two tuples
    containing deviceId and port"""
    if src == 0:
        src = 'a'
    if dst == 0:
        dst = 'a'
    src_device_id = "of:000000000000000" + str(src)
    dst_device_id = "of:000000000000000" + str(dst)
    headers = {
        'Accept': 'application/json',
    }
    response = requests.get('http://192.168.1.75:8181/onos/v1/links', headers=headers, auth=('karaf', 'karaf'))
    links = response.json()['links']
    for link in links:
        if link['src']['device'] == src_device_id and link['dst']['device'] == dst_device_id:
            sd_port = link['src']['port']
            dd_port = link['dst']['port']
            return [(src_device_id, int(sd_port)), (dst_device_id, int(dd_port))]


flows = {'flows': []}

user_src = input('Src: ')
user_dst = input('Dst: ')

src_switch = hs[user_src]['switch']
src_switch_nr = src_switch[-1::]
if src_switch_nr == 'a':
    src_switch_nr = 0
src_switch_nr = int(src_switch_nr)
src_port = hs[user_src]['port']
src_host = hs[user_src]['host']

dst_switch = hs[user_dst]['switch']
dst_switch_nr = dst_switch[-1::]
if dst_switch_nr == 'a':
    dst_switch_nr = 0
dst_switch_nr = int(dst_switch_nr)
dst_port = hs[user_dst]['port']
dst_host = hs[user_dst]['host']

# finding the shortest path
graph_links = [(1, 2), (1, 3), (2, 3), (3, 4), (3, 6), (3, 8), (6, 8), (4, 6),
               (4, 7), (6, 7), (5, 7), (6, 9), (9, 0), (7, 8), (7, 9)]

g = ig.Graph(
    10,
    graph_links
)

g.es["weight"] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

results = g.get_shortest_paths(src_switch_nr, to=dst_switch_nr, weights=g.es["weight"], output="epath")

if len(results[0]) > 0:
    # Add up the weights across all edges on the shortest path
    distance = 0
    for e in results[0]:
        distance += g.es[e]["weight"]
        g.es[e]["weight"] += 1
    print(g.es["weight"])
    print("Shortest weighted distance is: ", distance)
else:
    print("End node could not be reached!")

with open('sample.json') as file:
    sample = json.load(file)

# flows between switches and hosts
flow = copy.deepcopy(sample)
flow['deviceId'] = src_switch
flow['treatment']['instructions'][0]['port'] = src_port
flow['selector']['criteria'][0]['mac'] = src_host
flows['flows'].append(flow)

flow = copy.deepcopy(sample)
flow['deviceId'] = dst_switch
flow['treatment']['instructions'][0]['port'] = dst_port
flow['selector']['criteria'][0]['mac'] = dst_host
flows['flows'].append(flow)

route = [graph_links[result] for result in results[0]]

# print(route)

# setting the switches in correct order
for connection in route:
    if route.index(connection) != 0:
        if connection[0] != route[route.index(connection) - 1][1]:
            new_connection = (connection[1], connection[0])
            route[route.index(connection)] = new_connection
    elif src_switch_nr != connection[0]:
        new_connection = (connection[1], connection[0])
        route[route.index(connection)] = new_connection

# print(route)

# creating flows between switches
for connection in route:
    src_dst = connection
    link1 = find_link(src_dst[0], src_dst[1])
    print(link1)

    flow = copy.deepcopy(sample)
    flow['deviceId'] = link1[0][0]
    flow['treatment']['instructions'][0]['port'] = link1[0][1]
    flow['selector']['criteria'][0]['mac'] = dst_host
    flows['flows'].append(flow)

    flow = copy.deepcopy(sample)
    flow['deviceId'] = link1[1][0]
    flow['treatment']['instructions'][0]['port'] = link1[1][1]
    flow['selector']['criteria'][0]['mac'] = src_host
    flows['flows'].append(flow)

# print(flows)

flows_json = json.dumps(flows, indent=4)

headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
}

response = requests.post('http://192.168.1.75:8181/onos/v1/flows', headers=headers, data=flows_json,
                         auth=('karaf', 'karaf'))

# Graph for shortest path
g.es['width'] = 0.5
g.es[results[0]]['width'] = 2.5

fig, ax = plt.subplots()
ig.plot(
    g,
    target=ax,
    layout='circle',
    vertex_color='steelblue',
    vertex_label=range(g.vcount()),
    edge_width=g.es['width'],
    edge_label=g.es["weight"],
    edge_color='#666',
    edge_align_label=True,
    edge_background='white'
)
plt.show()
