from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import openai
import cv2
import numpy as np
import json
from io import BytesIO
import uuid
from fastapi.responses import JSONResponse
import random
import uvicorn
import traceback  # Import traceback to log detailed error information
import cv2
import uuid
from matplotlib import pyplot as plt
from sklearn.cluster import DBSCAN



app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ImageDescription(BaseModel):
    description: str

def generate_image(description):
    print("Generating image...")
    client = openai.OpenAI(api_key='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')
    styled_prompt = f"{description} - Depict the figure as described in the prompt using a stylus with a consistent line thickness, creating a functional and straightforward illustration. The style should be more practical, resembling a clear, uniform sketch rather than an artistic rendering. Use a simple, limited color palette, primarily black, with minimal use of colors like blue, red, and green to emphasize only the most distinctive features of the figure. The background should be completely plain, ensuring that the focus remains entirely on the figure without any artistic or environmental distractions."
    response = client.images.generate(
        model="dall-e-3",
        prompt=styled_prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )
    image_url = response.data[0].url
    print("Image generated:", image_url)
    return image_url

def download_image(url):
    print("Downloading image...")
    response = requests.get(url)
    if response.status_code == 200:
        print("Image downloaded")
        return BytesIO(response.content)
    else:
        raise Exception("Failed to download image")


def order_points_like_brush_stroke(x_indices, y_indices):
    print("Starting to order points...")

    # Check if the input lists are empty
    if len(x_indices) == 0:
        print("No points to order. Exiting function.")
        return []

    # Combine x and y indices into a single array of coordinates
    points = list(zip(x_indices, y_indices))
    print(f"Total points to order: {len(points)}")

    # Initialize the ordered points list with the first point
    ordered_points = [points.pop(0)]

    # Iterate until all points are ordered
    while points:
        last_point = ordered_points[-1]
        # Calculate distances from the last point to all remaining points
        distances = [np.linalg.norm(np.array(last_point) - np.array(point)) for point in points]

        # Find the index of the closest point
        closest_point_index = np.argmin(distances)
        print(f"Closest point found at index: {closest_point_index}")

        # Append the closest point to the ordered list and remove it from the remaining points
        ordered_points.append(points.pop(closest_point_index))
        print(f"Ordered points count: {len(ordered_points)}")

    print("Finished ordering points.")
    return ordered_points


def order_points_with_clustering(x_indices, y_indices):
    print("Starting point ordering with clustering...")

    if len(x_indices) == 0:
        print("No points to order. Exiting function.")
        return []

    points = np.array(list(zip(x_indices, y_indices)))
    print(f"Total points: {len(points)}")

    clustering = DBSCAN(eps=3, min_samples=2).fit(points)
    labels = clustering.labels_

    clustered_points = {}
    for label, point in zip(labels, points):
        if label not in clustered_points:
            clustered_points[label] = []
        clustered_points[label].append(point)

    print(f"Total clusters formed: {len(set(labels)) - (1 if -1 in labels else 0)}")

    ordered_points = []
    for label in sorted(clustered_points):
        cluster_points = clustered_points[label]
        cluster_points.sort(key=lambda p: (p[0], p[1]))
        ordered_points.extend(cluster_points)

        print(f"Processed cluster {label}, number of points in cluster: {len(cluster_points)}")

    print("Finished ordering points with clustering.")
    return ordered_points


def vectorize_image(image_data):
    nparr = np.frombuffer(image_data.getvalue(), np.uint8)
    print("PROGRESS NP: ", nparr)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    print("DECODE: ", img)
    if img is None:
        raise ValueError("Image data could not be decoded. Please check the source of the image data.")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 100, 200)

    # Instead of finding contours, use the edge points directly
    y_indices, x_indices = np.where(edges > 0)

    print("At ordered points")
    # Order the points to resemble a brush stroke
    # ordered_points = order_points_like_brush_stroke(x_indices, y_indices)
    ordered_points = order_points_with_clustering(x_indices, y_indices)

    print("Post ordered points")

    elements = []
    for x, y in ordered_points:


     # Instead of finding contours, use the edge points directly
    # y_indices, x_indices = np.where(edges > 0)

    # elements = []
    # for x, y in zip(x_indices, y_indices):
        elements.append({
            'type': 'rectangle',
            'version': 141,
            'versionNonce': 361174001,
            'isDeleted': False,
            'id': str(uuid.uuid4()),
            'fillStyle': 'hachure',
            'strokeWidth': 1,
            'strokeStyle': 'solid',
            'roughness': 1,
            'opacity': 100,
            'angle': 0,  # No angle needed as these are points
            'x': int(x),
            'y': int(y),
            'strokeColor': '#c92a2a',
            'backgroundColor': 'transparent',
            'width': 1,
            'height': 1,
            'seed': 1968410350,
            'groupIds': [],
            'boundElements': None,
            'locked': False,
            'link': None,
            'updated': 1,
            'roundness': {
                'type': 3,
                'value': 32
                }
            })

    print("ELEMENTS: ", elements)
    return elements

