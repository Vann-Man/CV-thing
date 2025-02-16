from imutils import face_utils
import dlib
import cv2
import numpy as np

p = "shape_predictor_68_face_landmarks.dat"
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(p)
heart_sunglasses = cv2.imread("heart2.png", cv2.IMREAD_UNCHANGED)
black_sunglasses = cv2.imread("heart.png", cv2.IMREAD_UNCHANGED)

cap = cv2.VideoCapture(0)

filter_active = True

def menu():
    global filter_active
    while True:
        print("\nMenu:")
        print("1. Activate Filter")
        print("2. Deactivate Filter")
        print("3. Exit")
        choice = input("Enter choice: ")
        
        if choice == "1":
            filter_active = True
            print("Filter activated.")
        elif choice == "2":
            filter_active = False
            print("Filter deactivated.")
        elif choice == "3":
            print("Exiting...")
            cap.release()
            cv2.destroyAllWindows()
            break
        else:
            print("Invalid choice. Try again.")

import threading
menu_thread = threading.Thread(target=menu, daemon=True)
menu_thread.start()

while True:
    _, image = cap.read()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    rects = detector(gray, 0)

    if filter_active:
        for (i, rect) in enumerate(rects):
            shape = predictor(gray, rect)
            shape = face_utils.shape_to_np(shape)

            left_eye = shape[36]
            right_eye = shape[45]
            center_eye = ((left_eye[0] + right_eye[0]) // 2, (left_eye[1] + right_eye[1]) // 2)
            eye_distance = int(((right_eye[0] - left_eye[0]) ** 2 + (right_eye[1] - left_eye[1]) ** 2) ** 0.5)
            angle = np.degrees(np.arctan2(right_eye[1] - left_eye[1], right_eye[0] - left_eye[0]))

            sun_width = int(eye_distance * 2)
            sun_height = int(sunglasses.shape[0] * (sun_width / sunglasses.shape[1]))
            resized_sunglasses = cv2.resize(sunglasses, (sun_width, sun_height), interpolation=cv2.INTER_AREA)

            rotation_matrix = cv2.getRotationMatrix2D((sun_width // 2, sun_height // 2), -1 * angle, 1)
            rotated_sunglasses = cv2.warpAffine(resized_sunglasses, rotation_matrix, (sun_width, sun_height),
                                                flags=cv2.INTER_AREA, borderMode=cv2.BORDER_CONSTANT,
                                                borderValue=(0, 0, 0, 0))

            top_left = (center_eye[0] - sun_width // 2, center_eye[1] - sun_height // 2)
            x1, y1 = max(0, top_left[0]), max(0, top_left[1])
            x2, y2 = min(image.shape[1], top_left[0] + sun_width), min(image.shape[0], top_left[1] + sun_height)

            overlay_sunglasses = rotated_sunglasses[
                max(0, -top_left[1]):min(sun_height, image.shape[0] - top_left[1]),
                max(0, -top_left[0]):min(sun_width, image.shape[1] - top_left[0])
            ]

            if overlay_sunglasses.shape[0] > 0 and overlay_sunglasses.shape[1] > 0:
                overlay_image = image[y1:y2, x1:x2]
                alpha_s = overlay_sunglasses[:, :, 3] / 255.0
                alpha_l = 1.0 - alpha_s

                for c in range(0, 3):
                    overlay_image[:, :, c] = (alpha_s * overlay_sunglasses[:, :, c] + alpha_l * overlay_image[:, :, c])
                
                image[y1:y2, x1:x2] = overlay_image

    cv2.imshow("Output", image)

    k = cv2.waitKey(5) & 0xFF
    if k == 27:
        break

cap.release()
cv2.destroyAllWindows()
