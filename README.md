# ERGO
## Simple Microservice Development Framework

Ergo is the substrate for the rapid development of cooperative microservices.

The primary emphasis with Ergo is to eliminate - as much as possible - the boilerplate infrastructure that is common to most software stacks to facilitate a larger developer emphasis on business-oriented development.  This is achieved with inversion of control and procedural injection.

For example; Consider the following python function in the file `math.py`:

```
# math.py

def product(x, y):
    return x * y
```

Ergo provides the tooling to execute this simple function using any one of a number of different patterns (eg. console application, http service, MQ worker, etc.)

To start an http service for the above function:

```
$ ergo http math.py:product
```

then to make a request against this service

```
$ curl -i "http://localhost?4&5"
[20]
```
