# build atf perf test container
FROM ubuntu:trusty-20150612
MAINTAINER yangqunwei@huawei.com
LABEL vendor=huawei project=atf
ENV TARGET /usr/bin/
ADD . ${TARGET}
WORKDIR /root/
ENTRYPOINT ["top", "-b"]
CMD ["-c"]
