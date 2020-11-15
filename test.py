from PIL import Image


def resizeImage(image):
    img = Image.open(image)
    width = 250
    height = 365
    resized_img = img.resize((width, height), Image.ANTIALIAS)
    resized_img.save(image)


resizeImage('Images/standart.jpg')