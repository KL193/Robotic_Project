import cv2
import mediapipe as mp
import numpy as np

# Setup MediaPipe Face Mesh
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1)

# Open webcam
cap = cv2.VideoCapture(0)

# Facial landmark indices
face_3d_indices = [1, 33, 263, 61, 291, 199]

while True:
    ret, frame = cap.read()
    if not ret:
        print("⚠️ Could not read frame from webcam")
        break

    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(img_rgb)

    if results.multi_face_landmarks:
        mesh = results.multi_face_landmarks[0]
        ih, iw, _ = frame.shape
        landmarks_2d, landmarks_3d = [], []

        for idx in face_3d_indices:
            lm = mesh.landmark[idx]
            x, y = int(lm.x * iw), int(lm.y * ih)
            landmarks_2d.append([x, y])
            landmarks_3d.append([x, y, lm.z * 3000])

        landmarks_2d = np.array(landmarks_2d, dtype=np.float64)
        landmarks_3d = np.array(landmarks_3d, dtype=np.float64)

        focal_length = 1 * iw
        cam_matrix = np.array([
            [focal_length, 0, iw / 2],
            [0, focal_length, ih / 2],
            [0, 0, 1]
        ])
        dist_coeffs = np.zeros((4, 1))

        success, rot_vec, trans_vec = cv2.solvePnP(
            landmarks_3d, landmarks_2d, cam_matrix, dist_coeffs
        )

        rmat, _ = cv2.Rodrigues(rot_vec)
        angles, _, _, _, _, _ = cv2.RQDecomp3x3(rmat)

        pitch, yaw, roll = angles
        text = "Looking Forward"
        if yaw < -10:
            text = "Looking Right"
        elif yaw > 10:
            text = "Looking Left"

        cv2.putText(frame, text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)

        nose_2d = tuple(landmarks_2d[0].astype(int))
        nose_end = cv2.projectPoints(
            np.array([[0.0, 0.0, 50.0]]),
            rot_vec, trans_vec, cam_matrix, dist_coeffs
        )[0]

        p2 = tuple(nose_end[0][0].astype(int))
        cv2.line(frame, nose_2d, p2, (255, 0, 0), 3)

    cv2.imshow('Webcam Head Pose Estimation', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
