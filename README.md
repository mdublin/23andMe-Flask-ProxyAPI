![](https://app.codeship.com/projects/2c3c7240-e1c9-0134-28ff-6eeea55d1ffc/status?branch=master)

Continuous integration via Codeship.

**Testing**:

Some simple tests are included in ```test_basics.py```, simply run the file with:
```$ python test_basics.py```

(make sure to kill the dev server first before running test module)

**Project Setup**:

cd inside the main directory and setup an a virtual environment directory with vritualenv via:

```$ virtualenv ENV```

Next, activate the virtual environment:

```$ source ENV/bin/activate```

then install the dependencies:

```$ pip install -r requirements.txt```


To run the Flask server:

```$ python main.py```

**Deployment to EC2**:

For the live production example, this entire directory is deployed on a free, vanilla AWS EC2 Ubuntu instance. However, instead of using the Flask server (which is ever only to be used during development), out Flask app is hosted using Gunicorn and Nginx, as an application and web server, respectively. In addition, you can also try using a client/server system monitoring and fault tolerance enabler, like [Supervisor](http://supervisord.org/introduction.html).

Fine tuning this deployment can be tricky sometimes, but the key thing is to first make sure your EC2 instance has Python2.7 or Python3 installed on it (which isn't always the case with EC2 instances). Assuming you have AWS CLI installed properly, SSH into your instance and try the following:

```sudo apt-get install build-essential checkinstall
sudo apt-get install libreadline-gplv2-dev libncursesw5-dev libssl-dev libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev```

Then download using the following command:

```cd ~/Downloads/
wget https://www.python.org/ftp/python/2.7.12/Python-2.7.12.tgz```

Extract and go to the directory:

```tar -xvf Python-2.7.12.tgz
cd Python-2.7.12```

Now, install using the command you just tried:
```
./configure
make
sudo checkinstall
```

For Gunicorn and Nginx configuration, [here's a great blog post to get you started](http://alexandersimoes.com/hints/2015/10/28/deploying-flask-with-nginx-gunicorn-supervisor-virtualenv-on-ubuntu.html).


You don't have to necessarily use something like Supervisor when initially getting things running, you can, after configuring Nginx, just cd into your project directory (make sure you've activated your virtualenv environment), and run Gunicorn with the following:

```$ gunicorn main:app —-timeout 120 —-w 4```

In both the above Gunicorn run command and in our Ngnix configuration file I have extended the timeout settings to allow for 23andMe's sometime-sluggish API responses.
