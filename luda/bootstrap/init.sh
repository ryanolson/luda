#!/bin/bash

# Add local user
# Either use the HOST_USER_ID if passed in at runtime or
# fallback

USER_ID=${HOST_USER_ID:-9001}
USER_NAME=${HOST_USER:-user}

echo "Starting with UID : $USER_ID"
useradd --shell /bin/bash -u $USER_ID -o -c "" --create-home -G sudo $USER_NAME > /dev/null 2>&1
export HOME=/home/$USER_NAME

if [ -n "$DEVTOOLS" ]; then
  apt update
  apt install -y --no-install-recommends sudo vim
  echo "$USER_NAME ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
fi

if [ ${#@} -eq 0 ]; then
    exec /bootstrap/su-exec $USER_NAME /bin/bash
else
    exec /bootstrap/su-exec $USER_NAME "$@"
fi
