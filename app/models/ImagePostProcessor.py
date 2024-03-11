import asyncio
import numpy as np
import cv2
import uuid
from sklearn.cluster import DBSCAN
from io import BytesIO
import requests  # Import requests for downloading images

class ImagePostProcessor:
    def __init__(self):
        pass

    def download_image(self, url):
        # Download the image from the given URL
        response = requests.get(url)
        if response.status_code == 200:
            return BytesIO(response.content)
        else:
            raise ValueError(f"Failed to download image from {url}")

    def order_points_with_clustering(self, x_indices, y_indices):
        if len(x_indices) == 0:
            return []

        points = np.array(list(zip(x_indices, y_indices)))
        clustering = DBSCAN(eps=3, min_samples=2).fit(points)
        labels = clustering.labels_

        clustered_points = {}
        for label, point in zip(labels, points):
            if label not in clustered_points:
                clustered_points[label] = []
            clustered_points[label].append(point)

        ordered_points = []
        for label in sorted(clustered_points):
            cluster_points = clustered_points[label]
            cluster_points.sort(key=lambda p: (p[0], p[1]))
            ordered_points.extend(cluster_points)

        return ordered_points

    def vectorize_image(self, image_data):
        img = cv2.imdecode(np.frombuffer(image_data.getvalue(), np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Image data could not be decoded.")

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)

        y_indices, x_indices = np.where(edges > 0)
        ordered_points = self.order_points_with_clustering(x_indices, y_indices)

        elements = []
        for x, y in ordered_points:
            elements.append({
                'type': 'rectangle',
                'id': str(uuid.uuid4()),
                'x': int(x),
                'y': int(y),
                'strokeColor': '#c92a2a',
                'width': 1,
                'height': 1,
            })

        return elements

    async def process_image(self, image_url):
        print("DEBUG IN POST PROCESSING")
        # Download the image from the URL asynchronously
        loop = asyncio.get_event_loop()
        image_data = await loop.run_in_executor(None, self.download_image, image_url)

        # Vectorize the image and reorder points
        vector_elements = self.vectorize_image(image_data)

        # Here you can implement additional post-processing steps as needed

        return vector_elements
