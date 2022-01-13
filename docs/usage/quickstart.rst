
Quickstart
==========

Install Ergo.

.. code-block:: zsh
   
   pipenv install ergo --pre

Write your business logic. ``example.py``:

.. code-block:: python

   def product(x, y):
       return float(x) * float(y)

Then, use ergo to turn your business logic into a running service!

.. code-block:: zsh

   pipenv run ergo http example.py:product 


Finally, test your service.

.. code-block:: zsh

   curl -i "http://localhost?x=4y=5"
