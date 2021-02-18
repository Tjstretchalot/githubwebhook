# Github Webhooks Integration

This is a very simple library for use with CI/CD pipelines. It sets up a
webserver. It has one endpoint - a POST to `/gh_webhook`. This will verify the
webhook signature using sha256. If it is valid, it executes a single shell
script.

## Environment Variables

- `GITHUB_WEBHOOKS_PORT`: (default: `80`) The port to listen on
- `GITHUB_WEBHOOKS_SECRET`: The secret to expect. Must be set.
- `GITHUB_WEBHOOKS_SCRIPT`: A fully qualified path to a script to execute when
  a verified event occurs.

## Complete Setup (EC2)

Assuming you have a public repository with `before_install.sh`,
`application_start.sh`, `application_stop.sh`, and `after_install.sh` in the
scripts folder within the repository, the following is a good basis for a
userdata script. Note you should read this and modify as appropriate:

Setup:

```sh
export GITHUB_WEBHOOKS_PORT=3000
export GITHUB_WEBHOOKS_SECRET=MYSECRET
export GITHUB_WEBHOOKS_REPO=https://github.com/MYNAME/MYREPO
```

Core:

```sh
sudo yum -y update
sudo yum -y install git wget
sudo yum -y install make glibc-devel gcc patch perl-core zlib-devel postgresql-devel
sudo yum -y install libffi libffi-devel
sudo yum -y remove python3

# Verify this is the latest openssl version at openssl.org
cd /usr/local/src
sudo wget https://www.openssl.org/source/openssl-1.1.1j.tar.gz
sudo tar -xf openssl-1.1.1j.tar.gz
cd openssl-1.1.1j
sudo ./config --prefix=/usr/local/ssl --openssldir=/usr/local/ssl shared zlib
sudo make
sudo make install
sudo bash -c 'echo "/usr/local/ssl/lib" > "/etc/ld.so.conf.d/openssl-1.1.1j.conf"'
sudo ldconfig -v
sudo cp -R /usr/local/ssl/bin /usr/

# Verify this is the most up-to-date python at python.org
cd /usr/local/src
sudo wget https://www.python.org/ftp/python/3.9.1/Python-3.9.1.tgz
sudo tar -xf Python-3.9.1.tgz
cd Python-3.9.1
sudo ./configure --prefix=/usr/local/python3.9 --enable-optimizations
sudo make
sudo make install
sudo ln -s /usr/local/python3.9/bin/python3.9 /usr/bin/python3
sudo python3 -m pip install --upgrade pip
sudo python3 -m pip install --upgrade uvicorn

cd /home/ec2-user
git clone --depth 1 $GITHUB_WEBHOOKS_REPO app
app/before_install.sh
app/application_start.sh
app/after_install.sh

export GITHUB_WEBHOOKS_SCRIPT=/home/ec2-user/app/gh_webhook.sh

echo "export GITHUB_WEBHOOKS_PORT=$GITHUB_WEBHOOKS_PORT" >> secrets.sh
echo "export GITHUB_WEBHOOKS_SECRET=$GITHUB_WEBHOOKS_SECRET" >> secrets.sh
echo "export GITHUB_WEBHOOKS_SCRIPT=$GITHUB_WEBHOOKS_SCRIPT" >> secrets.sh
chmod +x secrets.sh
sudo chown root secrets.sh
sudo chgrp root secrets.sh

echo "#!/usr/bin/env bash" >> gh_webhook.sh
echo "/home/ec2-user/app/before_install.sh" >> gh_webhook.sh
echo "/home/ec2-user/app/application_stop.sh" >> gh_webhook.sh
echo "rm -r /home/ec2-user/app"
echo "git clone --depth 1 $GITHUB_WEBHOOKS_REPO /home/ec2-user/app" >> gh_webhook.sh
echo "/home/ec2-user/app/application_start.sh" >> gh_webhook.sh
echo "/home/ec2-user/app/after_install.sh" >> gh_webhook.sh
chmod +x gh_webhook.sh

cd /usr/local/src
git clone --depth 1 https://github.com/tjstretchalot/githubwebhooks
cd githubwebhooks
./update.sh
echo "#!/usr/bin/env bash" >> mystart.sh
echo "source /home/ec2-user/secrets.sh" >> mystart.sh
echo "source start.sh" >> mystart.sh
chmod +x mystart.sh
screen -dmS githubwebhooks ./mystart.sh

sudo crontab -l > cron
echo "@daily sudo yum -y update" >> cron
echo "@reboot /usr/local/src/githubwebhooks/update.sh && screen -dmS githubwebhooks /usr/local/src/githubwebhooks/mystart.sh" >> cron
sudo crontab cron
rm cron
```

## Alternatives

This is a very simple alternative to common CI applications like CodePipeline,
TeamCity, etc, when only the most bare functionality is necessary.
