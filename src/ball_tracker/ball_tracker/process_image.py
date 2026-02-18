# Copyright 2023 Tiziano Fiorenzani (modifications by Josh Newans)
# Modified 2026 for face detection using face_recognition library

import cv2
import numpy as np
import face_recognition
import pickle
import os


# --- ALTE BALL-ERKENNUNG (auskommentiert) ---
# def find_circles(image, tuning_params):
#
#     blur = 5
#
#     x_min   = tuning_params["x_min"]
#     x_max   = tuning_params["x_max"]
#     y_min   = tuning_params["y_min"]
#     y_max   = tuning_params["y_max"]
#
#     search_window = [x_min, y_min, x_max, y_max]
#     working_image    = cv2.blur(image, (blur, blur))
#
#     #- Blur image to remove noise
#     # if blur > 0:
#     #     image    = cv2.blur(image, (blur, blur))
#
#     #- Search window
#     if search_window is None: search_window = [0.0, 0.0, 1.0, 1.0]
#     search_window_px = convert_rect_perc_to_pixels(search_window, image)
#
#     #- Convert image from BGR to HSV
#     working_image     = cv2.cvtColor(working_image, cv2.COLOR_BGR2HSV)
#
#     #- Apply HSV threshold
#     thresh_min = (tuning_params["h_min"], tuning_params["s_min"], tuning_params["v_min"])
#     thresh_max = (tuning_params["h_max"], tuning_params["s_max"], tuning_params["v_max"])
#     working_image    = cv2.inRange(working_image, thresh_min, thresh_max)
#
#     # Dilate and Erode
#     working_image = cv2.dilate(working_image, None, iterations=2)
#     working_image = cv2.erode(working_image, None, iterations=2)
#
#     # Make a copy of the image for tuning
#     tuning_image = cv2.bitwise_and(image,image,mask = working_image)
#
#     # Apply the search window
#     working_image = apply_search_window(working_image, search_window)
#
#     # Invert the image to suit the blob detector
#     working_image = 255-working_image
#
#     # Set up the SimpleBlobdetector with default parameters.
#     params = cv2.SimpleBlobDetector_Params()
#     params.minThreshold = 0
#     params.maxThreshold = 100
#     params.filterByArea = True
#     params.minArea = 30
#     params.maxArea = 20000
#     params.filterByCircularity = True
#     params.minCircularity = 0.1
#     params.filterByConvexity = True
#     params.minConvexity = 0.5
#     params.filterByInertia = True
#     params.minInertiaRatio = 0.5
#
#     detector = cv2.SimpleBlobDetector_create(params)
#     keypoints = detector.detect(working_image)
#
#     size_min_px = tuning_params['sz_min']*working_image.shape[1]/100.0
#     size_max_px = tuning_params['sz_max']*working_image.shape[1]/100.0
#     keypoints = [k for k in keypoints if k.size > size_min_px and k.size < size_max_px]
#
#     line_color=(0,0,255)
#     out_image = cv2.drawKeypoints(image, keypoints, np.array([]), line_color, cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
#     out_image = draw_window2(out_image, search_window_px)
#     tuning_image = cv2.drawKeypoints(tuning_image, keypoints, np.array([]), line_color, cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
#     tuning_image = draw_window2(tuning_image, search_window_px)
#
#     keypoints_normalised = [normalise_keypoint(working_image, k) for k in keypoints]
#     return keypoints_normalised, out_image, tuning_image
# --- ENDE ALTE BALL-ERKENNUNG ---


def load_encodings(path):
    """Lädt gespeicherte Gesichts-Encodings aus einer .pkl-Datei.
    Gibt (known_encodings, known_names) zurück, oder ([], []) wenn Datei nicht existiert."""
    expanded = os.path.expanduser(path)
    if not os.path.exists(expanded):
        return [], []
    with open(expanded, "rb") as f:
        data = pickle.load(f)
    return data["encodings"], data["names"]


def find_and_identify_faces(
    image, known_encodings, known_names, tolerance=0.6, model="hog"
):
    """Erkennt Gesichter im Bild und identifiziert sie anhand gespeicherter Encodings."""
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    face_locations = face_recognition.face_locations(rgb_image, model=model)
    face_encodings = face_recognition.face_encodings(rgb_image, face_locations)

    face_names = []
    for encoding in face_encodings:
        name = "unknown"
        if len(known_encodings) > 0:
            matches = face_recognition.compare_faces(
                known_encodings, encoding, tolerance=tolerance
            )
            face_distances = face_recognition.face_distance(known_encodings, encoding)
            if True in matches:
                best_match_index = int(np.argmin(face_distances))
                if matches[best_match_index]:
                    name = known_names[best_match_index]
        face_names.append(name)

    out_image = draw_face_boxes(image.copy(), face_locations, face_names)
    return face_locations, face_names, out_image


