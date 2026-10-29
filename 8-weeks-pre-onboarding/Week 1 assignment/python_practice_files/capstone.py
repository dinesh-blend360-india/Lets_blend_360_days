def fabinacci(n):
    if n<=1:
        return n
    return fabinacci(n-1)+fabinacci(n-2)

def fabinacci_iteration(n):
    if n<=1:
        return n
    a = 0
    b = 1
    for i in range(n):
        print(a, end=" ")
        a,b=b,a+b
    return a



def factorial(n):
    if n<=1:
        return n
    return n*factorial(n-1)

def factorial_iteration(n):
    if(n<=1):
        return n
    res = 1
    for i in range(1,n+1):
        res *= i
    return res



# 1. Find PI to the Nth Digit

import math

n = int(input("Enter number of decimal places: "))

if n < 0:
    print("Invalid number")
elif n > 15:
    print("Limit exceeded. Maximum allowed is 15 decimal places.")
else:
    print(f"Pi = {math.pi:.{n}f}")


# 2. Find e to the Nth Digit

import math

n = int(input("Enter number of decimal places: "))

if n < 0:
    print("Invalid number")
elif n > 15:
    print("Limit exceeded. Maximum allowed is 15 decimal places.")
else:
    print(f"e = {math.e:.{n}f}")


# 4. Prime Factorization

n = int(input("Enter a number: "))

if n <= 1:
    print("Prime factorization is not defined for this number.")
else:
    factors = []
    divisor = 2

    while divisor * divisor <= n:
        while n % divisor == 0:
            factors.append(divisor)
            n //= divisor

        divisor += 1

    if n > 1:
        factors.append(n)

    print("Prime Factors:", factors)


# 5. Next Prime Number

def is_prime(n):
    if n < 2:
        return False

    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False

    return True


n = int(input("Enter a starting number: "))

while True:
    n += 1

    while not is_prime(n):
        n += 1

    print("Next prime:", n)

    choice = input("Find another prime? (y/n): ").lower()

    if choice != "y":
        break


# 7. Mortgage Calculator

principal = float(input("Enter loan amount: "))
annual_rate = float(input("Enter annual interest rate (%): "))
years = int(input("Enter loan term (years): "))

monthly_rate = annual_rate / 100 / 12
number_of_payments = years * 12

if monthly_rate == 0:
    monthly_payment = principal / number_of_payments
else:
    monthly_payment = (
        principal
        * monthly_rate
        * (1 + monthly_rate) ** number_of_payments
        / ((1 + monthly_rate) ** number_of_payments - 1)
    )

total_payment = monthly_payment * number_of_payments
total_interest = total_payment - principal

print(f"Monthly Payment: {monthly_payment:.2f}")
print(f"Total Payment: {total_payment:.2f}")
print(f"Total Interest: {total_interest:.2f}")


# 9. Binary to Decimal and Decimal to Binary

choice = input(
    "Choose conversion:\n"
    "1. Binary to Decimal\n"
    "2. Decimal to Binary\n"
    "Enter choice: "
)

if choice == "1":

    binary = input("Enter binary number: ")

    if all(bit in "01" for bit in binary):
        decimal = int(binary, 2)
        print("Decimal:", decimal)
    else:
        print("Invalid binary number.")

elif choice == "2":

    decimal = int(input("Enter decimal number: "))

    if decimal >= 0:
        binary = bin(decimal)[2:]
        print("Binary:", binary)
    else:
        print("Please enter a non-negative number.")

else:
    print("Invalid choice.")


# 13. Distance Between Two Cities

lat1 = float(input("Enter latitude of city 1: "))
lon1 = float(input("Enter longitude of city 1: "))

lat2 = float(input("Enter latitude of city 2: "))
lon2 = float(input("Enter longitude of city 2: "))

unit = input("Enter unit (km/miles): ").lower()

lat1 = math.radians(lat1)
lon1 = math.radians(lon1)

lat2 = math.radians(lat2)
lon2 = math.radians(lon2)

dlat = lat2 - lat1
dlon = lon2 - lon1

a = (
    math.sin(dlat / 2) ** 2
    + math.cos(lat1)
    * math.cos(lat2)
    * math.sin(dlon / 2) ** 2
)

c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

earth_radius_km = 6371

distance_km = earth_radius_km * c

if unit == "km":
    print(f"Distance: {distance_km:.2f} km")

elif unit == "miles":
    distance_miles = distance_km * 0.621371
    print(f"Distance: {distance_miles:.2f} miles")

else:
    print("Invalid unit.")


# 15. Tax Calculator

cost = float(input("Enter cost: "))
tax_rate = float(input("Enter tax rate (%): "))

tax = cost * tax_rate / 100
total = cost + tax

print(f"Original Cost: {cost:.2f}")
print(f"Tax: {tax:.2f}")
print(f"Total Cost: {total:.2f}")


# 20. Coin Flip Simulation

import random

n = int(input("How many times do you want to flip the coin? "))

heads = 0
tails = 0

for _ in range(n):

    result = random.choice(["Heads", "Tails"])

    print(result)

    if result == "Heads":
        heads += 1
    else:
        tails += 1

# print("Results:")
# print("Heads:", heads)
# print("Tails:", tails)
# print("Total flips:", n)


# 21. str rev

def reverse_string(s):
    s = list(s)
    left = 0
    right = len(s)-1

    while left < right:
        s[left], s[right] = s[right], s[left]
        left += 1
        right -= 1

    return "".join(s)

#22 . count owls

def count_owls_consonents(txt):
    txt = txt.lower()
    owl = consonent = 0

    for i in txt:
        if i in "aeiou":
            owl += 1

        if i in "bcdfghjklmnpqrstvwxyz":
            consonent += 1

    return owl, consonent