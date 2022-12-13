#!/bin/bash

DHCP_CONFIG_FILE="/etc/dhcpcd.conf"
ROUTED_AP_CONFIG_FILE="/etc/sysctl.d/routed-ap.conf"
DNSMASQ_CONFIG_FILE="/etc/dnsmasq.conf"
HOSTAPD_CONFIG_FILE="/etc/hostapd/hostapd.conf"
DEFAULT_HOSTAPD_CONFIG_FILE="/etc/default/hostapd.conf"
RESOURCES=../resources


source ../variables/wlan-addr.env
echo "SETUP FOR RPI SERVER BOX"

echo "********STAGE 1: UPDATE AND UPGRADE SYSTEM ********"
# Update packages
sudo apt -y update
sudo apt -y upgrade


echo "********STAGE 2: INSTALL PACKAGES ********"
# Install the necessary packages necessary 
# to configure the PI as a Wifi access point 
sudo apt -y install python3-pip dnsmasq iptables
sudo apt -y install hostapd			
sudo systemctl unmask hostapd					
sudo systemctl enable hostapd					
sudo DEBIAN_FRONTEND=noninteractive apt install -y netfilter-persistent iptables-persistent	


echo "********STAGE 3: SET WLAN0 STATIC IP********"
sudo cp $DHCP_CONFIG_FILE $DHCP_CONFIG_FILE.orig
echo "Old file backup in: $DHCP_CONFIG_FILE.orig"
sudo mv $RESOURCES/dhcpcd.conf $DHCP_CONFIG_FILE
echo "    static ip_address=$RPI_SERVER_BOX_IP/24" >> $DHCP_CONFIG_FILE
echo "RPI server box IP: $RPI_SERVER_BOX_IP/24"


echo "********STAGE 4: SETUP TRAFIC FORDWARD TO ETH0********"
sudo cat <<EOF > $ROUTED_AP_CONFIG_FILE
net.ipv4.ip_forward=1
EOF
echo "File created : $ROUTED_AP_CONFIG_FILE"


echo "********STAGE 5: CONFIGURE HTTP TRAFFIC REDIRECTION TO RPI BOX********"
sudo iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 4000 -m conntrack --ctstate NEW -j DNAT --to $RPI_CAMERA_IP:$RPI_CAMERA_PORT
sudo iptables -t nat -A PREROUTING -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
sudo netfilter-persistent save


echo "********STAGE 6: CONFIGURE DHCP AND DNS SERVICES********"
sudo cp $DNSMASQ_CONFIG_FILE $DNSMASQ_CONFIG_FILE.orig
echo "Old file backup in: $DNSMASQ_CONFIG_FILE.orig"
sudo mv $RESOURCES/dnsmasq.conf $DNSMASQ_CONFIG_FILE
echo "$RPI_SERVER_BOX_IP" >> $DNSMASQ_CONFIG_FILE


echo "********STAGE 7: CONFIGURE NETWORK********"
sudo mv $RESOURCES/hostapd.conf $HOSTAPD_CONFIG_FILE
echo "File created : $HOSTAPD_CONFIG_FILE"
sudo cat <<EOF > $DEFAULT_HOSTAPD_CONFIG_FILE
DAEMON_CONF=$HOSTAPD_CONFIG_FILE
EOF
echo "DAEMON_CONF=$HOSTAPD_CONFIG_FILE"


echo "********STAGE 8: REBOOT********"
sudo reboot