class BranException(BaseException):
    def __init__(self, message="Default error message"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.__name__}: {self.message}'


class BranFileException(BranException):
    def __init__(self, message="Error loading file", file=None):
        self.message = message
        self.file = file
        super().__init__(self.message)

    def __str__(self):
        return f'{self.__name__}({self.file}): {self.message}'


class BranSerializerException(BranException):
    def __init__(self, message="Error loading file", obj=None):
        self.message = message
        self.obj = obj
        super().__init__(self.message)

    def __str__(self):
        return f'{self.__name__}({str(self.obj)}): {self.message}'
