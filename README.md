# Automated Deployment Demonstration

**This project is for demonstration purposes only. Don't use in production !**

The goal of this project is to demonstrate basic principles of automated
deployment of development and production infrastructure.

**Requirements:**  
* **Linux** or **Mac OSX** - operating system
* **Git**                  - source code storage and versioning
* **Vagrant**              - virtual machines provisioning
* **Ansible**              - infrastructure orchestration


# Basic knowledge
## YAML

A straightforward machine parseable data serialization format designed for:
* human readability
* interaction with scripting languages

## Ansible
Ansible is written in Python and it is using YAML for configuration. It is using
SSH to connect to servers. Ansible executes *playbooks*, which are the
definitions of tasks and environment to execute.  

The goal of a play is to map a group of hosts to some well defined *roles*,
represented by things Ansible calls *tasks*. At a basic level, a task is nothing
more than a call to an Ansible module.  

Whole process of playbook execution must be *idempotent*.


### Tasks
* create PostgreSQL user using 'shell' module (non-idempotent)  
```yaml
- name: Create 'dbuser' account in PostgreSQL db
  shell: createuser dbuser
```

* create PostgreSQL user using 'postgresql_user' module (idempotent)  
```yaml
- name: Create 'dbuser' account in PostgreSQL db
  postgresql_user:
    name: dbuser
    password: dbuser_password
    state: present
```

* install PostgreSQL (idempotent)
```yaml
- name: Install PostgreSQL
  apt:
    pkg: postgresql-9.3
    force: yes
    install_recommends: no
    state: latest
```

### Variables
* variable declaration  
```yaml
DATABASE_USER_NAME: dbuser
DATABASE_USER_PASSWORD: dbuser
```

* variable usage in task  
```yaml
- name: Create 'dbuser' account in PostgreSQL db
  postgresql_user:
    name: "{{ DATABASE_USER_NAME }}"
    password: "{{ DATABASE_USER_PASSWORD }}"
    state: present
```

### Templates (jinja2)
* variables declaration  
```yaml
DEBUG: yes

# list of users
USERS:
  - ivan
  - simon
  - joe
```

* variable usage in template and resulting file produced  
```html+jinja
{% if DEBUG %}
Running in debug mode !
{% endif %}

List of users:
{% for user in USERS %}
  * {{ user }}
{% endfor %}
```
```
Running in debug mode !

List of users:
  * ivan
  * simon
  * joe
```

* template deployment using 'template' module  
```yaml
- name: Configure PostgreSQL access policy
  template:
    src: postgresql/pg_hba.conf.j2
    dest: /etc/postgresql/9.3/main/pg_hba.conf
```

### Handlers
* handler declaration  
```yaml
- name: service postgresql restart
  service:
    name: postgresql
    state: restarted
```

* handler activation  
```yaml
- name: Configure PostgreSQL access policy
  template:
    src: postgresql/pg_hba.conf.j2
    dest: /etc/postgresql/9.3/main/pg_hba.conf
  notify:
    - service postgresql restart
```

### Files
* script deployment  
```yaml
- name: Install db-stats script
  copy:
    src: static/db-stats/db-stats.py
    dest: /opt/db-stats.py
```

### Roles
* **role** - collection of tasks, templates, handlers and variables creating
             usually one service. Roles can be reusable !  

* **playbook** - collection of selected roles  
```yaml
- hosts: db
  roles:
    - { role: basic }
    - { role: service-database }
```

### Directories structure
```
├── group_vars
│   └── all
├── host_vars
│   └── README
├── roles

│   ├── basic
│   │   ├── tasks
│   │   │   └── main.yml
│   │   └── templates
│   │       └── apt
│   │           └── sources.list.j2

│   ├── service-database
│   │   ├── handlers
│   │   │   └── main.yml
│   │   ├── tasks
│   │   │   └── main.yml
│   │   └── templates
│   │       └── postgresql
│   │           ├── pg_hba.conf.j2
│   │           └── pg_ident.conf.j2

│   ├── service-load-balancer
│   │   ├── handlers
│   │   │   └── main.yml
│   │   ├── tasks
│   │   │   └── main.yml
│   │   └── templates
│   │       └── haproxy
│   │           ├── haproxy.cfg.j2
│   │           └── haproxy.j2

│   ├── service-web
│       ├── files
│       │   └── static
│       │       └── db-stats
│       │           └── db-stats.py
│       ├── tasks
│       │   └── main.yml
│       ├── templates
│       │   ├── db-stats
│       │   │   └── db-stats.conf.j2
│       │   └── init
│       │       └── rc.local.j2
│       └── vars
│           └── main.yml

├── db-deploy.yml
├── db-test.yml
├── lb-deploy.yml
├── lb-test.yml
├── web-deploy.yml
└── web-test.yml
```

