from PIL import Image

# Open the three images you want to combine
place1 = Image.open('folkloresoft_profile.png')
place2 = Image.open('Korgabor_profile.png')
place3 = Image.open('rossztosz_profile.png')

new_size1 = (200, 200)
new_size2 = (150, 150)
new_size3 = (100, 100)

# Resize the images to the same size
image1 = place1.resize(new_size1)
image2 = place2.resize(new_size2)
image3 = place3.resize(new_size3)

background_image = Image.open('resources/uploads/podium.jpg')
background_image = background_image.convert('RGB')

combined_image = Image.new('RGB', background_image.size)

# Paste the background image onto the new image
combined_image.paste(background_image, (0, 0))

# 640x360

coord_image1 = (320-int(new_size1[0]/2),10)  # Coordinates for image1
coord_image2 = (44, 75)  # Coordinates for image2
coord_image3 = (450, 135)  # Coordinates for image3

# Paste the resized images onto the new image side by side
combined_image.paste(image1, coord_image1)
combined_image.paste(image2, coord_image2)
combined_image.paste(image3, coord_image3)

# Save the combined image
combined_image.save('combined_image_with_background.jpg')

# Optionally, display the combined image
#combined_image.show()