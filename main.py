#####
# DataMERGE - main.py
# Uses Opencv2 to grab images from a webcam
#####

import cv2
import time
from pyzbar import pyzbar
import hashlib
import json

# Init some objects
cap = cv2.VideoCapture(0)
qrDecoder = cv2.QRCodeDetector()
cv2.namedWindow("Results")
lastData = ""

# Get that camera's details and print it
frame_rate = cap.get(cv2.CAP_PROP_FPS)
width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
print("Using default camera (%dx%d, %dfps)" % (width,height,frame_rate))

def sha1(s):
    return hashlib.sha1(s).hexdigest()[:8]

def contains(l1, l2):
    return set(l2).issubset(l1)

def detectQR_zbar(inputImage):
    global lastData
    start = time.time()
    barcodes = pyzbar.decode(inputImage)
    end = time.time()
    # loop over the detected barcodes
    cv2.rectangle(inputImage, (0,0), (100,30), (0,0,0), cv2.FILLED)
    cv2.putText(inputImage, "%.2fms" % ((end-start)*1000), (10,20) ,cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,255), 2)
    for barcode in barcodes:
        # extract the bounding box location of the barcode and draw the
        # bounding box surrounding the barcode on the image
        (x, y, w, h) = barcode.rect
        cv2.rectangle(inputImage, (x, y), (x + w, y + h), (0, 0, 255), 2)

        # the barcode data is a bytes object so if we want to draw it on
        # our output image we need to convert it to a string first
        barcodeData = barcode.data.decode("utf-8")
        barcodeType = barcode.type

        # draw the barcode data and barcode type on the image
        text = "{} ({})".format(barcodeData, barcodeType)
        cv2.putText(inputImage, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                    0.5, (0, 0, 255), 2)

        # print the barcode type and data to the terminal
        if barcodeData != lastData:
            lastData = barcodeData
            return (barcodeData, inputImage, (end-start)*1000)
    return ("", inputImage, (end-start)*100)

def getNextCode_zbar(ignorelist):
    while True:
        # Get the image from the camera
        ret, img = cap.read()
        # Try to detect
        data, img, time = detectQR_zbar(img)
        # Wait 33ms (30fps) for a key and if it's ESC (27) break
        cv2.imshow("Results", img)
        if cv2.waitKey(33) == 27: break
        if data not in ignorelist: return data


# Loop forever
ignoreList = [""]
finishedscan = True
while True:
    if finishedscan:
        print("Waiting for title card...")
        finishedscan = False
    data = getNextCode_zbar(ignoreList)

    # If there's an error break
    if data == None: break

    # If there's a title card start the scan
    if data.startswith("DataMERGE"):
        start = 0

        # Get the data from the code (total size, order hashes)
        arr = data.split(".$")
        hashes = arr[1].split(",")
        total = len(hashes)
        meta = json.loads(arr[2])
        print("Found a title card! Total: %d, hashes: %s, meta: %s" % (total, ",".join(hashes), meta))
        scanned = 0
        ignored = ["", data]
        scanned = []
        scannedh = []

        # Start scanning for the codes
        while True:
            # Wait for code
            print("Scanning codes (%d / %d)..." % (len(scanned), total))
            data = getNextCode_zbar(ignored)
            hash = sha1(data.encode("utf-8"))

            # If the hash for the code isn't in the title card's hashlist don't add it
            if hash not in hashes: continue

            # For testing
            if start == 0: start = time.time()

            # Add the data and hash to the list
            ignored.append(data)
            scanned.append(data)
            scannedh.append(hash)

            # If we have all the hashes break
            if contains(scannedh, hashes):
                break

        # We have all the data, now we have to put it back in the right order
        ordered = [None] * total
        for d in scanned:
            # Put them in the same order as the hash list
            ordered[hashes.index(sha1(d.encode("utf-8")))] = d

        # Save the result in a file with it's hash to make it unique
        print("Saving the data...")
        result = "".join(ordered)
        filename = "result_%s.txt"% sha1(result.encode("utf-8"))
        if 'filename' in meta:
            filename = meta['filename']
        with open(filename, "w") as f:
            f.write(result)
            f.close()


        # The time is when the first data-code was scanned until the file was saved
        end = time.time()
        print("Finished scanning. Took %.2f seconds, saved as %s" % (end-start, filename))
        finishedscan = True


# Close the window
cv2.destroyAllWindows()