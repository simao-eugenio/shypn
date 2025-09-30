# Example API class
class ExampleAPI:
    def __init__(self, name: str):
        self.name = name

    def greet(self):
        return f"Hello from {self.name}!"
