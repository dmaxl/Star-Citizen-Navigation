import unittest

from scnav import compute, db, types


COORDINATES_IN = (
    "Coordinates: x:22462615339.086491 y:37186143497.515411 z:766202.569542 T:1674962568.3761563",
    "Coordinates: x:22462610969.103771 y:37186149702.314690 z:762582.542856 T:1674962588.713745",
    "Coordinates: x:22462608809.070953 y:37186154093.374184 z:760442.027380 T:1674962602.7946541",
    "Coordinates: x:22462605763.383167 y:37186160500.528336 z:755925.276390 T:1674962628.3547761",
    "Coordinates: x:22462602646.400471 y:37186165714.307335 z:753295.282496 T:1674962644.247022",
    "Coordinates: x:22462590658.282677 y:37186183125.569626 z:746029.936127 T:1674962699.0247486",
    "Coordinates: x:22462579781.074726 y:37186195947.871468 z:745156.561537 T:1674962755.4374888",
)

EXPECTED_DATA = (
    {"updated": "19:22:48", "target": "New Babbage", "player_actual_container": "microTech", "target_container": "microTech", "player_x": 522.646, "player_y": 408.242, "player_z": 766.203, "player_long": "-52.01\u00b0", "player_lat": "49.12\u00b0", "player_height": "13.4 km", "player_OM1": "OM-1 : 945.132 km", "player_OM2": "OM-3 : 1387.051 km", "player_OM3": "OM-5 : 1262.743 km", "player_closest_poi": "Tears of Fire Painting : 20.456 km", "player_state_of_the_day": "Before midnight", "player_next_event": "Sunrise", "player_next_event_time": "20:28:57", "target_x": 520.723, "target_y": 419.364, "target_z": 743.655, "target_long": "-51.15\u00b0", "target_lat": "48.04\u00b0", "target_height": "0.0 km", "target_OM1": "OM-1 : 965.064 km", "target_OM2": "OM-3 : 1365.666 km", "target_OM3": "OM-5 : 1254.277 km", "target_closest_QT_beacon": "POI itself : 0 km", "target_state_of_the_day": "Before midnight", "target_next_event": "Sunrise", "target_next_event_time": "20:34:38", "distance_to_poi": "25.215 km", "distance_to_poi_color": "#00ff00", "delta_distance_to_poi": "25.215 km", "delta_distance_to_poi_color": "#ff3700", "total_deviation": "122.5\u00b0", "total_deviation_color": "#ff3700", "horizontal_deviation": "0.0\u00b0", "horizontal_deviation_color": "#00ff00", "heading": "152.1\u00b0", "ETA": "-1 day, 4:34:02"},
    {"updated": "19:23:08", "target": "New Babbage", "player_actual_container": "microTech", "target_container": "microTech", "player_x": 521.713, "player_y": 409.886, "player_z": 762.583, "player_long": "-51.84\u00b0", "player_lat": "48.98\u00b0", "player_height": "10.8 km", "player_OM1": "OM-1 : 947.91 km", "player_OM2": "OM-3 : 1383.479 km", "player_OM3": "OM-5 : 1261.761 km", "player_closest_poi": "Tears of Fire Painting : 16.374 km", "player_state_of_the_day": "Before midnight", "player_next_event": "Sunrise", "player_next_event_time": "20:29:30", "target_x": 520.723, "target_y": 419.364, "target_z": 743.655, "target_long": "-51.15\u00b0", "target_lat": "48.04\u00b0", "target_height": "0.0 km", "target_OM1": "OM-1 : 965.064 km", "target_OM2": "OM-3 : 1365.666 km", "target_OM3": "OM-5 : 1254.277 km", "target_closest_QT_beacon": "POI itself : 0 km", "target_state_of_the_day": "Before midnight", "target_next_event": "Sunrise", "target_next_event_time": "20:34:38", "distance_to_poi": "21.191 km", "distance_to_poi_color": "#00ff00", "delta_distance_to_poi": "4.024 km", "delta_distance_to_poi_color": "#00ff00", "total_deviation": "10.7\u00b0", "total_deviation_color": "#ffd000", "horizontal_deviation": "9.4\u00b0", "horizontal_deviation_color": "#00ff00", "heading": "153.6\u00b0", "ETA": "0:01:47"},
    {"updated": "19:23:22", "target": "New Babbage", "player_actual_container": "microTech", "target_container": "microTech", "player_x": 521.972, "player_y": 411.149, "player_z": 760.442, "player_long": "-51.77\u00b0", "player_lat": "48.85\u00b0", "player_height": "9.8 km", "player_OM1": "OM-1 : 950.128 km", "player_OM2": "OM-3 : 1381.457 km", "player_OM3": "OM-5 : 1260.692 km", "player_closest_poi": "Tears of Fire Painting : 14.035 km", "player_state_of_the_day": "Before midnight", "player_next_event": "Sunrise", "player_next_event_time": "20:29:43", "target_x": 520.723, "target_y": 419.364, "target_z": 743.655, "target_long": "-51.15\u00b0", "target_lat": "48.04\u00b0", "target_height": "0.0 km", "target_OM1": "OM-1 : 965.064 km", "target_OM2": "OM-3 : 1365.666 km", "target_OM3": "OM-5 : 1254.277 km", "target_closest_QT_beacon": "POI itself : 0 km", "target_state_of_the_day": "Before midnight", "target_next_event": "Sunrise", "target_next_event_time": "20:34:38", "distance_to_poi": "18.731 km", "distance_to_poi_color": "#00ff00", "delta_distance_to_poi": "2.46 km", "delta_distance_to_poi_color": "#00ff00", "total_deviation": "10.7\u00b0", "total_deviation_color": "#ffd000", "horizontal_deviation": "5.9\u00b0", "horizontal_deviation_color": "#00ff00", "heading": "152.9\u00b0", "ETA": "0:01:47"},
    {"updated": "19:23:48", "target": "New Babbage", "player_actual_container": "microTech", "target_container": "microTech", "player_x": 523.392, "player_y": 411.901, "player_z": 755.925, "player_long": "-51.8\u00b0", "player_lat": "48.62\u00b0", "player_height": "7.5 km", "player_OM1": "OM-1 : 954.465 km", "player_OM2": "OM-3 : 1378.953 km", "player_OM3": "OM-5 : 1257.183 km", "player_closest_poi": "Tears of Fire Painting : 10.437 km", "player_state_of_the_day": "Before midnight", "player_next_event": "Sunrise", "player_next_event_time": "20:30:28", "target_x": 520.723, "target_y": 419.364, "target_z": 743.655, "target_long": "-51.15\u00b0", "target_lat": "48.04\u00b0", "target_height": "0.0 km", "target_OM1": "OM-1 : 965.064 km", "target_OM2": "OM-3 : 1365.666 km", "target_OM3": "OM-5 : 1254.277 km", "target_closest_QT_beacon": "POI itself : 0 km", "target_state_of_the_day": "Before midnight", "target_next_event": "Sunrise", "target_next_event_time": "20:34:38", "distance_to_poi": "14.607 km", "distance_to_poi_color": "#00ff00", "delta_distance_to_poi": "4.124 km", "delta_distance_to_poi_color": "#00ff00", "total_deviation": "35.2\u00b0", "total_deviation_color": "#ff3700", "horizontal_deviation": "40.9\u00b0", "horizontal_deviation_color": "#ff3700", "heading": "143.1\u00b0", "ETA": "0:01:31"},
    {"updated": "19:24:04", "target": "New Babbage", "player_actual_container": "microTech", "target_container": "microTech", "player_x": 523.108, "player_y": 413.624, "player_z": 753.295, "player_long": "-51.67\u00b0", "player_lat": "48.48\u00b0", "player_height": "6.1 km", "player_OM1": "OM-1 : 956.939 km", "player_OM2": "OM-3 : 1376.12 km", "player_OM3": "OM-5 : 1256.377 km", "player_closest_poi": "Tears of Fire Painting : 7.658 km", "player_state_of_the_day": "Before midnight", "player_next_event": "Sunrise", "player_next_event_time": "20:30:52", "target_x": 520.723, "target_y": 419.364, "target_z": 743.655, "target_long": "-51.15\u00b0", "target_lat": "48.04\u00b0", "target_height": "0.0 km", "target_OM1": "OM-1 : 965.064 km", "target_OM2": "OM-3 : 1365.666 km", "target_OM3": "OM-5 : 1254.277 km", "target_closest_QT_beacon": "POI itself : 0 km", "target_state_of_the_day": "Before midnight", "target_next_event": "Sunrise", "target_next_event_time": "20:34:38", "distance_to_poi": "11.47 km", "distance_to_poi_color": "#00ff00", "delta_distance_to_poi": "3.137 km", "delta_distance_to_poi_color": "#00ff00", "total_deviation": "7.3\u00b0", "total_deviation_color": "#00ff00", "horizontal_deviation": "5.3\u00b0", "horizontal_deviation_color": "#00ff00", "heading": "142.0\u00b0", "ETA": "0:00:58"},
    {"updated": "19:24:59", "target": "New Babbage", "player_actual_container": "microTech", "target_container": "microTech", "player_x": 521.227, "player_y": 419.217, "player_z": 746.03, "player_long": "-51.19\u00b0", "player_lat": "48.12\u00b0", "player_height": "2.0 km", "player_OM1": "OM-1 : 963.561 km", "player_OM2": "OM-3 : 1367.262 km", "player_OM3": "OM-5 : 1255.269 km", "player_closest_poi": "Chestnuts on an open fire : 2.377 km", "player_state_of_the_day": "Before midnight", "player_next_event": "Sunrise", "player_next_event_time": "20:32:25", "target_x": 520.723, "target_y": 419.364, "target_z": 743.655, "target_long": "-51.15\u00b0", "target_lat": "48.04\u00b0", "target_height": "0.0 km", "target_OM1": "OM-1 : 965.064 km", "target_OM2": "OM-3 : 1365.666 km", "target_OM3": "OM-5 : 1254.277 km", "target_closest_QT_beacon": "POI itself : 0 km", "target_state_of_the_day": "Before midnight", "target_next_event": "Sunrise", "target_next_event_time": "20:34:38", "distance_to_poi": "2.432 km", "distance_to_poi_color": "#00ff00", "delta_distance_to_poi": "9.038 km", "delta_distance_to_poi_color": "#00ff00", "total_deviation": "33.3\u00b0", "total_deviation_color": "#ff3700", "horizontal_deviation": "23.5\u00b0", "horizontal_deviation_color": "#ff3700", "heading": "162.5\u00b0", "ETA": "0:00:15"},
    {"updated": "19:25:55", "target": "New Babbage", "player_actual_container": "microTech", "target_container": "microTech", "player_x": 521.017, "player_y": 420.102, "player_z": 745.157, "player_long": "-51.12\u00b0", "player_lat": "48.07\u00b0", "player_height": "1.6 km", "player_OM1": "OM-1 : 964.462 km", "player_OM2": "OM-3 : 1366.045 km", "player_OM3": "OM-5 : 1255.199 km", "player_closest_poi": "New Babbage : 1.699 km", "player_state_of_the_day": "Before midnight", "player_next_event": "Sunrise", "player_next_event_time": "20:32:38", "target_x": 520.723, "target_y": 419.364, "target_z": 743.655, "target_long": "-51.15\u00b0", "target_lat": "48.04\u00b0", "target_height": "0.0 km", "target_OM1": "OM-1 : 965.064 km", "target_OM2": "OM-3 : 1365.666 km", "target_OM3": "OM-5 : 1254.277 km", "target_closest_QT_beacon": "POI itself : 0 km", "target_state_of_the_day": "Before midnight", "target_next_event": "Sunrise", "target_next_event_time": "20:34:38", "distance_to_poi": "1.699 km", "distance_to_poi_color": "#00ff00", "delta_distance_to_poi": "0.734 km", "delta_distance_to_poi_color": "#00ff00", "total_deviation": "70.3\u00b0", "total_deviation_color": "#ff3700", "horizontal_deviation": "81.7\u00b0", "horizontal_deviation_color": "#ff3700", "heading": "218.6\u00b0", "ETA": "0:02:11"},
)


class TestPlanetaryNav(unittest.TestCase):

    def setUp(self):
        self.database = db.getDatabase()

    def test_new_babbage(self):
        target = self.database['Containers']['microTech'].pois['New Babbage']

        for i, (input, expected) in enumerate(zip(COORDINATES_IN, EXPECTED_DATA, strict=True)):
            with self.subTest(i=i):
                input_splitted = input.replace(":", " ").split(" ")

                input_coords = types.Vector(
                    float(input_splitted[3])/1000,
                    float(input_splitted[5])/1000,
                    float(input_splitted[7])/1000
                )
                ts = float(input_splitted[9])

                data = compute.compute_planetary_nav(input_coords, target, ts)

                if i > 0:
                    # skip first result, due to rounding and all _old_* variables
                    # in compute module being 0 on first call the 'ETA' field
                    # in the result data is subject to jitter.
                    self.assertEqual(data, expected)