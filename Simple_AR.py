import numpy as np
import cv2 as cv

# The given video and calibration data
video_file = 'data/ChessBoard.mp4'
K = np.array([[1.18808292e+03, 0.00000000e+00, 3.51696936e+02], [0.00000000e+00, 1.18650185e+03, 6.24902687e+02], [0.00000000e+00, 0.00000000e+00, 1.00000000e+00]])
dist_coeff = np.array([0.02205492, 0.47085272, -0.01021119, 0.00712299, -1.24242936])
board_pattern = (10, 7)
board_cellsize = 0.025
board_criteria = cv.CALIB_CB_ADAPTIVE_THRESH + cv.CALIB_CB_NORMALIZE_IMAGE + cv.CALIB_CB_FAST_CHECK

# Open a video
video = cv.VideoCapture(video_file)
assert video.isOpened(), 'Cannot read the given input, ' + video_file

size_weight = 2

# Prepare a 3D box for SGD
box_s_lower = size_weight * board_cellsize * np.array([[1, 1,  -1], [2, 1, -1], [2, 1.25, -1], [2, 1.5, -1.25], [2, 1.75, -1], [2, 2,  -1], [1, 2,  -1], [1, 1.75, -1], [1, 1.5, -1.25], [1, 1.25, -1]])
box_s_upper = size_weight * board_cellsize * np.array([[1, 1, -2], [2, 1, -2], [2, 2, -2], [1, 2, -2]])
box_s_updown_index = [(0, 0), (1, 1), (5, 2), (6, 3)]

box_g_lower = size_weight * board_cellsize * np.array([[1, 0, -0.333], [2, 0, -0.333], [2, 0.333, -0.333], [2, 0.333, 0], [2, 1, 0], [1, 1, 0], [1, 0.333, 0], [1, 0.333, -0.333]])
box_g_upper = size_weight * board_cellsize * np.array([[1, 0, -1], [2, 0, -1], [2, 1, -1], [1, 1, -1]])
box_g_updown_index = [(0, 0), (1, 1), (4, 2), (5, 3)]

box_d_outer_lower = size_weight * board_cellsize * np.array([[1, 2, 0], [2, 2, 0], [2, 3, 0], [1, 3, 0]])
box_d_outer_upper = size_weight * board_cellsize * np.array([[1, 2, -1], [2, 2, -1], [2, 3, -1], [1, 3, -1]])
box_d_outer_updown_index = [(0, 0), (1, 1)]
box_d_inner_lower = size_weight * board_cellsize * np.array([[1, 2.667, -0.333], [2, 2.667, -0.333], [2, 3, -0.333], [1, 3, -0.333]])
box_d_inner_upper = size_weight * board_cellsize * np.array([[1, 2.667, -0.667], [2, 2.667, -0.667], [2, 3, -0.667], [1, 3, -0.667]])
box_d_inner_updown_index = [(0, 0), (1, 1)]
box_d_additional_lower = np.array([box_d_outer_lower[2], box_d_outer_lower[3], box_d_outer_upper[2], box_d_outer_upper[3]])
box_d_additional_upper = np.array([box_d_inner_upper[2], box_d_inner_lower[3], box_d_inner_upper[2], box_d_inner_upper[3]])
# Prepare 3D points on a chessboard
obj_points = board_cellsize * np.array([[c, r, 0] for r in range(board_pattern[1]) for c in range(board_pattern[0])])

def draw_box(lower, upper, index, color):
    line_lower, _ = cv.projectPoints(lower, rvec, tvec, K, dist_coeff)
    line_upper, _ = cv.projectPoints(upper, rvec, tvec, K, dist_coeff)
    cv.polylines(img, [np.int32(line_lower)], True, color, 2)
    cv.polylines(img, [np.int32(line_upper)], True, color, 2)
    for i_l, i_u in index:
        cv.line(img, np.int32(line_lower[i_l].flatten()), np.int32(line_upper[i_u].flatten()), color, 2)

# Run pose estimation
while True:
    # Read an image from the video
    valid, img = video.read()
    if not valid:
        break

    # Estimate the camera pose
    success, img_points = cv.findChessboardCorners(img, board_pattern, board_criteria)
    if success:
        ret, rvec, tvec = cv.solvePnP(obj_points, img_points, K, dist_coeff)

        draw_box(box_s_lower, box_s_upper, box_s_updown_index, (7, 0, 184))
        draw_box(box_g_lower, box_g_upper, box_g_updown_index, (173, 49, 0))
        draw_box(box_d_outer_lower, box_d_outer_upper, box_d_outer_updown_index, (143, 143, 143))
        draw_box(box_d_inner_lower, box_d_inner_upper, box_d_inner_updown_index, (143, 143, 143))

        line_lower, _ = cv.projectPoints(box_d_additional_lower, rvec, tvec, K, dist_coeff)
        line_upper, _ = cv.projectPoints(box_d_additional_upper, rvec, tvec, K, dist_coeff)
        for b, t in zip(line_lower, line_upper):
            cv.line(img, np.int32(b.flatten()), np.int32(t.flatten()), (143, 143, 143), 2)

        # Print the camera position
        R, _ = cv.Rodrigues(rvec) # Alternative) `scipy.spatial.transform.Rotation`
        p = (-R.T @ tvec).flatten()
        info = f'XYZ: [{p[0]:.3f} {p[1]:.3f} {p[2]:.3f}]'
        cv.putText(img, info, (10, 25), cv.FONT_HERSHEY_DUPLEX, 0.6, (0, 255, 0))

    # Show the image and process the key event
    cv.imshow('Pose Estimation (Chessboard)', img)
    key = cv.waitKey(10)
    if key == ord(' '):
        key = cv.waitKey()
    if key == 27: # ESC
        break

video.release()
cv.destroyAllWindows()