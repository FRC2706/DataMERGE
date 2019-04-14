import qrcode
import time
import pygame
import hashlib
import sys

# This splits strings into chunks of a specific length
def chunkstring(string, length):
    return (string[0+i:length+i] for i in range(0, len(string), length))

# This creates a QR code
def generate_code(data):
    qr = qrcode.QRCode(box_size=5)
    qr.add_data(data)
    qr.make(fit=True)
    return qr.make_image()

# This converts a Python Image Lib image into a Pygame image
def convert_img(img):
    img = img.convert("RGBA")
    size = img.size
    mode = img.mode
    data = img.tobytes()
    return pygame.image.fromstring(data, size, mode)

# Returns the first 8 characters of the sha1 hash of s
def sha1(s):
    return hashlib.sha1(s).hexdigest()[:8]

# Init some things
pygame.init()
screen = pygame.display.set_mode((970, 970))
currindex = -1
length = float(sys.argv[2])
lastchange = 0

# Load the data from the file
print("Loading data...")
data = ""
with open(sys.argv[1], "r") as f:
    data = f.read()
data = list(chunkstring(data, 512))

# Generate the qr codes
print("Generating QR Codes (%d)" % len(data))
codes = []
hashes = []
for chunk in data:
    codes.append(convert_img(generate_code(chunk)))
    hashes.append(sha1(chunk.encode("utf-8")))

# Generate the title card
titlecard = convert_img(generate_code("DataMERGE:%d:%s" % (len(data), ",".join(hashes))))


# This is all pygame stuff for displaying the images
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: pygame.quit()
        if event.type == pygame.MOUSEBUTTONUP:
            currindex = 0
            lastchange = time.time()

    # If currindex != -1 we're looping through the qr codes
    if currindex != -1:
        screen.fill((255,255,255))
        screen.blit(codes[currindex], codes[currindex].get_rect())
        if time.time() > lastchange + length:
            lastchange = time.time()
            currindex = (currindex + 1) % len(codes)

    # If it is -1 we're showing the title card and waiting until reader is ready
    else:
        screen.fill((255,255,255))
        screen.blit(titlecard, titlecard.get_rect())
    pygame.display.flip()

