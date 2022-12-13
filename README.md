# RPI-Box

# Use case : Camera Wi-Fi bands selective activation

This use case aims to show how a connected object can use the Thread tecnology to request the selective temporary activation of Livebox Wi-Fi bands

## **Topology**
![Topology](images/general_topology.png)

## [**rpi_box**]
Runs the intelligence of the orchestrator, this RPI commands the Wi-Fi bands of the livebox via telnet and acts as a border router for the Thread network. This code could be integrated into the livebox in future versions.
The orchestrator notifies periodically the current use situation and the Wi-Fi status to the cloud server.

## [**rpi_relays**](https://github.com/Nicolas44Hernandez/GreenHomeLan_RpiPanel)
Connected electrical panel, this panel is controlled by the orchestrator to manage the energy resources of the house.
Currently, for demo purposes, three of its relays are used as a visual notification of the status of the Wi-Fi bands as follows:
- 2.4 GHz : red
- 5 GHz: yellow
- 6 GHz: white

## [**rpi_cloud**](https://github.com/Nicolas44Hernandez/GreenHomeLan_RpiCloud)
Run a web server where connected users receive notifications and have access to the live video stream from the rpi_camera
This module is not part of the local network, it simulates a cloud web service.

## **rpi_camera**(https://github.com/Nicolas44Hernandez/GreenHomeLan_RpiCamera)
Connected object composed a doorbell, a camera and a presence sensor. This smart doorbell sends a notification and the live video stream to the cloud server (rpi_cloud) if someone rings the bell or the presence sensor detects something unusual.


## **Demostration scenario**
1. The next morning, Pauline leaves her house: no one is home anymore
The orchestrator triggers the use situation "absence low consumption"=> **Wi-Fi = OFF**

2. Someone rings the doorbell / Someone is detectected by the sensor: the rpi_camera asks for the Wi-Fi reactivation to send a notification and the video to Paulines terminal.
To achieve this, the rpi_camera sends a Thread message to the rpi_box requesting to turn on the 2.4GHz Wi-Fi band.

3. The rpi_box sends a telnet command to the box to activate the 2.4GHz Wi-Fi band. The livebox activates the 2.4GHz Wi-Fi band

4. The orchestrator (rpi_box) detects the Wi-Fi band activation and requests to turn on the associated lamp to the connected electrical panel (rpi_relays).

5. The rpi_camera connects to the Wi-Fi network and notifies the cloud server that someone has rang at the door.

6. Pauline can see on her terminal the live video stream of her house and she can know who is at the door.

7. At the end of the video transmission, the rpi_camera asks the rpi_box via a Thread message to turn off the Wi-Fi.

8. The rpi_box sends a telnet command to the box to desactivate the 2.4GHz Wi-Fi band. The livebox desactivates the 2.4GHz Wi-Fi band

9. The orchestrator (rpi_box) detects the Wi-Fi band desactivation and requests to turn off the associated lamp to the connected electrical panel (rpi_relays).

10. Pauline is back home.
The orchestrator triggers the use situation "presence low consumption"=> **Wi-Fi = ON**


## rpi_box installation and setup
You can found the installation and setup in the iner [README.md](server_box/README.md) file
