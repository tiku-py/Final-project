from abc import ABC, abstractmethod


class Person(ABC):
    def __init__(self, name, age, weight, height):
        self.name = name
        self.age = age
        self.weight = weight
        self.height = height

    @abstractmethod
    def calculate_bmi(self):
        pass

    @abstractmethod
    def get_BMI(self, bmi):
        pass

    @abstractmethod
    def print_info(self):
        pass


class Adult(Person):
    def calculate_bmi(self):
        return self.weight / ((self.height / 100) ** 2)

    def get_bmi_category(self, bmi):
        if bmi < 18.5:
            return "Underweight"
        elif 18.5 <= bmi < 24.9:
            return "Normal weight"
        elif 25 <= bmi < 29.9:
            return "Overweight"
        else:
            return "Obese"

    def print_info(self):
        bmi = self.calculate_bmi()
        category = self.get_bmi_category(bmi)
        print(f"Name: {self.name}, Age: {self.age}, BMI: {bmi:.2f}, Category: {category}")


class Kid(Person):
    def calculate_bmi(self):
        return self.weight / ((self.height / 100) ** 2)

    def get_bmi_category(self, bmi):
        if bmi < 14:
            return "Underweight"
        elif 14 <= bmi < 18:
            return "Normal weight"
        elif 18 <= bmi < 20:
            return "Overweight"
        else:
            return "Obese"

    def print_info(self):
        bmi = self.calculate_bmi()
        category = self.get_bmi_category(bmi)
        print(f"Name: {self.name}, Age: {self.age}, BMI: {bmi:.2f}, Category: {category}")



def main():
    name = input("Enter the name: ")
    age = int(input("Enter the age: "))
    weight = float(input("Enter the weight (kg): "))
    height = float(input("Enter the height (cm): "))

    if age >= 18:
        person = Adult(name, age, weight, height)
    else:
        person = Kid(name, age, weight, height)

    person.print_info()



main()
