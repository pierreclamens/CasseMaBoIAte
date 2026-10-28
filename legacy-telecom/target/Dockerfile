FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 openssh-server sudo findutils tini ca-certificates nginx-light \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash support \
    && passwd -l root \
    && rm -f /etc/ssh/ssh_host_* \
    && mkdir -p /run/sshd /var/lib/legacy-app /var/lib/legacy-state /srv/archive

COPY sshd_config /etc/ssh/sshd_config
COPY nginx.conf /etc/nginx/nginx.conf
COPY sudoers-support /etc/sudoers.d/support
COPY app /opt/legacy
COPY entrypoint.py healthcheck.py admin.py /opt/legacy/
RUN chmod 0440 /etc/sudoers.d/support \
    && visudo -cf /etc/sudoers.d/support \
    && chmod -R go-w /opt/legacy \
    && printf 'Archives clients : maintenance assurée par le compte support.\n' > /srv/archive/README.txt \
    && printf '\nLegacy Telecom — serveur de maintenance interne\n\n' > /etc/motd

EXPOSE 80 22
ENTRYPOINT ["/usr/bin/tini", "--", "python3", "/opt/legacy/entrypoint.py"]
