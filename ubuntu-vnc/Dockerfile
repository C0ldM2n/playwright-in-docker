FROM ubuntu:24.04 as build

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y curl make gcc

RUN curl -s -L https://github.com/ncopa/su-exec/archive/v0.2.tar.gz | tar zx -C /opt/ \
    && mv /opt/su-exec* /opt/su-exec \
    && cd /opt/su-exec \
    && make

####################################

FROM ubuntu:24.04

# For slim:
#   --build-arg ADDITIONAL_APT_GET_OPTS=--no-install-recommends
ARG ADDITIONAL_APT_GET_OPTS=""

RUN echo 'path-include=/usr/share/locale/en/LC_MESSAGES/*.mo' > /etc/dpkg/dpkg.cfg.d/includes \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y $ADDITIONAL_APT_GET_OPTS \
      dbus-x11 \
      ibus \
      ibus-gtk \
      ibus-gtk3 \
      ibus-gtk4 \
      im-config \
      lxqt \
      net-tools \
      novnc \
      papirus-icon-theme \
      sddm \
      sudo \
      supervisor \
      tzdata \
      x11vnc \
      xvfb \
      locales \
      language-pack-en \
      python3 \
      python3-pip \
      wget \
      unzip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Download fonts-liberation manually
RUN wget http://ftp.us.debian.org/debian/pool/main/f/fonts-liberation/fonts-liberation_1.07.4-11_all.deb && \
    dpkg -i fonts-liberation_1.07.4-11_all.deb && \
    rm fonts-liberation_1.07.4-11_all.deb

# Install Playwright and dependencies
RUN pip install playwright poetry --break-system-packages
RUN playwright install chromium --with-deps
RUN playwright install chrome --with-deps

# Set locale
RUN cp /usr/share/zoneinfo/America/New_York /etc/localtime \
    && echo 'America/New_York' > /etc/timezone \
    && locale-gen en_US.UTF-8 \
    && echo 'LC_ALL=en_US.UTF-8' > /etc/default/locale \
    && echo 'LANG=en_US.UTF-8' >> /etc/default/locale
ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8

# Set default vars
ENV DEFAULT_USER=developer \
    DEFAULT_PASSWD=vncpasswd

# Set sudoers for any user
RUN echo "ALL ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers.d/ALL

# Change permission so that non-root user can add users and groups
RUN chmod u+s /usr/sbin/useradd \
    && chmod u+s /usr/sbin/groupadd

# Expose VNC and noVNC ports
EXPOSE 5900
EXPOSE 80

# Setup
RUN install -o root -g root -m 0755 -d /var/run/dbus \
    && { \
        echo 'if [ -z "$XDG_RUNTIME_DIR" ] && [ -d "/run/user/$(id -u)" ]; then'; \
        echo '  export XDG_RUNTIME_DIR=/run/user/$(id -u)'; \
        echo 'fi'; \
    } > /etc/X11/Xsession.d/00xdg_runttime \
    && chmod 644 /etc/X11/Xsession.d/00xdg_runttime \
    && if [ -e /usr/share/lxqt/wallpapers/origami-light.png ]; then \
         update-alternatives --install \
           /usr/share/images/desktop-base/desktop-background desktop-background \
           /usr/share/lxqt/wallpapers/origami-light.png 99; \
       fi

# Disable unavailable features
RUN sed -i.org 's/plugins=.*/plugins=mainmenu, showdesktop, desktopswitch, quicklaunch, taskbar, tray, statusnotifier, worldclock/' /etc/xdg/lxqt/panel.conf \
    && mv /etc/xdg/autostart/lxqt-powermanagement.desktop /etc/xdg/autostart/lxqt-powermanagement.desktop.disabled

# Set supervisord conf
RUN { \
      echo '[supervisord]'; \
      echo 'user=root'; \
      echo 'nodaemon=true'; \
      echo 'logfile=/var/log/supervisor/supervisord.log'; \
      echo 'childlogdir=/var/log/supervisor'; \
      echo '[program:dbus]'; \
      echo 'priority=10'; \
      echo 'command=/usr/bin/dbus-daemon --system --nofork --nopidfile'; \
      echo '[program:sddm]'; \
      echo 'priority=20'; \
      echo 'command=/usr/bin/sddm'; \
      echo '[program:x11vnc]'; \
      echo 'priority=30'; \
      echo 'command=/usr/local/bin/start-x11vnc.sh'; \
      echo '[program:novnc]'; \
      echo 'priority=40'; \
      echo 'user=${USER}'; \
      echo 'command=/usr/share/novnc/utils/novnc_proxy --vnc localhost:5900 --listen 80'; \
    } > /etc/supervisor/vnc.conf.template

# Set scripts and configuration for SDDM and Xvfb
RUN mkdir /etc/sddm.conf.d \
    && { \
        echo '[General]'; \
        echo 'DisplayServer=x11'; \
        echo '[X11]'; \
        echo 'ServerPath=/usr/local/bin/start-Xvfb.sh'; \
        echo 'ServerArguments=-screen 0 ${RESOLUTION}'; \
        echo '[Autologin]'; \
        echo 'User=${USER}'; \
        echo 'Session=lxqt'; \
    } > /etc/sddm.conf.d/xvfb_autologin.conf.tmplate \
    && { \
        # Xvfb wrapper script for SDDM.
        # Processes args from SDDM, removes unnecessary ones (-background, -seat, vt*), and executes Xvfb.
        echo '#!/bin/bash'; \
        echo 'args=()'; \
        echo 'while [ $# -gt 0 ]; do'; \
        echo '    case "$1" in'; \
        echo '        -background) shift 2 ;;'; \
        echo '        -seat) shift 2 ;;'; \
        echo '        vt*) shift ;;'; \
        echo '        *) args+=("$1"); shift ;;'; \
        echo '    esac'; \
        echo 'done'; \
        echo 'exec /usr/bin/Xvfb "${args[@]}"'; \
    } > /usr/local/bin/start-Xvfb.sh  \
    && chmod +x /usr/local/bin/start-Xvfb.sh \
    && { \
        # x11vnc auto start script for SDDM.
        # Continuously checks for X display and auth file, then starts x11vnc when both are available.
        echo '#!/bin/bash'; \
        echo 'while true; do'; \
        echo '    display_num=$(find /tmp/.X11-unix/ -type s 2>/dev/null | sed "s/.*X//")'; \
        echo '    auth=$(find /var/run/sddm/ -type f 2>/dev/null)'; \
        echo '    if [[ -n $display_num && -n $auth ]]; then'; \
        echo '        exec /usr/bin/x11vnc -display ":$display_num" -auth "$auth" -rfbauth /etc/x11vnc.passwd -rfbport 5900 -xkb -forever -shared -repeat -capslock'; \
        echo '    fi'; \
        echo '    sleep 0.1'; \
        echo 'done'; \
    } > /usr/local/bin/start-x11vnc.sh \
    && chmod +x /usr/local/bin/start-x11vnc.sh

WORKDIR /app

# Copying project dependecy files
COPY pyproject.toml poetry.lock /app/

# Installing project dependencies
ENV PATH="/root/.local/bin:$PATH"
RUN poetry config virtualenvs.create true
RUN poetry config virtualenvs.in-project true
RUN poetry install --no-interaction --no-ansi

# Copying src folder
COPY src /app/src

COPY --from=build \
    /opt/su-exec/su-exec /usr/sbin/su-exec

# Copy entrypoint script
COPY start.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/start.sh

ENTRYPOINT ["start.sh"]