def draw_face_boxes(image, face_locations, face_names):
    """Zeichnet Bounding Boxes und Namen auf das Bild."""
    color_map = {"unknown": (128, 128, 128)}
    default_colors = [
        (0, 255, 0),  # Grün   – Person 1
        (255, 128, 0),  # Orange – Person 2
        (0, 128, 255),  # Blau   – Person 3
    ]
    color_idx = 0

    for (top, right, bottom, left), name in zip(face_locations, face_names):
        if name not in color_map:
            color_map[name] = default_colors[color_idx % len(default_colors)]
            color_idx += 1
        color = color_map[name]
        cv2.rectangle(image, (left, top), (right, bottom), color, 2)
        cv2.rectangle(image, (left, bottom - 28), (right, bottom), color, cv2.FILLED)
        cv2.putText(
            image,
            name,
            (left + 4, bottom - 8),
            cv2.FONT_HERSHEY_DUPLEX,
            0.6,
            (255, 255, 255),
            1,
        )
    return image


def normalise_face(image, face_location):
    """Normalisiert eine Gesichtsposition auf [-1, 1] relativ zur Bildmitte."""
    rows = float(image.shape[0])
    cols = float(image.shape[1])
    center_x = 0.5 * cols
    center_y = 0.5 * rows
    top, right, bottom, left = face_location
    face_cx = (left + right) / 2.0
    face_cy = (top + bottom) / 2.0
    norm_x = (face_cx - center_x) / center_x
    norm_y = (face_cy - center_y) / center_y
    norm_size = float(right - left) / cols
    return norm_x, norm_y, norm_size


# ---------- Apply search window: returns the image
# -- return(image)
def apply_search_window(image, window_adim=[0.0, 0.0, 1.0, 1.0]):
    rows = image.shape[0]
    cols = image.shape[1]
    x_min_px = int(cols * window_adim[0] / 100)
    y_min_px = int(rows * window_adim[1] / 100)
    x_max_px = int(cols * window_adim[2] / 100)
    y_max_px = int(rows * window_adim[3] / 100)

    # --- Initialize the mask as a black image
    mask = np.zeros(image.shape, np.uint8)

    # --- Copy the pixels from the original image corresponding to the window
    mask[y_min_px:y_max_px, x_min_px:x_max_px] = image[
        y_min_px:y_max_px, x_min_px:x_max_px
    ]

    # --- return the mask
    return mask


# ---------- Draw search window: returns the image
# -- return(image)
def draw_window2(
    image,  # - Input image
    rect_px,  # - window in adimensional units
    color=(255, 0, 0),  # - line's color
    line=5,  # - line's thickness
):

    # -- Draw a rectangle from top left to bottom right corner

    return cv2.rectangle(
        image, (rect_px[0], rect_px[1]), (rect_px[2], rect_px[3]), color, line
    )


def convert_rect_perc_to_pixels(rect_perc, image):
    rows = image.shape[0]
    cols = image.shape[1]

    scale = [cols, rows, cols, rows]

    # x_min_px    = int(cols*window_adim[0])
    # y_min_px    = int(rows*window_adim[1])
    # x_max_px    = int(cols*window_adim[2])
    # y_max_px    = int(rows*window_adim[3])
    return [int(a * b / 100) for a, b in zip(rect_perc, scale)]


def normalise_keypoint(cv_image, kp):
    rows = float(cv_image.shape[0])
    cols = float(cv_image.shape[1])
    # print(rows, cols)
    center_x = 0.5 * cols
    center_y = 0.5 * rows
    # print(center_x)
    x = (kp.pt[0] - center_x) / (center_x)
    y = (kp.pt[1] - center_y) / (center_y)
    return cv2.KeyPoint(x, y, kp.size / cv_image.shape[1])


def create_tuning_window(initial_values):
    cv2.namedWindow("Tuning", 0)
    cv2.createTrackbar("x_min", "Tuning", initial_values["x_min"], 100, no_op)
    cv2.createTrackbar("x_max", "Tuning", initial_values["x_max"], 100, no_op)
    cv2.createTrackbar("y_min", "Tuning", initial_values["y_min"], 100, no_op)
    cv2.createTrackbar("y_max", "Tuning", initial_values["y_max"], 100, no_op)
    cv2.createTrackbar("h_min", "Tuning", initial_values["h_min"], 180, no_op)
    cv2.createTrackbar("h_max", "Tuning", initial_values["h_max"], 180, no_op)
    cv2.createTrackbar("s_min", "Tuning", initial_values["s_min"], 255, no_op)
    cv2.createTrackbar("s_max", "Tuning", initial_values["s_max"], 255, no_op)
    cv2.createTrackbar("v_min", "Tuning", initial_values["v_min"], 255, no_op)
    cv2.createTrackbar("v_max", "Tuning", initial_values["v_max"], 255, no_op)
    cv2.createTrackbar("sz_min", "Tuning", initial_values["sz_min"], 100, no_op)
    cv2.createTrackbar("sz_max", "Tuning", initial_values["sz_max"], 100, no_op)


def get_tuning_params():
    trackbar_names = [
        "x_min",
        "x_max",
        "y_min",
        "y_max",
        "h_min",
        "h_max",
        "s_min",
        "s_max",
        "v_min",
        "v_max",
        "sz_min",
        "sz_max",
    ]
    return {key: cv2.getTrackbarPos(key, "Tuning") for key in trackbar_names}


def wait_on_gui():
    cv2.waitKey(2)


def no_op(x):
    pass
