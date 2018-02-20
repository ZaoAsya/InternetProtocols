Сначала на каждый роутер добавляем физический модуль NM-1FE-TX

PC0
IP Address: 10.8.1.18
Subnet Mask: 255.255.255.0
Default Gateway: 10.8.1.1

PC1
IP Address: 10.8.1.19
Subnet Mask: 255.255.255.0
Default Gateway: 10.8.1.1

Server1
IP Address: 192.168.1.18
Subnet Mask: 255.255.255.0

Server2
IP Address: 192.168.2.18
Subnet Mask: 255.255.255.0

Server3
IP Address: 192.168.3.18
Subnet Mask: 255.255.255.0



Настройка маршрутизаторов на примере настройкии одного из интерфейсов на Router3:

Router>enable
Router#conf t
Router(config)#int fa1/0
Router(config-if)#ip address 192.168.2.1 255.255.255.0
Router(config-if)#no shutdown
Router(config-if)#exit
Router(config)#exit
Router#wr mem



Настройка протокола RIP на примере Router1:

Router>enable
Router#conf t
Enter configuration commands, one per line.  End with CNTL/Z.
Router(config)#router rip
Router(config-router)#network 192.168.10.0
Router(config-router)#network 10.8.1.0
Router(config-router)#network 192.168.1.0
Router(config-router)#exit
Router(config)#exit



Результаты

Router1:

Router#show ip route
Codes: C - connected, S - static, I - IGRP, R - RIP, M - mobile, B - BGP
       D - EIGRP, EX - EIGRP external, O - OSPF, IA - OSPF inter area
       N1 - OSPF NSSA external type 1, N2 - OSPF NSSA external type 2
       E1 - OSPF external type 1, E2 - OSPF external type 2, E - EGP
       i - IS-IS, L1 - IS-IS level-1, L2 - IS-IS level-2, ia - IS-IS inter area
       * - candidate default, U - per-user static route, o - ODR
       P - periodic downloaded static route

Gateway of last resort is not set

     10.0.0.0/24 is subnetted, 1 subnets
C       10.8.1.0 is directly connected, FastEthernet0/1
C    192.168.1.0/24 is directly connected, FastEthernet1/0
R    192.168.2.0/24 [120/1] via 192.168.10.2, 00:00:17, FastEthernet0/0
     192.168.10.0/30 is subnetted, 2 subnets
C       192.168.10.0 is directly connected, FastEthernet0/0
R       192.168.10.4 [120/1] via 192.168.10.2, 00:00:17, FastEthernet0/0

Router#show ip interface brief

Interface              IP-Address      OK? Method Status                Protocol
 
FastEthernet0/0        192.168.10.1    YES manual up                    up
 
FastEthernet0/1        10.8.1.1        YES manual up                    up
 
FastEthernet1/0        192.168.1.1     YES manual up                    up
 
Vlan1                  unassigned      YES unset  administratively down down


Router2:

Router#show ip route
Codes: C - connected, S - static, I - IGRP, R - RIP, M - mobile, B - BGP
       D - EIGRP, EX - EIGRP external, O - OSPF, IA - OSPF inter area
       N1 - OSPF NSSA external type 1, N2 - OSPF NSSA external type 2
       E1 - OSPF external type 1, E2 - OSPF external type 2, E - EGP
       i - IS-IS, L1 - IS-IS level-1, L2 - IS-IS level-2, ia - IS-IS inter area
       * - candidate default, U - per-user static route, o - ODR
       P - periodic downloaded static route

Gateway of last resort is not set

R    10.0.0.0/8 [120/1] via 192.168.10.1, 00:00:17, FastEthernet0/0
R    192.168.1.0/24 [120/1] via 192.168.10.1, 00:00:17, FastEthernet0/0
C    192.168.2.0/24 is directly connected, FastEthernet1/0
     192.168.10.0/30 is subnetted, 2 subnets
C       192.168.10.0 is directly connected, FastEthernet0/0
C       192.168.10.4 is directly connected, FastEthernet0/1

Router#show ip interface brief
Interface              IP-Address      OK? Method Status                Protocol
 
FastEthernet0/0        192.168.10.2    YES manual up                    up
 
FastEthernet0/1        192.168.10.6    YES manual up                    up
 
FastEthernet1/0        192.168.2.1     YES manual up                    up
 
Vlan1                  unassigned      YES unset  administratively down down

Router3:

Router#show ip route
Codes: C - connected, S - static, I - IGRP, R - RIP, M - mobile, B - BGP
       D - EIGRP, EX - EIGRP external, O - OSPF, IA - OSPF inter area
       N1 - OSPF NSSA external type 1, N2 - OSPF NSSA external type 2
       E1 - OSPF external type 1, E2 - OSPF external type 2, E - EGP
       i - IS-IS, L1 - IS-IS level-1, L2 - IS-IS level-2, ia - IS-IS inter area
       * - candidate default, U - per-user static route, o - ODR
       P - periodic downloaded static route

Gateway of last resort is not set

     10.0.0.0/24 is subnetted, 1 subnets
C       10.8.1.0 is directly connected, FastEthernet0/0
R    192.168.1.0/24 [120/1] via 10.8.1.1, 00:00:22, FastEthernet0/0
C    192.168.2.0/24 is directly connected, FastEthernet1/0
     192.168.10.0/30 is subnetted, 1 subnets
C       192.168.10.4 is directly connected, FastEthernet0/1

Router#show ip interface brief
Interface              IP-Address      OK? Method Status                Protocol
 
FastEthernet0/0        10.8.1.2        YES manual up                    up
 
FastEthernet0/1        192.168.10.6    YES manual up                    up
 
FastEthernet1/0        192.168.2.1     YES manual up                    up
 
Vlan1                  unassigned      YES unset  administratively down down