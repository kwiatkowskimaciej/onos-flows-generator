import copy
import json
import requests
from hosts_switches import hs

flows = {'flows': []}

user_src = input('Src: ')
user_dst = input('Dst: ')

src_switch = hs[user_src]['switch']
src_port = hs[user_src]['port']
src_host = hs[user_src]['host']

dst_switch = hs[user_dst]['switch']
dst_port = hs[user_dst]['port']
dst_host = hs[user_dst]['host']

headers = {
    'Accept': 'application/json',
}

paths = requests.get(f'http://192.168.1.75:8181/onos/v1/paths/{src_switch}/{dst_switch}', headers=headers, auth=('karaf', 'karaf'))
links = paths.json()['paths'][0]['links']

with open('sample.json') as file:
    sample = json.load(file)

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

for link in links:
    flow = copy.deepcopy(sample)
    flow['deviceId'] = link['src']['device']
    flow['treatment']['instructions'][0]['port'] = link['src']['port']
    flow['selector']['criteria'][0]['mac'] = dst_host
    flows['flows'].append(flow)

    flow = copy.deepcopy(sample)
    flow['deviceId'] = link['dst']['device']
    flow['treatment']['instructions'][0]['port'] = link['dst']['port']
    flow['selector']['criteria'][0]['mac'] = src_host
    flows['flows'].append(flow)

flows_json = json.dumps(flows, indent=4)

headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
}

response = requests.post('http://192.168.1.75:8181/onos/v1/flows', headers=headers, data=flows_json,
                         auth=('karaf', 'karaf'))
print(response)
