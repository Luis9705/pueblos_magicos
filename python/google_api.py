def get_geocode_locations(geocode_result):
    locations = []
    for address in geocode_result:
        location = address['geometry']['location']
        locations.append([location['lat'], location['lng']])
    return locations


def get_duration_matrix(distance_matrix_result):
    """ Returns the durations matrix of a google response.
    :param distance_matrix_result: Is the response of gmaps.distance_matrix()
    :type distance_matrix_result: a dictionary, with a list of rows and elements
    
    :rtype: matrix of durations, list of lists.
    """
    if 'rows' not in distance_matrix_result: return []
    M = len(distance_matrix_result['rows'])
    if M == 0: return []
    N = len(distance_matrix_result['rows'][0]['elements'])
    matrix = [[None for j in range(N)] for i in range(M)]
    for i, row in enumerate(distance_matrix_result['rows']):
        elements = row['elements']
        for j, element in enumerate(elements):
            if element['status'] == 'OK':
                #if traffic time was calculated, return this time
                if 'duration_in_traffic' in element.keys():
                    matrix[i][j] = element['duration_in_traffic']['value']
                else:
                    matrix[i][j] = element['duration']['value']
    return matrix


def get_distance_matrix(distance_matrix_result):
    """ Returns the distance matrix of a google response.
    :param distance_matrix_result: Is the response of gmaps.distance_matrix()
    :type distance_matrix_result: a dictionary, with a list of rows and elements
    
    :rtype: matrix of distances, list of lists.
    """
    if 'rows' not in distance_matrix_result: return []
    M = len(distance_matrix_result['rows'])
    if M == 0: return []
    N = len(distance_matrix_result['rows'][0]['elements'])
    matrix = [[None for j in range(N)] for i in range(M)]
    for i, row in enumerate(distance_matrix_result['rows']):
        elements = row['elements']
        for j, element in enumerate(elements):
            if element['status'] == 'OK':
                matrix[i][j] = element['distance']['value']
    return matrix

def get_directions_polylines(directions_result):
    """ Returns the polylines of a directions response

    :param directions_result: Is the response of gmaps.distance_matrix()
    :type directions_result: a list of directions dictionaries
    
    :rtype: list of Google-encoded polyline strings.
    """
    polylines = []
    if len(directions_result) > 0:
        for direction in directions_result:
            if 'overview_polyline' in direction:
                polylines.append(direction['overview_polyline']['points'])
            else:
                polyline.append(None)
    return polylines

def get_directions_total_distance(directions_result):
    """ Returns the total distance (in meters) of all the directions

    :param directions_result: Is the response of gmaps.distance_matrix()
    :type directions_result: a list of directions dictionaries
    
    :rtype: list of integers with the total distance in meters
    """
    distances = get_directions_legs_distance(directions_result)
    
    return list(map(lambda x: sum(x), distances))

def get_directions_legs_distance(directions_result):
    """ Returns the distance between each waypoint in the direction

    :param directions_result: Is the response of gmaps.distance_matrix()
    :type directions_result: a list of directions dictionaries
    
    :rtype: list of list with the  distance of each waypoint
    """
    distances = []
    for direction in directions_result:
        if 'legs' in direction:
            distance = []
            for leg in direction['legs']:
                distance.append(leg['distance']['value'])
            distances.append(distance)
    return distances


def get_directions_total_duration(directions_result):
    """ Returns the total duration (in seconds) of all the directions

    :param directions_result: Is the response of gmaps.distance_matrix()
    :type directions_result: a list of directions dictionaries
    
    :rtype: list of integers with the total duration in seconds
    """
    durations = get_directions_legs_duration(directions_result)
    
    return list(map(lambda x: sum(x), durations))

def get_directions_legs_duration(directions_result):
    """ Returns the total duration (in seconds) of all the directions

    :param directions_result: Is the response of gmaps.distance_matrix()
    :type directions_result: a list of directions dictionaries
    
    :rtype: list of integers with the total duration in seconds
    """
    distances = []
    for direction in directions_result:
        if 'legs' in direction:
            distance = []
            for leg in direction['legs']:
                if 'duration_in_traffic' in leg:
                    distance.append(leg['duration_in_traffic']['value'])
                else:
                    distance.append(leg['duration']['value'])
            distances.append(distance)
    return distances

def waypoints_via(waypoints):
    """ Returns the waypoints with the via parameter added
    This influences the route but avoid stopovers

    :param waypoints: The coordinates of the waypoints
    :type waypoints: a list of coordinates [lat, lon]
    
    :rtype: a string of waypoints in via format
    """   
    return '|'.join([f'via:{lat},{lon}' for (lat,lon) in waypoints])
        

def decode_polyline(polyline_str):
    """ Decodes a google polyline into a list of coordinates
    Reference:
    https://stackoverflow.com/questions/15380712/how-to-decode-polylines-from-google-maps-direction-api-in-php
    :param polyline_str: A google polyline
    :type polyline_str: string
    
    :rtype: list of coordinates in format [lat, lon]
    """
    index, lat, lng = 0, 0, 0
    coordinates = []
    changes = {'latitude': 0, 'longitude': 0}

    # Coordinates have variable length when encoded, so just keep
    # track of whether we've hit the end of the string. In each
    # while loop iteration, a single coordinate is decoded.
    while index < len(polyline_str):
        # Gather lat/lon changes, store them in a dictionary to apply them later
        for unit in ['latitude', 'longitude']:
            shift, result = 0, 0

            while True:
                byte = ord(polyline_str[index]) - 63
                index += 1
                result |= (byte & 0x1f) << shift
                shift += 5
                if not byte >= 0x20:
                    break

            if (result & 1):
                changes[unit] = ~(result >> 1)
            else:
                changes[unit] = (result >> 1)

        lat += changes['latitude']
        lng += changes['longitude']

        coordinates.append([lat / 100000.0, lng / 100000.0])

    return coordinates


def encode_coords(coords):
    '''Encodes a polyline using Google's polyline algorithm

    See http://code.google.com/apis/maps/documentation/polylinealgorithm.html
    for more information.

    :param coords: Coordinates to transform (list of tuples in order: latitude,
    longitude).
    :type coords: list
    :returns: Google-encoded polyline string.
    :rtype: string
    '''

    result = []

    prev_lat = 0
    prev_lng = 0

    for x, y in coords:
        lat, lng = int(y * 1e5), int(x * 1e5)

        d_lat = _encode_value(lat - prev_lat)
        d_lng = _encode_value(lng - prev_lng)

        prev_lat, prev_lng = lat, lng

        result.append(d_lng)
        result.append(d_lat)

    return ''.join(c for r in result for c in r)


def _split_into_chunks(value):
    while value >= 32:  # 2^5, while there are at least 5 bits

        # first & with 2^5-1, zeros out all the bits other than the first five
        # then OR with 0x20 if another bit chunk follows
        yield (value & 31) | 0x20
        value >>= 5
    yield value


def _encode_value(value):
    # Step 2 & 4
    value = ~(value << 1) if value < 0 else (value << 1)

    # Step 5 - 8
    chunks = _split_into_chunks(value)

    # Step 9-10
    return (chr(chunk + 63) for chunk in chunks)




