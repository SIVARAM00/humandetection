from flask import Flask, request, jsonify
import cv2
import os
import tempfile

app = Flask(__name__)

# Load MobileNet SSD model
prototxt = "deploy.prototxt.txt"
model = "res10_300x300_ssd_iter_140000_fp16.caffemodel"
net = cv2.dnn.readNetFromCaffe(prototxt, model)

@app.route("/detect", methods=["POST"])
def detect():
    if "video" not in request.files:
        return jsonify({"error": "No video file provided"}), 400

    video_file = request.files["video"]
    temp_dir = tempfile.mkdtemp()
    input_path = os.path.join(temp_dir, "input.mp4")
    video_file.save(input_path)

    output_dir = os.path.join(temp_dir, "frames")
    os.makedirs(output_dir, exist_ok=True)

    cap = cv2.VideoCapture(input_path)
    frame_count = 0
    results = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        h, w = frame.shape[:2]
        blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 1.0,
                                     (300, 300), (104.0, 177.0, 123.0))
        net.setInput(blob)
        detections = net.forward()

        human_found = False
        for i in range(detections.shape[2]):
            confidence = detections[0, 0, i, 2]
            idx = int(detections[0, 0, i, 1])
            if confidence > 0.5 and idx == 15:
                human_found = True
                break

        if human_found:
            output_path = os.path.join(output_dir, f"frame_{frame_count:04d}.jpg")
            cv2.imwrite(output_path, frame)
            results.append(os.path.basename(output_path))

        frame_count += 1

    cap.release()
    return jsonify({
        "message": f"Processed {frame_count} frames",
        "frames_with_people": len(results),
        "frames": results
    })
