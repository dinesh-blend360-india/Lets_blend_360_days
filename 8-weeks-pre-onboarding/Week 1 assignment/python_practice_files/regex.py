import re

# Searching for Basic Patterns
text = "The person's phone number is 408-555-1234. Call soon!"
print('phone' in text)

pattern = 'phone'
print(re.search(pattern, text))

pattern = "NOT IN TEXT"
print(re.search(pattern, text))

pattern = 'phone'
match = re.search(pattern, text)
print(match)
print(match.span())
print(match.start())
print(match.end())

text = "my phone is a new phone"
match = re.search("phone", text)
print(match.span())

matches = re.findall("phone", text)
print(matches)
print(len(matches))

for match in re.finditer("phone", text):
    print(match.span())

print(match.group())


# Identifiers for Characters in Patterns
text = "My telephone number is 408-555-1234"
phone = re.search(r'\d\d\d-\d\d\d-\d\d\d\d', text)
print(phone.group())


# Quantifiers
print(re.search(r'\d{3}-\d{3}-\d{4}', text))


# Groups
phone_pattern = re.compile(r'(\d{3})-(\d{3})-(\d{4})')
results = re.search(phone_pattern, text)

# The entire result
print(results.group())

# Can then also call by group position.
# Remember groups were separated by parenthesis ()
# Something to note is that group ordering starts at 1. Passing in 0 returns everything
print(results.group(1))
print(results.group(2))
print(results.group(3))

# We only had three groups of parenthesis (This will throw an IndexError if uncommented)
# print(results.group(4))


# Additional Regex Syntax

# Or operator |
print(re.search(r"man|woman", "This man was here."))
print(re.search(r"man|woman", "This woman was here."))


# The Wildcard Character
print(re.findall(r".at", "The cat in the hat sat here."))
print(re.findall(r".at", "The bat went splat"))
print(re.findall(r"...at", "The bat went splat"))

# One or more non-whitespace that ends with 'at'
print(re.findall(r'\S+at', "The bat went splat"))


# Starts with and Ends With
# Ends with a number
print(re.findall(r'\d$', 'This ends with a number 2'))
# Starts with a number
print(re.findall(r'^\d', '1 is the loneliest number.'))


# Exclusion
phrase = "there are 3 numbers 34 inside 5 this sentence."
print(re.findall(r'[^\d]', phrase))
print(re.findall(r'[^\d]+', phrase))

test_phrase = 'This is a string! But it has punctuation. How can we remove it?'
print(re.findall('[^!.? ]+', test_phrase))
clean = ' '.join(re.findall('[^!.? ]+', test_phrase))
print(clean)


# Brackets for Grouping
text = 'Only find the hypen-words in this sentence. But you do not know how long-ish they are'
print(re.findall(r'[\w]+-[\w]+', text))


# Parenthesis for Multiple Options
# Find words that start with cat and end with one of these options: 'fish','nap', or 'claw'
text = 'Hello, would you like some catfish?'
texttwo = "Hello, would you like to take a catnap?"
textthree = "Hello, have you seen this caterpillar?"

print(re.search(r'cat(fish|nap|claw)', text))
print(re.search(r'cat(fish|nap|claw)', texttwo))
# None returned
print(re.search(r'cat(fish|nap|claw)', textthree))