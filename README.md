[![Join the chat at https://gitter.im/Akergateway/Aker](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/Akergateway/Aker?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

# Aker SSH Gateway
![alt text](aker_logo.png "Aker")


### What is Aker?
Aker is a security tool that helps you configure your own Linux ssh jump/bastion host. Named after an Egyptian mythology deity who guarded the borders, Aker would act as choke point through which all your sysadmins and support staff access Linux production servers. Aker SSH gateway includes a lot of security features that would help you manage and administer thousands of Linux servers at ease. For a detailed look check our [Wiki](https://github.com/aker-gateway/Aker/wiki)  


### Motivation
I couldn't find an open source tool similar to [CryptoAuditor](https://www.ssh.com/products/cryptoauditor/) and [fudo](http://www.wheelsystems.com/en/products/wheel-fudo-psm/), such tools  are beneficial if you're seeking becoming PCI-DSS or HIPAA compliant for example, regardless of security standards compliance access to the server should be controlled and organized in a way convenient to both traditional and cloud workloads.


### Current Featuers

* Supports FreeIPA 4.2 , 4.3 and 4.4 (Optional)
* Extensible, [Write Your Own Module](https://github.com/aker-gateway/Aker/wiki/IdP-Modules#writing-your-custom-idp-module)
* Session Playback
* Extract Session Commands
* SIEM-Ready json Session Logs
* Elasticsearch Integration

### Roadmap
* Phase 0
    * Integration with an identity provider (FreeIPA)
    * Extendable Modular structure, plugin your own module
    * Integration with config management tools
    * Parsable audit logs (json, shipped to Elasticsearch)
    * Highly available setup
    * Session playback


* Phase 1
    * Admin WebUI
    * Live session monitoring
    * Cloud support (AWS,OpenStack etc..) or On-premises deployments
    * Command filtering (Prevent destructive commands like rm -rf)
    * Encrypt sessions logs stored on disk.


* Phase 2
    * Support for graphical protocols (RDP, VNC, X11) monitoring
    * User productivity dashboard


### See it in action
[![Aker - in action](https://i1.ytimg.com/vi/O-boM3LbVT4/hqdefault.jpg)](https://www.youtube.com/watch?v=H6dCCw666Xw)


### Requirements
Software:
* Linux (Tested on CentOS, Fedora and ubuntu)
* Python (Tested on 2.7)
* (Optional) FreeIPA, Tested on FreeIPA 4.2 & 4.3
* redis

Python Modules:
* configparser
* urwid
* paramiko
* wcwidth
* pyte
* redis

### Installation


#### Automated :
* Use [this ansible playbook](https://github.com/aker-gateway/aker-freeipa-playbook)


#### Manually:
Aker can be setup on a FreeIPA client or indepentantly using json config file.

* Common Steps (FreeIPA or Json):

    * Clone the repo
    ```
    git clone https://github.com/aker-gateway/Aker.git /usr/bin/aker/
    ```

    * Install dependencies (adapt for Ubuntu)
    ```
    yum -y install epel-release
    yum -y install python2-paramiko python-configparser python-redis python-urwid python2-wcwidth redis
    ```

    * Set files executable perms
    ```
    chmod 755 /usr/bin/aker/aker.py
    chmod 755 /usr/bin/aker/akerctl.py
    ```

    * Setup logdir and perms
    ```
    mkdir /var/log/aker
    chmod 777 /var/log/aker
    ```

    * Enforce aker on all users but root, edit sshd_config
    ```
    Match Group *,!root
    ForceCommand /usr/bin/aker/aker.py
    ```

    * Restart ssh
    * Restart redis


* Choosing FreeIPA:
    * Assumptions:
        * Aker server already enrolled to FreeIPA domain

    * Create /etc/aker and copy /usr/bin/aker/aker.ini in it and edit it like below :
      ```
      [General]
      log_level = INFO
      ssh_port = 22

      # Identity Provider to determine the list of available hosts
      # options shipped are IPA, Json. Default is IPA
      idp = IPA
      hosts_file = /etc/aker/hosts.json

      # FreeIPA hostgroup name contatining Aker gateways
      # to be excluded from hosts presented to user
      gateway_group = gateways
      ```


* Choosing Json:
    * Create /etc/aker and copy /usr/bin/aker/aker.ini in it and edit it like below :
      ```
      [General]
      log_level = INFO
      ssh_port = 22

      # Identity Provider to determine the list of available hosts
      # options shipped are IPA, Json. Default is IPA
      idp = Json
      hosts_file = /etc/aker/hosts.json

      # FreeIPA hostgroup name contatining Aker gateways
      # to be excluded from hosts presented to user
      gateway_group = gateways
      ```

      * Edit /etc/aker/hosts.json to add users and hosts, a sample `hosts.json` file is provided .


* Aker also consumes commandline arguments:

```
usage: aker.py [-h] [--config CONFIG] [--log-file LOG_FILE]
           [--log-level LOG_LEVEL] [--session-log-dir SESSION_LOG_DIR]

optional arguments:
  -h, --help            show this help message and exit
  --config CONFIG, -c CONFIG
                        Path to config file
  --log-file LOG_FILE   Path to log file
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL,FATAL}
                        Set log level
  --session-log-dir SESSION_LOG_DIR
                        Session log dir
```

### Contributing
Currently I work on the code in my free time, any assistance is highly appreciated. Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests.
