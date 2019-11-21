# Change Interface VLAN by MAC Address
A python script to identify the access switch port that a user's computer is
 plugged into and change the VLAN on the switch interface. This script is a
  rough draft primarily intended show a basic proof of concept and is not
   intended
   to be used in production environments in its current state.
  
### Summary
This script was designed with the assumption that access switches in a campus
 network are linked together via PortChannels. With this in mind, the script
  loops through access switches to see if there is a matching entry in their
   MAC address table for the desired MAC address, specifically if the
    matching interface is a GigabitEthernet interface in this scenario. An
     alternate approach could be to start at the distribution level and
      "drill down" to which access switch is connected to the device, but
       that would arguably entail more complicated logic which can be avoided
        once certain assumptions can be made about the network design (as
         just previously mentioned).
         
Code comments provide more granular information about the script.
