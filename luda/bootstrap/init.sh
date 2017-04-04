#!/bin/bash

# Add local user
# Either use the HOST_USER_ID if passed in at runtime or
# fallback

USER_ID=${HOST_USER_ID:-9001}
USER_NAME=${HOST_USER:-user}

GRP_ID=${HOST_GROUP_ID:-1001}
GRP_NAME=${HOST_GROUP:-nvidia}

echo "Starting with UID : $USER_ID"
echo "Starting with GID : $GRP_ID"
addgroup --gid ${GRP_ID} ${GRP_NAME}
useradd --shell /bin/bash -u $USER_ID --gid $GRP_ID -o -c "" --create-home \
  -G sudo,$GRP_NAME $USER_NAME > /dev/null 2>&1
export HOME=/home/$USER_NAME

if [ -n "$DEVTOOLS" ]; then
  apt update
  apt install -y --no-install-recommends sudo
fi
echo "$USER_NAME ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

if [ ${#@} -eq 0 ]; then
    exec /bootstrap/su-exec $USER_NAME /bin/bash
else
    exec /bootstrap/su-exec $USER_NAME "$@"
fi

