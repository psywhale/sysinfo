# Documentation for {{ name }}
{{ summary }}

### Document Version
{{ date }}

#### System Administrator

#### Secondary Administrator

#### Administrator Access

see Ghost Share

#### Support Contract

if any

#### Roles

Roles go here

### Criticality 

#### Category
Critical / Essential / Necessary / Desirable

#### Confidentiality
Red / Green / White / Black

#### WOSC Asset tag

na

#### Location
* Physical: HLC 144 Hubroom
* Logical: vcenter.campus.wosc.edu
* Backups: 


### Software Version 

#### General Information
* OS Name: {{ os }}
* CPUs: {{ cpucount }}
* Cores per socket: {{ socket }}
* RAM: {{ memory }}
* Number of Disks: {{ numDisks }}
{% for disk in disks %}
    * Mount {{ disk.diskPath }}  {{ disk.capacity }}
{% endfor %}
### Network Information
#### Firewall Information
* Watchguard HLC144
* NAT IP aka Public IP: 164.58.169.XXX 
* Ports open to Public
   * 80 ; 443 
* Ports open to Campus
   * 22 ssh ;
   
#### IP Configuration
{% for net in Net %}
* {{ net.mac }}
  * Network: {{ net.network }}
  * {{ net.ipv4 }}
  * Subnet
  * Gw
  * dns
{% endfor %}

#### Management Interfaces
* vcenter.campus.wosc.edu
  * Port: 9443
* SSH
  * port 22
* Perferred Method: SSH

### Backup Information

#### Backup Procedures
* When?
* How
1. Step 1
2. sdf
3. sadf

#### Backup Assuance Procedures

#### Backup Assuance Log Location

#### Disaster Recovery Procedures



