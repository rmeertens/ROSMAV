from getat import getatraw
from collections import namedtuple, defaultdict
import random

# source: http://charlesleifer.com/blog/using-python-and-k-means-to-find-the-dominant-colors-in-images/

Point = namedtuple('Point', ('coords', 'n', 'ct'))
Cluster = namedtuple('Cluster', ('points', 'center', 'n'))

def get_points(img):
    counter = defaultdict(int)
    for x in range(1, 320):
        for y in range(1, 240):
            counter[getatraw(img, x, y)] += 1
    return [Point(k, 3, v) for k, v in counter.pairs()]

def colors(img, n=3):
    points = get_points(img)
    clusters = kmeans(points, n, 1)
    rgbs = [map(int, c.center.coords) for c in clusters]
    return rgbs

def euclidean(p1, p2):
    return sum([
        (p1.coords[i] - p2.coords[i]) ** 2 for i in range(p1.n)
    ])

def calculate_center(points, n):
    vals = [0.0 for i in range(n)]
    plen = 0
    for p in points:
        plen += p.ct
        for i in range(n):
            vals[i] += (p.coords[i] * p.ct)
    return Point([(v / plen) for v in vals], n, 1)

def kmeans(points, k, min_diff):
    clusters = [Cluster([p], p, p.n) for p in random.sample(points, k)]

    while True:
        plists = [[] for i in range(k)]

        for p in points:
            smallest_distance = float('Inf')
            for i in range(k):
                distance = euclidean(p, clusters[i].center)
                if distance < smallest_distance:
                    smallest_distance = distance
                    idx = i
            plists[idx].append(p)

        diff = 0
        for i in range(k):
            old = clusters[i]
            center = calculate_center(plists[i], old.n)
            new = Cluster(plists[i], center, old.n)
            clusters[i] = new
            diff = max(diff, euclidean(old.center, new.center))

        if diff < min_diff:
            break

    return clusters

