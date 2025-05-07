# bed-occupancy
An app that optimizes hospital resource management by simulating patient admissions, bed allocations, and managing no-shows effectively. Ideal for predictive occupancy planning and streamlined departmental coordination

## Table of contents
* [Technologies](#technologies)
* [Setup](#setup)
* [Screenshots](#screenshots)
* [Status](#status)
* [Our team](#our-team)

## Technologies

- [Python](https://www.python.org/downloads/) _version: 3.13_, and its libraries:
  - [streamlit](https://docs.streamlit.io/) _version: 1.41.1_
  - [pydantic](https://docs.pydantic.dev/latest/) _version: 2.11.4_
  - [pandas](https://pandas.pydata.org/) _version: 2.2.3_
  - [fastapi](https://fastapi.tiangolo.com/) _version: 0.115.12_
  - and many other less important modules listed [here](./requirements.txt)
- [Docker](https://docs.docker.com/) _version: 27.4_

## Setup

In order to run this app, docker is required.

If you don't have docker installed on your computer yet, you can install it [here](https://docs.docker.com/get-started/get-docker/)

Once you have docker installed, follow these guidelines:
1. Clone the repo on your local machine
   1. You can do it by running this command in terminal:
        ```
        git clone https://github.com/datarabbit-ai/bed-occupancy
        ```
2. Prepare the `.env` file, it should be placed in the project's root folder

    It should contain variables like this:
    ```

    ```

3. Make sure you are in the project's root folder and run the command:
   1.
    ```
    docker compose up
    ```
    There are two versions of this command: `docker-compose up` and `docker compose up`. On Windows you can run both and it will work fine, however on Linux, it is recommended to pick the second version (without the dash). The command `docker compose up` forces docker to use `docker_compose_v2` which is just better, more stable and more reliable.
   2. By running the above command, docker should:
     - launch faker, which will allow you to create a database and/or fill it with data
     - will launch the backend and frontend of the application, allowing the browser to open the application, view data from the database and simulate the other day's hospital occupancy rates
   3. The whole process could take **even a few minutes**, especially when running for the first time
4. If you see in docker logs that frontend container is starting to run, you can [visit the webapp in browser](http://localhost:8501)

## Screenshots

Correctly set up and working app looks like this:


## Status

The project is: _in development_

## Our team
People and their roles:

[Rumeleq](https://github.com/Rumeleq) -

[wiktorKycia](https://github.com/wiktorKycia) -

[JanTopolewski](https://github.com/JanTopolewski) -
