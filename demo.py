import dockerlib
import perflib
import json
import time
import itertools


def calculate(nic_statistics_before, nic_statistics_after):
    # {'TX bytes': '0', 'RX bytes': '1022', 'TX packets': '0', 'RX packets': '4'}
    _before = {"TX bytes": 0, "RX bytes": 0}
    _after = {"TX bytes": 0, "RX bytes": 0}
    for v in itertools.chain(nic_statistics_before["senders"], nic_statistics_before["receivers"]):
        _before["TX bytes"] += int(v["TX bytes"])
        _before["RX bytes"] += int(v["RX bytes"])
    for v in itertools.chain(nic_statistics_after["senders"], nic_statistics_after["receivers"]):
        _after["TX bytes"] += int(v["TX bytes"])
        _after["RX bytes"] += int(v["RX bytes"])
    _after["TX bytes"] -= _before["TX bytes"]
    _after["RX bytes"] -= _before["RX bytes"]
    return _after


def perf_test_tu(filepath, image="atf/perftest", container_num=2, perftool="netperf", test_name="udp", pktsize=64, delay=0, duration=20):
    assert container_num % 2 == 0
    assert pktsize > 0
    assert delay >= 0
    assert duration >= 1
    # load env config file
    with open(filepath) as f:
        config = json.load(f)
    # clean environment
    proxy = dockerlib.Proxy(config["env"]["hosta"]["ip"])
    proxy.destroy_all_containers()
    # start generating network packets
    ipgen = dockerlib.IpGen("192.168.100.1-192.168.100.120")
    proxy.start_containers(image=image, duplicate=container_num, ipgen=ipgen)
    containers = proxy.get_all_containers()
    containers1 = containers[0:container_num / 2]
    containers2 = containers[container_num / 2:container_num]
    perftool = perflib.PktGen(perftool)
    for c in containers2:
        c.execute(perftool.create_server_cmd())
        assert c.check_process_exists(perftool.server_prog_name(), num=1)

    for c1, c2 in zip(containers1, containers2):
        perf_cmd = perftool.create_client_cmd(c2.ip,
                                              pktsize=pktsize,
                                              delay=delay,
                                              testname=test_name)
        c1.execute(detach=True, cmd=perf_cmd)
    # sleep 3 to wait for netperf process's exit delay because connection failure
    time.sleep(3)
    for c in containers1:
        assert c.check_process_exists(perftool.client_prog_name(), num=1)
    # collect nic statistics phase1
    nic_statistics_before = dict(senders=[], receivers=[])
    for c in containers1:
        nic_statistics_before["senders"].append(c.get_nic_statistics("eth0"))
    for c in containers2:
        nic_statistics_before['receivers'].append(c.get_nic_statistics("eth0"))
    # wait some time
    time.sleep(duration)
    # collect nic statistics phase2
    nic_statistics_after = dict(senders=[], receivers=[])
    for c in containers1:
        nic_statistics_after['senders'].append(c.get_nic_statistics("eth0"))
    for c in containers2:
        nic_statistics_after['receivers'].append(c.get_nic_statistics("eth0"))
    # calculate results
    results = calculate(nic_statistics_before, nic_statistics_after)
    results["container_num"] = container_num
    results["perf_cmd_example"] = perf_cmd
    print json.dumps(results, indent=4)
    # mongolib.upload(results, db="container_performance")
    proxy.destroy_all_containers()


if __name__ == "__main__":
    import logging
    LOG = logging.getLogger(__name__)
    logging.basicConfig(level=logging.DEBUG)
    perf_test_tu("env.json", container_num=10, pktsize=64, test_name="tcp")
