#coding=utf8
from abc import ABCMeta
from abc import abstractmethod


class _Base(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def create_client_cmd(self, server, testname="udp", delay=0, duration=0, unit="m", pktsize=64, sbuf=8196):
        pass

    @abstractmethod
    def create_server_cmd(self, portnum):
        pass

    @abstractmethod
    def client_prog_name(self):
        pass

    @abstractmethod
    def server_prog_name(self):
        pass


class PktGen(_Base):
    def __init__(self, perftool):
        if perftool == "netperf":
            self.proxy = Netperf()
        else:
            raise KeyError("%s is not supported right now." % item)

    def create_client_cmd(self, server, testname="udp", delay=0, duration=0, unit="m", pktsize=64, sbuf=8196):
        return self.proxy.create_client_cmd(server,
                                            testname=testname,
                                            delay=delay,
                                            duration=duration,
                                            unit=unit,
                                            pktsize=pktsize,
                                            sbuf=sbuf)

    def create_server_cmd(self, portnum=None):
        return self.proxy.create_server_cmd(portnum=portnum)

    def client_prog_name(self):
        return self.proxy.client_prog_name()

    def server_prog_name(self):
        return self.proxy.server_prog_name()


class Netperf(_Base):
    def __init__(self):
        self.testname = {
            "udp": "UDP_STREAM",
            "tcp": "TCP_STREAM",
            "tcp_rr": "TCP_RR",
            "udp_rr": "UDP_RR"
        }

    def create_client_cmd(self, server, testname="udp", delay=0, duration=0, unit="m", pktsize=64, sbuf=8196):
        cmd = "netperf -H " + server + " -t " + self.testname[testname] + " -s " + str(delay) + \
              " -l " + str(duration) + " -f " + unit + " -- " + " -m " + str(pktsize) + \
              " -M " + str(pktsize) + " -s " + str(sbuf) + " -S " + str(sbuf)
        return cmd

    def create_server_cmd(self, portnum=None):
        if portnum is None:
            portnum = 12865
        return "netserver -p %s" % portnum

    @staticmethod
    def client_prog_name():
        return "netperf"

    @staticmethod
    def server_prog_name():
        return "netserver"