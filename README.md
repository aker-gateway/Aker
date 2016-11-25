# Aker SSH Gateway
![alt text](aker_logo.png "Aker")


### What is Aker?
Aker is a security tool that helps you configure your own Linux ssh jump/bastion host. Named after an Egyptian mythology deity who guarded the borders, Aker would act as choke point through which all your sysadmins and support staff access Linux production servers. Aker SSH gateway includes a lot of security features that would help you manage and administer thousands of Linux servers at ease. For a detailed look check our [Wiki](https://github.com/aker-gateway/Aker/wiki)  


### Motivation
I couldn't find an open source tool similar to [CryptoAuditor](https://www.ssh.com/products/cryptoauditor/) and [fudo](http://www.wheelsystems.com/en/products/wheel-fudo-psm/), such tools  are beneficial if you're seeking becoming PCI-DSS or HIPAA compliant for example, regardless of security standards compliance access to the server should be controlled and organized in a way convenient to both traditional and cloud workloads.


### Roadmap
* Phase 0
  * Integration with an identity provider (FreeIPA for now)
  * Parsable audit logs (json for example to work with Elasticsearch)
  * Highly available setup

* Phase 1
  * Admin WebUI
  * Session playback
  * Live session monitoring
  * Cloud support (AWS,OpenStack etc..) or On-premises deployments
  * Command filtering (Prevent destructive commands like rm -rf)
  * Encrypt sessions logs stored on disk.
  
* Phase 2
  * Support for graphical protocols (RDP, VNC, X11) monitoring
  * User productivity dashboard 
  
  
### See it in action
[![Aker - in action](https://i1.ytimg.com/vi/O-boM3LbVT4/hqdefault.jpg)](https://www.youtube.com/watch?v=O-boM3LbVT4)


### Requirements
Software:
- Linux (Tested on CentOS and ubuntu)
- Python (Tested on 2.7)
    
Python Modules:
- configparser
- urwid
- paramiko


### Installation
* First the dependencies 
~~~
yum install python2-paramiko python-configparser python-urwid
~~~

* Copying files
```
cp *.py /bin/aker/
```

* Copy aker.ini in /etc/ and edit it to include users and servers like below :
```
[General] 
log_level = DEBUG

[anazmy]
;; is user enabled
enabled = True

;; hosts section include the hosts allowed
;; for this user, one entry per line 
;; format: hostname,port,username
hosts = websrv1.example.com,22,root
	srv2.example.com,22,root
	oracldb.example.com,22,root
	dbsrv1.example.com,22,root

```

* Add `/bin/aker/aker.py` to /etc/shells 
```
echo "/bin/aker/aker.py" >> /etc/shells 
```

* Change user shell to aker
```
chsh -s /bin/aker/aker.py username
```

### Contributing
Currently I work on the code in my free time, any assistance is highly appreciated. Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests.
