import pycurl, json
import time
import dateutil.parser
from datetime import datetime
from datetime import timezone
import pprint

BASE_URL = "http://127.0.0.1:3001/generator/"
#BASE_URL = "http://127.0.0.1:5000/generator/"

num_gens = 2
num_gens = num_gens + 1
AGGREGRATION_DELAY = 9
EFFICIENCY_CONSTANT = 0.29329722222222

start_times = dict()
most_recent_times = dict()
power_totals = dict()
fuel_totals = dict()
num_data_points = dict()
power_data_dict = dict()
fuel_data_dict = dict()

#TODO
def process_eff(generator_num):
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(power_data_dict)
    pp.pprint(fuel_data_dict)
    gen_key_fuel = 'generator{}fuel'.format(generator_num)
    gen_key_power = 'generator{}power'.format(generator_num)
    gen_key = 'generator{}'.format(generator_num)

    gen_power = power_totals[gen_key]
    gen_fuel = fuel_totals[gen_key]
    start_time_fuel = start_times[gen_key_fuel]
    recent_time_fuel = most_recent_times[gen_key_fuel]
    start_time_power = start_times[gen_key_power]
    recent_time_power = most_recent_times[gen_key_power]

    time_dif_fuel = recent_time_fuel - start_time_fuel
    time_dif_fuel_sec = time_dif_fuel.days * 24 * 3600 + time_dif_fuel.seconds

    time_dif_power = recent_time_power - start_time_power
    time_dif_power_sec = time_dif_power.days * 24 * 3600 + time_dif_power.seconds

    fuel_data_points = num_data_points[gen_key_fuel]
    power_data_points = num_data_points[gen_key_power]

    avg_fuel = gen_fuel/fuel_data_points
    avg_power = gen_power/power_data_points


    avg_efficiency = avg_fuel/(avg_power*EFFICIENCY_CONSTANT)


    efficiency_json = json.dumps({
    'generator': generator_num,
    'startTimeFuel': start_time_fuel.isoformat(),
    'startTimePower': start_time_power.isoformat(),
    'recentTimeFuel': recent_time_fuel.isoformat(),
    'recentTimePower': recent_time_power.isoformat(),
    'powerTotal': gen_power,
    'fuelTotal': gen_fuel,
    'avgFuel': avg_fuel,
    'avgPower': avg_power,
    'efficiency': avg_efficiency,
    }, indent=2, sort_keys=True)


    print(efficiency_json)

    start_times[gen_key_fuel] = None
    start_times[gen_key_power] = None
    power_totals[gen_key] = 0
    fuel_totals[gen_key] = 0
    num_data_points[gen_key_fuel] = 0
    num_data_points[gen_key_power] = 0
    return

def on_receive_fuel(data):
    #print(data)
    content = json.loads(data)

    #print()
    generator = content['generator']

    if 'Generator: {}'.format(generator) not in fuel_data_dict:
        fuel_data_dict['Generator: {}'.format(generator)] = list()

    fuel_data_dict['Generator: {}'.format(generator)].append(content)

    #gen_timestamp = datetime.utcfromtimestamp(content['time'])

    gen_timestamp = dateutil.parser.parse(content['time'])

    most_recent_times['generator{}fuel'.format(generator)] = gen_timestamp

    if 'generator{}fuel'.format(generator) in  num_data_points:
        num_data_points['generator{}fuel'.format(generator)] = num_data_points['generator{}fuel'.format(generator)] + 1
    else:
        num_data_points['generator{}fuel'.format(generator)] = 1

    if not ('generator{}fuel'.format(generator) in start_times) or start_times['generator{}fuel'.format(generator)] == None:
        start_times['generator{}fuel'.format(generator)] = gen_timestamp

    #print('fuel generator: {} time: {}'.format(generator, content['time']))


    if 'generator{}'.format(generator) not in fuel_totals:
        fuel_totals['generator{}'.format(generator)] = 0

    fuel_temp = fuel_totals['generator{}'.format(generator)]
    fuel_totals['generator{}'.format(generator)] = fuel_temp + int(content['fuelConsumed'])


def on_receive_power(data):
    #print(data)
    content = json.loads(data)

    #print()
    generator = content['generator']

    if 'Generator: {}'.format(generator) not in power_data_dict:
        power_data_dict['Generator: {}'.format(generator)] = list()

    power_data_dict['Generator: {}'.format(generator)].append(content)

    #gen_timestamp = datetime.utcfromtimestamp(content['time'])

    gen_timestamp = dateutil.parser.parse(content['time'])

    most_recent_times['generator{}power'.format(generator)] = gen_timestamp

    if 'generator{}power'.format(generator) in  num_data_points:
        num_data_points['generator{}power'.format(generator)] = num_data_points['generator{}power'.format(generator)] + 1
    else:
        num_data_points['generator{}power'.format(generator)] = 1

    if not ('generator{}power'.format(generator) in start_times) or start_times['generator{}power'.format(generator)] == None:
        start_times['generator{}power'.format(generator)] = gen_timestamp
    else:
        time_diff = gen_timestamp - start_times['generator{}power'.format(generator)]
        time_diff_sec = time_diff.days * 24 * 3600 + time_diff.seconds
        if time_diff_sec >= AGGREGRATION_DELAY:
            process_eff(content['generator'])

    #print('power generator: {} time: {}'.format(generator, content['time']))

    if 'generator{}'.format(generator) not in power_totals:
        power_totals['generator{}'.format(generator)] = 0

    power_temp = power_totals['generator{}'.format(generator)]
    power_totals['generator{}'.format(generator)] = power_temp + int(content['powerProduced'])


# Pre-allocate a list of curl objects
m = pycurl.CurlMulti()
#m.setopt(pycurl.M_MAX_CONCURRENT_STREAMS, 6000)

for gen_num in range(1, num_gens):
    conn_fuel = pycurl.Curl()
    conn_fuel.setopt(pycurl.URL, '{}{}/fuelConsumed'.format(BASE_URL, gen_num))
    conn_fuel.setopt(pycurl.WRITEFUNCTION, on_receive_fuel)
    m.add_handle(conn_fuel)

    conn_power = pycurl.Curl()
    conn_power.setopt(pycurl.URL, '{}{}/powerProduced'.format(BASE_URL, gen_num))
    conn_power.setopt(pycurl.WRITEFUNCTION, on_receive_power)
    m.add_handle(conn_power)

while 1:
    ret, num_handles = m.perform()
    time.sleep(0.1)