### Tasks delegation
* ask 'db' service to create user account from 'web' service
```yaml
- name: Create 'dbuser' account in PostgreSQL db
  postgresql_user:
    name: dbuser
    password: dbuser_password
    state: present
  delegate_to: db
```

* ask 'lb' service to remove 'web' server from load balancer before running maintenance
```yaml
- name: Remove server from load balancer
  shell: >
    sed -i "/server {{ ansible_eth1.ipv4.address }}/d" /etc/haproxy/haproxy.cfg
    &&
    service haproxy reload
  delegate_to: lb
```

### Tests
* integration test - test if database is running
```yaml
- name: Test if database is up and running
  shell: >
    psql -U postgres -d postgres -tAc "SELECT version()"
```


## Vagrant
### Vagrant file
* configuration file written in Ruby  
```ruby
Vagrant.configure(2) do |config|

  # basic OS image
  config.vm.box = "trusty-canonical"
  config.vm.box_url = "http://cloud-images.ubuntu.com/vagrant/trusty/current/trusty-server-cloudimg-i386-vagrant-disk1.box"

  # shared directory between host OS and VM
  config.vm.synced_folder '.', '/vagrant'

  # ports forwarding
  config.vm.network "forwarded_port", guest: 80, host: 8080

  # VirtualBox machine configuration
  config.vm.provider "virtualbox" do |vb|
    vb.gui = true      # launch VirtualBox GUI console
    vb.memory = "1024" # customize the amount of memory on the VM
  end

  # start shell provisioner by direct code injection
  config.vm.provision "shell", inline: <<-SHELL
    sudo apt-get update
    sudo apt-get install -y postgresql-9.3
  SHELL

end
```

### Commands
 * **vagrant up**         - start VM(s)
 * **vagrant status**     - check VM(s) status
 * **vagrant provision**  - run provisioner once VM(s) is up (after code update)
 * **vagrant ssh**        - connect to VM(s)
 * **vagrant halt**       - halt VM(s)
 * **vagrant destroy**    - delete VM(s)




# Demonstration
## Services
**Implemented services:**  
* db  - database service
* web - web service (simple app returning some data from db)
* lb  - load balancer service on top of the web service

**Active TCP ports forwarded from VMs to host machine:**  
* db  - PostgreSQL          - vm: 5432, host: 15432
* lb  - load balancer stats - vm: 8100, host: 18100
* lb  - web service         - vm: 80,   host: 10080
* web - web service         - vm: 8000, host: 18000


## Installation instructions - Ubuntu 14.04
### Ansible
* add Ansible repository  
```sh
$ sudo apt-get install software-properties-common
$ sudo apt-add-repository ppa:ansible/ansible
$ sudo apt-get update
```

* install Ansible  
```sh
$ sudo apt-get install ansible
```

### VirtualBox
* install Dynamic Kernel Module Support Framework  
```sh
$ sudo apt-get install dkms
```

* download and install VirtualBox 5 package from
  https://www.virtualbox.org/wiki/Downloads  

* install missing dependencies  
```sh
$ sudo apt-get -f install
```

### Vagrant
* download and install latest Vagrant package from
  http://www.vagrantup.com/downloads.html  

* install missing dependencies  
```sh
$ sudo apt-get -f install
```


## Deployment
* clone source code from Git  
```sh
$ git clone <GIT-REPOSITORY-URL>
```

* set APT_PROXY variable to Apt caching server if available (optional)  
```sh
$ export APT_PROXY=http://<IP-ADDRESS>:<PORT>
```

* start all services in virtual machines  
```sh
$ vagrant up
```

* launch load balancer stats and web services in web browser  
```sh
$ firefox http://localhost:18100/ http://localhost:10080/
```

* delete all services  
```sh
$ vagrant destroy
```
