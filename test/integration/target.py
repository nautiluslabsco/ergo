def product(x, y):
    return float(x) * float(y)

class Product:
	def __call__(self, x, y) -> float:
		return product(x, y)
