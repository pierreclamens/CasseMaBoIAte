FROM debian:bookworm-slim
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 curl nmap openssh-client sshpass ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /root
