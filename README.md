### 说明
1.  Build目录：构建atf/perftest容器镜像的dockerfile netperf二进制文件等。 
2.  Demo.py: tu测试场景编码示例。 
3.  Dockerlib：容器操作库。
4.  Env.json:环境配置信息。
5.  Perflib.py: 性能测试工具如netperf命令组装。

### 测试
执行：python demo.py   
返回结果： 
    {
        "container_num": 10, 
        "perf_cmd_example": "netperf -H 192.168.100.1 -t TCP_STREAM -s 0 -l 0 -f m --  -m 64 -M 64 -s 8196 -S 8196", 
        "TX bytes": 7284470092, 
        "RX bytes": 7300334606  
    }
