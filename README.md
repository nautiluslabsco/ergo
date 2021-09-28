# ERGO
## Simple Microservice Development Framework

Ergo is the substrate for the rapid development of coordinated microservices.

The primary emphasis with Ergo is to eliminate - as much as possible - the boilerplate infrastructure that is common to most software stacks to facilitate a larger developer emphasis on business-oriented development.  This is achieved with inversion of control and procedural injection.

For example; Consider the following python function in a file `math.py`:

```
# math.py

def product(x, y):
    return float(x) * float(y)
```

Ergo provides the tooling to bootstrap this simple function into any one of a variety of environments (eg. console application, http service, MQ worker, etc.)

To start an http service for the above function:

```
$ ergo http math.py:product
```

then to make a request against this service

```
$ curl -i "http://localhost?x=4&y=5"
20.0
```
