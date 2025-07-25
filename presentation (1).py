import cv2
import mediapipe as mp
import numpy as np

# Initialize MediaPipe
mp_hands = mp.solutions.hands
mp_face_mesh = mp.solutions.face_mesh
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    max_num_hands=2,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=2,
    refine_landmarks=True,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)

# Open webcam
cap = cv2.VideoCapture(0)

# 3D model points for head pose
model_points = np.array([
    [0.0, 0.0, 0.0],         
    [0.0, -330.0, -65.0],    
    [-225.0, 170.0, -135.0], 
    [225.0, 170.0, -135.0],  
    [-150.0, -150.0, -125.0],
    [150.0, -150.0, -125.0]  
], dtype=np.float64)

while True:
    ret, frame = cap.read()
    if not ret:
        print("⚠️ Could not read frame from webcam")
        break

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img_h, img_w = frame.shape[:2]

    # Hands
    hand_results = hands.process(rgb_frame)
    hand_count = len(hand_results.multi_hand_landmarks) if hand_results.multi_hand_landmarks else 0
    if hand_results.multi_hand_landmarks:
        for hand_landmarks in hand_results.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

    # Face
    face_results = face_mesh.process(rgb_frame)
    if face_results.multi_face_landmarks:
        for face_landmarks in face_results.multi_face_landmarks:
            mp_draw.draw_landmarks(
                image=frame,
                landmark_list=face_landmarks,
                connections=mp_face_mesh.FACEMESH_TESSELATION,
                landmark_drawing_spec=None,
                connection_drawing_spec=mp_draw.DrawingSpec(color=(0, 255, 255), thickness=1, circle_radius=1)
            )
            mp_draw.draw_landmarks(
                image=frame,
                landmark_list=face_landmarks,
                connections=mp_face_mesh.FACEMESH_CONTOURS,
                landmark_drawing_spec=None,
                connection_drawing_spec=mp_draw.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=1)
            )

            image_points = np.array([
                [face_landmarks.landmark[1].x * img_w, face_landmarks.landmark[1].y * img_h],
                [face_landmarks.landmark[152].x * img_w, face_landmarks.landmark[152].y * img_h],
                [face_landmarks.landmark[263].x * img_w, face_landmarks.landmark[263].y * img_h],
                [face_landmarks.landmark[33].x * img_w, face_landmarks.landmark[33].y * img_h],
                [face_landmarks.landmark[287].x * img_w, face_landmarks.landmark[287].y * img_h],
                [face_landmarks.landmark[57].x * img_w, face_landmarks.landmark[57].y * img_h]
            ], dtype=np.float64)

            focal_length = img_w
            center = (img_w / 2, img_h / 2)
            camera_matrix = np.array([
                [focal_length, 0, center[0]],
                [0, focal_length, center[1]],
                [0, 0, 1]
            ], dtype="double")
            dist_coeffs = np.zeros((4, 1))

            success, rotation_vector, translation_vector = cv2.solvePnP(
                model_points, image_points, camera_matrix, dist_coeffs
            )

            nose_end, _ = cv2.projectPoints(
                np.array([[0.0, 0.0, 1000.0]]),
                rotation_vector,
                translation_vector,
                camera_matrix,
                dist_coeffs
            )

            p1 = (int(image_points[0][0]), int(image_points[0][1]))
            p2 = (int(nose_end[0][0][0]), int(nose_end[0][0][1]))
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]

            if abs(dx) > abs(dy):
                direction = "Looking Right" if dx > 15 else "Looking Left"
            else:
                direction = "Looking Down" if dy > 15 else "Looking Up"

            if abs(dx) < 30 and abs(dy) < 30:
                direction = "Looking Center"

            cv2.line(frame, p1, p2, (0, 0, 255), 3)
            cv2.putText(frame, direction, (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 100, 0), 2)
            cv2.putText(frame, f"dx: {dx:.2f}, dy: {dy:.2f}", (30, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(frame, f"Hands detected: {hand_count}", (30, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

    cv2.imshow("Webcam: Hand + Head + Face", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
