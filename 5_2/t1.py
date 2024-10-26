import requests

# Define the URL
url = 'https://finans.mynet.com/borsa/hisseler/acsel-acipayam-seluloz/'

# Send the request
response = requests.get(url)

# Prepare the content to write to the file
response_content = f"Response attributes:\n{dir(response)}\n\nResponse text:\n{response.text}"  # Limiting to 1000 characters for brevity

# Write to a text file
with open("response_details.txt", "w") as file:
    file.write(response_content)

print("Response details have been saved to response_details.txt")
