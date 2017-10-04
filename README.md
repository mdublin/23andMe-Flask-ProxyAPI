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

Regarding the Nginx configuration, here's what seems to work well, allowing for both https:

```
server {
   #listen 80;
   #server_name 54.186.189.234;

    # this line is for allowing https only
    listen 443 ssl;
    server_name ec2-54-186-189-234.us-west-2.compute.amazonaws.com;
    ssl_certificate /etc/nginx/ssl/nginx.crt;
    ssl_certificate_key /etc/nginx/ssl/nginx.key;


    root /home/ubuntu/23andmeproxyapi;

    access_log /home/ubuntu/23andmeproxyapi/logs/nginx/access.log;
    error_log /home/ubuntu/23andmeproxyapi/logs/nginx/access.log;

    location / {



if ($request_method = 'OPTIONS') {
        add_header 'Access-Control-Allow-Origin' '*';
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
        #
        # Custom headers and headers various browsers *should* be OK with but aren't
        #
        add_header 'Access-Control-Allow-Headers' 'DNT,X-CustomHeader,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Content-Range,Range';
        #
        # Tell client that this pre-flight info is valid for 20 days
        #
        add_header 'Access-Control-Max-Age' 1728000;
        add_header 'Content-Type' 'text/plain charset=UTF-8';
        add_header 'Content-Length' 0;
        return 204;
     }
     if ($request_method = 'POST') {
        add_header 'Access-Control-Allow-Origin' '*';
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
        add_header 'Access-Control-Allow-Headers' 'DNT,X-CustomHeader,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Content-Range,Range';
        add_header 'Access-Control-Expose-Headers' 'DNT,X-CustomHeader,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Content-Range,Range';
     }
     if ($request_method = 'GET') {
        add_header 'Access-Control-Allow-Origin' '*';
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
        add_header 'Access-Control-Allow-Headers' 'DNT,X-CustomHeader,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Content-Range,Range';
        add_header 'Access-Control-Expose-Headers' 'DNT,X-CustomHeader,Keep-Alive,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Content-Range,Range';
     }



        proxy_set_header 'Access-Control-Allow-Origin' '*';
        proxy_set_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';

###END OF NEW###

        #proxy_ignore_headers Set-Cookie;
        #proxy_hide_header Set-Cookie;


        proxy_connect_timeout 90s;
        proxy_read_timeout 300s;

        proxy_set_header X-Forward-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $http_host;
        proxy_redirect off;
        if (!-f $request_filename) {
            proxy_pass http://127.0.0.1:8000;
            break;
        }
    }

    location /static {
        alias  /home/ubuntu/23andmeproxyapi/static/;
        autoindex on;
    }
}
```

You don't have to necessarily use something like Supervisor when initially getting things running, you can, after configuring Nginx, just cd into your project directory (make sure you've activated your virtualenv environment), and run Gunicorn with the following:

```$ gunicorn main:app —-timeout 120 —-w 4```

In both the above Gunicorn run command and in our Ngnix configuration file I have extended the timeout settings to allow for 23andMe's sometime-sluggish API responses.
