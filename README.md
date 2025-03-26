# Python Playwright with MetaMask and GUI using in Docker container

This project sets up Python Playwright with MetaMask using a GUI application in Docker container. The goal is to make it easy to start and run the application in a containerized environment, add GUI usage in Docker container, and make it possible to run the application on all platforms.

The test application in this repository, loads the MetaMask extension, creates a new wallet, displays the seed phrase of this wallet in the terminal and adds a test network (Polygon zkEVM Cardona Testnet) to the wallet.

## Files structure
- **Dockerfile**: The Dockerfile used to build the image for this application.
- **docker-compose.yml**: The Docker Compose file that defines the services and how they interact in the container.
- **start.sh**: A shell script to simplify the process of running the application and container environment.
- **README.md**: This file that explains how to set up and run the project.
- **/ubuntu-vnc**: Docker image with Ubuntu 24 and VNC. Default VNC port is 5900, you can change this port in Dockerfile.

## Usage

**Step 1:** Setting up your application

- Environments
- Application settings
- Other things

**Step 2:** Setting up `start.sh` and Docker Compose.

You need to specify the name of the file to start, and the path to it (if it is not in the Dockerfile folder) in the `start.sh` file.
```bash
poetry run python ./src/main.py
```
Compose file contains path's to files, what you need to mount in your Docker container. Use `Volumes` in Compose file for this. Edit path's or change files.

**Step 3:** Run the Application Using Docker Compose.

```bash
docker compose up
```
If you don't have an image with name "_playwright-img_", it will be built automatically. Image size was around ~2 gigabytes. It depends on the size of your application.

**Important note!** If you update application files, Dockerfile or `start.sh`, you need to rebuild Docker application image (_does not apply to those directories and files that are mounted into an already prepared image using Docker Compose_).
```bash
docker compose up --build
```

## Troubleshooting

If you encounter issues, try:
- Ensure that Docker and Docker Compose are running properly.
- Check your application logs.
- Check Docker Compose logs.
```bash
docker compose logs -f
```
- Try to use Chromium channel instead of Chrome (**don't forget to change the Dockerfile** for install chromium, and channel of the browser in your application).
```Dockerfile
RUN python3 -m pip install --no-cache-dir poetry playwright && \
    playwright install chromium --with-deps
```
- Try HEADLESS=True.
- Try to rebuild image (or fully).
```bash
docker compose up --build
```
- Try to run your application in VNC container.

If application doesn't start, ensure that Docker and Docker Compose are running properly.

## Container details

### Dockerfile
Creating Docker image with Python 3.12 using the most lightweight image on, with 2 stages. In the 1st stage the virtual environment, and application dependencies are created. The 2nd stage installs the dependencies for headed mode, copies the virtual environment that was created in the first stage and installs the browser for your application.

### docker-compose.yml
Docker Compose makes it easier to launch an application. Compose creates the service and mounts the partitions needed to run the application. 

| Volume              | Description                                                      |
|---------------------|------------------------------------------------------------------|
| `/extension`        | The directory where MetaMask extension is stored.                |                               |
| `/.env`             | File in which the application operation parameters are recorded. |

### start.sh
This is a script that starts Xvfb, configures it and then runs the `main.py` file. When the application is finished, the Xvfb service will be killed.