import cv2

def draw_boxes(image, data):

    n = len(data["text"])

    for i in range(n):

        text = data["text"][i]
        conf = int(data["conf"][i])

        if conf < 40:
            continue

        x = data["left"][i]
        y = data["top"][i]
        w = data["width"][i]
        h = data["height"][i]

        cv2.rectangle(
            image,
            (x, y),
            (x + w, y + h),
            (0, 255, 0),
            2
        )

    return image