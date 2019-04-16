# Autonomous Vehicle Routing in Congested Networks
Oregon State University Senior Capstone - 2019

With the increasing popularity and interest in autonomous vehicle development, the question of the impact of their implementation onto modern transportation networks arises. Safety and efficiency remain two important topics that surround the discussion of autonomous vehicles, and more research is needed before the autonomous vehicles are introduced onto the roadways completely.

This project aids in the process of autonomous vehicle research, providing an interface in which the user may view a given transportation network and the car models active within it. On the network will be active autonomous models, with a connective capability to one another, as well as models representing human driven vehicles. Through this simulation of both models, the user will be able to monitor how the autonomous vehicles are interacting with one another as well as with the human driven vehicles.

## Members
* Eytan Brodsky
* Liang Du
* Samantha Estrada
* Shengjun Gu
* Charles Koll

## Requirements
* Provide an accurate simulation of traffic
* User interface (GUI) should provide details such as the number, position, and other parameters of each variable
in the environment.
* GUI should be easily manipulated by the user, granting them the ability to simulate different conditions and pause the simulation at any time.
* Simulation should be displayed to the user at a minimum of 10 frames per second.
* All vehicles will individually route to their destination, and will have different destinations.

## Deliverables
* A GUI interface presenting the run simulation, with the ability to be interactive with the user.
* Data for the autonomous vehicles' behaviors, represented by graphs and tables.

## Dependencies
* UNIX
* Bash
* Python (version >= 3.6, with module venv)

(Note: In this document, the assumed command in Bash is `python3`. If different on your machine, replace with the corresponding command.)

## Instructions to run AV Routing Project
* `make python=python3`
(Be sure to replace `python3` with the corresponding command)

In the browser:

* Select _data.json_ under the _src_ directory for the infrastructure file.
* Select _vehicle\_layout.json_ under the _src_ directory for the vehicles file.
* Click the _Build_ button.
