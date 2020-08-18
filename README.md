# bbqspy

## Overview
This tool allows users to receive and record temperature data from the Inkbird Smart BBQ Thermometer.  This tool has only been tested against the Inkbird model IBT-4XS using a RaspberryPi 3b.  I built this because I felt the device's companion mobile app had insufficient support for recording data over the course of a cooking session.

## Process Overview
The first step in learning how to communicate with a particular bluetooth device is discovering it's adapter address.  There are a number of ways to do this; I used the nRF Connect app on Android to gather some basic information about the thermometer.  

