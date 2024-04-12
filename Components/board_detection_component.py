import cv2
import math


##detect the chessboard on web view
def detectChessboard(webViewPath, viewWidth, viewHeight):
    # Step 1: Load the Image
    img = cv2.imread(webViewPath)
    height, width, channels = img.shape
    print(height, width)
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Gaussian blur
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # Canny edge detection
    edges = cv2.Canny(blur, 50, 150)

    # Hough transform
    # height / 2 ensure the line at least half of the image
    lines = cv2.HoughLinesP(
        edges, 1, math.pi / 180, 30, minLineLength=height / 4, maxLineGap=10
    )

    # Store vertical and horizontal lines
    vertical_lines = []
    horizontal_lines = []

    for line in lines:
        x1, y1, x2, y2 = line[0]
        if abs(x2 - x1) < 1:  # select vertical lines
            y1 += 10
            y2 -= 10
            # cv2.line(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            vertical_lines.append((x1, y1, x2, y2))

        if abs(y2 - y1) < 1:  # select horizontal lines
            x1 -= 10
            x2 += 10
            # cv2.line(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
            horizontal_lines.append((x1, y1, x2, y2))

    intersect_points = []
    for v_line in vertical_lines:
        for h_line in horizontal_lines:
            x1_v, y1_v, x2_v, y2_v = v_line
            x1_h, y1_h, x2_h, y2_h = h_line
            if (x1_h <= x1_v <= x2_h) and (y2_v <= y1_h <= y1_v):
                intersect_points.append((x1_v, y1_h))
                # cv2.circle(img, (x1_v, y1_h), 10, (255, 0, 0), -1)

    upper_left = None
    lower_right = None

    sorted_by_x = sorted(intersect_points, key=lambda x: (x[0], x[1]))
    print(sorted_by_x)

    trust_horizontal = []
    for i in sorted_by_x:
        tuples_with_x = [t for t in sorted_by_x if t[0] == i[0]]  ## horizontal line
        if len(tuples_with_x) == 9:
            ##test whether the line can be trust
            len_interval = (tuples_with_x[-1][0] - tuples_with_x[0][0]) / 8

            intervals = []
            for j in range(len(tuples_with_x) - 1):
                intervals.append(tuples_with_x[j + 1][0] - tuples_with_x[j][0])

            all_pass = True
            for interval in intervals:
                if not math.isclose(interval, len_interval, abs_tol=len_interval * 0.1):
                    all_pass = False
                    break

            if all_pass:
                trust_horizontal = tuples_with_x
                break

    sorted_by_y = sorted(intersect_points, key=lambda x: (x[1], x[0]))
    print(sorted_by_y)

    trust_vertical = []
    for i in sorted_by_y:
        tuples_with_y = [t for t in sorted_by_y if t[1] == i[1]]  ## vertical line
        if len(tuples_with_y) == 9:
            ##test whether the line can be trust
            ##condition = pattern interval
            len_interval = (tuples_with_y[-1][1] - tuples_with_y[0][1]) / 8

            intervals = []
            for j in range(len(tuples_with_y) - 1):
                intervals.append(tuples_with_y[j + 1][1] - tuples_with_y[j][1])

            all_pass = True
            for interval in intervals:
                if not math.isclose(interval, len_interval, abs_tol=len_interval * 0.1):
                    all_pass = False
                    break

            if all_pass:
                trust_vertical = tuples_with_y
                break
    upper_left = (trust_vertical[0][0], trust_horizontal[0][1])
    lower_right = (trust_vertical[-1][0], trust_horizontal[-1][1])
    # cv2.circle(img, upper_left, 10, (0, 255, 0), -1)
    # cv2.circle(img, lower_right, 10, (0, 0, 255), -1)

    # upper left and lower right point method
    # for i in sorted_by_x:
    #     tuples_with_x = [t for t in sorted_by_x if t[0] == i[0]]
    #     if 7 <= len(tuples_with_x) <= 11:
    #         tuples_with_y = [t for t in sorted_by_x if t[1] == tuples_with_x[-1][1]]
    #         if 7 <= len(tuples_with_y) <= 11:
    #             upper_left = tuples_with_x[0]
    #             lower_right = tuples_with_y[-1]
    #             cv2.circle(img, upper_left, 10, (0, 255, 0), -1)
    #             cv2.circle(img, lower_right, 10, (0, 0, 255), -1)
    #             break

    widthFactor = viewWidth / img.shape[1]
    heightFactor = viewHeight / img.shape[0]

    w = (lower_right[0] - upper_left[0]) * widthFactor
    h = (lower_right[1] - upper_left[1]) * heightFactor
    # cv2.imshow("lines.jpg", img)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    return (
        int(upper_left[0] * widthFactor),
        int(upper_left[1] * heightFactor),
        int(w),
        int(h),
    )


def classify_pixel_color(rgb):

    threshold = 127
    sum = 0
    for i in rgb:
        sum += i

    if (sum / 3) > threshold:
        return "WHITE"
    else:
        return "BLACK"


##detect the user's assigned color
def userColor(image_path):
    # Load the image
    image = cv2.imread(image_path)

    # Get the dimensions of the image
    height, width, _ = image.shape

    # Find the coordinates of the center pixel
    center_x = width // 2
    center_y = height // 2

    # Get the color of the center pixel
    center_pixel_color = image[center_y, center_x]

    return classify_pixel_color(center_pixel_color)
