# **Partie Box : Procédure d'installation et de configuration**

## **1. Installation de l'OS Raspbian sur rapsberry**
Nous allons installer un OS au raspebrry pi simulant la box. Dans toute la procédure, ce raspberry pi sera nommé rpi_box.
Afin de faciliter l'accès au dépôt et de bénéficier des derniers correctifs de l'OS raspbian, il est judicieux de prendre la dernière version Bullseye.
- [raspios_lite_Bullseye](https://downloads.raspberrypi.org/raspios_lite_armhf/images/raspios_lite_armhf-2022-04-07/)


Flasher l'image raspios_lite sur la cartes sd du raspberry via l'outil Etcher : https://www.balena.io/etcher/

## **2. Configuration de l'OS Raspbian**

Connectez le rpi_box par par Ethernet et branchez y un clavier, et un écran via le port HDMI.
Pour accéder aux commandes du raspberrypi, nous avons laissé par défaut (dentifiant : pi et mot de passe : raspberry)


Il est possible de changer le mot de passe (non expliqué dans ce document). Déterminez l'adresse IP de l'interface eth0 rpi_box par la commande

```bash
ifconfig
```

l'addresse ip se trouve dans la premiere ligne du block eth0
```bash
eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 10.242.82.1  netmask 255.255.255.0  broadcast 10.242.82.255
        inet6 fe80::db6f:275a:6832:41e2  prefixlen 64  scopeid 0x20<link>
```
Notez-la pour vous connecter en ssh a la RPI.

désormais on appellera l'adresse IP de la box RPI sur son interface eth0 <RPI_BOX_IP_ETH0>

Activer l'option ssh (désactivé par défaut) et configurer les options de localisation:

```bash
sudo raspi-config
```

* Activer l'option ssh (Interface Options)
* Configurer la timezone (Localization Options -> Timezone)
* Configurer WLAN country pour activer l'interface wlan0 (Localization Options -> WLAN Country)

Redémarrer la RPI

```bash
sudo reboot now
```

Par la suite, l'écran et le clavier ne sont plus utiles. On peut se connecter par SSH via l'outil Putty en indiquant l'adresse ip préalabelement récupérée.

Une fois connecté en  SSH, il est utile si cela est nécessaire, de changer le clavier en mode azerty, on peut le configurer de la manière suivante :

```bash
sudo nano /etc/default/keyboard
```

puis modifier la ligne XKBLAYOUT="gb" par XKBLAYOUT="fr"

Pour arrêter de recevoir des variables d'environnement du client SSH il faut modifier le fichier de configuration ssh:

```bash
sudo nano /etc/ssh/sshd_config
```

 Marquer la ligne `AcceptEnv LANG LC_* ` comme commentaire.

 ## **3. Configuration de la RPI comme point d'access WiFi**

 Cette procédure peut être effectuée de façon [automatique](#configuration-automatique) ou [manuellement](#configuration-manuelle).

 ## **Configuration Automatique**

La configuration RPI automatique est fait via le script
`Server_Box/setup/scripts/rpi-server-box-setup.sh`

Il est necessaire d'ajouter les adresses IP du réseau à configurer dans le fichier de configuration `Server_Box/setup/scripts/rpi-server-box-setup.sh`

```
RPI_SERVER_BOX_IP=192.168.4.1 -> Adresse IP de la interface wlan0 (WiFi) de la RPI box
RPI_CAMERA_IP=192.168.4.12 -> Adresse IP de la camera
RPI_CAMERA_PORT=4000 -> Port de la camera
```

Pour lancer le script de configuration automatique il est nécessaire de copier le répertoire setup via scp dans la RPI_Box, pour cela:
```bash
scp -r Server_Box/setup/ <PI_USER>@<RPI_BOX_IP_ETH0>:
```

Se connecter via SSH a la RPI_Box
```bash
ssh <PI_USER>@<RPI_BOX_IP_ETH0>
```

lancer le script depuis le répertoire `setup/scripts`
```bash
cd setup/scripts
chmod +x rpi-server-box-setup.sh
sudo ./rpi-server-box-setup.sh
```

On peut valider le process apres le redemarage de la rpi_box
Le point d'accès de la rpi_box sera maintenant visible par `rpibox` avec comme mot de passe `greenhomelan`
## **Configuration Manuelle**

### **Installation des packages**

Nous allons ici installer les paquets issues de dépot linux :

```bash
sudo apt update
sudo apt upgrade
sudo apt install python3-pip (est ce nécessaire?)
sudo apt install dnsmasq
sudo apt install iptables
```

## **Configuration du rpi_box en tant que point d'accès Wi-Fi**

le rpi_box doit être configuré comme point d'accès Wi-Fi. Les commandes pour la configuration sont les suivantes :

```bash
sudo apt install hostapd
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
```

```bash
sudo DEBIAN_FRONTEND=noninteractive apt install -y netfilter-persistent iptables-persistent
sudo reboot
```

Par la suite, le fichier dhcpcd.conf est configuré pour l'attribution d'une adresse statique

```bash
sudo nano /etc/dhcpcd.conf
```

Les 3 lignes de code ci-dessous doit être copier dans le fichier (ctr+x pour sortir du mode nano)

```
interface wlan0
    static ip_address=192.168.4.1/24
    nohook wpa_supplicant
```

Ensuite, il faut activer le routage	en éditant un nouveau fichier :

```bash
sudo nano /etc/sysctl.d/routed-ap.conf
```

en copiant/collant cette ligne

```
net.ipv4.ip_forward=1
```

Les 2 commandes suivent la manière dont le routage du traffic HTTP doit être réaliser par le rpi-box en le redirigeant vers vers le rapsberry pi de la camera dont l'adresse est 192.168.4.12 et sur le port 4000. Cette indication est à modifier si l'adresse IP du raspberry camera est différente.


```bash
sudo iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 4000 -m conntrack --ctstate NEW -j DNAT --to 192.168.4.12:4000
```

```bash
sudo iptables -t nat -A PREROUTING -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
```

Puis les 2 commandes suivantes servent à finaliser le routage

```bash
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
```

Pour rendre les règles de routage persistente:
```bash
sudo netfilter-persistent save
```


Ensuite, on configure les services DHCP et DNS par les commandes suivantes :

```bash
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
sudo nano /etc/dnsmasq.conf
```

les 4 lignes ci-dessous sont à copier coller dans le fichier dnsmasq.conf en remplacement de l'existant. On indique ici, la plage des adresses IP de tout éléments venant se connecter sur le point d'acceès rpi_box avec une durée de 300 jours.

```
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,300d
domain=wlan
address=/gw.wlan/192.168.4.1
```

Pour finaliser la configuration du point d'accès, on configure les paramètres réseau en proposant un nom de réseau et un mot de passe

```bash
sudo nano /etc/hostapd/hostapd.conf
```

puis copier coller les lignes ci-dessous.
```
interface=wlan0
driver=nl80211
ssid=rpibox
hw_mode=g
channel=7
macaddr_acl=0
wmm_enabled=1
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=greenhomelan
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
country_code=FR
```

Puis on indique l'emplacement de la configuration

```bash
sudo nano /etc/default/hostapd
```

```
DAEMON_CONF="/etc/hostapd/hostapd.conf"
```

Le rpi_box aura donc une adresse ip fixe wifi dont l'adresse est : 192.168.4.1 en plus de son adresse Ethernet. On peut le vérifier par la commande:

```bash
sudo ifconfig
```
où etho et wlan0 on chacun une adresse ip attribué avec wlan0 valant 192.168.4.1

On valide le tout par le redémarrage du rpi-box

```bash
sudo reboot now
```

Le point d'accès de la rpi_box sera maintenant visible par `rpibox` avec comme mot de passe `greenhomelan`
(un autre mot de passe est possible du moment qu'il est renseigné dans le fichier hostapd.conf)

## **4. Installation du serveur Nodejs**

Dans un premier temps, il faut récupérer le répertoire sur GitHub:

`git clone git@github.com:clemanthkar/GreenHomeLan_Camera.git`

Aller dans le répertoire GreenHomeLan/Server_Box qui correspond à notre environnement de travail pour le rpi_box. Installer les dépendances suivantes:

```bash
npm init (valider chaque lignes)
```



 Puis installation des toutes les dépendances :

```bash
npm i express
npm i axios
npm i cors
npm i child_process
npm i onoff
npm i util
```

Avant de lancer le server il faut renseigner une information contenue dans le fichier config.js

```
MSERV_ADR : {
        "e4:5f:01:0e:34:3f" : "http://192.168.1.29:8000",
        "e4:5f:01:0e:31:ed" : "http://172.16.57.127:8000"
    }
```
L'obejt MSERV_ADR prend comme clé l'adresse mac du rpi-cloud et la valeur l'adresse IP du cloud. Cela signifie que le rpi-cloud doit être entièrement configuré er fonctionnel pour récuéprer ces informations par l'intermédiaire de la commande suivante :

```bash
sudo arp -a
```

Le serveur est ensuite prêt à être lancé :

```bash
node server_box.js
```

A noter qu'il faut lancer le server_box.js au préalable et qu'il faut faire un ping sur le cloud pour favoriser la découverte qui n'est pour l'instant pas systématique.


## **5. Installation du serveur Flask**

il est possible d'exécuter le code dans une post de dev, pour cela il est nécessaire d'avoir installé python 3.9

Pour installer le gestionaire de dependences [poetry](https://python-poetry.org/)

```bash
 curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
```

Configure poetry pour pouvoir créer des environements virtuels dans le repertoire du projet

```bash
poetry config virtualenvs.in-project true
```

Creer le environnement virtuel avec les dépendances:
```bash
cd server_box
poetry install
```

Activer le environnement virtuel:
```bash
poetry shell
```

Pour lancer l'application il faut définir les variables d'environnement:
```bash
export FLASK_APP="server_box/server/app:create_app()"
export FLASK_ENV=development
```

Create logfiles

Log files defined in configuration file located in *server_box/server/config/logging-config.yml* must be created before launching the application

```bash
mkdir logs
mkdir logs/manager
mkdir logs/interface
touch logs/app.log logs/orchestrator.log logs/api-rest.log
touch logs/manager/camera.log logs/manager/electrical_panel.log logs/manager/thread.log logs/manager/wifi_bands.log logs/manager/ip_discovery.log
touch logs/interface/mqtt.log logs/interface/thread.log logs/interface/telnet.log
```

Pour lancer l'application flask, depuis Server_Box
```bash
flask run
```

## **Open Thread setup**
The complete installation and network setup procedure can be found [here](https://espace.agir.orange.com/display/HOMEINAI/How+to+set+up+OpenThread+Network)

First, you need to retrieve Git Project:

```bash
git clone https://github.com/openthread/ot-br-posix.git --depth 1
```
Then you need to execute a scripts to bootstrap the Thread Border Router (not with sudo):

```bash
cd ot-br-posix
./script/bootstrap
```
You will need to also retrieve infrastructure network interface (e.g. Wi-Fi/Ethernet) to specified it in a script to start Thread Border Router:

Use this command to determine correct interface
```bash
ip addr
```

Execute script
```bash
INFRA_IF_NAME=<interface> ./script/setup
#Examples Below
#INFRA_IF_NAME=eth0 ./script/setup
#INFRA_IF_NAME=wlan0 ./script/setup
```

Note: If your Raspberry Pi is connected by an Ethernet cable, specify the Ethernet interface name (e.g. eth0)

You can verify the installation  by verifying otbr-agent status:

```bash
sudo service otbr-agent status
```
Note: otbr-agent service is not active, because it requires an RCP chip to run.

Connect nRF52840-dongle to your Raspberry Pi/NUC (the one flashed with ot-rcp.hex), restart otbr-agent service and recheck status to observe everything is now working fine:

```bash
sudo service otbr-agent restart
sudo service otbr-agent status
```

## **Set the rpi-box application as a service**

Copy the service file
```bash
sudo cp server_box/service/rpi-box.service /etc/systemd/system/
```

Register service
```bash
sudo systemctl daemon-reload
sudo systemctl enable rpi-box
sudo systemctl restart rpi-box
```

## **Disable Bluethoot and Wifi interfaces**
```bash
sudo nano /boot/config.txt
```

Find the section *[all]* and add the following lines
```bash
dtoverlay=disable-wifi
dtoverlay=disable-bt
```
