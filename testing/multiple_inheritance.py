class Class1:
    def __init__(self):
        print("Class1 init")


class Class2:
    def __init__(self):
        print("Class2 init")


class Class3(Class2, Class1):
    def __init__(self):
        super().__init__()


c = Class3()
