"""
In all of these options, the ergo runtime is fully responsible for managing transaction state. It knows to do this
either by reading a config flag or by inferring from the function params/body.

option 1
"""


def order_sandwich(inbox: ErgoInbox, context, toppings):  # noqa
    for topping, variety in toppings.items():
        yield {topping: variety}
    for message in inbox:
        sandwich = message.get("sandwich")
        if validate_sandwich(sandwich):
            yield context.respond(sandwich)
            yield StopIteration


"""
option 2
"""


def order_sandwich(context, toppings):  # noqa
    for topping, variety in toppings.items():
        yield {topping: variety}
    while True:
        message = yield
        sandwich = message.get("sandwich")
        if validate_sandwich(sandwich):
            yield context.respond(sandwich)


"""
pros: 
    ergo is no longer an application dependency
cons:
    unclear how to generalize this approach for other languages
    managing concurrent inbound and outbound data with yield can be complex and error prone
"""

"""
option 3
"""


def order_sandwich(context, toppings, sandwich=None, **kwargs):  # noqa
    if validate_sandwich(sandwich):
        yield context.respond(sandwich)
    else:
        for topping, variety in toppings.items():
            yield {topping: variety}


"""
If order_sandwich is an ordinary amqp component, how does it finally send the sandwich back to an HTTP gateway?

option 4

gateway.yml:
    ...
    protocol: http
    rpc_target:
        - sandwich  # implements www.{hostname}.com/sandwich

gateway_alt.yml
    rpc_target:
        - sandwich.rpc_in:sandwich.rpc_out

order_sandwich.yml:
    ...
    protocol: amqp
    subtopic: sandwich.rpc_in

assemble_sandwich.yml
    ...
    protocol: amqp
    pubtopic: sandwich.rpc_out


Pros:
AMQP components are "pure", don't require ergo interaction.
RPCInvocable is simpler to implement than ergo transactions.
Efficiency: the synchronous component doesn't have to sift through every intermediate message in the transaction. It can 
    simply return the first message that shows up in its callback queue.

Cons:
Ergo transactions/convergence are still necessary for something besides synchronous responses?

"""


def validate_sandwich(sandwich): pass
