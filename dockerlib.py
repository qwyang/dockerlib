#coding=utf8
import subprocess
import re
import os
import logging
from iptools import IpRange
from docker import Client
LOG = logging.getLogger(__name__)


class IpGen(object):
    def __init__(self, ip_range, netmask=24):
        ip1, ip2 = ip_range.split('-')
        self.range = IpRange(ip1, ip2)
        self.current = 0
        self.netmask = netmask

    def available(self):
        return len(self.range) - self.current > 0

    def alloc(self):
        if self.available():
            ip = self.range[self.current]
            self.current += 1
            return self._itoa(ip)
        else:
            raise Exception("sorry, all ips have been allocated.")

    def _itoa(self, ip):
        return ip + '/' + str(self.netmask)


class CmdResult(object):
    def __init__(self, retcode=0, stdout="", stderr=""):
        self.retcode = retcode
        self.stdout = stdout
        self.stderr = stderr

    @property
    def sucess(self):
        return self.retcode == 0


class Proxy(object):
    def __init__(self, server=None, port=2375, version="1.19"):
        if server is None:
            self.url = 'unix:///var/run/docker.sock'
        else:
            self.url = "tcp://%s:%s" % (server, port)
        self._cli = Client(base_url=self.url, version=version)
        assert self._cli.ping() == "OK"

    def get_all_containers(self):
        all = []
        for attrs in self._cli.containers():
            for key in attrs.keys():
                attrs[key.lower()] = attrs[key]
                attrs.pop(key)
            attrs["url"] = self.url
            all.append(Container(attrs))
        return all

    def destroy_all_containers(self):
        for c in self.get_all_containers():
            self._cli.remove_container(c.id, force=True)

    def start_containers(self, image, duplicate, ipgen, cmd=None):
        for i in range(duplicate):
            host_config=self._cli.create_host_config(privileged=True)
            tmp = self._cli.create_container(image, host_config=host_config, command=cmd)
            cid = tmp.get("Id")
            LOG.debug("container %s created.", cid)
            self._cli.start(cid)
            LOG.debug("container %s started.", cid)
            ip = ipgen.alloc()
            command = "docker -H " + self.url + " exec " + cid + " ifconfig eth0 " + ip + " up"
            ret = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            if ret.wait() != 0:
                raise Exception("[Error] set up ip for %s failed!cmd=%s" % (cid, cmd))


class Container(object):
    def __init__(self, attrs):
        self.attrs = attrs

    def execute(self, cmd, detach=False):  #### 直接使用docker命令行的方式补齐返回结果
        # use docker cmd other than docker-py
        command = "docker " + "-H " + self.url + " exec "
        command += " -d " if detach else ""
        command += self.id + " " + cmd
        LOG.debug(command)
        ret = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        retcode = ret.wait()
        stdout = ret.stdout.read()
        stderr = ret.stderr.read()
        return CmdResult(retcode, stdout, stderr)

    def check_process_exists(self, pname=None, pid=None, num=1):
        out = self.execute("ps -A")
        assert out.sucess
        if pid is not None:
            for line in out.stdout.splitlines():
                values = line.split()
                pid_x, name = values[0], values[3]
                if pid_x == str(pid):
                    return True
        if pname is not None:
            count = 0
            for line in out.stdout.splitlines():
                values = line.split()
                pid, name = values[0], values[3]
                if pname == name:
                    count += 1
            if count == num:
                return True
        return False

    def get_nic_statistics(self, device="eth0"):  #### execute函数的调用
        statistics = dict()
        result = self.execute("ifconfig % s" % device)
        matches = re.findall(r'RX packets:(\d+)', result.stdout, re.MULTILINE)
        statistics["RX packets"] = matches[0]
        matches = re.findall(r'TX packets:(\d+)', result.stdout, re.MULTILINE)
        statistics["TX packets"] = matches[0]
        matches = re.findall(r'RX bytes:(\d+)', result.stdout, re.MULTILINE)
        statistics["RX bytes"] = matches[0]
        matches = re.findall(r'TX bytes:(\d+)', result.stdout, re.MULTILINE)
        statistics["TX bytes"] = matches[0]
        return statistics

    @property
    def ip(self):
        result = self.execute("ifconfig eth0")
        matches = re.findall(r'inet addr:(\d+\.\d+\.\d+\.\d+)', result.stdout, re.MULTILINE)
        return matches[0]

    def __getattr__(self, item):
        if item in self.attrs:
            return self.attrs[item]
